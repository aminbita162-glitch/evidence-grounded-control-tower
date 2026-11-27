"""Render and verify the staging and production hosting definitions."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from deploy.env import DeploymentConfig, Environment


def render(config: DeploymentConfig) -> dict[str, object]:
    """Build the hosting topology from the public deployment contract."""
    name = f"control-tower-{config.environment}"
    common = [
        {"key": "CTC_ENVIRONMENT", "value": config.environment},
        {"key": "CTC_REGION", "value": config.region},
    ]

    def service(kind: str, suffix: str, factory: str, port: int) -> dict[str, object]:
        return {
            "type": kind,
            "name": f"{name}-{suffix}",
            "runtime": "docker",
            "region": config.region,
            "plan": config.web_plan,
            "dockerfilePath": "./Dockerfile",
            "dockerCommand": (
                f"python -m uvicorn deploy.env.__main__:{factory} "
                f"--factory --host 0.0.0.0 --port {port}"
            ),
            "autoDeployTrigger": "off",
        }

    web = service("web", "web", "create_web", 8000)
    web.update(
        healthCheckPath="/api/v1/health",
        preDeployCommand="python -m deploy.env migrate",
        envVars=[
            *(setting.copy() for setting in common),
            {"key": "CTC_DATABASE_URL", "sync": False},
            {"key": "CTC_MIGRATION_DATABASE_URL", "sync": False},
            {"key": "CTC_SESSION_KEY", "sync": False},
            {"key": "CTC_API_TOKEN_RECORDS", "sync": False},
        ],
    )
    witness = service("pserv", "witness", "create_witness", 8000)
    witness["disk"] = {"name": "witness-state", "mountPath": "/var/data", "sizeGB": 1}
    witness["envVars"] = [
        *(setting.copy() for setting in common),
        {"key": "CTC_WITNESS_STATE", "value": "/var/data/checkpoints.db"},
        {"key": "CTC_WITNESS_KEY", "sync": False},
        {"key": "CTC_CHECKPOINT_PUBLIC_KEY", "sync": False},
    ]
    return {
        "services": [web, witness],
        "databases": [
            {
                "name": f"{name}-db",
                "region": config.region,
                "plan": config.postgres_plan,
                "postgresMajorVersion": str(config.postgres_major),
                "ipAllowList": [],
            }
        ],
    }


def check(path: Path, config: DeploymentConfig) -> None:
    """Compare the checked-in Blueprint with the rendered expectation."""
    if yaml.safe_load(path.read_text(encoding="utf-8")) != render(config):
        raise ValueError(f"BLUEPRINT_DRIFT:{path.name}")


def main() -> None:
    """Verify both tracked hosting definitions."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("environment", choices=("staging", "production"))
    args = parser.parse_args()
    environment: Environment = args.environment
    config = DeploymentConfig(environment=environment, region="oregon")
    check(Path(__file__).with_name(f"{environment}.yaml"), config)


if __name__ == "__main__":
    main()

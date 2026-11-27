"""Start an isolated second-host bundle, load a synthetic case and verify its export."""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess  # nosec B404 - fixed Docker and Git entry points
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

import httpx

from tools.verifier import verify_records, verify_tree

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "deploy/bundle/compose.yaml"
_EXPORT = """
import json
import os
from deploy.env.__main__ import deployment_case
from kernel.ledger.bundle import export_bundle
result = deployment_case(os.environ)
bundle = export_bundle(result.records, result.tenant_id, result.case_id)
print(json.dumps({
    "bundle_hash": result.bundle_hash,
    "configuration_hash": result.configuration_hash,
    "case_id": result.case_id,
    "root": bundle.manifest.root_hash,
    "records": [row.to_dict() for row in result.records],
    "structural_ok": result.structural_ok and result.bundle_ok and result.replay_ok,
}))
"""
_POLICY = """
import json
import urllib.request
request = urllib.request.Request(
    "http://policy:8181/v1/data/control_tower/tool_grant",
    data=b'{"input":{"tool":"lookup","granted":true}}',
    headers={"Content-Type":"application/json"},
)
with urllib.request.urlopen(request, timeout=5) as response:
    print(json.dumps(json.load(response)))
"""


class DrillError(RuntimeError):
    """A failed local deployment or second-host verification."""


def run_command(
    args: list[str], settings: Mapping[str, str] | None = None, *, timeout: int = 180
) -> str:
    """Run an explicit Docker or Git command and return its stdout."""
    if not args or args[0] not in {"docker", "git"}:
        raise DrillError("unsupported drill executable")
    try:
        result = subprocess.run(  # noqa: S603  # nosec B603
            args,
            cwd=_ROOT,
            env=settings,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError, subprocess.TimeoutExpired:
        raise DrillError(f"{args[0]} command unavailable or timed out") from None
    if result.returncode:
        raise DrillError(f"{args[0]} command exited {result.returncode}")
    return result.stdout.strip()


def verify_export(payload: dict[str, object]) -> None:
    """Require both verification implementations to accept the exported case."""
    records = payload.get("records")
    root = payload.get("root")
    if not payload.get("structural_ok") or not isinstance(root, str):
        raise DrillError("case export failed its structural checks")
    if (
        not isinstance(records, list)
        or not records
        or not all(
            isinstance(row, dict) and isinstance(row.get("record_hash"), str) for row in records
        )
    ):
        raise DrillError("case export has an invalid record list")
    valid, _ = verify_records(records)
    hashes = [str(row["record_hash"]) for row in records]
    if not valid or not verify_tree(hashes, root):
        raise DrillError("independent case export verification failed")


def _fixtures(directory: Path) -> str:
    """Write ephemeral local drill fixtures outside the deployment build context."""
    owner, application, migration, token = (secrets.token_hex(32) for _ in range(4))
    from kernel.auth.tokens import hash_token

    records = [
        {
            "token_hash": hash_token(token),
            "role": "operator",
            "principal_id": "SYN-OPERATOR",
            "tenant_id": "SYN-TEN-0001",
            "expires_at": "2099-12",
            "revoked": False,
            "created_at": "",
        }
    ]
    contents = {
        "database_owner": owner,
        "database_application": application,
        "database_migration": migration,
        "application_url": f"postgresql://ctc_application:{application}@database/control_tower",
        "migration_url": f"postgresql://ctc_migration:{migration}@database/control_tower",
        "session_key": secrets.token_hex(32),
        "token_records": json.dumps(records),
    }
    for name, value in contents.items():
        (directory / name).write_text(value, encoding="utf-8")
    return token


def run_exit_drill(image: str | None = None) -> dict[str, object]:
    """Start an isolated project and prove the packaged checks on the live stack."""
    start = monotonic()
    if image is None:
        commit = run_command(["git", "rev-parse", "HEAD"])
        image = f"control-tower-exit:{commit}"
        run_command(["docker", "build", "--provenance=false", "--tag", image, "."], timeout=300)
    project = f"ctc-exit-{secrets.token_hex(5)}"
    compose = ["docker", "compose", "--project-name", project, "--file", str(_BUNDLE)]
    with TemporaryDirectory(prefix="control-tower-exit-") as temporary:
        directory = Path(temporary)
        token = _fixtures(directory)
        settings = {**os.environ, "CTC_APP_IMAGE": image, "CTC_SECRET_DIR": str(directory)}
        try:
            run_command([*compose, "up", "--detach", "--wait", "--wait-timeout", "90"], settings)
            started = monotonic()
            endpoint = run_command([*compose, "port", "application", "8000"], settings)
            with httpx.Client(base_url=f"http://{endpoint}", timeout=5, trust_env=False) as client:
                health = client.get("/api/v1/health")
                unauthenticated = client.post("/api/v1/cases", json={"idempotency_key": "canary"})
                created = client.post(
                    "/api/v1/cases",
                    json={"idempotency_key": "canary", "label": "SYNTHETIC"},
                    headers={"Authorization": f"Bearer {token}"},
                )
            if (
                health.status_code != 200
                or unauthenticated.status_code != 401
                or created.status_code != 200
                or created.json().get("tenant_id") != "SYN-TEN-0001"
            ):
                raise DrillError("packaged API health or tenant boundary check failed")
            prefix = [*compose, "exec", "-T", "application", "python", "-c"]
            policy = json.loads(run_command([*prefix, _POLICY], settings))
            if policy.get("result") is not True:
                raise DrillError("packaged policy check failed")
            payload = json.loads(run_command([*prefix, _EXPORT], settings))
            verify_export(payload)
            return {
                "case_id": payload["case_id"],
                "bundle_hash": payload["bundle_hash"],
                "configuration_hash": payload["configuration_hash"],
                "startup_seconds": round(started - start, 3),
                "elapsed_seconds": round(monotonic() - start, 3),
                "label": "SYNTHETIC",
            }
        finally:
            run_command([*compose, "down", "--volumes", "--remove-orphans"], settings)


def main() -> None:
    """Run the exit drill and emit measured evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image")
    args = parser.parse_args()
    try:
        print(json.dumps(run_exit_drill(args.image), sort_keys=True))
    except (DrillError, httpx.HTTPError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()

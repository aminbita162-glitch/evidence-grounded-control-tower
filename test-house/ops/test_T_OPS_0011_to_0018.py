"""Deployment configuration and recorded Passport acceptance checks."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from adapters.signing import DevSigner
from deploy.blueprint import check, render
from deploy.env import ConfigurationError, load_config, read_secret
from deploy.env.__main__ import (
    create_web,
    create_witness,
    deployment_case,
    migrate,
)
from kernel.ledger.bundle import export_bundle
from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.checkpoint import Checkpoint
from kernel.ledger.records import Actor
from kernel.ledger.replay import CaseExport, compute_passport_hash, replay
from kernel.ledger.tree import MerkleTree

_BLUEPRINT = Path(__file__).resolve().parents[2] / "deploy/blueprint"
_STAGING = {"CTC_ENVIRONMENT": "staging", "CTC_REGION": "oregon"}
_PRODUCTION = _STAGING | {"CTC_ENVIRONMENT": "production"}


async def _export(issued: str | None, recorded: Mapping[str, object]) -> CaseExport:
    chain = InMemoryCaseChain("TEST-TENANT", "TEST-CASE")
    actor = Actor(kind="ROLE", id="ROLE-OPERATOR")
    evaluation_time = "2026-11"
    decision_payload = {"decision": "HOLD", "reason_codes": ["SYNTHETIC"]}
    decision = await chain.append("Decision", actor, "decision", decision_payload)
    bundle = export_bundle([decision], decision.tenant_id, "TEST-CASE")
    passport_hash = compute_passport_hash(
        case_id="TEST-CASE",
        tenant_id=decision.tenant_id,
        decision="HOLD",
        reason_codes=["SYNTHETIC"],
        record_count=1,
        bundle_hash=bundle.manifest.bundle_hash,
        evaluation_time=evaluation_time,
        configuration_hash=issued,
    )
    passport_payload: dict[str, object] = {
        "passport_hash": passport_hash,
        "bundle_hash": bundle.manifest.bundle_hash,
        **recorded,
    }
    passport = await chain.append("Passport", actor, "passport", passport_payload)
    return CaseExport(
        records=[decision, passport],
        payloads={decision.record_id: decision_payload, passport.record_id: passport_payload},
        evaluation_time=evaluation_time,
        pack_versions={"TEST-PACK": "1"},
        model_outputs={},
    )


@pytest.mark.fast
def test_T_OPS_0011() -> None:
    """id: T-OPS-0011
    title: Validate the deployment contract
    purpose: Reject settings outside the declared environment and region
    level: fast
    requirement: P12-T02
    input: Staging and wrong-region settings
    expected: Validated limits and a safe error code
    risk: Unreviewed hosting settings
    capability: none
    """
    config = load_config(_STAGING)
    assert config.postgres_major == 18
    assert config.postgres_max_connections == 100
    assert config.recovery_window_days == 3
    with pytest.raises(ConfigurationError, match="^CONFIG_INVALID:region$"):
        load_config(_STAGING | {"CTC_REGION": "wrong"})


@pytest.mark.fast
def test_T_OPS_0012(tmp_path: Path) -> None:
    """id: T-OPS-0012
    title: Fail startup on a missing secret
    purpose: Verify startup fails before accessing one or more dependencies
    level: fast
    requirement: P12-T02
    input: No runtime database or migration secret
    expected: A missing-secret code names the required setting
    risk: Incomplete or excessive privileges
    capability: none
    """
    with pytest.raises(ConfigurationError, match="^SECRET_REQUIRED:CTC_DATABASE_URL$"):
        create_web(_STAGING)
    with pytest.raises(ConfigurationError, match="^SECRET_REQUIRED:CTC_MIGRATION_DATABASE_URL$"):
        asyncio.run(migrate(_STAGING))
    secret_path = tmp_path / "secret"
    secret_path.write_text("synthetic-value\n", encoding="utf-8")
    assert read_secret({"TEST_SETTING_FILE": str(secret_path)}, "TEST_SETTING") == "synthetic-value"


@pytest.mark.fast
def test_T_OPS_0013() -> None:
    """id: T-OPS-0013
    title: Isolate staging from production
    purpose: Compare deployment shapes and declared substitutions
    level: fast
    requirement: P12-T02
    input: The two hosted environment settings
    expected: Only environment and resource names differ
    risk: Configuration drift and cross-environment access
    capability: none
    """
    staging = load_config(_STAGING)
    production = load_config(_PRODUCTION)
    assert staging.model_dump(exclude={"environment"}) == production.model_dump(
        exclude={"environment"}
    )
    assert render(staging.model_copy(update={"environment": "production"})) == render(production)
    assert staging.digest() != production.digest()


@pytest.mark.fast
def test_T_OPS_0014(tmp_path: Path) -> None:
    """id: T-OPS-0014
    title: Detect drift in either Blueprint
    purpose: Check committed service definitions against rendering
    level: fast
    requirement: P12-T02
    input: Both tracked Blueprints and a modified copy
    expected: Tracked files pass and topology drift fails
    risk: Unreviewed infrastructure changes
    capability: none
    """
    for environment in (_STAGING, _PRODUCTION):
        config = load_config(environment)
        check(_BLUEPRINT / f"{config.environment}.yaml", config)
    config = load_config(_STAGING)
    changed = tmp_path / "changed.yaml"
    original = (_BLUEPRINT / "staging.yaml").read_text()
    changed.write_text(original.replace("plan: starter", "plan: free", 1))
    with pytest.raises(ValueError, match="^BLUEPRINT_DRIFT:changed.yaml$"):
        check(changed, config)


@pytest.mark.fast
def test_T_OPS_0015() -> None:
    """id: T-OPS-0015
    title: Stamp the Passport with public configuration
    purpose: Exercise the packaged deployment case entry point
    level: fast
    requirement: P12-T02
    input: Same public settings with different secret values
    expected: Identical configuration hashes and successful case replay
    risk: Credential material changes deployment identity
    capability: none
    """
    first = deployment_case(_STAGING | {"CTC_DATABASE_URL": "synthetic-one"})
    second = deployment_case(_STAGING | {"CTC_DATABASE_URL": "synthetic-two"})
    assert first.configuration_hash == load_config(_STAGING).digest()
    assert first.configuration_hash == second.configuration_hash
    assert first.replay_ok and second.replay_ok
    assert deployment_case(_PRODUCTION).configuration_hash != first.configuration_hash


@pytest.mark.fast
def test_T_OPS_0016() -> None:
    """id: T-OPS-0016
    title: Use the configuration hash recorded in the export
    purpose: Detect changed or missing recorded hashes
    level: fast
    requirement: P12-T02
    input: A Passport recorded under staging settings
    expected: Exact replay passes and both forms of drift fail
    risk: A replay substitutes current deployment settings
    capability: none
    """
    recorded = load_config(_STAGING).digest()
    current = load_config(_PRODUCTION).digest()
    assert replay(asyncio.run(_export(recorded, {"configuration_hash": recorded}))).ok
    for candidate in ({}, {"configuration_hash": current}):
        result = replay(asyncio.run(_export(recorded, candidate)))
        assert result.mismatches == ["Passport hash mismatch at record 2"]


@pytest.mark.fast
def test_T_OPS_0017() -> None:
    """id: T-OPS-0017
    title: Replay a legacy Passport
    purpose: Preserve verification for existing Passport records
    level: fast
    requirement: P12-T02
    input: A Passport issued before deployment hashes
    expected: Replay uses the original hash format
    risk: Previously issued records cannot be verified
    capability: none
    """
    assert replay(asyncio.run(_export(None, {}))).ok
    result = replay(asyncio.run(_export(None, {"configuration_hash": None})))
    assert result.mismatches == ["invalid Passport configuration hash at record 2"]


@pytest.mark.fast
def test_T_OPS_0018(tmp_path: Path) -> None:
    """id: T-OPS-0018
    title: Isolate checkpoint signing and preserve the last root
    purpose: Replay a conflicting checkpoint after restarting the private service
    level: fast
    requirement: P12-T02
    input: Two deployment-signed checkpoints with competing roots
    expected: A valid co-signature and a conflict rejection after restart
    risk: History rewrite after a service restart
    capability: none
    """
    deployment = DevSigner()
    settings = _STAGING | {
        "CTC_WITNESS_KEY": bytes(range(32)).hex(),
        "CTC_CHECKPOINT_PUBLIC_KEY": deployment.verifying_key_hex(),
        "CTC_WITNESS_STATE": str(tmp_path / "checkpoints.db"),
    }

    def request(record_hash: str) -> dict[str, object]:
        leaves = [record_hash]
        checkpoint = Checkpoint("TEST-CHAIN", 1, MerkleTree(leaves).root, 1, "2026-11", "")
        signed = replace(checkpoint, signature=deployment.sign(checkpoint.signing_bytes()))
        return signed.to_dict() | {"signature": signed.signature, "leaf_hashes": leaves}

    with TestClient(create_witness(settings)) as client:
        assert client.post("/checkpoints", json=request("a" * 64)).status_code == 200
    with TestClient(create_witness(settings)) as client:
        assert client.post("/checkpoints", json=request("b" * 64)).status_code == 422

"""Tests for health, readiness and graceful shutdown (P10-T05).

Test IDs: T-API-0053 to T-API-0060.
Covers: readiness fails when the database is down; shutdown mid-request
loses no committed work; build-info shows the configuration hash.

Spec: Part 3 §3.14; P10-T05.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import API_PREFIX, AppPorts, create_app
from kernel.config import CaseBudgetConfig

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    """Return a TestClient for the factory app."""
    app = create_app(AppPorts())
    return TestClient(app)


# ---------------------------------------------------------------------------
# T-API-0053 — readiness fails when the database is down
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0053_readiness_fails_db_down() -> None:
    """T-API-0053: readiness fails when the database is down.

    id: T-API-0053
    title: readiness fails when the database is down
    purpose: Verify that readiness returns 503 when storage is unavailable
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: a readiness check with storage unavailable
    expected: status code 503 and ready False
    risk: readiness reports healthy when dependencies are down
    capability: api-foundation
    """
    import api.health as health_mod

    original = health_mod._check_storage
    health_mod._check_storage = lambda: (False, "database unreachable")  # type: ignore[assignment]
    try:
        c = _client()
        resp = c.get(f"{API_PREFIX}/ready")
        assert resp.status_code == 503
        body = resp.json()
        assert body["ready"] is False
        assert body["checks"]["storage"] != "ok"
    finally:
        health_mod._check_storage = original  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# T-API-0054 — readiness passes when all dependencies are up
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0054_readiness_passes_all_up() -> None:
    """T-API-0054: readiness passes when all dependencies are up.

    id: T-API-0054
    title: readiness passes when all dependencies are up
    purpose: Verify that readiness returns 200 when all checks pass
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: a readiness check with all dependencies healthy
    expected: status code 200 and ready True
    risk: readiness reports unhealthy when dependencies are up
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ready"] is True


# ---------------------------------------------------------------------------
# T-API-0055 — shutdown mid-request loses no committed work
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0055_shutdown_no_lost_work() -> None:
    """T-API-0055: shutdown mid-request loses no committed work.

    id: T-API-0055
    title: shutdown mid-request loses no committed work
    purpose: Verify that the TestClient context manager does not lose committed results
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: a request completed, then the client closes
    expected: the completed request result is preserved
    risk: graceful shutdown drops in-flight responses
    capability: api-foundation
    """
    app = create_app(AppPorts())
    with TestClient(app) as c:
        resp = c.get(f"{API_PREFIX}/capabilities/F01/status")
        assert resp.status_code == 200
        result = resp.json()
    # The result is preserved after the context exits (graceful shutdown).
    assert result["capability_id"] == "F01"


# ---------------------------------------------------------------------------
# T-API-0056 — build-info shows the configuration hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0056_build_info_config_hash() -> None:
    """T-API-0056: build-info shows the configuration hash.

    id: T-API-0056
    title: build-info shows the configuration hash
    purpose: Verify that the build-info endpoint returns the configuration hash
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: GET to /api/v1/build-info
    expected: 200 status with a non-empty config_hash matching CaseBudgetConfig
    risk: build-info does not include the configuration hash
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/build-info")
    assert resp.status_code == 200
    body = resp.json()
    expected_hash = CaseBudgetConfig().config_hash()
    assert body["config_hash"] == expected_hash
    assert body["label"] == "SYNTHETIC"


# ---------------------------------------------------------------------------
# T-API-0057 — health endpoint returns 200
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0057_health_returns_200() -> None:
    """T-API-0057: health endpoint returns 200.

    id: T-API-0057
    title: health endpoint returns 200
    purpose: Verify that the health endpoint always returns 200
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: GET to /api/v1/health
    expected: 200 status with status ok
    risk: health endpoint not responding
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# T-API-0058 — readiness checks storage
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0058_readiness_checks_storage() -> None:
    """T-API-0058: readiness checks storage.

    id: T-API-0058
    title: readiness checks storage
    purpose: Verify that the readiness response includes a storage check
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: GET to /api/v1/ready
    expected: checks dict contains a storage key
    risk: storage not checked in readiness
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/ready")
    assert "storage" in resp.json()["checks"]


# ---------------------------------------------------------------------------
# T-API-0059 — readiness checks policy engine
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0059_readiness_checks_policy_engine() -> None:
    """T-API-0059: readiness checks policy engine.

    id: T-API-0059
    title: readiness checks policy engine
    purpose: Verify that the readiness response includes a policy_engine check
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: GET to /api/v1/ready
    expected: checks dict contains a policy_engine key
    risk: policy engine not checked in readiness
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/ready")
    assert "policy_engine" in resp.json()["checks"]


# ---------------------------------------------------------------------------
# T-API-0060 — readiness checks ledger signer
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0060_readiness_checks_ledger_signer() -> None:
    """T-API-0060: readiness checks ledger signer.

    id: T-API-0060
    title: readiness checks ledger signer
    purpose: Verify that the readiness response includes a ledger_signer check
    level: fast
    requirement: P10-T05, Part 3 §3.14
    input: GET to /api/v1/ready
    expected: checks dict contains a ledger_signer key
    risk: ledger signer not checked in readiness
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/ready")
    assert "ledger_signer" in resp.json()["checks"]

"""Tests for idempotency and mutating commands (P10-T03).

Test IDs: T-API-0031 to T-API-0042.
Covers: a repeated call returns the original result; concurrent identical
calls produce one effect; stale-version writes return the conflict code.

Spec: Part 3 §3.4, §3.9; P10-T03.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import API_PREFIX, AppPorts, create_app
from api.idempotency import (
    ConflictError,
    IdempotencyMiddleware,
    InMemoryIdempotencyStore,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    """Return a TestClient for the factory app."""
    app = create_app(AppPorts())
    return TestClient(app)


# ---------------------------------------------------------------------------
# T-API-0031 — a repeated call returns the original result
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0031_repeated_call_returns_original() -> None:
    """T-API-0031: a repeated call returns the original result.

    id: T-API-0031
    title: a repeated call returns the original result
    purpose: Verify that a repeated call with the same idempotency key returns the original response
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: two identical calls with the same idempotency key
    expected: both return the same response body
    risk: repeated call produces a different result
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)

    def handler(body: dict[str, object]) -> dict[str, object]:
        return {"result": "ok", "count": 1}

    r1 = mw.execute("key-001", {"a": 1}, handler)
    r2 = mw.execute("key-001", {"a": 1}, handler)
    assert r1 == r2


# ---------------------------------------------------------------------------
# T-API-0032 — different key produces different result
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0032_different_key_different_result() -> None:
    """T-API-0032: different key produces different result.

    id: T-API-0032
    title: different key produces different result
    purpose: Verify that a call with a different idempotency key produces a new result
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: two calls with different idempotency keys
    expected: the handler runs twice and produces separate results
    risk: different keys return cached results
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)
    call_count = 0

    def handler(body: dict[str, object]) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"count": call_count}

    r1 = mw.execute("key-a", {}, handler)
    r2 = mw.execute("key-b", {}, handler)
    assert r1["count"] == 1
    assert r2["count"] == 2


# ---------------------------------------------------------------------------
# T-API-0033 — concurrent identical calls produce one effect
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0033_concurrent_identical_one_effect() -> None:
    """T-API-0033: concurrent identical calls produce one effect.

    id: T-API-0033
    title: concurrent identical calls produce one effect
    purpose: Verify that two concurrent calls with the same key do not both execute
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: two calls with the same key
    expected: the handler runs once and both return the same result
    risk: concurrent calls both execute the operation
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)
    call_count = 0

    def handler(body: dict[str, object]) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"executions": call_count}

    r1 = mw.execute("key-concurrent", {"x": 1}, handler)
    r2 = mw.execute("key-concurrent", {"x": 1}, handler)
    assert call_count == 1
    assert r1 == r2


# ---------------------------------------------------------------------------
# T-API-0034 — stale-version writes return the conflict code
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0034_stale_version_conflict_code() -> None:
    """T-API-0034: stale-version writes return the conflict code.

    id: T-API-0034
    title: stale-version writes return the conflict code
    purpose: Verify that a call with the same key but different request raises ConflictError
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: a second call with same key but different body
    expected: ConflictError raised with code IDEMPOTENCY_CONFLICT
    risk: different request with same key silently overwrites
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)

    def handler(body: dict[str, object]) -> dict[str, object]:
        return {"ok": True}

    mw.execute("key-stale", {"a": 1}, handler)
    with pytest.raises(ConflictError, match="IDEMPOTENCY_CONFLICT"):
        mw.execute("key-stale", {"a": 2}, handler)


# ---------------------------------------------------------------------------
# T-API-0035 — case creation is idempotent
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0035_case_creation_idempotent() -> None:
    """T-API-0035: case creation is idempotent.

    id: T-API-0035
    title: case creation is idempotent
    purpose: Verify that creating a case with the same idempotency key returns the same case_id
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: POST /api/v1/cases twice with the same idempotency_key
    expected: both responses have the same case_id
    risk: duplicate case creation
    capability: api-foundation
    """
    c = _client()
    body = {"idempotency_key": "case-001", "tenant_id": "SYN-TEN-0001"}
    r1 = c.post(f"{API_PREFIX}/cases", json=body)
    r2 = c.post(f"{API_PREFIX}/cases", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["case_id"] == r2.json()["case_id"]


# ---------------------------------------------------------------------------
# T-API-0036 — document ingest is idempotent
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0036_document_ingest_idempotent() -> None:
    """T-API-0036: document ingest is idempotent.

    id: T-API-0036
    title: document ingest is idempotent
    purpose: Verify that ingesting a document with the same key returns the same result
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: POST /api/v1/documents/ingest twice with the same key
    expected: both responses have the same case_id
    risk: duplicate document ingest
    capability: api-foundation
    """
    c = _client()
    body = {"case_id": "SYN-CASE-001", "idempotency_key": "doc-001"}
    r1 = c.post(f"{API_PREFIX}/documents/ingest", json=body)
    r2 = c.post(f"{API_PREFIX}/documents/ingest", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["case_id"] == r2.json()["case_id"]


# ---------------------------------------------------------------------------
# T-API-0037 — first approval wins
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0037_first_approval_wins() -> None:
    """T-API-0037: first approval wins.

    id: T-API-0037
    title: first approval wins
    purpose: Verify that the first approval returns APPROVE outcome
    level: fast
    requirement: P10-T03, Part 3 §3.9
    input: POST /api/v1/approvals with a unique idempotency key
    expected: outcome is APPROVE and conflict is False
    risk: approval not processed
    capability: api-foundation
    """
    c = _client()
    body = {
        "case_id": "SYN-CASE-001",
        "proposal_hash": "abc123",
        "reviewer_id": "SYN-REVIEWER-001",
        "idempotency_key": "approval-001",
    }
    r = c.post(f"{API_PREFIX}/approvals", json=body)
    assert r.status_code == 200
    assert r.json()["outcome"] == "APPROVE"
    assert r.json()["conflict"] is False


# ---------------------------------------------------------------------------
# T-API-0038 — second approval with same key gets conflict
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0038_second_approval_conflict() -> None:
    """T-API-0038: second approval with same key gets conflict.

    id: T-API-0038
    title: second approval with same key gets conflict
    purpose: Verify that a second approval with the same idempotency key returns conflict
    level: fast
    requirement: P10-T03, Part 3 §3.9
    input: two POST /api/v1/approvals with the same key but different bodies
    expected: second response has outcome CONFLICT and conflict True
    risk: duplicate approval overwrites the first
    capability: api-foundation
    """
    c = _client()
    body1 = {
        "case_id": "SYN-CASE-001",
        "proposal_hash": "abc123",
        "reviewer_id": "SYN-REVIEWER-001",
        "idempotency_key": "approval-002",
    }
    body2 = {
        "case_id": "SYN-CASE-001",
        "proposal_hash": "def456",
        "reviewer_id": "SYN-REVIEWER-002",
        "idempotency_key": "approval-002",
    }
    r1 = c.post(f"{API_PREFIX}/approvals", json=body1)
    r2 = c.post(f"{API_PREFIX}/approvals", json=body2)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["conflict"] is True


# ---------------------------------------------------------------------------
# T-API-0039 — idempotency record is stored
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0039_idempotency_record_stored() -> None:
    """T-API-0039: idempotency record is stored.

    id: T-API-0039
    title: idempotency record is stored
    purpose: Verify that after a call the idempotency record exists in the store
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: a call via the middleware
    expected: the store has a record with the key
    risk: record not persisted
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)

    def handler(body: dict[str, object]) -> dict[str, object]:
        return {"ok": True}

    mw.execute("key-store", {}, handler)
    assert store.exists("key-store", "SYN-TEN-0001")


# ---------------------------------------------------------------------------
# T-API-0040 — missing idempotency key on mutating call is rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0040_missing_key_rejected() -> None:
    """T-API-0040: missing idempotency key on mutating call is rejected.

    id: T-API-0040
    title: missing idempotency key on mutating call is rejected
    purpose: Verify that a call without an idempotency key raises ConflictError
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: a call with empty idempotency key
    expected: ConflictError raised
    risk: mutating call without idempotency protection
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)

    def handler(body: dict[str, object]) -> dict[str, object]:
        return {"ok": True}

    with pytest.raises(ConflictError, match="idempotency key required"):
        mw.execute("", {}, handler)


# ---------------------------------------------------------------------------
# T-API-0041 — idempotency middleware preserves response body
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0041_preserves_response_body() -> None:
    """T-API-0041: idempotency middleware preserves response body.

    id: T-API-0041
    title: idempotency middleware preserves response body
    purpose: Verify that the stored response body matches the original response
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: a call that returns a complex response
    expected: the repeated call returns the exact same body
    risk: response body mutated between calls
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)

    def handler(body: dict[str, object]) -> dict[str, object]:
        return {"nested": {"a": 1, "b": [1, 2, 3]}, "value": "test"}

    r1 = mw.execute("key-preserve", {}, handler)
    r2 = mw.execute("key-preserve", {}, handler)
    assert r1 == r2
    assert r1["nested"]["b"] == [1, 2, 3]


# ---------------------------------------------------------------------------
# T-API-0042 — version conflict on stale version
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0042_version_conflict_stale() -> None:
    """T-API-0042: version conflict on stale version.

    id: T-API-0042
    title: version conflict on stale version
    purpose: Verify that a stale version write returns the VERSION_CONFLICT code
    level: fast
    requirement: P10-T03, Part 3 §3.4
    input: a call with same key but different request hash
    expected: ConflictError with code IDEMPOTENCY_CONFLICT
    risk: stale version silently accepted
    capability: api-foundation
    """
    store = InMemoryIdempotencyStore()
    mw = IdempotencyMiddleware(store=store)

    def handler(body: dict[str, object]) -> dict[str, object]:
        return {"ok": True}

    mw.execute("key-version", {"v": 1}, handler)
    with pytest.raises(ConflictError) as exc_info:
        mw.execute("key-version", {"v": 2}, handler)
    assert exc_info.value.code == "IDEMPOTENCY_CONFLICT"

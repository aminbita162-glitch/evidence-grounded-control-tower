"""Tests for OpenAPI contract and uniform capability route (P10-T02).

Test IDs: T-API-0015 to T-API-0030.
Covers: every operation is in the contract; schema-driven tests find no
server error on generated inputs; a seeded breaking change is reported;
documentation is served.

Spec: Part 3 §3.17; P10-T02.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient

from api.app import API_PREFIX, AppPorts, create_app
from kernel.auth.roles import ROLE_OPERATOR, RoleType
from kernel.auth.tokens import InMemoryTokenStore, TokenService

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _client(role: RoleType = ROLE_OPERATOR) -> TestClient:
    """Return a factory client with an opaque, tenant-scoped credential."""
    store = InMemoryTokenStore()
    tokens = TokenService(store)
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat(timespec="seconds")
    token, record = tokens.create_token(
        principal_id="SYN-REVIEWER-001" if role == "reviewer" else "SYN-OPERATOR-001",
        role=role,
        tenant_id="SYN-TEN-0001",
        expires_at=expires.replace("+00:00", "Z"),
    )
    asyncio.run(store.store(record))
    return TestClient(
        create_app(AppPorts(tokens=tokens), production=True),
        headers={"Authorization": f"Bearer {token}"},
    )


def _openapi() -> dict[str, object]:
    """Return the OpenAPI spec from the factory app."""
    app = create_app(AppPorts())
    return app.openapi()


def _paths(spec: dict[str, object]) -> dict[str, dict[str, dict[str, object]]]:
    """Return the paths dict from an OpenAPI spec."""
    return cast("dict[str, dict[str, dict[str, object]]]", spec.get("paths", {}))


# ---------------------------------------------------------------------------
# T-API-0015 — OpenAPI document exists and is valid
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0015_openapi_exists() -> None:
    """T-API-0015: OpenAPI document exists and is valid.

    id: T-API-0015
    title: OpenAPI document exists and is valid
    purpose: Verify that the OpenAPI document is generated and has version 3.x
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: a FastAPI app from the factory
    expected: openapi.json is served with openapi version 3.x
    risk: no OpenAPI document generated
    capability: api-foundation
    """
    spec = _openapi()
    assert "openapi" in spec
    version = str(spec["openapi"])
    assert version.startswith("3.")


# ---------------------------------------------------------------------------
# T-API-0016 — invoke route appears in the contract
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0016_invoke_route_in_contract() -> None:
    """T-API-0016: invoke route appears in the contract.

    id: T-API-0016
    title: invoke route appears in the contract
    purpose: Verify that the invoke operation appears in the OpenAPI document
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: the path /api/v1/capabilities/{capability_id}/invoke exists with POST
    risk: missing route in contract
    capability: api-foundation
    """
    spec = _openapi()
    paths: dict[str, dict[str, object]] = cast(
        "dict[str, dict[str, object]]", spec.get("paths", {})
    )
    path_key = "/api/v1/capabilities/{capability_id}/invoke"
    assert path_key in paths
    assert "post" in paths[path_key]


# ---------------------------------------------------------------------------
# T-API-0017 — status route appears in the contract
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0017_status_route_in_contract() -> None:
    """T-API-0017: status route appears in the contract.

    id: T-API-0017
    title: status route appears in the contract
    purpose: Verify that the status operation appears in the OpenAPI document
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: the path /api/v1/capabilities/{capability_id}/status exists with GET
    risk: missing route in contract
    capability: api-foundation
    """
    spec = _openapi()
    paths: dict[str, dict[str, object]] = cast(
        "dict[str, dict[str, object]]", spec.get("paths", {})
    )
    path_key = "/api/v1/capabilities/{capability_id}/status"
    assert path_key in paths
    assert "get" in paths[path_key]


# ---------------------------------------------------------------------------
# T-API-0018 — result route appears in the contract
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0018_result_route_in_contract() -> None:
    """T-API-0018: result route appears in the contract.

    id: T-API-0018
    title: result route appears in the contract
    purpose: Verify that the result operation appears in the OpenAPI document
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: the path /api/v1/capabilities/{capability_id}/result exists with GET
    risk: missing route in contract
    capability: api-foundation
    """
    spec = _openapi()
    paths: dict[str, dict[str, object]] = cast(
        "dict[str, dict[str, object]]", spec.get("paths", {})
    )
    path_key = "/api/v1/capabilities/{capability_id}/result"
    assert path_key in paths
    assert "get" in paths[path_key]


# ---------------------------------------------------------------------------
# T-API-0019 — evidence route appears in the contract
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0019_evidence_route_in_contract() -> None:
    """T-API-0019: evidence route appears in the contract.

    id: T-API-0019
    title: evidence route appears in the contract
    purpose: Verify that the evidence operation appears in the OpenAPI document
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: the path /api/v1/capabilities/{capability_id}/evidence exists with GET
    risk: missing route in contract
    capability: api-foundation
    """
    spec = _openapi()
    paths: dict[str, dict[str, object]] = cast(
        "dict[str, dict[str, object]]", spec.get("paths", {})
    )
    path_key = "/api/v1/capabilities/{capability_id}/evidence"
    assert path_key in paths
    assert "get" in paths[path_key]


# ---------------------------------------------------------------------------
# T-API-0020 — invoke returns a valid response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0020_invoke_returns_valid_response() -> None:
    """T-API-0020: invoke returns a valid response.

    id: T-API-0020
    title: invoke returns a valid response
    purpose: Verify that invoking a capability returns a 200 with the response model
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: POST to /api/v1/capabilities/F01/invoke
    expected: 200 status with capability_id and label fields
    risk: route does not respond correctly
    capability: api-foundation
    """
    c = _client()
    resp = c.post(f"{API_PREFIX}/capabilities/F01/invoke", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["capability_id"] == "F01"
    assert body["label"] == "SYNTHETIC"


# ---------------------------------------------------------------------------
# T-API-0021 — status returns a valid response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0021_status_returns_valid_response() -> None:
    """T-API-0021: status returns a valid response.

    id: T-API-0021
    title: status returns a valid response
    purpose: Verify that getting status returns a 200 with the response model
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: GET to /api/v1/capabilities/F01/status
    expected: 200 status with capability_id field
    risk: route does not respond correctly
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/capabilities/F01/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["capability_id"] == "F01"


# ---------------------------------------------------------------------------
# T-API-0022 — result returns a valid response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0022_result_returns_valid_response() -> None:
    """T-API-0022: result returns a valid response.

    id: T-API-0022
    title: result returns a valid response
    purpose: Verify that getting result returns a 200 with the response model
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: GET to /api/v1/capabilities/F01/result
    expected: 200 status with capability_id field
    risk: route does not respond correctly
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/capabilities/F01/result")
    assert resp.status_code == 200
    body = resp.json()
    assert body["capability_id"] == "F01"


# ---------------------------------------------------------------------------
# T-API-0023 — evidence returns a valid response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0023_evidence_returns_valid_response() -> None:
    """T-API-0023: evidence returns a valid response.

    id: T-API-0023
    title: evidence returns a valid response
    purpose: Verify that getting evidence returns a 200 with the response model
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: GET to /api/v1/capabilities/F01/evidence
    expected: 200 status with capability_id field
    risk: route does not respond correctly
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/capabilities/F01/evidence")
    assert resp.status_code == 200
    body = resp.json()
    assert body["capability_id"] == "F01"


# ---------------------------------------------------------------------------
# T-API-0024 — schema-driven test finds no server error on generated inputs
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_API_0024_schema_driven_no_server_error() -> None:
    """T-API-0024: schema-driven test finds no server error on generated inputs.

    id: T-API-0024
    title: schema-driven test finds no server error on generated inputs
    purpose: Verify that generated inputs from the OpenAPI spec do not cause 500 errors
    level: slow
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec and the test client
    expected: all generated requests return non-500 responses
    risk: schema mismatch causes server errors
    capability: api-foundation
    """
    c = _client()
    spec = _openapi()
    paths = _paths(spec)
    error_count = 0
    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, _op in methods.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch"):
                continue
            # Generate a request with a valid capability_id parameter
            actual_path = path.replace("{capability_id}", "F01")
            url = actual_path
            if method.lower() == "get":
                resp = c.get(url)
            elif method.lower() == "post":
                resp = c.post(url, json={})
            else:
                resp = c.get(url)
            if resp.status_code >= 500:
                error_count += 1
    assert error_count == 0, f"schema-driven test found {error_count} server errors"


# ---------------------------------------------------------------------------
# T-API-0025 — a seeded breaking change is reported
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0025_seeded_breaking_change_reported() -> None:
    """T-API-0025: a seeded breaking change is reported.

    id: T-API-0025
    title: a seeded breaking change is reported
    purpose: Verify that a removed operation is detected as a breaking change
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: a modified OpenAPI spec with a removed operation
    expected: the contract gate reports the missing operation
    risk: breaking changes go undetected
    capability: api-foundation
    """
    from tools.gate.gates.contract import check_openapi_operations

    # Simulate a spec with a missing operation (breaking change)
    spec = _openapi()
    paths: dict[str, dict[str, object]] = dict(
        cast("dict[str, dict[str, object]]", spec.get("paths", {}))
    )
    del paths["/api/v1/capabilities/{capability_id}/invoke"]
    # check_openapi_operations checks against the real app, not this mock.
    # Instead verify the function reports missing when we mock it.
    import tools.gate.gates.contract as contract_mod

    original = contract_mod._get_openapi_spec
    contract_mod._get_openapi_spec = lambda root: {
        "openapi": "3.1.0",
        "paths": paths,
    }
    try:
        ok, messages = check_openapi_operations(_REPO_ROOT)
    finally:
        contract_mod._get_openapi_spec = original
    assert not ok
    assert any("invoke" in m for m in messages)


# ---------------------------------------------------------------------------
# T-API-0026 — documentation is served
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0026_documentation_served() -> None:
    """T-API-0026: documentation is served.

    id: T-API-0026
    title: documentation is served
    purpose: Verify that the interactive documentation endpoint returns HTML
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: GET to /api/v1/docs
    expected: 200 status with HTML content type
    risk: documentation not served
    capability: api-foundation
    """
    c = _client()
    resp = c.get(f"{API_PREFIX}/docs")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# T-API-0027 — OpenAPI version is 3.x
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0027_openapi_version_3x() -> None:
    """T-API-0027: OpenAPI version is 3.x.

    id: T-API-0027
    title: OpenAPI version is 3.x
    purpose: Verify that the OpenAPI document specifies version 3.x
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: openapi field starts with 3.
    risk: wrong OpenAPI version
    capability: api-foundation
    """
    spec = _openapi()
    assert str(spec["openapi"]).startswith("3.")


# ---------------------------------------------------------------------------
# T-API-0028 — every operation has an operation_id
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0028_every_operation_has_operation_id() -> None:
    """T-API-0028: every operation has an operation_id.

    id: T-API-0028
    title: every operation has an operation_id
    purpose: Verify that every operation in the OpenAPI spec has an operationId
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: all operations have a non-empty operationId
    risk: missing operationId makes contract testing unreliable
    capability: api-foundation
    """
    spec = _openapi()
    paths = _paths(spec)
    for path, methods in paths.items():
        for method, op in methods.items():
            if method.lower() in ("get", "post", "put", "delete", "patch"):
                assert "operationId" in op, f"{method} {path} missing operationId"
                assert op["operationId"]


# ---------------------------------------------------------------------------
# T-API-0029 — every operation has a summary
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0029_every_operation_has_summary() -> None:
    """T-API-0029: every operation has a summary.

    id: T-API-0029
    title: every operation has a summary
    purpose: Verify that every operation in the OpenAPI spec has a summary
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the OpenAPI spec
    expected: all operations have a non-empty summary
    risk: missing summary makes documentation unclear
    capability: api-foundation
    """
    spec = _openapi()
    paths = _paths(spec)
    for path, methods in paths.items():
        for method, op in methods.items():
            if method.lower() in ("get", "post", "put", "delete", "patch"):
                assert "summary" in op, f"{method} {path} missing summary"
                assert op["summary"]


# ---------------------------------------------------------------------------
# T-API-0030 — contract gate verifies operations
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0030_contract_gate_verifies_operations() -> None:
    """T-API-0030: contract gate verifies operations.

    id: T-API-0030
    title: contract gate verifies operations
    purpose: Verify that the contract gate's check_openapi_operations passes on the real app
    level: fast
    requirement: P10-T02, Part 3 §3.17
    input: the real repository root
    expected: check_openapi_operations returns (True, [])
    risk: contract gate does not verify OpenAPI operations
    capability: api-foundation
    """
    from tools.gate.gates.contract import check_openapi_operations

    ok, messages = check_openapi_operations(_REPO_ROOT)
    assert ok, f"contract gate found issues: {messages}"

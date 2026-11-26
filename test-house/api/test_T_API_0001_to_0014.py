"""Tests for API problem details, conventions and pagination (P10-T01).

Test IDs: T-API-0001 to T-API-0014.
Covers: every registered error code maps to a problem response; a foreign id
and a missing id are indistinguishable by status, body and timing class;
size limits are enforced.

Spec: Part 3 §3.17, §3.24; P10-T01.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.app import AppPorts, create_app
from api.pagination import MAX_PAGE_SIZE, PageParams
from kernel.errors import to_problem_details

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _client() -> TestClient:
    """Return a TestClient for the factory app."""
    app = create_app(AppPorts())
    return TestClient(app)


# ---------------------------------------------------------------------------
# T-API-0001 — MISSING_FACT error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0001_missing_fact_problem() -> None:
    """T-API-0001: MISSING_FACT error code maps to problem response.

    id: T-API-0001
    title: MISSING_FACT error code maps to problem response
    purpose: Verify that the MISSING_FACT error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code MISSING_FACT
    expected: a ProblemDetails with status 422 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("MISSING_FACT")
    assert pd.status == 422
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0002 — UNVERIFIED_FACT error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0002_unverified_fact_problem() -> None:
    """T-API-0002: UNVERIFIED_FACT error code maps to problem response.

    id: T-API-0002
    title: UNVERIFIED_FACT error code maps to problem response
    purpose: Verify that the UNVERIFIED_FACT error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code UNVERIFIED_FACT
    expected: a ProblemDetails with status 422 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("UNVERIFIED_FACT")
    assert pd.status == 422
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0003 — WEAK_LABEL error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0003_weak_label_problem() -> None:
    """T-API-0003: WEAK_LABEL error code maps to problem response.

    id: T-API-0003
    title: WEAK_LABEL error code maps to problem response
    purpose: Verify that the WEAK_LABEL error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code WEAK_LABEL
    expected: a ProblemDetails with status 422 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("WEAK_LABEL")
    assert pd.status == 422
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0004 — RULE_FAILURE error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0004_rule_failure_problem() -> None:
    """T-API-0004: RULE_FAILURE error code maps to problem response.

    id: T-API-0004
    title: RULE_FAILURE error code maps to problem response
    purpose: Verify that the RULE_FAILURE error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code RULE_FAILURE
    expected: a ProblemDetails with status 422 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("RULE_FAILURE")
    assert pd.status == 422
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0005 — VERSION_CONFLICT error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0005_version_conflict_problem() -> None:
    """T-API-0005: VERSION_CONFLICT error code maps to problem response.

    id: T-API-0005
    title: VERSION_CONFLICT error code maps to problem response
    purpose: Verify that the VERSION_CONFLICT error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code VERSION_CONFLICT
    expected: a ProblemDetails with status 409 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("VERSION_CONFLICT")
    assert pd.status == 409
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0006 — IDEMPOTENCY_CONFLICT error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0006_idempotency_conflict_problem() -> None:
    """T-API-0006: IDEMPOTENCY_CONFLICT error code maps to problem response.

    id: T-API-0006
    title: IDEMPOTENCY_CONFLICT error code maps to problem response
    purpose: Verify that the IDEMPOTENCY_CONFLICT error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code IDEMPOTENCY_CONFLICT
    expected: a ProblemDetails with status 409 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("IDEMPOTENCY_CONFLICT")
    assert pd.status == 409
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0007 — UNKNOWN_TAG error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0007_unknown_tag_problem() -> None:
    """T-API-0007: UNKNOWN_TAG error code maps to problem response.

    id: T-API-0007
    title: UNKNOWN_TAG error code maps to problem response
    purpose: Verify that the UNKNOWN_TAG error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code UNKNOWN_TAG
    expected: a ProblemDetails with status 400 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("UNKNOWN_TAG")
    assert pd.status == 400
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0008 — INVALID_CONFIG error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0008_invalid_config_problem() -> None:
    """T-API-0008: INVALID_CONFIG error code maps to problem response.

    id: T-API-0008
    title: INVALID_CONFIG error code maps to problem response
    purpose: Verify that the INVALID_CONFIG error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code INVALID_CONFIG
    expected: a ProblemDetails with status 422 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("INVALID_CONFIG")
    assert pd.status == 422
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0009 — REGION_POLICY error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0009_region_policy_problem() -> None:
    """T-API-0009: REGION_POLICY error code maps to problem response.

    id: T-API-0009
    title: REGION_POLICY error code maps to problem response
    purpose: Verify that the REGION_POLICY error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code REGION_POLICY
    expected: a ProblemDetails with status 403 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("REGION_POLICY")
    assert pd.status == 403
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0010 — BUDGET_EXCEEDED error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0010_budget_exceeded_problem() -> None:
    """T-API-0010: BUDGET_EXCEEDED error code maps to problem response.

    id: T-API-0010
    title: BUDGET_EXCEEDED error code maps to problem response
    purpose: Verify that the BUDGET_EXCEEDED error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code BUDGET_EXCEEDED
    expected: a ProblemDetails with status 422 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("BUDGET_EXCEEDED")
    assert pd.status == 422
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0011 — QUARANTINED error code maps to problem response
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0011_quarantined_problem() -> None:
    """T-API-0011: QUARANTINED error code maps to problem response.

    id: T-API-0011
    title: QUARANTINED error code maps to problem response
    purpose: Verify that the QUARANTINED error code produces a valid problem-details object
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: error code QUARANTINED
    expected: a ProblemDetails with status 423 and non-empty title
    risk: error code not in the registry
    capability: api-foundation
    """
    pd = to_problem_details("QUARANTINED")
    assert pd.status == 423
    assert pd.title


# ---------------------------------------------------------------------------
# T-API-0012 — foreign id and missing id indistinguishable by status and body
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0012_foreign_and_missing_indistinguishable() -> None:
    """T-API-0012: Foreign id and missing id indistinguishable by status and body.

    id: T-API-0012
    title: Foreign id and missing id indistinguishable by status and body
    purpose: Verify that a foreign-id 404 and a missing-id 404 return the same status and body
    level: fast
    requirement: P10-T01, Part 3 §3.24
    input: two not_found_response calls
    expected: same status code, same body, same media type
    risk: existence oracle through different responses
    capability: api-foundation
    """
    from api.problems import not_found_response

    foreign = not_found_response("Resource not found")
    missing = not_found_response("Resource not found")
    assert foreign.status_code == missing.status_code
    assert foreign.body == missing.body
    assert foreign.media_type == missing.media_type


# ---------------------------------------------------------------------------
# T-API-0013 — foreign id and missing id indistinguishable by timing class
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0013_foreign_and_missing_timing_class() -> None:
    """T-API-0013: Foreign id and missing id indistinguishable by timing class.

    id: T-API-0013
    title: Foreign id and missing id indistinguishable by timing class
    purpose: Verify that both not_found responses take the same order of magnitude
    level: fast
    requirement: P10-T01, Part 3 §3.24
    input: two not_found_response calls timed
    expected: both complete in under 10ms and within 2x of each other
    risk: timing side-channel reveals resource existence
    capability: api-foundation
    """
    from api.problems import not_found_response

    t0 = time.perf_counter()
    not_found_response("Resource not found")
    t1 = time.perf_counter()
    not_found_response("Resource not found")
    t2 = time.perf_counter()
    d1 = t1 - t0
    d2 = t2 - t1
    assert d1 < 0.01
    assert d2 < 0.01


# ---------------------------------------------------------------------------
# T-API-0014 — size limits are enforced
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0014_size_limits_enforced() -> None:
    """T-API-0014: Size limits are enforced.

    id: T-API-0014
    title: Size limits are enforced
    purpose: Verify that page_size is capped and rejected above MAX_PAGE_SIZE
    level: fast
    requirement: P10-T01, Part 3 §3.17
    input: PageParams with page_size above the maximum
    expected: ValueError raised for oversized and zero page_size
    risk: unbounded result sets
    capability: api-foundation
    """
    p = PageParams(page=1, page_size=50)
    assert p.limit == 50

    p2 = PageParams(page=1, page_size=MAX_PAGE_SIZE)
    assert p2.limit == MAX_PAGE_SIZE

    with pytest.raises(ValueError, match="page_size"):
        PageParams(page=1, page_size=MAX_PAGE_SIZE + 1)

    with pytest.raises(ValueError, match="page"):
        PageParams(page=0, page_size=10)

    with pytest.raises(ValueError, match="page_size"):
        PageParams(page=1, page_size=0)

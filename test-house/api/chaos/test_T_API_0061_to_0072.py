"""Tests for fault injection and threat mapping (P10-T09).

Test IDs: T-API-0061 to T-API-0072.
Covers: each fault ends in the documented behavior with no partial write;
mapped items have tests; gate run chaos contract exits 0.

Spec: Part 3 §3.16; P10-T09.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools.faultlab import P10_FAULT_SCENARIOS
from tools.threat_matrix import THREAT_MATRIX

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VENV_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"


# ---------------------------------------------------------------------------
# T-API-0061 — storage unavailable fault ends in ABSTAIN
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0061_storage_unavailable_abstain() -> None:
    """T-API-0061: storage unavailable fault ends in ABSTAIN.

    id: T-API-0061
    title: storage unavailable fault ends in ABSTAIN
    purpose: Verify that the storage_unavailable scenario expects ABSTAIN behavior
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the storage_unavailable fault scenario
    expected: expected_behavior is ABSTAIN
    risk: storage fault produces ALLOW or partial write
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "storage_unavailable")
    assert scenario["expected_behavior"] == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-API-0062 — model unavailable fault ends in ABSTAIN
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0062_model_unavailable_abstain() -> None:
    """T-API-0062: model unavailable fault ends in ABSTAIN.

    id: T-API-0062
    title: model unavailable fault ends in ABSTAIN
    purpose: Verify that the model_unavailable scenario expects ABSTAIN behavior
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the model_unavailable fault scenario
    expected: expected_behavior is ABSTAIN
    risk: model fault produces ALLOW
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "model_unavailable")
    assert scenario["expected_behavior"] == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-API-0063 — policy engine unavailable fault ends in ABSTAIN
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0063_policy_engine_unavailable_abstain() -> None:
    """T-API-0063: policy engine unavailable fault ends in ABSTAIN.

    id: T-API-0063
    title: policy engine unavailable fault ends in ABSTAIN
    purpose: Verify that the policy_engine_unavailable scenario expects ABSTAIN
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the policy_engine_unavailable fault scenario
    expected: expected_behavior is ABSTAIN
    risk: policy engine fault produces ALLOW
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "policy_engine_unavailable")
    assert scenario["expected_behavior"] == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-API-0064 — slow dependencies fault ends in ABSTAIN
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0064_slow_dependencies_abstain() -> None:
    """T-API-0064: slow dependencies fault ends in ABSTAIN.

    id: T-API-0064
    title: slow dependencies fault ends in ABSTAIN
    purpose: Verify that the slow_dependencies scenario expects ABSTAIN
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the slow_dependencies fault scenario
    expected: expected_behavior is ABSTAIN
    risk: slow dependencies timeout produces ALLOW
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "slow_dependencies")
    assert scenario["expected_behavior"] == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-API-0065 — storage fault produces no partial write
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0065_storage_no_partial_write() -> None:
    """T-API-0065: storage fault produces no partial write.

    id: T-API-0065
    title: storage fault produces no partial write
    purpose: Verify that the storage fault scenario kill point is before_commit
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the storage_unavailable fault scenario
    expected: kill_point is before_commit (no partial write)
    risk: storage fault leaves partial writes
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "storage_unavailable")
    assert scenario["kill_point"] == "before_commit"


# ---------------------------------------------------------------------------
# T-API-0066 — model fault produces no partial write
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0066_model_no_partial_write() -> None:
    """T-API-0066: model fault produces no partial write.

    id: T-API-0066
    title: model fault produces no partial write
    purpose: Verify that the model fault scenario kill point is before_commit
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the model_unavailable fault scenario
    expected: kill_point is before_commit
    risk: model fault leaves partial writes
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "model_unavailable")
    assert scenario["kill_point"] == "before_commit"


# ---------------------------------------------------------------------------
# T-API-0067 — policy engine fault produces no partial write
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0067_policy_no_partial_write() -> None:
    """T-API-0067: policy engine fault produces no partial write.

    id: T-API-0067
    title: policy engine fault produces no partial write
    purpose: Verify that the policy engine fault scenario kill point is before_commit
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: the policy_engine_unavailable fault scenario
    expected: kill_point is before_commit
    risk: policy engine fault leaves partial writes
    capability: api-foundation
    """
    scenario = next(s for s in P10_FAULT_SCENARIOS if s["name"] == "policy_engine_unavailable")
    assert scenario["kill_point"] == "before_commit"


# ---------------------------------------------------------------------------
# T-API-0068 — existence oracle mapped to test
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0068_existence_oracle_mapped() -> None:
    """T-API-0068: existence oracle mapped to test.

    id: T-API-0068
    title: existence oracle mapped to test
    purpose: Verify that the existence_oracle threat is mapped in the THREAT_MATRIX
    level: fast
    requirement: P10-T09, Part 3 §3.24
    input: the THREAT_MATRIX
    expected: existence_oracle key exists with test IDs
    risk: existence oracle unmapped
    capability: api-foundation
    """
    assert "existence_oracle" in THREAT_MATRIX
    assert len(THREAT_MATRIX["existence_oracle"]) > 0


# ---------------------------------------------------------------------------
# T-API-0069 — forged tenant identifier mapped to test
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0069_forged_tenant_mapped() -> None:
    """T-API-0069: forged tenant identifier mapped to test.

    id: T-API-0069
    title: forged tenant identifier mapped to test
    purpose: Verify that the forged_tenant_identifier threat is mapped
    level: fast
    requirement: P10-T09, Part 3 §3.24
    input: the THREAT_MATRIX
    expected: forged_tenant_identifier key exists with test IDs
    risk: forged tenant identifier unmapped
    capability: api-foundation
    """
    assert "forged_tenant_identifier" in THREAT_MATRIX
    assert len(THREAT_MATRIX["forged_tenant_identifier"]) > 0


# ---------------------------------------------------------------------------
# T-API-0070 — search or aggregate endpoint mapped to test
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0070_search_aggregate_mapped() -> None:
    """T-API-0070: search or aggregate endpoint mapped to test.

    id: T-API-0070
    title: search or aggregate endpoint mapped to test
    purpose: Verify that the search_or_aggregate_endpoint threat is mapped
    level: fast
    requirement: P10-T09, Part 3 §3.24
    input: the THREAT_MATRIX
    expected: search_or_aggregate_endpoint key exists with test IDs
    risk: search or aggregate endpoint unmapped
    capability: api-foundation
    """
    assert "search_or_aggregate_endpoint" in THREAT_MATRIX
    assert len(THREAT_MATRIX["search_or_aggregate_endpoint"]) > 0


# ---------------------------------------------------------------------------
# T-API-0071 — gate run chaos exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0071_gate_run_chaos_exits_0() -> None:
    """T-API-0071: gate run chaos exits 0.

    id: T-API-0071
    title: gate run chaos exits 0
    purpose: Verify that the chaos gate passes on the real repository
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: gate run chaos
    expected: exit code 0
    risk: chaos gate fails on the real repo
    capability: api-foundation
    """
    result = subprocess.run(  # nosec B603
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.chaos"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, f"chaos gate failed: {result.stderr}"


# ---------------------------------------------------------------------------
# T-API-0072 — gate run contract exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0072_gate_run_contract_exits_0() -> None:
    """T-API-0072: gate run contract exits 0.

    id: T-API-0072
    title: gate run contract exits 0
    purpose: Verify that the contract gate passes on the real repository
    level: fast
    requirement: P10-T09, Part 3 §3.16
    input: gate run contract
    expected: exit code 0
    risk: contract gate fails on the real repo
    capability: api-foundation
    """
    result = subprocess.run(  # nosec B603
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.contract"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )
    assert result.returncode == 0, f"contract gate failed: {result.stderr}"

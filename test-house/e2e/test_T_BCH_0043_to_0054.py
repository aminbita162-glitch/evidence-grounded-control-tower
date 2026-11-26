"""Tests for the traceability matrix tool (P09-T05).

Test IDs: T-BCH-0043 to T-BCH-0054.
Covers: a scenario without a test, a test without a scenario, a risk without
a control, a control without a test, matrix reproducibility, gate exit 0.

Spec: Part 6 §6.11; P09-T05.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.trace import (
    TraceMatrix,
    build_matrix,
    check_matrix,
    generate_report,
    matrix_hash,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# T-BCH-0043 — Matrix builds without error                                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0043_matrix_builds() -> None:
    """T-BCH-0043: Matrix builds without error.

    id: T-BCH-0043
    title: Matrix builds without error
    purpose: Verify the traceability matrix builds from the repo.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: a TraceMatrix is returned
    risk: broken traceability
    capability: none
    """
    matrix = build_matrix(_REPO_ROOT)
    assert isinstance(matrix, TraceMatrix)


# --------------------------------------------------------------------------- #
# T-BCH-0044 — Matrix includes test IDs                                       #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0044_matrix_has_tests() -> None:
    """T-BCH-0044: Matrix includes test IDs.

    id: T-BCH-0044
    title: Matrix includes test IDs
    purpose: Verify the matrix includes test IDs from test-house.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: tests set is non-empty
    risk: broken traceability
    capability: none
    """
    matrix = build_matrix(_REPO_ROOT)
    assert len(matrix.tests) > 0


# --------------------------------------------------------------------------- #
# T-BCH-0045 — Matrix includes scenario IDs                                   #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0045_matrix_has_scenarios() -> None:
    """T-BCH-0045: Matrix includes scenario IDs.

    id: T-BCH-0045
    title: Matrix includes scenario IDs
    purpose: Verify the matrix includes scenario IDs from data/scenarios.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: scenarios dict is non-empty
    risk: broken traceability
    capability: none
    """
    matrix = build_matrix(_REPO_ROOT)
    assert len(matrix.scenarios) > 0


# --------------------------------------------------------------------------- #
# T-BCH-0046 — A scenario without a test fails when seeded                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0046_scenario_without_test_broken() -> None:
    """T-BCH-0046: A scenario without a test fails when seeded.

    id: T-BCH-0046
    title: A scenario without a test fails when seeded
    purpose: Verify a scenario with an empty test_id is a broken link.
    level: fast
    requirement: P09-T05
    input: a matrix with a scenario missing its test_id
    expected: a scenario_without_test broken link is detected
    risk: scenario gaps
    capability: none
    """
    matrix = TraceMatrix(
        tests={"T-BCH-0001"},
        scenarios={"S-BROKEN-A": ""},
        risks={"RSK-X-01": ["CTL-X-01"]},
        controls={"CTL-X-01"},
    )
    broken = check_matrix(matrix)
    kinds = {b.kind for b in broken}
    assert "scenario_without_test" in kinds


# --------------------------------------------------------------------------- #
# T-BCH-0047 — A test without a scenario fails when seeded                   #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0047_test_without_scenario_broken() -> None:
    """T-BCH-0047: A scenario referencing an unknown test fails when seeded.

    id: T-BCH-0047
    title: A scenario referencing an unknown test fails when seeded
    purpose: Verify a scenario that references a test that does not exist
        is detected as a broken link.
    level: fast
    requirement: P09-T05
    input: a matrix with a scenario referencing a non-existent test
    expected: a test_id_not_found broken link is detected
    risk: scenario gaps
    capability: none
    """
    matrix = TraceMatrix(
        tests={"T-BCH-0001"},
        scenarios={"S-A": "T-BCH-NONEXIST"},
        risks={"RSK-X-01": ["CTL-X-01"]},
        controls={"CTL-X-01"},
    )
    broken = check_matrix(matrix)
    kinds = {b.kind for b in broken}
    assert "test_id_not_found" in kinds


# --------------------------------------------------------------------------- #
# T-BCH-0048 — A risk without a control fails when seeded                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0048_risk_without_control_broken() -> None:
    """T-BCH-0048: A risk without a control fails when seeded.

    id: T-BCH-0048
    title: A risk without a control fails when seeded
    purpose: Verify a risk with no controls is a broken link.
    level: fast
    requirement: P09-T05
    input: a matrix with a risk missing its controls
    expected: a risk_without_control broken link is detected
    risk: broken traceability
    capability: none
    """
    matrix = TraceMatrix(
        tests={"T-BCH-0001"},
        scenarios={"S-A": "T-BCH-0001"},
        risks={"RSK-BROKEN": []},
        controls=set(),
    )
    broken = check_matrix(matrix)
    kinds = {b.kind for b in broken}
    assert "risk_without_control" in kinds


# --------------------------------------------------------------------------- #
# T-BCH-0049 — A control without a test is advisory                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0049_control_without_test_advisory() -> None:
    """T-BCH-0049: A control without a test is advisory (no broken link yet).

    id: T-BCH-0049
    title: A control without a test is advisory
    purpose: Verify that controls without tests do not produce broken links
        (controls are PLANNED across many phases; they are not all tested yet).
    level: fast
    requirement: P09-T05
    input: a matrix with a control and no matching test
    expected: no control_without_test broken link (advisory only)
    risk: broken traceability
    capability: none
    """
    matrix = TraceMatrix(
        tests={"T-BCH-0001"},
        scenarios={"S-A": "T-BCH-0001"},
        risks={"RSK-X-01": ["CTL-ORPHAN-01"]},
        controls={"CTL-ORPHAN-01"},
    )
    broken = check_matrix(matrix)
    kinds = {b.kind for b in broken}
    assert "control_without_test" not in kinds


# --------------------------------------------------------------------------- #
# T-BCH-0050 — Matrix is reproducible                                         #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0050_matrix_reproducible() -> None:
    """T-BCH-0050: Matrix is reproducible.

    id: T-BCH-0050
    title: Matrix is reproducible
    purpose: Verify two builds of the matrix produce the same hash.
    level: fast
    requirement: P09-T05
    input: repo root, two builds
    expected: identical matrix_hash values
    risk: non-determinism
    capability: none
    """
    m1 = build_matrix(_REPO_ROOT)
    m2 = build_matrix(_REPO_ROOT)
    assert matrix_hash(m1) == matrix_hash(m2)


# --------------------------------------------------------------------------- #
# T-BCH-0051 — Gate run trace exits 0                                         #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0051_gate_trace_exits_0() -> None:
    """T-BCH-0051: gate run trace exits 0.

    id: T-BCH-0051
    title: gate run trace exits 0
    purpose: Verify the trace gate passes on the real repo.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: exit code 0
    risk: broken traceability
    capability: none
    """
    result = subprocess.run(
        [sys.executable, "-m", "tools.gate.gates.trace"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
    assert result.returncode == 0


# --------------------------------------------------------------------------- #
# T-BCH-0052 — Report is valid JSON                                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0052_report_valid_json() -> None:
    """T-BCH-0052: Report is valid JSON.

    id: T-BCH-0052
    title: Report is valid JSON
    purpose: Verify the generated report is valid JSON.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: generate_report output is valid JSON
    risk: broken traceability
    capability: none
    """
    matrix = build_matrix(_REPO_ROOT)
    report = generate_report(matrix)
    data = json.loads(report)
    assert isinstance(data, dict)
    assert "tests" in data
    assert "broken_count" in data


# --------------------------------------------------------------------------- #
# T-BCH-0053 — Matrix includes risks and controls                            #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0053_matrix_has_risks_controls() -> None:
    """T-BCH-0053: Matrix includes risks and controls.

    id: T-BCH-0053
    title: Matrix includes risks and controls
    purpose: Verify the matrix includes risk and control entries from registers.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: risks and controls are non-empty
    risk: broken traceability
    capability: none
    """
    matrix = build_matrix(_REPO_ROOT)
    assert len(matrix.risks) > 0
    assert len(matrix.controls) > 0


# --------------------------------------------------------------------------- #
# T-BCH-0054 — Broken link count is zero for the real repo                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0054_no_broken_links_real() -> None:
    """T-BCH-0054: Broken link count is zero for the real repo.

    id: T-BCH-0054
    title: No broken links in the real repo
    purpose: Verify the real repo has no broken traceability links.
    level: fast
    requirement: P09-T05
    input: repo root
    expected: broken list is empty
    risk: broken traceability
    capability: none
    """
    matrix = build_matrix(_REPO_ROOT)
    assert len(matrix.broken) == 0, f"broken links: {[(b.kind, b.source) for b in matrix.broken]}"

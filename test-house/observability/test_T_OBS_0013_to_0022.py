"""Tests for canary case, objectives and reconciliation (P10-T07).

Test IDs: T-OBS-0013 to T-OBS-0022.
Covers: the canary passes on a healthy stack and fails on a seeded fault;
a deleted span is reported as a gap; objectives parse and evaluate.

Spec: Part 3 §3.14; P10-T07.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.canary import (
    CANARY_INTERVAL_SECONDS,
    ERROR_BUDGETS,
    OBJECTIVES,
    CanaryResult,
    evaluate_objectives,
    reconcile,
    run_canary,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# T-OBS-0013 — canary passes on a healthy stack
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0013_canary_passes_healthy() -> None:
    """T-OBS-0013: canary passes on a healthy stack.

    id: T-OBS-0013
    title: canary passes on a healthy stack
    purpose: Verify that the canary case passes when the skeleton is healthy
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: run_canary with default seed
    expected: passed is True and error is empty
    risk: canary false-positives on a healthy stack
    capability: api-foundation
    """
    result = run_canary()
    assert result.passed is True
    assert result.error == ""
    assert result.label == "SYNTHETIC"


# ---------------------------------------------------------------------------
# T-OBS-0014 — canary fails on a seeded fault
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0014_canary_fails_fault() -> None:
    """T-OBS-0014: canary fails on a seeded fault.

    id: T-OBS-0014
    title: canary fails on a seeded fault
    purpose: Verify that the canary fails when the skeleton raises an exception
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: run_canary with a broken skeleton (simulated)
    expected: passed is False and error is non-empty
    risk: canary does not detect faults
    capability: api-foundation
    """
    import tools.canary as canary_mod

    original = canary_mod.run_skeleton

    def _broken(_seed: int = 42) -> object:
        raise RuntimeError("seeded fault")

    canary_mod.run_skeleton = _broken  # type: ignore[assignment]
    try:
        result = run_canary()
    finally:
        canary_mod.run_skeleton = original
    assert result.passed is False
    assert "seeded fault" in result.error


# ---------------------------------------------------------------------------
# T-OBS-0015 — a deleted span is reported as a gap
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0015_deleted_span_gap() -> None:
    """T-OBS-0015: a deleted span is reported as a gap.

    id: T-OBS-0015
    title: a deleted span is reported as a gap
    purpose: Verify that a trace record without a ledger counterpart is reported as a gap
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: trace records with seq 1,2,3 and ledger records with seq 1,2
    expected: reconciliation reports one gap for seq 3
    risk: deleted spans not detected as gaps
    capability: api-foundation
    """
    traces = [{"seq": 1}, {"seq": 2}, {"seq": 3}]
    ledger = [{"seq": 1}, {"seq": 2}]
    result = reconcile(traces, ledger)
    assert not result.ok
    assert len(result.gaps) == 1
    assert "3" in result.gaps[0]


# ---------------------------------------------------------------------------
# T-OBS-0016 — no gap when traces match ledger
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0016_no_gap_when_match() -> None:
    """T-OBS-0016: no gap when traces match ledger.

    id: T-OBS-0016
    title: no gap when traces match ledger
    purpose: Verify that reconciliation passes when all traces have ledger records
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: matching trace and ledger records
    expected: ok is True and gaps is empty
    risk: false gap detection on matching records
    capability: api-foundation
    """
    traces = [{"seq": 1}, {"seq": 2}]
    ledger = [{"seq": 1}, {"seq": 2}]
    result = reconcile(traces, ledger)
    assert result.ok
    assert len(result.gaps) == 0


# ---------------------------------------------------------------------------
# T-OBS-0017 — objectives parse correctly
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0017_objectives_parse() -> None:
    """T-OBS-0017: objectives parse correctly.

    id: T-OBS-0017
    title: objectives parse correctly
    purpose: Verify that objectives are well-formed data with name, target and window
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: the OBJECTIVES list
    expected: each entry has name, target and window keys
    risk: malformed objectives data
    capability: api-foundation
    """
    for obj in OBJECTIVES:
        assert "name" in obj
        assert "target" in obj
        assert "window" in obj


# ---------------------------------------------------------------------------
# T-OBS-0018 — error budgets parse correctly
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0018_error_budgets_parse() -> None:
    """T-OBS-0018: error budgets parse correctly.

    id: T-OBS-0018
    title: error budgets parse correctly
    purpose: Verify that error budgets are well-formed data with name, budget and window
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: the ERROR_BUDGETS list
    expected: each entry has name, budget and window keys
    risk: malformed error budget data
    capability: api-foundation
    """
    for eb in ERROR_BUDGETS:
        assert "name" in eb
        assert "budget" in eb
        assert "window" in eb


# ---------------------------------------------------------------------------
# T-OBS-0019 — evaluate_objectives with passing results
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0019_objectives_passing() -> None:
    """T-OBS-0019: evaluate_objectives with passing results.

    id: T-OBS-0019
    title: evaluate_objectives with passing results
    purpose: Verify that all-passing canary results evaluate to all-True objectives
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: a list of passing CanaryResults
    expected: all objective evaluations are True
    risk: objectives evaluation wrong
    capability: api-foundation
    """
    results = [CanaryResult(passed=True, duration_seconds=0.1) for _ in range(10)]
    evaluation = evaluate_objectives(results)
    assert all(evaluation.values())


# ---------------------------------------------------------------------------
# T-OBS-0020 — evaluate_objectives with a failing result
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0020_objectives_failing() -> None:
    """T-OBS-0020: evaluate_objectives with a failing result.

    id: T-OBS-0020
    title: evaluate_objectives with a failing result
    purpose: Verify that a failing canary result lowers the canary_pass_rate objective
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: a list with one failing result
    expected: canary_pass_rate is False
    risk: failing canary not detected in objectives
    capability: api-foundation
    """
    results = [
        CanaryResult(passed=True, duration_seconds=0.1),
        CanaryResult(passed=False, duration_seconds=0.1),
    ]
    evaluation = evaluate_objectives(results)
    assert evaluation["canary_pass_rate"] is False


# ---------------------------------------------------------------------------
# T-OBS-0021 — canary interval is 5 minutes (300 seconds)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0021_canary_interval_5min() -> None:
    """T-OBS-0021: canary interval is 5 minutes (300 seconds).

    id: T-OBS-0021
    title: canary interval is 5 minutes (300 seconds)
    purpose: Verify that the canary interval is 300 seconds per D-32 section 3
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: CANARY_INTERVAL_SECONDS
    expected: value is 300
    risk: wrong canary schedule
    capability: api-foundation
    """
    assert CANARY_INTERVAL_SECONDS == 300


# ---------------------------------------------------------------------------
# T-OBS-0022 — canary result carries SYNTHETIC label
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0022_canary_label_synthetic() -> None:
    """T-OBS-0022: canary result carries SYNTHETIC label.

    id: T-OBS-0022
    title: canary result carries SYNTHETIC label
    purpose: Verify that the canary result is labelled SYNTHETIC
    level: fast
    requirement: P10-T07, Part 3 §3.14
    input: run_canary
    expected: label is SYNTHETIC
    risk: canary data presented as real
    capability: api-foundation
    """
    result = run_canary()
    assert result.label == "SYNTHETIC"

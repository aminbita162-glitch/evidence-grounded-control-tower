"""Tests for scenario format and bench runner (P09-T02).

Test IDs: T-BCH-0013 to T-BCH-0022.
Covers: scenario loading from JSON; bench runner determinism; unmet
expectations fail with the scenario id; runner exception handling;
report counts; scenario without test_id.

Spec: Part 3 §3.12; Part 6 §6.11; Part 4 §4.5; P09-T02.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from data.scenarios import (
    Scenario,
    ScenarioError,
    load_scenario,
    load_scenarios,
)
from tools.bench import run_bench

_SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "data" / "scenarios"


def _stub_runner(inputs: list[object]) -> str:
    """A deterministic stub runner that returns ALLOW for any input."""
    return "ALLOW"


def _hold_runner(inputs: list[object]) -> str:
    """A deterministic stub runner that returns HOLD."""
    return "HOLD"


def _error_runner(inputs: list[object]) -> str:
    """A runner that always raises."""
    raise RuntimeError("stub failure")


# --------------------------------------------------------------------------- #
# T-BCH-0013 — Bench runner is deterministic                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0013_bench_deterministic() -> None:
    """T-BCH-0013: Bench runner is deterministic.

    id: T-BCH-0013
    title: Bench runner is deterministic
    purpose: Verify that the same scenarios and runner produce the same report.
    level: fast
    requirement: P09-T02, Part 3 §3.12
    input: two scenario stubs, ALLOW runner, run twice
    expected: identical reports
    risk: scenario gaps
    capability: none
    """
    scs = [
        Scenario(id="S-A", kind="normal", expected_outcome="ALLOW", test_id="T-BCH-0013"),
        Scenario(id="S-B", kind="boundary", expected_outcome="ALLOW", test_id="T-BCH-0013"),
    ]
    r1 = run_bench(scs, _stub_runner)
    r2 = run_bench(scs, _stub_runner)
    assert r1.passed == r2.passed == 2
    assert r1.failed == r2.failed == 0
    assert [e.scenario_id for e in r1.entries] == [e.scenario_id for e in r2.entries]


# --------------------------------------------------------------------------- #
# T-BCH-0014 — Unmet expectation fails with the scenario id                   #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0014_unmet_expectation_fails() -> None:
    """T-BCH-0014: Unmet expectation fails with the scenario id.

    id: T-BCH-0014
    title: Unmet expectation fails with the scenario id
    purpose: Verify that a scenario whose actual outcome differs from expected
        produces a failed entry with the scenario id.
    level: fast
    requirement: P09-T02
    input: scenario expecting ALLOW, runner returns HOLD
    expected: entry has passed=False and scenario_id set
    risk: scenario gaps
    capability: none
    """
    sc = Scenario(id="S-FAIL", kind="normal", expected_outcome="ALLOW", test_id="T-BCH-0014")
    report = run_bench([sc], _hold_runner)
    assert report.failed == 1
    assert report.entries[0].scenario_id == "S-FAIL"
    assert not report.entries[0].passed


# --------------------------------------------------------------------------- #
# T-BCH-0015 — Met expectation passes                                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0015_met_expectation_passes() -> None:
    """T-BCH-0015: Met expectation passes.

    id: T-BCH-0015
    title: Met expectation passes
    purpose: Verify that a scenario whose actual outcome matches expected passes.
    level: fast
    requirement: P09-T02
    input: scenario expecting HOLD, runner returns HOLD
    expected: entry has passed=True
    risk: scenario gaps
    capability: none
    """
    sc = Scenario(id="S-PASS", kind="boundary", expected_outcome="HOLD", test_id="T-BCH-0015")
    report = run_bench([sc], _hold_runner)
    assert report.passed == 1
    assert report.entries[0].passed


# --------------------------------------------------------------------------- #
# T-BCH-0016 — Scenario loading from JSON                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0016_scenario_loading() -> None:
    """T-BCH-0016: Scenario loading from JSON.

    id: T-BCH-0016
    title: Scenario loading from JSON
    purpose: Verify that a scenario JSON file loads into a Scenario object.
    level: fast
    requirement: P09-T02
    input: s_stub_001.json
    expected: id=S-STUB-001, kind=normal
    risk: broken traceability
    capability: none
    """
    sc = load_scenario(_SCENARIOS_DIR / "s_stub_001.json")
    assert sc.id == "S-STUB-001"
    assert sc.kind == "normal"
    assert sc.expected_outcome == "ALLOW"
    assert sc.basis == "PR-09"


# --------------------------------------------------------------------------- #
# T-BCH-0017 — Invalid scenario kind is rejected                              #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0017_invalid_kind_rejected() -> None:
    """T-BCH-0017: Invalid scenario kind is rejected.

    id: T-BCH-0017
    title: Invalid scenario kind is rejected
    purpose: Verify that an unknown scenario kind raises ScenarioError.
    level: fast
    requirement: P09-T02
    input: JSON with kind='unexpected'
    expected: ScenarioError raised
    risk: scenario gaps
    capability: none
    """
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"id": "S-X", "kind": "unexpected"}, f)
        path = Path(f.name)
    try:
        with pytest.raises(ScenarioError):
            load_scenario(path)
    finally:
        path.unlink()


# --------------------------------------------------------------------------- #
# T-BCH-0018 — Missing required fields are rejected                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0018_missing_fields_rejected() -> None:
    """T-BCH-0018: Missing required fields are rejected.

    id: T-BCH-0018
    title: Missing required fields are rejected
    purpose: Verify that a scenario JSON missing the id field raises ScenarioError.
    level: fast
    requirement: P09-T02
    input: JSON without 'id'
    expected: ScenarioError raised
    risk: broken traceability
    capability: none
    """
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump({"kind": "normal"}, f)
        path = Path(f.name)
    try:
        with pytest.raises(ScenarioError):
            load_scenario(path)
    finally:
        path.unlink()


# --------------------------------------------------------------------------- #
# T-BCH-0019 — Bench report counts are correct                               #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0019_report_counts() -> None:
    """T-BCH-0019: Bench report counts are correct.

    id: T-BCH-0019
    title: Bench report counts are correct
    purpose: Verify that the bench report counts match the number of
        passing and failing scenarios.
    level: fast
    requirement: P09-T02
    input: 3 scenarios, 1 fails
    expected: passed=2, failed=1
    risk: scenario gaps
    capability: none
    """
    scs = [
        Scenario(id="S-1", expected_outcome="ALLOW", test_id="T-BCH-0019"),
        Scenario(id="S-2", expected_outcome="ALLOW", test_id="T-BCH-0019"),
        Scenario(id="S-3", expected_outcome="HOLD", test_id="T-BCH-0019"),
    ]
    report = run_bench(scs, _stub_runner)
    assert report.passed == 2
    assert report.failed == 1
    assert len(report.entries) == 3


# --------------------------------------------------------------------------- #
# T-BCH-0020 — Runner exception produces a failed entry                       #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0020_runner_exception() -> None:
    """T-BCH-0020: Runner exception produces a failed entry.

    id: T-BCH-0020
    title: Runner exception produces a failed entry
    purpose: Verify that a runner that raises an exception produces a
        failed entry with reason set.
    level: fast
    requirement: P09-T02
    input: scenario, error runner
    expected: entry has passed=False, actual=ERROR
    risk: skeleton drift
    capability: none
    """
    sc = Scenario(id="S-ERR", expected_outcome="ALLOW", test_id="T-BCH-0020")
    report = run_bench([sc], _error_runner)
    assert report.failed == 1
    assert report.entries[0].actual == "ERROR"
    assert report.entries[0].reason


# --------------------------------------------------------------------------- #
# T-BCH-0021 — All scenarios from the scenario directory pass                 #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0021_all_scenarios_pass() -> None:
    """T-BCH-0021: All scenarios from the scenario directory pass.

    id: T-BCH-0021
    title: All scenarios from the scenario directory pass
    purpose: Verify that loading and running all committed scenarios
        with a stub ALLOW runner produces the expected pass/fail split.
    level: fast
    requirement: P09-T02
    input: data/scenarios/ directory
    expected: S-STUB-001 passes (ALLOW), S-STUB-002 fails (HOLD vs ALLOW)
    risk: scenario gaps
    capability: none
    """
    scs = load_scenarios(_SCENARIOS_DIR)
    assert len(scs) >= 2
    report = run_bench(scs, _stub_runner)
    s1 = [e for e in report.entries if e.scenario_id == "S-STUB-001"]
    assert s1 and s1[0].passed
    s2 = [e for e in report.entries if e.scenario_id == "S-STUB-002"]
    assert s2 and not s2[0].passed


# --------------------------------------------------------------------------- #
# T-BCH-0022 — Scenario without test_id has empty test_id                     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0022_no_test_id() -> None:
    """T-BCH-0022: Scenario without test_id has empty test_id in entry.

    id: T-BCH-0022
    title: Scenario without test_id has empty test_id
    purpose: Verify that a scenario without a test_id produces a bench entry
        with an empty test_id (the trace tool lists it as missing).
    level: fast
    requirement: P09-T02, Part 6 §6.12
    input: scenario without test_id
    expected: entry.test_id == ''
    risk: broken traceability
    capability: none
    """
    sc = Scenario(id="S-NOTEST", expected_outcome="ALLOW", test_id="")
    report = run_bench([sc], _stub_runner)
    assert report.entries[0].test_id == ""

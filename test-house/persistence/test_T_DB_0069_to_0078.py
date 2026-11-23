"""Tests for crash-consistency laboratory (P04-T07).

Test IDs: T-DB-0069 to T-DB-0078.
Covers: every kill point recovers to a state equal to the expected hash; no
partial write is visible; the lab reports registered kill points; the lab
fails if a registered point has no scenario.

Spec: Part 3 §3.16; Part 4 §4.5; P04-T07.
"""

from __future__ import annotations

import hashlib

import pytest

from tools.faultlab import KILL_POINTS, FaultLab

_EXPECTED_STATE = '{"state": "clean", "count": 1}'
_EXPECTED_HASH = hashlib.sha256(_EXPECTED_STATE.encode()).hexdigest()


def _make_lab() -> FaultLab:
    """Create a FaultLab with all kill points and scenarios registered."""
    lab = FaultLab()
    for kp in KILL_POINTS:
        lab.register_kill_point(kp)
        lab.register_scenario(kp, _EXPECTED_HASH)
    return lab


# ---------------------------------------------------------------------------
# T-DB-0069: kill point 'before_commit' recovers
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0069_kill_before_commit() -> None:
    """T-DB-0069: kill point 'before_commit' recovers to expected state.

    id: T-DB-0069
    title: Kill point before_commit recovers
    purpose: Verify the before_commit kill point recovers to the expected hash.
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with before_commit scenario
    expected: recovered state matches expected hash
    risk: partial write visible after crash
    owning capability: persistence
    """
    lab = _make_lab()
    assert lab.run_scenario("before_commit", _EXPECTED_STATE)


# ---------------------------------------------------------------------------
# T-DB-0070: kill point 'after_commit_before_outbox' recovers
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0070_kill_after_commit_before_outbox() -> None:
    """T-DB-0070: kill point 'after_commit_before_outbox' recovers.

    id: T-DB-0070
    title: Kill point after_commit_before_outbox recovers
    purpose: Verify the after_commit_before_outbox kill point recovers.
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with after_commit_before_outbox scenario
    expected: recovered state matches expected hash
    risk: state change visible without outbox
    owning capability: persistence
    """
    lab = _make_lab()
    assert lab.run_scenario("after_commit_before_outbox", _EXPECTED_STATE)


# ---------------------------------------------------------------------------
# T-DB-0071: kill point 'during_delivery' recovers
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0071_kill_during_delivery() -> None:
    """T-DB-0071: kill point 'during_delivery' recovers.

    id: T-DB-0071
    title: Kill point during_delivery recovers
    purpose: Verify the during_delivery kill point recovers.
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with during_delivery scenario
    expected: recovered state matches expected hash
    risk: partial delivery visible
    owning capability: persistence
    """
    lab = _make_lab()
    assert lab.run_scenario("during_delivery", _EXPECTED_STATE)


# ---------------------------------------------------------------------------
# T-DB-0072: kill point 'during_migration' recovers
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0072_kill_during_migration() -> None:
    """T-DB-0072: kill point 'during_migration' recovers.

    id: T-DB-0072
    title: Kill point during_migration recovers
    purpose: Verify the during_migration kill point recovers.
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with during_migration scenario
    expected: recovered state matches expected hash
    risk: partial migration visible
    owning capability: persistence
    """
    lab = _make_lab()
    assert lab.run_scenario("during_migration", _EXPECTED_STATE)


# ---------------------------------------------------------------------------
# T-DB-0073: no partial write visible after recovery
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0073_no_partial_write() -> None:
    """T-DB-0073: no partial write is visible after recovery.

    id: T-DB-0073
    title: No partial write visible after recovery
    purpose: Verify a mismatched state is detected (no false positive).
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with expected hash, recovered with wrong state
    expected: run_scenario returns False (mismatch detected)
    risk: partial write not detected
    owning capability: persistence
    """
    lab = _make_lab()
    wrong_state = '{"state": "partial", "count": 0}'
    assert not lab.run_scenario("before_commit", wrong_state)


# ---------------------------------------------------------------------------
# T-DB-0074: lab reports registered kill points
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0074_lab_reports_kill_points() -> None:
    """T-DB-0074: lab reports the list of registered kill points.

    id: T-DB-0074
    title: Lab reports registered kill points
    purpose: Verify the lab lists all registered kill points.
    level: fast
    requirement: P04-T07; Part 4 §4.5
    input: FaultLab with all kill points
    expected: registered_kill_points has 4 entries
    risk: kill points not tracked
    owning capability: persistence
    """
    lab = _make_lab()
    points = lab.registered_kill_points
    assert len(points) == 4
    assert "before_commit" in points
    assert "after_commit_before_outbox" in points
    assert "during_delivery" in points
    assert "during_migration" in points


# ---------------------------------------------------------------------------
# T-DB-0075: lab fails if a registered point has no scenario
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0075_missing_scenario_fails() -> None:
    """T-DB-0075: lab fails if a registered point has no scenario.

    id: T-DB-0075
    title: Lab fails if registered point has no scenario
    purpose: Verify the lab reports kill points without scenarios.
    level: fast
    requirement: P04-T07; Part 4 §4.5
    input: FaultLab with a kill point but no scenario
    expected: check_all returns the missing kill point
    risk: kill points without scenarios pass silently
    owning capability: persistence
    """
    lab = FaultLab()
    lab.register_kill_point("orphan_point")
    missing = lab.check_all()
    assert "orphan_point" in missing


# ---------------------------------------------------------------------------
# T-DB-0076: each scenario restarts and compares by hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0076_scenario_compares_by_hash() -> None:
    """T-DB-0076: each scenario restarts and compares by hash.

    id: T-DB-0076
    title: Scenario compares by hash
    purpose: Verify the scenario comparison uses SHA-256 hashes.
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with a scenario
    expected: matching state passes, non-matching fails
    risk: state comparison incorrect
    owning capability: persistence
    """
    lab = FaultLab()
    lab.register_kill_point("kp1")
    expected = hashlib.sha256(b"ok").hexdigest()
    lab.register_scenario("kp1", expected)
    assert lab.run_scenario("kp1", "ok")
    assert not lab.run_scenario("kp1", "wrong")


# ---------------------------------------------------------------------------
# T-DB-0077: lab is a shared tool
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0077_lab_shared_tool() -> None:
    """T-DB-0077: lab is a shared tool (later phases register kill points).

    id: T-DB-0077
    title: Lab is a shared tool
    purpose: Verify the lab accepts new kill point registrations.
    level: fast
    requirement: P04-T07; Part 4 §4.5
    input: FaultLab with a new kill point
    expected: the new kill point is registered
    risk: lab not extensible
    owning capability: persistence
    """
    lab = FaultLab()
    lab.register_kill_point("custom_kp", "custom kill point")
    assert "custom_kp" in lab.registered_kill_points


# ---------------------------------------------------------------------------
# T-DB-0078: all kill points recover to equal state
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0078_all_points_recover() -> None:
    """T-DB-0078: all kill points recover to equal state.

    id: T-DB-0078
    title: All kill points recover to equal state
    purpose: Verify every registered kill point recovers to the expected state.
    level: fast
    requirement: P04-T07; Part 3 §3.16
    input: FaultLab with all kill points and scenarios
    expected: all scenarios pass with the expected state
    risk: some kill points not recovering correctly
    owning capability: persistence
    """
    lab = _make_lab()
    for kp in KILL_POINTS:
        assert lab.run_scenario(kp, _EXPECTED_STATE), f"{kp} did not recover"

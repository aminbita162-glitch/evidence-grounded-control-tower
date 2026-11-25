"""Tests for action classes and autonomy levels (P07-T04).

Test IDs: T-ORC-0043 to T-ORC-0050.
Covers: action class semantics, autonomy level enforcement, E-irrev
capping, default level, system-chain event recording.

Spec: Part 3 §3.30; P07-T04.
"""

from __future__ import annotations

import pytest

from kernel.containment.autonomy import (
    DEFAULT_LEVEL,
    AutonomyError,
    AutonomyPolicy,
    default_policy,
)

# ---------------------------------------------------------------------------
# T-ORC-0043 — E-irrev without a bound approval is blocked at A0
# ---------------------------------------------------------------------------
# id: T-ORC-0043
# title: E-irrev without a bound approval is blocked at A0
# purpose: Verify that E-irrev is blocked at A0 even with bound approval.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: an AutonomyPolicy at A0 with E-irrev and has_bound_approval=True
# expected: can_execute("E-irrev") is False
# risk: E-irrev executes below A2
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0043_eirrev_blocked_at_a0() -> None:
    """E-irrev is blocked at A0."""
    policy = AutonomyPolicy(
        "t1", "cap1", level="A0", action_classes=("E-irrev",), has_bound_approval=True
    )
    assert policy.can_execute("E-irrev") is False


# ---------------------------------------------------------------------------
# T-ORC-0044 — E-irrev without a bound approval is blocked at A2
# ---------------------------------------------------------------------------
# id: T-ORC-0044
# title: E-irrev without a bound approval is blocked at A2
# purpose: Verify that E-irrev is blocked at A2 without bound approval.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: an AutonomyPolicy at A2 with E-irrev and has_bound_approval=False
# expected: can_execute("E-irrev") is False
# risk: E-irrev executes without approval
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0044_eirrev_blocked_without_approval() -> None:
    """E-irrev is blocked at A2 without bound approval."""
    policy = AutonomyPolicy(
        "t1", "cap1", level="A2", action_classes=("E-irrev",), has_bound_approval=False
    )
    assert policy.can_execute("E-irrev") is False


# ---------------------------------------------------------------------------
# T-ORC-0045 — E-irrev with a bound approval is allowed at A2
# ---------------------------------------------------------------------------
# id: T-ORC-0045
# title: E-irrev with a bound approval is allowed at A2
# purpose: Verify that E-irrev is allowed at A2 with bound approval.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: an AutonomyPolicy at A2 with E-irrev and has_bound_approval=True
# expected: can_execute("E-irrev") is True
# risk: E-irrev blocked when approved
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0045_eirrev_allowed_with_approval() -> None:
    """E-irrev is allowed at A2 with bound approval."""
    policy = AutonomyPolicy(
        "t1", "cap1", level="A2", action_classes=("E-irrev",), has_bound_approval=True
    )
    assert policy.can_execute("E-irrev") is True


# ---------------------------------------------------------------------------
# T-ORC-0046 — No level above A2 can be configured
# ---------------------------------------------------------------------------
# id: T-ORC-0046
# title: No level above A2 can be configured
# purpose: Verify that setting a level above A2 raises AutonomyError.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: set_level("A3")
# expected: AutonomyError is raised
# risk: unbounded autonomy level
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0046_no_level_above_a2() -> None:
    """No level above A2 can be configured."""
    policy = AutonomyPolicy("t1", "cap1")
    with pytest.raises(AutonomyError, match="not valid"):
        policy.set_level("A3")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# T-ORC-0047 — The default level is A1
# ---------------------------------------------------------------------------
# id: T-ORC-0047
# title: The default level is A1
# purpose: Verify that a default policy has level A1.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: default_policy("t1", "cap1")
# expected: level == A1
# risk: wrong default gives excess autonomy
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0047_default_is_a1() -> None:
    """The default autonomy level is A1."""
    policy = default_policy("t1", "cap1")
    assert policy.level == "A1"
    assert DEFAULT_LEVEL == "A1"


# ---------------------------------------------------------------------------
# T-ORC-0048 — A0 allows only R (observe)
# ---------------------------------------------------------------------------
# id: T-ORC-0048
# title: A0 allows only R (observe)
# purpose: Verify that A0 permits only the read action class.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: an AutonomyPolicy at A0
# expected: can_execute("R") is True, can_execute("P") is False
# risk: A0 allows proposals
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0048_a0_observe_only() -> None:
    """A0 allows only R."""
    policy = AutonomyPolicy("t1", "cap1", level="A0")
    assert policy.can_execute("R") is True
    assert policy.can_execute("P") is False


# ---------------------------------------------------------------------------
# T-ORC-0049 — A1 allows R and P but not E-rev or E-irrev
# ---------------------------------------------------------------------------
# id: T-ORC-0049
# title: A1 allows R and P but not E-rev or E-irrev
# purpose: Verify that A1 permits R and P but blocks effects.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: an AutonomyPolicy at A1
# expected: R True, P True, E-rev False, E-irrev False
# risk: A1 allows effects without approval
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0049_a1_propose_only() -> None:
    """A1 allows R and P but not E-rev or E-irrev."""
    policy = AutonomyPolicy("t1", "cap1", level="A1")
    assert policy.can_execute("R") is True
    assert policy.can_execute("P") is True
    assert policy.can_execute("E-rev") is False
    assert policy.can_execute("E-irrev") is False


# ---------------------------------------------------------------------------
# T-ORC-0050 — A level change is recorded as a system-chain event
# ---------------------------------------------------------------------------
# id: T-ORC-0050
# title: A level change is recorded as a system-chain event
# purpose: Verify that set_level records the change in the change log.
# level: fast
# requirement: P07-T04, Part 3 §3.30
# input: set_level from A1 to A2
# expected: change_log has one entry containing the transition
# risk: unrecorded autonomy changes
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0050_change_recorded() -> None:
    """A level change is recorded as a system-chain event."""
    policy = AutonomyPolicy("t1", "cap1", level="A1")
    policy.set_level("A2")
    assert len(policy.change_log) == 1
    assert "A1->A2" in policy.change_log[0]

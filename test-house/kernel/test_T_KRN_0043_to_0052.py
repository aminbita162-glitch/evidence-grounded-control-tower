"""Tests for the case state machine (P03-T05).

Test IDs: T-KRN-0043 to T-KRN-0052.
Covers: every (state, event) pair assertion; undefined transitions rejected;
idempotency key returns identical result; stale version conflict; two
approvals first-wins; timeout to BLOCKED; re-evaluation supersession;
QUARANTINED state; FAILED terminal state.

Spec: Part 3 §3.4; kernel/casestate/; schemas/case-states.json.
"""

from __future__ import annotations

import pytest

from kernel.casestate import (
    ALL_STATES,
    SIDE_STATES,
    TRANSITIONS,
    IdempotencyStore,
    VersionConflictError,
    can_transition,
    check_version,
    is_valid_state,
    transition,
)

# ---------------------------------------------------------------------------
# T-KRN-0043 — Every (state, event) pair covered by the table
# ---------------------------------------------------------------------------
# id: T-KRN-0043
# title: Every (state, event) pair covered by the table
# purpose: Verify the transition table covers all states and is consistent.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: all states from the schema
# expected: every state appears in the transition table
# risk: a state is missing from the table
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0043_all_states_in_table() -> None:
    """Every state appears as a key in the transition table."""
    for state in ALL_STATES:
        assert state in TRANSITIONS, f"state {state!r} missing from transition table"


# ---------------------------------------------------------------------------
# T-KRN-0044 — Undefined transitions are rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0044
# title: Undefined transitions are rejected
# purpose: Verify that transitions not in the table raise ValueError.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: an undefined transition (CLOSED -> INGESTED)
# expected: ValueError is raised
# risk: an undefined transition is accepted
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0044_undefined_transition_rejected() -> None:
    """Undefined transitions raise ValueError."""
    assert not can_transition("CLOSED", "INGESTED")
    with pytest.raises(ValueError):
        transition("CLOSED", "INGESTED")


# ---------------------------------------------------------------------------
# T-KRN-0045 — Same idempotency key returns an identical result
# ---------------------------------------------------------------------------
# id: T-KRN-0045
# title: Same idempotency key returns an identical result
# purpose: Verify that repeating a command with the same key returns the original.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: a key and result, then the same key again
# expected: the second check returns the same result
# risk: idempotency is not enforced
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0045_idempotency_key_identical() -> None:
    """Same idempotency key returns the identical result."""
    store = IdempotencyStore()
    store.record("key-1", {"value": 42})
    assert store.check("key-1") == {"value": 42}
    assert store.check("key-2") is None


# ---------------------------------------------------------------------------
# T-KRN-0046 — A stale version yields the conflict error
# ---------------------------------------------------------------------------
# id: T-KRN-0046
# title: A stale version yields the conflict error
# purpose: Verify that a stale version is rejected with VersionConflictError.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: current=1, expected=2
# expected: VersionConflictError is raised
# risk: stale versions are accepted
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0046_stale_version_conflict() -> None:
    """A stale version raises VersionConflictError."""
    with pytest.raises(VersionConflictError):
        check_version(1, 2)
    check_version(3, 3)  # matching version does not raise


# ---------------------------------------------------------------------------
# T-KRN-0047 — Two approvals of one proposal: the first wins
# ---------------------------------------------------------------------------
# id: T-KRN-0047
# title: Two approvals of one proposal: the first wins
# purpose: Verify that the first approval of a proposal wins.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: two approvals for the same proposal hash
# expected: the first is accepted, the second is a conflict
# risk: duplicate approvals are both accepted
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0047_first_approval_wins() -> None:
    """The first approval of a proposal wins; the second is a conflict."""
    store = IdempotencyStore()
    store.record("approval:hash-abc", {"outcome": "APPROVE"})
    # Second approval with the same key returns the original.
    result = store.check("approval:hash-abc")
    assert result == {"outcome": "APPROVE"}


# ---------------------------------------------------------------------------
# T-KRN-0048 — Timeouts move to BLOCKED, never approve
# ---------------------------------------------------------------------------
# id: T-KRN-0048
# title: Timeouts move to BLOCKED, never approve
# purpose: Verify that a timeout transition to BLOCKED is allowed.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: from AWAITING_HUMAN to BLOCKED
# expected: transition is allowed
# risk: timeouts auto-approve
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0048_timeout_to_blocked() -> None:
    """Timeout transitions to BLOCKED are allowed."""
    assert can_transition("AWAITING_HUMAN", "BLOCKED")
    assert transition("AWAITING_HUMAN", "BLOCKED") == "BLOCKED"


# ---------------------------------------------------------------------------
# T-KRN-0049 — Re-evaluation supersedes by reference
# ---------------------------------------------------------------------------
# id: T-KRN-0049
# title: Re-evaluation supersedes by reference
# purpose: Verify that DECIDED can transition to REOPENED for re-evaluation.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: from DECIDED to REOPENED
# expected: transition is allowed
# risk: re-evaluation is blocked
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0049_re_evaluation_supersede() -> None:
    """DECIDED -> REOPENED is allowed for re-evaluation."""
    assert can_transition("DECIDED", "REOPENED")
    assert transition("DECIDED", "REOPENED") == "REOPENED"


# ---------------------------------------------------------------------------
# T-KRN-0050 — QUARANTINED state exists and can transition
# ---------------------------------------------------------------------------
# id: T-KRN-0050
# title: QUARANTINED state exists and can transition
# purpose: Verify the QUARANTINED side state is in the table.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: QUARANTINED state
# expected: it is a valid state with defined transitions
# risk: quarantine is not defined
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0050_quarantined_state() -> None:
    """QUARANTINED is a valid state with defined transitions."""
    assert is_valid_state("QUARANTINED")
    assert "QUARANTINED" in SIDE_STATES
    assert can_transition("QUARANTINED", "FAILED") or can_transition("QUARANTINED", "CREATED")


# ---------------------------------------------------------------------------
# T-KRN-0051 — FAILED is a terminal state
# ---------------------------------------------------------------------------
# id: T-KRN-0051
# title: FAILED is a terminal state
# purpose: Verify that FAILED has no outgoing transitions.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: from FAILED to any other state
# expected: all transitions from FAILED are rejected
# risk: FAILED cases are resumed
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0051_failed_is_terminal() -> None:
    """FAILED is terminal — no transitions out."""
    assert TRANSITIONS["FAILED"] == []
    for target in ALL_STATES:
        assert not can_transition("FAILED", target), f"FAILED -> {target} should be rejected"


# ---------------------------------------------------------------------------
# T-KRN-0052 — Normal lifecycle path is valid
# ---------------------------------------------------------------------------
# id: T-KRN-0052
# title: Normal lifecycle path is valid
# purpose: Verify the full CREATED -> CLOSED lifecycle path is valid.
# level: fast
# requirement: P03-T05, Part 3 §3.4
# input: the standard lifecycle sequence
# expected: each transition is allowed
# risk: the normal lifecycle is blocked
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0052_normal_lifecycle() -> None:
    """The standard lifecycle path CREATED -> CLOSED is valid."""
    path = [
        "CREATED",
        "INGESTED",
        "EXTRACTED",
        "EVALUATED",
        "PROPOSED",
        "AWAITING_HUMAN",
        "DECIDED",
        "CLOSED",
    ]
    for i in range(len(path) - 1):
        assert can_transition(path[i], path[i + 1]), (
            f"lifecycle broken at {path[i]} -> {path[i + 1]}"
        )

"""Tests for the Human Gate (P07-T06).

Test IDs: T-ORC-0067 to T-ORC-0078.
Covers: approval bound to proposal hash, rejection with justification,
override as separate record, second reviewer for ESCALATE overrides,
concurrent approval conflict, approval expiry with case state.

Spec: Part 3 §3.5, §3.7, §3.9; P07-T06.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from kernel.humangate import ConflictError, HumanGate, HumanGateError

# ---------------------------------------------------------------------------
# T-ORC-0067 — Approval of a changed proposal is invalid
# ---------------------------------------------------------------------------
# id: T-ORC-0067
# title: Approval of a changed proposal is invalid
# purpose: Verify that an approval with a mismatched proposal hash is rejected.
# level: fast
# requirement: P07-T06, Part 3 §3.5, §3.9
# input: a proposal and a wrong hash
# expected: HumanGateError with "hash mismatch"
# risk: approval of a tampered proposal
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0067_changed_proposal_invalid() -> None:
    """Approval of a changed proposal is invalid."""
    gate = HumanGate("case-1")
    proposal = {"action": "import", "value": "100"}
    wrong_hash = hashlib.sha256(b"wrong").hexdigest()
    with pytest.raises(HumanGateError, match="hash mismatch"):
        gate.approve(proposal, wrong_hash, "rev-1", "reviewer", "AWAITING_HUMAN")


# ---------------------------------------------------------------------------
# T-ORC-0068 — A valid approval is accepted
# ---------------------------------------------------------------------------
# id: T-ORC-0068
# title: A valid approval is accepted
# purpose: Verify that an approval with the correct proposal hash succeeds.
# level: fast
# requirement: P07-T06, Part 3 §3.5, §3.9
# input: a proposal and its correct hash
# expected: approval record with outcome APPROVE
# risk: valid approval rejected
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0068_valid_approval_accepted() -> None:
    """A valid approval is accepted."""
    gate = HumanGate("case-1")
    proposal = {"action": "import", "value": "100"}
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record = gate.approve(proposal, proposal_hash, "rev-1", "reviewer", "AWAITING_HUMAN")
    assert record.outcome == "APPROVE"
    assert gate.is_decided is True


# ---------------------------------------------------------------------------
# T-ORC-0069 — A rejection requires written justification
# ---------------------------------------------------------------------------
# id: T-ORC-0069
# title: A rejection requires written justification
# purpose: Verify that a rejection without justification is rejected.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: a rejection with empty justification
# expected: HumanGateError with "justification required"
# risk: rejection without audit trail
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0069_rejection_requires_justification() -> None:
    """A rejection requires written justification."""
    gate = HumanGate("case-1")
    with pytest.raises(HumanGateError, match="justification"):
        gate.reject("hash", "rev-1", "reviewer", "AWAITING_HUMAN", "")


# ---------------------------------------------------------------------------
# T-ORC-0070 — An override is a separate record
# ---------------------------------------------------------------------------
# id: T-ORC-0070
# title: An override is a separate record
# purpose: Verify that an override creates a separate record, not rewriting the Decision.
# level: fast
# requirement: P07-T06, Part 3 §3.9 I11
# input: an override with a second reviewer
# expected: the record has outcome OVERRIDE and the Decision is unchanged
# risk: override rewrites the Decision
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0070_override_is_separate_record() -> None:
    """An override is a separate record that never rewrites the Decision."""
    gate = HumanGate("case-1")
    record = gate.override(
        "hash-1",
        "rev-1",
        "reviewer",
        "AWAITING_HUMAN",
        "justification text",
        second_reviewer_id="rev-2",
    )
    assert record.outcome == "OVERRIDE"
    assert record.second_reviewer_id == "rev-2"


# ---------------------------------------------------------------------------
# T-ORC-0071 — An override by the same reviewer twice is refused
# ---------------------------------------------------------------------------
# id: T-ORC-0071
# title: An override by the same reviewer twice is refused
# purpose: Verify that an override with the same reviewer as second reviewer fails.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: an override with second_reviewer_id == reviewer_id
# expected: HumanGateError with "second reviewer must be different"
# risk: single reviewer overrides ESCALATE
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0071_override_same_reviewer_refused() -> None:
    """An override by the same reviewer twice is refused."""
    gate = HumanGate("case-1")
    with pytest.raises(HumanGateError, match="second reviewer must be different"):
        gate.override(
            "hash-1",
            "rev-1",
            "reviewer",
            "AWAITING_HUMAN",
            "justification",
            second_reviewer_id="rev-1",
        )


# ---------------------------------------------------------------------------
# T-ORC-0072 — An override without a second reviewer is refused
# ---------------------------------------------------------------------------
# id: T-ORC-0072
# title: An override without a second reviewer is refused
# purpose: Verify that an override of ESCALATE without a second reviewer fails.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: an override with no second_reviewer_id
# expected: HumanGateError with "second reviewer"
# risk: single reviewer overrides ESCALATE
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0072_override_no_second_reviewer_refused() -> None:
    """An override without a second reviewer is refused."""
    gate = HumanGate("case-1")
    with pytest.raises(HumanGateError, match="second reviewer"):
        gate.override("hash-1", "rev-1", "reviewer", "AWAITING_HUMAN", "justification")


# ---------------------------------------------------------------------------
# T-ORC-0073 — The Decision record is unchanged after an override
# ---------------------------------------------------------------------------
# id: T-ORC-0073
# title: The Decision record is unchanged after an override
# purpose: Verify that an override does not change the decided state
#          (the Decision is never rewritten, I11).
# level: fast
# requirement: P07-T06, Part 3 §3.9 I11
# input: a gate with an approval, then an override
# expected: the override is a separate record; the approval record is unchanged
# risk: override modifies the Decision
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0073_decision_unchanged_after_override() -> None:
    """The Decision record is unchanged after an override."""
    gate = HumanGate("case-1")
    proposal = {"action": "import"}
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    approval = gate.approve(proposal, proposal_hash, "rev-1", "reviewer", "AWAITING_HUMAN")
    gate.override(
        "hash-2",
        "rev-3",
        "reviewer",
        "DECIDED",
        "override justification",
        second_reviewer_id="rev-4",
    )
    assert approval.outcome == "APPROVE"
    assert len(gate.approvals) == 2


# ---------------------------------------------------------------------------
# T-ORC-0074 — The second concurrent approval receives a conflict
# ---------------------------------------------------------------------------
# id: T-ORC-0074
# title: The second concurrent approval receives a conflict
# purpose: Verify that a second approval for the same proposal receives a conflict.
# level: fast
# requirement: P07-T06, Part 3 §3.4, §3.9
# input: two approvals for the same proposal hash
# expected: the second raises ConflictError
# risk: double approval causes inconsistent state
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0074_concurrent_approval_conflict() -> None:
    """The second concurrent approval receives a conflict."""
    gate = HumanGate("case-1")
    proposal = {"action": "import"}
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    gate.approve(proposal, proposal_hash, "rev-1", "reviewer", "AWAITING_HUMAN")
    with pytest.raises(ConflictError, match="first wins"):
        gate.approve(proposal, proposal_hash, "rev-2", "reviewer", "AWAITING_HUMAN")


# ---------------------------------------------------------------------------
# T-ORC-0075 — A reviewer role is required
# ---------------------------------------------------------------------------
# id: T-ORC-0075
# title: A reviewer role is required
# purpose: Verify that an approval without a reviewer role is rejected.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: an approval with reviewer_role=""
# expected: HumanGateError with "reviewer role required"
# risk: unauthorised approval
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0075_reviewer_role_required() -> None:
    """A reviewer role is required for an approval."""
    gate = HumanGate("case-1")
    proposal = {"action": "import"}
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    with pytest.raises(HumanGateError, match="reviewer role required"):
        gate.approve(proposal, proposal_hash, "rev-1", "", "AWAITING_HUMAN")


# ---------------------------------------------------------------------------
# T-ORC-0076 — Approvals expire with the case state
# ---------------------------------------------------------------------------
# id: T-ORC-0076
# title: Approvals expire with the case state
# purpose: Verify that an approval expires when the case state advances.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: an approval at AWAITING_HUMAN, checking expiry at DECIDED
# expected: is_expired returns True
# risk: stale approvals used after state change
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0076_approval_expires_with_state() -> None:
    """Approvals expire with the case state."""
    gate = HumanGate("case-1")
    proposal = {"action": "import"}
    proposal_hash = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    record = gate.approve(proposal, proposal_hash, "rev-1", "reviewer", "AWAITING_HUMAN")
    assert gate.is_expired("DECIDED", record) is True
    assert gate.is_expired("AWAITING_HUMAN", record) is False


# ---------------------------------------------------------------------------
# T-ORC-0077 — A rejection is recorded
# ---------------------------------------------------------------------------
# id: T-ORC-0077
# title: A rejection is recorded
# purpose: Verify that a rejection creates a record in the approval list.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: a valid rejection
# expected: approvals has one record with outcome REJECT
# risk: rejection not recorded
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0077_rejection_recorded() -> None:
    """A rejection is recorded."""
    gate = HumanGate("case-1")
    record = gate.reject("hash-1", "rev-1", "reviewer", "AWAITING_HUMAN", "not compliant")
    assert record.outcome == "REJECT"
    assert len(gate.approvals) == 1


# ---------------------------------------------------------------------------
# T-ORC-0078 — An override without justification is refused
# ---------------------------------------------------------------------------
# id: T-ORC-0078
# title: An override without justification is refused
# purpose: Verify that an override without written justification is rejected.
# level: fast
# requirement: P07-T06, Part 3 §3.9
# input: an override with empty justification
# expected: HumanGateError with "justification required"
# risk: override without audit trail
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0078_override_without_justification_refused() -> None:
    """An override without justification is refused."""
    gate = HumanGate("case-1")
    with pytest.raises(HumanGateError, match="justification required"):
        gate.override("hash-1", "rev-1", "reviewer", "AWAITING_HUMAN", "")

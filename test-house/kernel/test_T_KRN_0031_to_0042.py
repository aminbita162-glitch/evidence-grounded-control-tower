"""Tests for fact statuses and ALLOW eligibility (P03-T04).

Test IDs: T-KRN-0031 to T-KRN-0042.
Covers: status transition table; conflicted fact → ESCALATE; missing fact →
ABSTAIN; SECONDARY never ALLOW; SYNTHETIC stamp; CALIBRATED_SYNTHETIC →
ESCALATE; VALIDATED_TENANT → ALLOW; ALLOW without basis rejected; reader
returns only VERIFIED facts; transition validation.

Spec: Part 3 §3.3, §3.8; kernel/facts/; kernel/decision/.
"""

from __future__ import annotations

import pytest

from kernel.decision import FactEntry, evaluate_allow
from kernel.facts.reader import VerifiedFactReader
from kernel.facts.status import TRANSITIONS, can_transition, transition
from kernel.types.decision import DecisionValue

# ---------------------------------------------------------------------------
# T-KRN-0031 — Every status transition allowed or rejected as tabulated
# ---------------------------------------------------------------------------
# id: T-KRN-0031
# title: Every status transition allowed or rejected as tabulated
# purpose: Verify the transition table matches the spec for all pairs.
# level: fast
# requirement: P03-T04, Part 3 §3.3
# input: all (from, to) status pairs
# expected: allowed transitions pass, disallowed ones fail
# risk: an invalid transition is allowed
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0031_status_transitions_tabulated() -> None:
    """All transitions match the table."""
    for from_status, allowed in TRANSITIONS.items():
        for to_status in TRANSITIONS:
            expected = to_status in allowed
            assert can_transition(from_status, to_status) == expected, (
                f"transition {from_status}->{to_status}: expected {expected}"
            )


# ---------------------------------------------------------------------------
# T-KRN-0032 — A conflicted fact key yields ESCALATE with both citations
# ---------------------------------------------------------------------------
# id: T-KRN-0032
# title: A conflicted fact key yields ESCALATE with both citations
# purpose: Verify that conflicting facts produce ESCALATE.
# level: fast
# requirement: P03-T04, Part 3 §3.3
# input: two non-superseded values for one key
# expected: the key is detected as conflicting
# risk: conflicts are not detected
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0032_conflicted_fact_escalate() -> None:
    """A conflicted fact key is detected."""
    from kernel.facts.conflict import find_conflicting_keys

    values = {"price": [("100", "VERIFIED"), ("200", "VERIFIED")]}
    conflicts = find_conflicting_keys(values)
    assert "price" in conflicts


# ---------------------------------------------------------------------------
# T-KRN-0033 — A missing fact yields ABSTAIN
# ---------------------------------------------------------------------------
# id: T-KRN-0033
# title: A missing fact yields ABSTAIN
# purpose: Verify that a missing required fact produces ABSTAIN.
# level: fast
# requirement: P03-T04, Part 3 §3.8
# input: no facts, a required key
# expected: ABSTAIN with MISSING_FACT reason
# risk: missing facts are not handled
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0033_missing_fact_abstain() -> None:
    """A missing required fact yields ABSTAIN."""
    result = evaluate_allow([], ["required_key"], [], "SYNTHETIC", None)
    assert result.value == DecisionValue.ABSTAIN
    assert any("MISSING_FACT" in r for r in result.reason_codes)


# ---------------------------------------------------------------------------
# T-KRN-0034 — SECONDARY input never gives ALLOW
# ---------------------------------------------------------------------------
# id: T-KRN-0034
# title: SECONDARY input never gives ALLOW
# purpose: Verify that a SECONDARY-labeled fact cannot produce ALLOW.
# level: fast
# requirement: P03-T04, Part 3 §3.8
# input: a fact with SECONDARY label
# expected: ABSTAIN, not ALLOW
# risk: weak-label data supports ALLOW
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0034_secondary_never_allow() -> None:
    """A SECONDARY-labeled fact yields ABSTAIN, never ALLOW."""
    facts = [FactEntry("key", "value", "VERIFIED", "SECONDARY")]
    result = evaluate_allow(facts, ["key"], [], "SYNTHETIC", None)
    assert result.value != DecisionValue.ALLOW
    assert result.value == DecisionValue.ABSTAIN


# ---------------------------------------------------------------------------
# T-KRN-0035 — SYNTHETIC-origin ALLOW carries the stamp
# ---------------------------------------------------------------------------
# id: T-KRN-0035
# title: SYNTHETIC-origin ALLOW carries the stamp
# purpose: Verify that an ALLOW on SYNTHETIC data is stamped SYNTHETIC.
# level: fast
# requirement: P03-T04, Part 3 §3.8, decision D-26
# input: SYNTHETIC data origin with VALIDATED_TENANT basis
# expected: ALLOW with stamped_label='SYNTHETIC'
# risk: SYNTHETIC ALLOW is not stamped
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0035_synthetic_allow_stamped() -> None:
    """SYNTHETIC-origin ALLOW carries the SYNTHETIC stamp."""
    facts = [FactEntry("key", "value", "VERIFIED", "OFFICIAL")]
    result = evaluate_allow(facts, ["key"], [], "SYNTHETIC", None)
    assert result.value == DecisionValue.ALLOW
    assert result.stamped_label == "SYNTHETIC"


# ---------------------------------------------------------------------------
# T-KRN-0036 — Real-data ALLOW with CALIBRATED_SYNTHETIC becomes ESCALATE
# ---------------------------------------------------------------------------
# id: T-KRN-0036
# title: Real-data ALLOW with CALIBRATED_SYNTHETIC becomes ESCALATE
# purpose: Verify CALIBRATED_SYNTHETIC on real data escalates.
# level: fast
# requirement: P03-T04, Part 3 §3.8, §5.1.6a
# input: non-SYNTHETIC origin with CALIBRATED_SYNTHETIC basis
# expected: ESCALATE with REVIEW.UNVALIDATED_CALIBRATION reason
# risk: unvalidated calibration supports ALLOW on real data
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0036_calibrated_synthetic_escalates() -> None:
    """CALIBRATED_SYNTHETIC on real data becomes ESCALATE."""
    facts = [FactEntry("key", "value", "VERIFIED", "OFFICIAL")]
    result = evaluate_allow(facts, ["key"], [], "REAL", "CALIBRATED_SYNTHETIC")
    assert result.value == DecisionValue.ESCALATE
    assert "REVIEW.UNVALIDATED_CALIBRATION" in result.reason_codes


# ---------------------------------------------------------------------------
# T-KRN-0037 — Real-data ALLOW with VALIDATED_TENANT stays ALLOW
# ---------------------------------------------------------------------------
# id: T-KRN-0037
# title: Real-data ALLOW with VALIDATED_TENANT stays ALLOW
# purpose: Verify VALIDATED_TENANT basis allows ALLOW on real data.
# level: fast
# requirement: P03-T04, Part 3 §3.8, §5.1.6a
# input: non-SYNTHETIC origin with VALIDATED_TENANT basis
# expected: ALLOW
# risk: validated tenant data is not allowed
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0037_validated_tenant_allows() -> None:
    """VALIDATED_TENANT basis on real data stays ALLOW."""
    facts = [FactEntry("key", "value", "VERIFIED", "OFFICIAL")]
    result = evaluate_allow(facts, ["key"], [], "REAL", "VALIDATED_TENANT")
    assert result.value == DecisionValue.ALLOW


# ---------------------------------------------------------------------------
# T-KRN-0038 — ALLOW without a declared basis is rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0038
# title: ALLOW without a declared basis is rejected
# purpose: Verify that real-data ALLOW without calibration_basis is ABSTAIN.
# level: fast
# requirement: P03-T04, Part 3 §3.8
# input: non-SYNTHETIC origin with None calibration_basis
# expected: ABSTAIN with MISSING_CALIBRATION_BASIS
# risk: ALLOW without basis is permitted
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0038_allow_without_basis_rejected() -> None:
    """Real-data ALLOW without a declared basis is rejected (ABSTAIN)."""
    facts = [FactEntry("key", "value", "VERIFIED", "OFFICIAL")]
    result = evaluate_allow(facts, ["key"], [], "REAL", None)
    assert result.value == DecisionValue.ABSTAIN
    assert any("MISSING_CALIBRATION_BASIS" in r for r in result.reason_codes)


# ---------------------------------------------------------------------------
# T-KRN-0039 — The reader never returns a non-VERIFIED fact
# ---------------------------------------------------------------------------
# id: T-KRN-0039
# title: The reader never returns a non-VERIFIED fact
# purpose: Verify VerifiedFactReader returns None for non-VERIFIED facts.
# level: fast
# requirement: P03-T04, Part 3 §3.3
# input: facts with various statuses
# expected: only VERIFIED facts are returned
# risk: rules read non-VERIFIED facts
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0039_reader_only_verified() -> None:
    """The reader returns only VERIFIED facts."""
    reader = VerifiedFactReader(
        {
            "verified": ("val1", "VERIFIED"),
            "proposed": ("val2", "PROPOSED"),
            "conflicted": ("val3", "CONFLICTED"),
            "superseded": ("val4", "SUPERSEDED"),
            "rejected": ("val5", "REJECTED"),
        }
    )
    assert reader.get("verified") == "val1"
    assert reader.get("proposed") is None
    assert reader.get("conflicted") is None
    assert reader.get("superseded") is None
    assert reader.get("rejected") is None
    assert reader.get("missing") is None


# ---------------------------------------------------------------------------
# T-KRN-0040 — PROPOSED → VERIFIED transition is allowed
# ---------------------------------------------------------------------------
# id: T-KRN-0040
# title: PROPOSED to VERIFIED transition is allowed
# purpose: Verify the standard fact verification transition.
# level: fast
# requirement: P03-T04, Part 3 §3.3
# input: from PROPOSED to VERIFIED
# expected: transition succeeds
# risk: facts cannot be verified
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0040_proposed_to_verified() -> None:
    """PROPOSED → VERIFIED is allowed."""
    assert can_transition("PROPOSED", "VERIFIED")
    assert transition("PROPOSED", "VERIFIED") == "VERIFIED"


# ---------------------------------------------------------------------------
# T-KRN-0041 — VERIFIED → SUPERSEDED transition is allowed
# ---------------------------------------------------------------------------
# id: T-KRN-0041
# title: VERIFIED to SUPERSEDED transition is allowed
# purpose: Verify the supersession transition.
# level: fast
# requirement: P03-T04, Part 3 §3.3
# input: from VERIFIED to SUPERSEDED
# expected: transition succeeds
# risk: facts cannot be superseded
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0041_verified_to_superseded() -> None:
    """VERIFIED → SUPERSEDED is allowed."""
    assert can_transition("VERIFIED", "SUPERSEDED")
    assert transition("VERIFIED", "SUPERSEDED") == "SUPERSEDED"


# ---------------------------------------------------------------------------
# T-KRN-0042 — REJECTED → VERIFIED transition is rejected (terminal state)
# ---------------------------------------------------------------------------
# id: T-KRN-0042
# title: REJECTED is a terminal state
# purpose: Verify that REJECTED cannot transition to any other status.
# level: fast
# requirement: P03-T04, Part 3 §3.3
# input: from REJECTED to VERIFIED
# expected: transition is rejected
# risk: rejected facts are re-verified
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0042_rejected_is_terminal() -> None:
    """REJECTED is terminal — no transitions out."""
    assert not can_transition("REJECTED", "VERIFIED")
    with pytest.raises(ValueError):
        transition("REJECTED", "VERIFIED")

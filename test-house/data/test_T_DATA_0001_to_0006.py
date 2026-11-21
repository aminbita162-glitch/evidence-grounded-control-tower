"""Tests for the label taxonomy helper (P02-T01).

Test IDs: T-DATA-0001 to T-DATA-0006.
Covers: order total preorder with SIMULATED_RULE=SYNTHETIC tie; weakest_of
associativity, commutativity, idempotency; ALLOW-eligibility; unknown-label
rejection.

Spec: Part 3 §3.8; schemas/labels.json; data/labels/__init__.py.
"""

from __future__ import annotations

from itertools import combinations_with_replacement

import pytest

from data.labels import (
    ALLOW_ELIGIBLE,
    LABEL_RANKS,
    LABELS,
    LabelError,
    compare_labels,
    is_allow_eligible,
    weakest_of,
)

# ---------------------------------------------------------------------------
# T-DATA-0001: total preorder with stated order
# ---------------------------------------------------------------------------

_EXPECTED_ORDER = [
    ("OFFICIAL", "DERIVED"),
    ("DERIVED", "SECONDARY"),
    ("SECONDARY", "SIMULATED_RULE"),
    ("SECONDARY", "SYNTHETIC"),
    ("SIMULATED_RULE", "ASSUMPTION"),
    ("SYNTHETIC", "ASSUMPTION"),
    ("ASSUMPTION", "UNVERIFIED"),
]


@pytest.mark.fast
@pytest.mark.parametrize("stronger,weaker", _EXPECTED_ORDER)
def test_T_DATA_0001_label_order(stronger: str, weaker: str) -> None:
    """T-DATA-0001: strength order is a total preorder with the stated tie.

    id: T-DATA-0001
    title: Label strength order is a total preorder with stated tie
    purpose: Verify order is total preorder with SIMULATED_RULE=SYNTHETIC tie.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: all 7 labels
    expected: OFFICIAL > DERIVED > SECONDARY > {SIMULATED_RULE=SYNTHETIC} > ASSUMPTION > UNVERIFIED
    risk: label ordering error yields wrong ALLOW eligibility decision
    owning capability: data-labels
    """
    assert compare_labels(stronger, weaker) > 0
    assert compare_labels(weaker, stronger) < 0


@pytest.mark.fast
def test_T_DATA_0001_total_preorder_reflexive() -> None:
    """T-DATA-0001: strength order is a total preorder with the stated tie.

    id: T-DATA-0001
    title: Label strength order is a total preorder with stated tie
    purpose: Verify order is total preorder with SIMULATED_RULE=SYNTHETIC tie.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: all 7 labels
    expected: OFFICIAL > DERIVED > SECONDARY > {SIMULATED_RULE=SYNTHETIC} > ASSUMPTION > UNVERIFIED
    risk: label ordering error yields wrong ALLOW eligibility decision
    owning capability: data-labels
    """
    for label in LABELS:
        assert compare_labels(label, label) == 0, f"{label!r} not equal to itself"


@pytest.mark.fast
def test_T_DATA_0001_total_preorder_all_pairs() -> None:
    """T-DATA-0001: strength order is a total preorder with the stated tie.

    id: T-DATA-0001
    title: Label strength order is a total preorder with stated tie
    purpose: Verify order is total preorder with SIMULATED_RULE=SYNTHETIC tie.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: all 7 labels
    expected: OFFICIAL > DERIVED > SECONDARY > {SIMULATED_RULE=SYNTHETIC} > ASSUMPTION > UNVERIFIED
    risk: label ordering error yields wrong ALLOW eligibility decision
    owning capability: data-labels
    """
    for a, b in combinations_with_replacement(LABELS, 2):
        result = compare_labels(a, b)
        reverse = compare_labels(b, a)
        if result > 0:
            assert reverse < 0
        elif result < 0:
            assert reverse > 0
        else:
            assert reverse == 0


# ---------------------------------------------------------------------------
# T-DATA-0002: SIMULATED_RULE and SYNTHETIC are tied
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0002_simulated_rule_synthetic_tied() -> None:
    """T-DATA-0002: SIMULATED_RULE and SYNTHETIC are tied in strength.

    id: T-DATA-0002
    title: SIMULATED_RULE and SYNTHETIC are tied in strength
    purpose: Verify the tie between SIMULATED_RULE and SYNTHETIC.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: SIMULATED_RULE, SYNTHETIC
    expected: compare_labels returns 0
    risk: incorrect tie causes one to dominate the other in weakest_of
    owning capability: data-labels
    """
    assert compare_labels("SIMULATED_RULE", "SYNTHETIC") == 0
    assert compare_labels("SYNTHETIC", "SIMULATED_RULE") == 0
    assert LABEL_RANKS["SIMULATED_RULE"] == LABEL_RANKS["SYNTHETIC"]


# ---------------------------------------------------------------------------
# T-DATA-0003: weakest_of is commutative
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0003_weakest_of_commutative() -> None:
    """T-DATA-0003: weakest_of is commutative.

    id: T-DATA-0003
    title: weakest_of is commutative
    purpose: weakest_of([a, b]) rank equals weakest_of([b, a]) rank for all pairs.
    level: fast
    requirement: P02-T01; Part 3 §3.8 weakest-of rule
    input: all ordered pairs of distinct labels
    expected: commutative result (by rank)
    risk: ordering dependency causes wrong derived label
    owning capability: data-labels
    """
    label_list = sorted(LABELS)
    for a in label_list:
        for b in label_list:
            rank_ab = LABEL_RANKS[weakest_of([a, b])]
            rank_ba = LABEL_RANKS[weakest_of([b, a])]
            assert rank_ab == rank_ba


# ---------------------------------------------------------------------------
# T-DATA-0004: weakest_of is associative
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0004_weakest_of_associative() -> None:
    """T-DATA-0004: weakest_of is associative.

    id: T-DATA-0004
    title: weakest_of is associative
    purpose: weakest_of([a, b, c]) rank equals weakest_of([a, weakest_of([b, c])]) rank.
    level: fast
    requirement: P02-T01; Part 3 §3.8 weakest-of rule
    input: all ordered triples of labels
    expected: associative result (by rank)
    risk: non-associativity causes inconsistent label propagation
    owning capability: data-labels
    """
    label_list = sorted(LABELS)
    for a in label_list:
        for b in label_list:
            for c in label_list:
                direct = LABEL_RANKS[weakest_of([a, b, c])]
                nested = LABEL_RANKS[weakest_of([a, weakest_of([b, c])])]
                assert direct == nested


# ---------------------------------------------------------------------------
# T-DATA-0005: weakest_of is idempotent
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize("label", sorted(LABELS))
def test_T_DATA_0005_weakest_of_idempotent_pair(label: str) -> None:
    """T-DATA-0005: weakest_of is idempotent.

    id: T-DATA-0005
    title: weakest_of is idempotent
    purpose: weakest_of([x, x]) equals x and weakest_of([x]) equals x.
    level: fast
    requirement: P02-T01; Part 3 §3.8 weakest-of rule
    input: each of the 7 labels
    expected: same label returned
    risk: non-idempotency changes label on self-composition
    owning capability: data-labels
    """
    assert weakest_of([label, label]) == label
    assert weakest_of([label]) == label


# ---------------------------------------------------------------------------
# T-DATA-0006: ALLOW eligibility and unknown label rejection
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize("label", ["OFFICIAL", "DERIVED"])
def test_T_DATA_0006_allow_eligible(label: str) -> None:
    """T-DATA-0006: only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected.

    id: T-DATA-0006
    title: Only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected
    purpose: Verify ALLOW-eligibility and that unknown labels are rejected.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: all 7 labels; unknown label string
    expected: OFFICIAL and DERIVED eligible; others not; unknown raises LabelError
    risk: wrong eligibility allows weak-evidence ALLOW decisions
    owning capability: data-labels
    """
    assert is_allow_eligible(label)


@pytest.mark.fast
@pytest.mark.parametrize(
    "label", ["SECONDARY", "SIMULATED_RULE", "SYNTHETIC", "ASSUMPTION", "UNVERIFIED"]
)
def test_T_DATA_0006_not_allow_eligible(label: str) -> None:
    """T-DATA-0006: only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected.

    id: T-DATA-0006
    title: Only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected
    purpose: Verify ALLOW-eligibility and that unknown labels are rejected.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: all 7 labels; unknown label string
    expected: OFFICIAL and DERIVED eligible; others not; unknown raises LabelError
    risk: wrong eligibility allows weak-evidence ALLOW decisions
    owning capability: data-labels
    """
    assert not is_allow_eligible(label)


@pytest.mark.fast
def test_T_DATA_0006_allow_eligible_set_and_rejection() -> None:
    """T-DATA-0006: only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected.

    id: T-DATA-0006
    title: Only OFFICIAL and DERIVED are ALLOW-eligible; unknown label rejected
    purpose: Verify ALLOW-eligibility and that unknown labels are rejected.
    level: fast
    requirement: P02-T01; Part 3 §3.8
    input: all 7 labels; unknown label string
    expected: OFFICIAL and DERIVED eligible; others not; unknown raises LabelError
    risk: wrong eligibility allows weak-evidence ALLOW decisions
    owning capability: data-labels
    """
    assert frozenset({"OFFICIAL", "DERIVED"}) == ALLOW_ELIGIBLE
    with pytest.raises(LabelError):
        compare_labels("BOGUS", "OFFICIAL")
    with pytest.raises(LabelError):
        weakest_of(["OFFICIAL", "UNKNOWN_LABEL"])
    with pytest.raises(LabelError):
        is_allow_eligible("FAKE_LABEL")
    with pytest.raises(ValueError):
        weakest_of([])

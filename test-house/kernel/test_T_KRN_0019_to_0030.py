"""Tests for core value types and the decision lattice (P03-T03).

Test IDs: T-KRN-0019 to T-KRN-0030.
Covers: lattice associativity, commutativity, idempotency, monotonicity
(property tests); combined reasons = union of inputs; floats rejected in
Money and Quantity; rounding mode mandatory; weakest-of agrees with the
P02 helper on all label pairs; Money currency mismatch; Duration validation;
Identifier immutability.

Spec: Part 3 §3.3, §3.8; kernel/types/; kernel/ports/; schemas/labels.json.
"""

from __future__ import annotations

from decimal import Decimal
from itertools import combinations_with_replacement, product

import pytest

from kernel.types.decision import DecisionValue, combine_decisions
from kernel.types.identifier import Identifier
from kernel.types.label import label_rank, weakest_of
from kernel.types.money import Money
from kernel.types.quantity import Quantity
from kernel.types.time import Duration

_DECISION_VALUES = list(DecisionValue)
_all_pairs = list(combinations_with_replacement(_DECISION_VALUES, 2))
_all_triples = list(product(_DECISION_VALUES, repeat=3))


# ---------------------------------------------------------------------------
# T-KRN-0019 — Lattice combine is associative
# ---------------------------------------------------------------------------
# id: T-KRN-0019
# title: Lattice combine is associative
# purpose: Verify (a combine b) combine c == a combine (b combine c).
# level: fast
# requirement: P03-T03, Part 3 §3.8
# input: all triples of DecisionValue
# expected: associativity holds for every triple
# risk: combine is not associative, yielding different results for different grouping
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0019_combine_associative() -> None:
    """combine_decisions is associative over all triples."""
    for a, b, c in _all_triples:
        left, _ = combine_decisions([a, b], [[], []])
        right_val, right_reasons = combine_decisions([left, c], [[], []])
        left2, _ = combine_decisions([b, c], [[], []])
        left_val, left_reasons = combine_decisions([a, left2], [[], []])
        assert right_val == left_val, f"associativity failed for {a}, {b}, {c}"


# ---------------------------------------------------------------------------
# T-KRN-0020 — Lattice combine is commutative
# ---------------------------------------------------------------------------
# id: T-KRN-0020
# title: Lattice combine is commutative
# purpose: Verify a combine b == b combine a.
# level: fast
# requirement: P03-T03, Part 3 §3.8
# input: all pairs of DecisionValue
# expected: commutativity holds for every pair
# risk: combine is order-dependent
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0020_combine_commutative() -> None:
    """combine_decisions is commutative over all pairs."""
    for a, b in _all_pairs:
        ab, _ = combine_decisions([a, b], [[], []])
        ba, _ = combine_decisions([b, a], [[], []])
        assert ab == ba, f"commutativity failed for {a}, {b}"


# ---------------------------------------------------------------------------
# T-KRN-0021 — Lattice combine is idempotent
# ---------------------------------------------------------------------------
# id: T-KRN-0021
# title: Lattice combine is idempotent
# purpose: Verify a combine a == a.
# level: fast
# requirement: P03-T03, Part 3 §3.8
# input: every DecisionValue
# expected: combining a value with itself yields the same value
# risk: duplicate inputs produce a different result
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0021_combine_idempotent() -> None:
    """combine_decisions is idempotent: a combine a == a."""
    for v in _DECISION_VALUES:
        result, _ = combine_decisions([v, v], [[], []])
        assert result == v, f"idempotency failed for {v}"


# ---------------------------------------------------------------------------
# T-KRN-0022 — Lattice combine is monotone (property test)
# ---------------------------------------------------------------------------
# id: T-KRN-0022
# title: Lattice combine is monotone
# purpose: Verify combine(a, b) >= max(a, b) always.
# level: fast
# requirement: P03-T03, Part 3 §3.8
# input: all pairs of DecisionValue
# expected: the combined value is at least as severe as both inputs
# risk: combine produces a less severe result than an input
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0022_combine_monotone() -> None:
    """combine_decisions is monotone: result >= max(inputs)."""
    for a, b in _all_pairs:
        result, _ = combine_decisions([a, b], [[], []])
        assert result >= max(a, b), f"monotonicity failed for {a}, {b}"


# ---------------------------------------------------------------------------
# T-KRN-0023 — Combined reasons equal the union of inputs
# ---------------------------------------------------------------------------
# id: T-KRN-0023
# title: Combined reasons equal the union of inputs
# purpose: Verify combine keeps all reason codes from every input.
# level: fast
# requirement: P03-T03, Part 3 §3.8
# input: two decisions with distinct reason codes
# expected: combined reasons contain all codes from both inputs
# risk: reason codes are dropped during combination
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0023_combined_reasons_union() -> None:
    """combine_decisions unions all reason codes."""
    _, reasons = combine_decisions(
        [DecisionValue.HOLD, DecisionValue.ESCALATE],
        [["R1", "R2"], ["R3"]],
    )
    assert set(reasons) == {"R1", "R2", "R3"}


# ---------------------------------------------------------------------------
# T-KRN-0024 — Floats are rejected in Money
# ---------------------------------------------------------------------------
# id: T-KRN-0024
# title: Floats are rejected in Money
# purpose: Verify Money rejects float amounts.
# level: fast
# requirement: P03-T03, Part 3 §3.3
# input: a Money with a float amount
# expected: TypeError is raised
# risk: floating-point money causes precision errors
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0024_floats_rejected_in_money() -> None:
    """Money rejects float amounts."""
    Money(amount=Decimal("3.14"), currency="USD")  # OK — Decimal is valid
    with pytest.raises(TypeError):
        Money(amount=3.14, currency="USD")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# T-KRN-0025 — Floats are rejected in Quantity
# ---------------------------------------------------------------------------
# id: T-KRN-0025
# title: Floats are rejected in Quantity
# purpose: Verify Quantity rejects float values.
# level: fast
# requirement: P03-T03, Part 3 §3.3
# input: a Quantity with a float value
# expected: TypeError is raised
# risk: floating-point quantities cause precision errors
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0025_floats_rejected_in_quantity() -> None:
    """Quantity rejects float values."""
    with pytest.raises(TypeError):
        Quantity(value=3.14, unit="kg")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# T-KRN-0026 — Rounding mode is mandatory in Money
# ---------------------------------------------------------------------------
# id: T-KRN-0026
# title: Rounding mode is mandatory in Money
# purpose: Verify Money has a rounding mode (default is explicit).
# level: fast
# requirement: P03-T03, Part 3 §3.3
# input: a Money instance
# expected: rounding attribute is not None
# risk: arithmetic without explicit rounding causes ambiguous results
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0026_rounding_mode_mandatory() -> None:
    """Money has a non-None rounding mode."""
    m = Money(amount=Decimal("10.00"), currency="USD")
    assert m.rounding is not None


# ---------------------------------------------------------------------------
# T-KRN-0027 — Weakest-of agrees with the P02 helper on all label pairs
# ---------------------------------------------------------------------------
# id: T-KRN-0027
# title: Weakest-of agrees with the P02 helper on all label pairs
# purpose: Verify kernel weakest_of matches data.labels.weakest_of.
# level: fast
# requirement: P03-T03, Part 3 §3.8
# input: all pairs of labels
# expected: kernel weakest_of returns the same label as the P02 helper
# risk: the kernel label logic diverges from the P02 helper
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0027_weakest_of_agrees_with_p2() -> None:
    """kernel weakest_of matches data.labels.weakest_of for all pairs."""
    from data.labels import weakest_of as p2_weakest_of
    from kernel.types.label import LABELS

    for a in LABELS:
        for b in LABELS:
            assert label_rank(weakest_of(a, b)) == label_rank(p2_weakest_of([a, b])), (
                f"weakest_of mismatch for {a!r}, {b!r}"
            )


# ---------------------------------------------------------------------------
# T-KRN-0028 — Money add with mismatched currency fails
# ---------------------------------------------------------------------------
# id: T-KRN-0028
# title: Money add with mismatched currency fails
# purpose: Verify Money.add rejects different currencies.
# level: fast
# requirement: P03-T03, Part 3 §3.3
# input: two Money with different currencies
# expected: ValueError is raised
# risk: money is added across currencies silently
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0028_money_currency_mismatch() -> None:
    """Money.add rejects different currencies."""
    a = Money(amount=Decimal("10.00"), currency="USD")
    b = Money(amount=Decimal("5.00"), currency="EUR")
    with pytest.raises(ValueError):
        a.add(b)


# ---------------------------------------------------------------------------
# T-KRN-0029 — Duration rejects negative values
# ---------------------------------------------------------------------------
# id: T-KRN-0029
# title: Duration rejects negative values
# purpose: Verify Duration rejects negative seconds.
# level: fast
# requirement: P03-T03, Part 3 §3.3
# input: a Duration with negative seconds
# expected: ValueError is raised
# risk: negative durations cause logic errors
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0029_duration_rejects_negative() -> None:
    """Duration rejects negative seconds."""
    with pytest.raises(ValueError):
        Duration(seconds=-1)


# ---------------------------------------------------------------------------
# T-KRN-0030 — Identifier is opaque and immutable
# ---------------------------------------------------------------------------
# id: T-KRN-0030
# title: Identifier is opaque and immutable
# purpose: Verify Identifier is frozen and holds a string value.
# level: fast
# requirement: P03-T03, Part 3 §3.3
# input: an Identifier instance
# expected: field mutation raises; str() returns the value
# risk: identifiers are mutable or non-string
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0030_identifier_immutable() -> None:
    """Identifier is frozen and opaque."""
    ident = Identifier(value="case-001")
    assert str(ident) == "case-001"
    with pytest.raises(AttributeError):
        ident.value = "changed"  # type: ignore[misc]

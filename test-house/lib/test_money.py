"""Known answers, properties and differential checks for fixed-point money."""

from decimal import Context, Decimal, Inexact
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from kernel.lib.money import (
    CurrencyTable,
    Money,
    RateDatum,
    RoundAt,
    RoundingRule,
    add,
    allocate,
    convert,
    round_at,
    within_tolerance,
)

_TABLE = CurrencyTable({"USD": 2, "JPY": 0}, "SYN-FX-TABLE")
_CONTEXT = Context(prec=20)


def _usd(value: str) -> Money:
    return Money(Decimal(value), "USD")


def _cents(value: int) -> Money:
    return Money(Decimal(value).scaleb(-2, context=_CONTEXT), "USD")


def _add(left: Money, right: Money) -> Money:
    return add(left, right, currencies=_TABLE, context=_CONTEXT)


def _round(mode: str, expected: str) -> None:
    rule = RoundingRule(RoundAt.LINE, mode, "SYN-RULE")
    result = round_at(_usd("-1.005"), RoundAt.LINE, currencies=_TABLE, context=_CONTEXT, rule=rule)
    assert result.money.amount == Decimal(expected)


@pytest.mark.fast
def test_T_LIB_0011() -> None:
    """Check round half even.

    id: T-LIB-0011
    title: Round half even
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round half even
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_HALF_EVEN", "-1.00")


@pytest.mark.fast
def test_T_LIB_0012() -> None:
    """Check round half up.

    id: T-LIB-0012
    title: Round half up
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round half up
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_HALF_UP", "-1.01")


@pytest.mark.fast
def test_T_LIB_0013() -> None:
    """Check round half down.

    id: T-LIB-0013
    title: Round half down
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round half down
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_HALF_DOWN", "-1.00")


@pytest.mark.fast
def test_T_LIB_0014() -> None:
    """Check round toward positive infinity.

    id: T-LIB-0014
    title: Round toward positive infinity
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round toward positive infinity
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_CEILING", "-1.00")


@pytest.mark.fast
def test_T_LIB_0015() -> None:
    """Check round toward negative infinity.

    id: T-LIB-0015
    title: Round toward negative infinity
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round toward negative infinity
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_FLOOR", "-1.01")


@pytest.mark.fast
def test_T_LIB_0016() -> None:
    """Check round away from zero.

    id: T-LIB-0016
    title: Round away from zero
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round away from zero
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_UP", "-1.01")


@pytest.mark.fast
def test_T_LIB_0017() -> None:
    """Check round toward zero.

    id: T-LIB-0017
    title: Round toward zero
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round toward zero
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_DOWN", "-1.00")


@pytest.mark.fast
def test_T_LIB_0018() -> None:
    """Check round away from zero when the retained digit is zero or five.

    id: T-LIB-0018
    title: Round away from zero when the retained digit is zero or five
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Round away from zero when the retained digit is zero or five
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    _round("ROUND_05UP", "-1.01")


@pytest.mark.fast
@given(*([st.integers(-(10**8), 10**8)] * 3))
def test_T_LIB_0019(a: int, b: int, c: int) -> None:
    """Check add exact amounts associatively.

    id: T-LIB-0019
    title: Add exact amounts associatively
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Add exact amounts associatively
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    left = _add(_add(_cents(a), _cents(b)), _cents(c))
    right = _add(_cents(a), _add(_cents(b), _cents(c)))
    assert left == right


@pytest.mark.fast
@given(st.integers(-(10**8), 10**8), st.integers(1, 100), st.integers(0, 100))
def test_T_LIB_0020(total: int, a: int, b: int) -> None:
    """Check conserve total units across allocations.

    id: T-LIB-0020
    title: Conserve total units across allocations
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Conserve total units across allocations
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    allocation = allocate(_cents(total), {"A": a, "B": b}, currencies=_TABLE, context=_CONTEXT)
    assert sum(value.amount for value in allocation.values()) == _cents(total).amount


@pytest.mark.fast
def test_T_LIB_0021() -> None:
    """Check reject mixed currencies without conversion.

    id: T-LIB-0021
    title: Reject mixed currencies without conversion
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Reject mixed currencies without conversion
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    with pytest.raises(ValueError, match="mixed currencies"):
        _add(_usd("4"), Money(Decimal(1), "JPY"))


@pytest.mark.fast
def test_T_LIB_0022() -> None:
    """Check retain the recorded conversion rate and weakest label.

    id: T-LIB-0022
    title: Retain the recorded conversion rate and weakest label
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Retain the recorded conversion rate and weakest label
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    rate = RateDatum("USD", "JPY", Decimal("2.5"), "SYN-RATE", "SYNTHETIC")
    result = convert(_usd("4"), rate, label="DERIVED", currencies=_TABLE, context=_CONTEXT)
    assert result.money == Money(Decimal(10), "JPY")
    assert result.rate == rate
    assert result.label == "SYNTHETIC"


@pytest.mark.fast
def test_T_LIB_0023() -> None:
    """Check require the rate direction to match.

    id: T-LIB-0023
    title: Require the rate direction to match
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Require the rate direction to match
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    rate = RateDatum("JPY", "USD", Decimal("2.5"), "SYN-RATE", "SYNTHETIC")
    with pytest.raises(ValueError, match="does not apply"):
        convert(_usd("4"), rate, label="SYNTHETIC", currencies=_TABLE, context=_CONTEXT)


@pytest.mark.fast
def test_T_LIB_0024() -> None:
    """Check reject currencies absent from the pack.

    id: T-LIB-0024
    title: Reject currencies absent from the pack
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Reject currencies absent from the pack
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    with pytest.raises(ValueError, match="absent"):
        _add(_usd("4"), Money(Decimal(1), "EUR"))


@pytest.mark.fast
def test_T_LIB_0025() -> None:
    """Check keep exact amounts until the declared rounding point.

    id: T-LIB-0025
    title: Keep exact amounts until the declared rounding point
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Keep exact amounts until the declared rounding point
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    amount = _usd("1.005")
    rule = RoundingRule(RoundAt.TOTAL, "ROUND_HALF_UP", "SYN-RULE")
    assert (
        round_at(amount, RoundAt.LINE, currencies=_TABLE, context=_CONTEXT, rule=rule).money
        == amount
    )
    rounded = round_at(amount, RoundAt.TOTAL, currencies=_TABLE, context=_CONTEXT, rule=rule)
    assert rounded.money.amount == Decimal("1.01")
    assert rounded.source_id == "SYN-RULE"


@pytest.mark.fast
def test_T_LIB_0026() -> None:
    """Check label fallback presentation rounding as an assumption.

    id: T-LIB-0026
    title: Label fallback presentation rounding as an assumption
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Label fallback presentation rounding as an assumption
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    rounded = round_at(_usd("1.005"), RoundAt.PRESENTATION, currencies=_TABLE, context=_CONTEXT)
    assert rounded.money.amount == Decimal("1.00")
    assert rounded.label == "ASSUMPTION"


@pytest.mark.fast
@given(st.integers(-100000, 100000))
def test_T_LIB_0027(value: int) -> None:
    """Check compare roundings against a rational oracle.

    id: T-LIB-0027
    title: Compare roundings against a rational oracle
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Compare roundings against a rational oracle
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    amount = Money(Decimal(value).scaleb(-3, context=_CONTEXT), "USD")
    rounded = round_at(amount, RoundAt.PRESENTATION, currencies=_TABLE, context=_CONTEXT)
    assert Fraction(rounded.money.amount) == Fraction(round(Fraction(value, 10)), 100)


@pytest.mark.fast
def test_T_LIB_0028() -> None:
    """Check break allocation ties by key.

    id: T-LIB-0028
    title: Break allocation ties by key
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Break allocation ties by key
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    allocation = allocate(_usd("0.01"), {"B": 1, "A": 1}, currencies=_TABLE, context=_CONTEXT)
    assert allocation == {"A": _usd("0.01"), "B": _usd("0.00")}


@pytest.mark.fast
def test_T_LIB_0029() -> None:
    """Check reject implicit rounding of working amounts.

    id: T-LIB-0029
    title: Reject implicit rounding of working amounts
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Reject implicit rounding of working amounts
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    with pytest.raises(Inexact):
        add(_usd("1.01"), _usd("0.01"), currencies=_TABLE, context=Context(prec=2))


@pytest.mark.fast
def test_T_LIB_0030() -> None:
    """Check compare at currency minor units with explicit tolerance.

    id: T-LIB-0030
    title: Compare at currency minor units with explicit tolerance
    purpose: Verify exact arithmetic and the recorded rounding policy
    level: fast
    requirement: P13-T02
    input: Synthetic monetary amounts and explicit arithmetic settings
    expected: Compare at currency minor units with explicit tolerance
    risk: An arithmetic or rounding error changes an advisory outcome
    capability: shared-library
    """
    assert within_tolerance(
        _usd("1.005"),
        _usd("1.014"),
        tolerance_units=1,
        rounding="ROUND_HALF_EVEN",
        currencies=_TABLE,
        context=_CONTEXT,
    )
    assert not within_tolerance(
        _usd("1.005"),
        _usd("1.014"),
        tolerance_units=0,
        rounding="ROUND_HALF_EVEN",
        currencies=_TABLE,
        context=_CONTEXT,
    )

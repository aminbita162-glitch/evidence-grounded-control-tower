"""Replay, provenance and stability checks for calculation trees."""

from dataclasses import replace
from decimal import Decimal, Inexact, localcontext

import pytest

from kernel.contracts._generated.decision import Decision
from kernel.lib.calctrace import (
    Calculation,
    DecimalSettings,
    Formula,
    Operand,
    Operation,
    calculate,
    with_calculations,
)

_SETTINGS = DecimalSettings(precision=12, rounding="ROUND_HALF_EVEN")


def _operand(value: str, unit: str = "USD", label: str = "SYNTHETIC") -> Operand:
    return Operand("SYN-OPERAND", Decimal(value), unit, label)


def _calculate(
    operation: Operation,
    left: Operand | Calculation,
    right: Operand | Calculation,
    *,
    unit: str = "USD",
) -> Calculation:
    return calculate(
        Formula(operation, 1, operation, "SYN-RULE"), _SETTINGS, left, right, unit=unit
    )


def _sum() -> Calculation:
    return _calculate(Operation.ADD, _operand("1.50"), _operand("2.00"))


@pytest.mark.fast
def test_T_LIB_0031() -> None:
    """Check replay a money sum.

    id: T-LIB-0031
    title: Replay a money sum
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Replay a money sum
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _sum()
    assert trace.result.value == Decimal("3.50")
    assert trace.replay() == trace.result


@pytest.mark.fast
def test_T_LIB_0032() -> None:
    """Check replay a quantity difference.

    id: T-LIB-0032
    title: Replay a quantity difference
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Replay a quantity difference
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _calculate(Operation.SUBTRACT, _operand("4", "kg"), _operand("1.5", "kg"), unit="kg")
    assert trace.replay().value == Decimal("2.5")


@pytest.mark.fast
def test_T_LIB_0033() -> None:
    """Check replay nested arithmetic.

    id: T-LIB-0033
    title: Replay nested arithmetic
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Replay nested arithmetic
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _calculate(Operation.MULTIPLY, _sum(), _operand("2", "kg"), unit="USD")
    assert trace.replay().value == Decimal("7.00")
    assert trace.payload()["type"] == "CALCULATION_TRACE"


@pytest.mark.fast
def test_T_LIB_0034() -> None:
    """Check preserve the weaker label through nesting.

    id: T-LIB-0034
    title: Preserve the weaker label through nesting
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Preserve the weaker label through nesting
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    weak = _operand("2", "kg", "UNVERIFIED")
    trace = _calculate(Operation.MULTIPLY, _sum(), weak, unit="USD")
    assert trace.replay().label == "UNVERIFIED"


@pytest.mark.fast
def test_T_LIB_0035() -> None:
    """Check use context-specific quantization.

    id: T-LIB-0035
    title: Use context-specific quantization
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Use context-specific quantization
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _calculate(Operation.QUANTIZE, _operand("1.005"), _operand("0.01"))
    assert trace.replay().value == Decimal("1.00")


@pytest.mark.fast
def test_T_LIB_0036() -> None:
    """Check reject a modified recorded output.

    id: T-LIB-0036
    title: Reject a modified recorded output
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Reject a modified recorded output
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _sum()
    tampered = replace(trace, result=replace(trace.result, value=Decimal(99)))
    with pytest.raises(ValueError, match="does not reproduce"):
        tampered.replay()


@pytest.mark.fast
def test_T_LIB_0037() -> None:
    """Check produce stable hashes for identical trees.

    id: T-LIB-0037
    title: Produce stable hashes for identical trees
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Produce stable hashes for identical trees
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    assert _sum().digest() == _sum().digest()
    assert len(_sum().digest()) == 64


@pytest.mark.fast
def test_T_LIB_0038() -> None:
    """Check commit operand and rule provenance to the hash.

    id: T-LIB-0038
    title: Commit operand and rule provenance to the hash
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Commit operand and rule provenance to the hash
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _sum()
    other = replace(trace, formula=replace(trace.formula, rule_or_source="SYN-RULE-02"))
    assert trace.digest() != other.digest()


@pytest.mark.fast
def test_T_LIB_0039() -> None:
    """Check use recorded context instead of ambient context.

    id: T-LIB-0039
    title: Use recorded context instead of ambient context
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Use recorded context instead of ambient context
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _sum()
    with localcontext() as ambient:
        ambient.prec = 1
        assert trace.replay().value == Decimal("3.50")
        assert _sum().digest() == trace.digest()


@pytest.mark.fast
def test_T_LIB_0040() -> None:
    """Check keep existing decision data when adding unique trace references.

    id: T-LIB-0040
    title: Keep existing Decision data when adding unique trace references
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Keep existing Decision data when adding unique trace references
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    decision = Decision(
        tenant_id="SYN-TEN",
        schema_version=1,
        decision_id="SYN-DECISION",
        value="HOLD",
        reason_codes=["SYN-REASON"],
        evaluation_time="SYN-TIME",
        configuration_hash="0" * 64,
    )
    trace = _sum()
    bound = with_calculations(decision, trace, trace)
    assert bound.calculation_trace_hashes == [trace.digest()]
    assert bound.reason_codes == decision.reason_codes
    assert decision.calculation_trace_hashes is None


@pytest.mark.fast
def test_T_LIB_0041() -> None:
    """Check reject incompatible units on addition.

    id: T-LIB-0041
    title: Reject incompatible units on addition
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Reject incompatible units on addition
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    with pytest.raises(ValueError, match="matching units"):
        _calculate(Operation.ADD, _operand("1"), _operand("1", "kg"))


@pytest.mark.fast
def test_T_LIB_0042() -> None:
    """Check keep exact division and reject unrecorded rounding.

    id: T-LIB-0042
    title: Keep exact division and reject unrecorded rounding
    purpose: Verify replay and provenance of computed costs and quantities
    level: fast
    requirement: P13-T03
    input: Synthetic operands with declared formula and context
    expected: Keep exact division and reject unrecorded rounding
    risk: A computed amount cannot be explained or replayed
    capability: shared-library
    """
    trace = _calculate(Operation.DIVIDE, _operand("8"), _operand("4", "kg"), unit="USD/kg")
    assert trace.replay().value == Decimal(2)
    with pytest.raises(Inexact):
        _calculate(Operation.DIVIDE, _operand("1"), _operand("3", "kg"), unit="USD/kg")

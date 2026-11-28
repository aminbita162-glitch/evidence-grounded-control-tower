"""Check landed-cost invariants against exact arithmetic and K05."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.k05 import Line, ReferencePack, ValuationInputs
from capabilities.k05 import evaluate as k05
from capabilities.l02 import (
    Component,
    DutyKind,
    DutyPack,
    DutyRate,
    Estimate,
    Goods,
    Kind,
    Preference,
    Range,
    Reason,
    TaxRate,
    evaluate,
)
from kernel.decision import FactEntry
from kernel.lib.money import CurrencyTable, Money, RateDatum, RoundAt, RoundingRule
from kernel.lib.valuation import Adjustment, FxPack, ValuationRule

DAY = date(2024, 3, 1)
AT = datetime(2024, 3, 1, tzinfo=UTC)
FROM, TO = DAY - timedelta(days=30), DAY + timedelta(days=30)
SRC = "SRC-SYNTHETIC-L02"
CURRENCIES = CurrencyTable({"USD": 2, "EUR": 2}, SRC)
FX = FxPack("synthetic-fx", CURRENCIES, {}, "DERIVED")
RULES = {"CIF": ValuationRule("synthetic-cif", (), "DERIVED")}
GOODS = Goods(
    "G1",
    "1101",
    Money(Decimal(100), "USD"),
    "DERIVED",
    SRC,
    "CIF",
    DAY,
    {},
    Decimal(10),
    Decimal(25),
    quantities_verified=True,
)
AD = DutyRate("D1", "1101", DutyKind.AD_VALOREM, "USD", "DERIVED", FROM, TO, Decimal("0.05"))
TAX = TaxRate("T1", "VAT", "DERIVED", Decimal("0.10"), ("VALUATION", "DUTY"), FROM, TO)


def cost(
    goods: Goods = GOODS,
    rate: DutyRate = AD,
    *,
    taxes: tuple[TaxRate, ...] = (TAX,),
    components: tuple[Component, ...] = (),
    fx: FxPack = FX,
    facts: tuple[FactEntry, ...] = (),
    required: frozenset[str] = frozenset(),
) -> Estimate:
    return evaluate(
        (goods,),
        components=components,
        rates=DutyPack("1", SRC, FROM, TO, (rate,)),
        taxes=taxes,
        fx=fx,
        valuation_rules=RULES,
        currency="USD",
        at=DAY,
        facts=facts,
        required_components=required,
    )


def actual(result: Estimate) -> Decimal:
    assert result.total is not None
    return result.total.base


def component(code: str, value: str = "20", currency: str = "USD") -> Component:
    return Component(code, Range.exact(Decimal(value)), currency, Kind.DOCUMENT, "DERIVED", SRC)


@pytest.mark.fast
@given(price=st.integers(1, 10**10), factor=st.integers(1, 10**5))
def test_T_L02_0201_ad_valorem_scales(price: int, factor: int) -> None:
    """
    id: T-L02-0201
    title: Ad valorem duty scales with goods value
    purpose: Detect nonlinear or rounded intermediate arithmetic
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Generated synthetic prices and factors
    expected: Duty scales exactly with price
    risk: HZ-03
    capability: L02
    """
    first = cost(replace(GOODS, value=Money(Decimal(price), "USD"))).duties[0]
    scaled = cost(replace(GOODS, value=Money(Decimal(price * factor), "USD"))).duties[0]
    assert scaled.amount == first.amount * factor


@pytest.mark.fast
@given(price=st.integers(1, 10**9), rate=st.integers(0, 80), tax=st.integers(0, 50))
def test_T_L02_0202_fraction_oracle(price: int, rate: int, tax: int) -> None:
    """
    id: T-L02-0202
    title: Duty and tax match a rational oracle
    purpose: Check independently computed decimal products and total
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Generated synthetic integer prices and proportional rates
    expected: Duty, tax and their total agree with exact fractions
    risk: HZ-03
    capability: L02
    """
    report = cost(
        replace(GOODS, value=Money(Decimal(price), "USD")),
        replace(AD, ad_valorem=Decimal(rate).scaleb(-2)),
        taxes=(replace(TAX, rate=Decimal(tax).scaleb(-2)),),
    )
    duty = price * Fraction(rate, 100)
    vat = (price + duty) * Fraction(tax, 100)
    assert Fraction(report.duties[0].amount) == duty
    assert Fraction(actual(report)) == price + duty + vat


@pytest.mark.fast
@given(price=st.integers(1, 10**8))
def test_T_L02_0203_parallel_k05_and_l02_basis(price: int) -> None:
    """
    id: T-L02-0203
    title: K05 and L02 produce an identical basis
    purpose: Verify the two consumers use the shared documentary valuation
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Generated synthetic shipment values
    expected: Basis amount and provenance match K05
    risk: HZ-03
    capability: L02
    """
    amount = Money(Decimal(price), "USD")
    goods = replace(GOODS, value=amount)
    other = k05(
        ValuationInputs(
            amount,
            amount,
            "CIF",
            DAY,
            {},
            (Line(goods.id, goods.code, amount, Decimal(1), "kg", goods.label),),
            goods.label,
        ),
        at=AT,
        fx=FX,
        rules=RULES,
        reference=ReferencePack(
            "test-reference", "SYNTHETIC", SRC, AT, AT + timedelta(days=1), {}, {}, {}
        ),
        calibration=None,
        data_origin="SYNTHETIC",
    )
    assert cost(goods).duties[0].basis == other.basis


@pytest.mark.fast
def test_T_L02_0204_specific_weight_conversion() -> None:
    """
    id: T-L02-0204
    title: Specific weight conversion
    purpose: Specific weight conversion
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Specific weight conversion
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, kind=DutyKind.SPECIFIC, specific=Decimal(2))
    assert (
        cost(rate=rate).duties[0].amount
        == cost(replace(GOODS, weight=Decimal(25000), weight_unit="g"), rate).duties[0].amount
    )


@pytest.mark.fast
def test_T_L02_0205_ad_valorem_exact() -> None:
    """
    id: T-L02-0205
    title: Ad valorem exact
    purpose: Ad valorem exact
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Ad valorem exact
    risk: HZ-03
    capability: L02
    """
    assert cost().duties[0].amount == Decimal(5)


@pytest.mark.fast
def test_T_L02_0206_specific_exact() -> None:
    """
    id: T-L02-0206
    title: Specific exact
    purpose: Specific exact
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Specific exact
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, kind=DutyKind.SPECIFIC, specific=Decimal(2))
    assert cost(rate=rate).duties[0].amount == Decimal(50)


@pytest.mark.fast
def test_T_L02_0207_compound_exact() -> None:
    """
    id: T-L02-0207
    title: Compound exact
    purpose: Compound exact
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Compound exact
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, kind=DutyKind.COMPOUND, specific=Decimal(2))
    assert cost(rate=rate).duties[0].amount == Decimal(55)


@pytest.mark.fast
def test_T_L02_0208_components_sum_to_total() -> None:
    """
    id: T-L02-0208
    title: Components sum to total
    purpose: Components sum to total
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Components sum to total
    risk: HZ-03
    capability: L02
    """
    result = cost(components=(component("FREIGHT"),))
    assert actual(result) == sum(
        line.converted.base for line in result.components if line.converted is not None
    )


@pytest.mark.fast
def test_T_L02_0209_range_order() -> None:
    """
    id: T-L02-0209
    title: Range order
    purpose: Range order
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Range order
    risk: HZ-03
    capability: L02
    """
    result = cost(
        components=(
            Component(
                "PORT",
                Range(Decimal(1), Decimal(5), Decimal(15)),
                "USD",
                Kind.ASSUMPTION,
                "ASSUMPTION",
                SRC,
            ),
        )
    )
    assert result.total is not None
    assert result.total.minimum < result.total.base < result.total.maximum


@pytest.mark.fast
def test_T_L02_0210_range_origin_weakens_total() -> None:
    """
    id: T-L02-0210
    title: Range origin weakens total
    purpose: Range origin weakens total
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Range origin weakens total
    risk: HZ-03
    capability: L02
    """
    result = cost(
        components=(
            Component("PORT", Range.exact(Decimal(3)), "USD", Kind.ASSUMPTION, "ASSUMPTION", SRC),
        )
    )
    assert result.label == "ASSUMPTION"


@pytest.mark.fast
def test_T_L02_0211_required_component_missing() -> None:
    """
    id: T-L02-0211
    title: Required component missing
    purpose: Required component missing
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Required component missing
    risk: HZ-03
    capability: L02
    """
    result = cost(required=frozenset({"FREIGHT"}))
    assert result.total is None and "FREIGHT" in result.missing


@pytest.mark.fast
def test_T_L02_0212_no_implicit_fx() -> None:
    """
    id: T-L02-0212
    title: No implicit fx
    purpose: No implicit fx
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: No implicit fx
    risk: HZ-03
    capability: L02
    """
    result = cost(components=(component("FREIGHT", currency="EUR"),))
    freight = next(row for row in result.components if row.component.code == "FREIGHT")
    assert result.total is None and freight.fx_rate is None


@pytest.mark.fast
def test_T_L02_0213_dated_fx() -> None:
    """
    id: T-L02-0213
    title: Dated fx
    purpose: Dated fx
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Dated fx
    risk: HZ-03
    capability: L02
    """
    rate = RateDatum("EUR", "USD", Decimal("1.25"), SRC, "DERIVED")
    result = cost(
        components=(component("FREIGHT", currency="EUR"),),
        fx=replace(FX, rates={(DAY, "EUR", "USD"): rate}),
    )
    assert result.components[-2].fx_rate == rate.value or any(
        row.fx_rate == rate.value for row in result.components
    )


@pytest.mark.fast
def test_T_L02_0214_unverified_goods() -> None:
    """
    id: T-L02-0214
    title: Unverified goods
    purpose: Unverified goods
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unverified goods
    risk: HZ-03
    capability: L02
    """
    assert Reason.UPSTREAM in cost(replace(GOODS, verified=False)).reason_codes


@pytest.mark.fast
def test_T_L02_0215_unknown_declared_code() -> None:
    """
    id: T-L02-0215
    title: Unknown declared code
    purpose: Unknown declared code
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unknown declared code
    risk: HZ-03
    capability: L02
    """
    assert Reason.CODE in cost(replace(GOODS, code="1102")).reason_codes


@pytest.mark.fast
def test_T_L02_0216_absent_valuation_rule() -> None:
    """
    id: T-L02-0216
    title: Absent valuation rule
    purpose: Absent valuation rule
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Absent valuation rule
    risk: HZ-03
    capability: L02
    """
    assert Reason.RULE in cost(replace(GOODS, incoterm="NONE")).reason_codes


@pytest.mark.fast
def test_T_L02_0217_unsupported_goods_currency() -> None:
    """
    id: T-L02-0217
    title: Unsupported goods currency
    purpose: Unsupported goods currency
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unsupported goods currency
    risk: HZ-03
    capability: L02
    """
    assert Reason.CURRENCY in cost(replace(GOODS, value=Money(Decimal(1), "ZZZ"))).reason_codes


@pytest.mark.fast
def test_T_L02_0218_missing_goods_fx() -> None:
    """
    id: T-L02-0218
    title: Missing goods fx
    purpose: Missing goods fx
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Missing goods fx
    risk: HZ-03
    capability: L02
    """
    assert Reason.FX in cost(replace(GOODS, value=Money(Decimal(1), "EUR"))).reason_codes


@pytest.mark.fast
def test_T_L02_0219_duty_start_inclusive() -> None:
    """
    id: T-L02-0219
    title: Duty start inclusive
    purpose: Duty start inclusive
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Duty start inclusive
    risk: HZ-03
    capability: L02
    """
    assert cost(rate=replace(AD, valid_from=DAY)).duties


@pytest.mark.fast
def test_T_L02_0220_duty_end_exclusive() -> None:
    """
    id: T-L02-0220
    title: Duty end exclusive
    purpose: Duty end exclusive
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Duty end exclusive
    risk: HZ-03
    capability: L02
    """
    assert Reason.CODE in cost(rate=replace(AD, valid_until=DAY)).reason_codes


@pytest.mark.fast
def test_T_L02_0221_tax_start_inclusive() -> None:
    """
    id: T-L02-0221
    title: Tax start inclusive
    purpose: Tax start inclusive
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Tax start inclusive
    risk: HZ-03
    capability: L02
    """
    assert actual(cost(taxes=(replace(TAX, valid_from=DAY),))) == Decimal("115.50")


@pytest.mark.fast
def test_T_L02_0222_tax_end_exclusive() -> None:
    """
    id: T-L02-0222
    title: Tax end exclusive
    purpose: Tax end exclusive
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Tax end exclusive
    risk: HZ-03
    capability: L02
    """
    assert actual(cost(taxes=(replace(TAX, valid_until=DAY),))) == Decimal(105)


@pytest.mark.fast
def test_T_L02_0223_tax_base_value_only() -> None:
    """
    id: T-L02-0223
    title: Tax base value only
    purpose: Tax base value only
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Tax base value only
    risk: HZ-03
    capability: L02
    """
    assert actual(cost(taxes=(replace(TAX, base_codes=("VALUATION",)),))) == Decimal(115)


@pytest.mark.fast
def test_T_L02_0224_tax_base_dependency() -> None:
    """
    id: T-L02-0224
    title: Tax base dependency
    purpose: Tax base dependency
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Tax base dependency
    risk: HZ-03
    capability: L02
    """
    result = cost(taxes=(replace(TAX, base_codes=("FREIGHT",)),))
    assert result.total is None and "VAT" in result.missing


@pytest.mark.fast
def test_T_L02_0225_no_units_without_verification() -> None:
    """
    id: T-L02-0225
    title: No units without verification
    purpose: No units without verification
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: No units without verification
    risk: HZ-03
    capability: L02
    """
    assert cost(replace(GOODS, quantities_verified=False)).unit_costs is None


@pytest.mark.fast
def test_T_L02_0226_no_specific_without_units() -> None:
    """
    id: T-L02-0226
    title: No specific without units
    purpose: No specific without units
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: No specific without units
    risk: HZ-03
    capability: L02
    """
    assert (
        Reason.UPSTREAM
        in cost(
            replace(GOODS, quantities_verified=False), replace(AD, kind=DutyKind.SPECIFIC)
        ).reason_codes
    )


@pytest.mark.fast
def test_T_L02_0227_unit_cost_per_piece() -> None:
    """
    id: T-L02-0227
    title: Unit cost per piece
    purpose: Unit cost per piece
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unit cost per piece
    risk: HZ-03
    capability: L02
    """
    result = cost()
    assert result.unit_costs is not None and result.unit_costs.per_piece == Decimal("11.55")


@pytest.mark.fast
def test_T_L02_0228_unit_cost_per_kg() -> None:
    """
    id: T-L02-0228
    title: Unit cost per kg
    purpose: Unit cost per kg
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unit cost per kg
    risk: HZ-03
    capability: L02
    """
    result = cost()
    assert result.unit_costs is not None and result.unit_costs.per_kg == Decimal("4.62")


@pytest.mark.fast
def test_T_L02_0229_unit_cost_per_line() -> None:
    """
    id: T-L02-0229
    title: Unit cost per line
    purpose: Unit cost per line
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unit cost per line
    risk: HZ-03
    capability: L02
    """
    result = cost()
    assert result.unit_costs is not None and result.unit_costs.per_line == actual(result)


@pytest.mark.fast
def test_T_L02_0230_verified_preference() -> None:
    """
    id: T-L02-0230
    title: Verified preference
    purpose: Verified preference
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Verified preference
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, preference=Preference("origin", "yes", Decimal("0.03")))
    result = cost(rate=rate, facts=(FactEntry("origin", "yes", "VERIFIED", "DERIVED"),))
    assert result.duties[0].preferred and result.duties[0].amount == Decimal(3)


@pytest.mark.fast
def test_T_L02_0231_unverified_preference() -> None:
    """
    id: T-L02-0231
    title: Unverified preference
    purpose: Unverified preference
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unverified preference
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, preference=Preference("origin", "yes", Decimal("0.03")))
    result = cost(rate=rate, facts=(FactEntry("origin", "yes", "PROPOSED", "DERIVED"),))
    assert not result.duties[0].preferred and result.duties[0].amount == Decimal(5) and result.notes


@pytest.mark.fast
def test_T_L02_0232_withdrawn_preference() -> None:
    """
    id: T-L02-0232
    title: Withdrawn preference
    purpose: Withdrawn preference
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Withdrawn preference
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, preference=Preference("origin", "yes", Decimal("0.03")))
    assert cost(rate=rate, facts=(FactEntry("origin", "no", "VERIFIED", "DERIVED"),)).duties[
        0
    ].amount == Decimal(5)


@pytest.mark.fast
def test_T_L02_0233_weak_preference() -> None:
    """
    id: T-L02-0233
    title: Weak preference
    purpose: Weak preference
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Weak preference
    risk: HZ-03
    capability: L02
    """
    rate = replace(AD, preference=Preference("origin", "yes", Decimal("0.03")))
    assert cost(rate=rate, facts=(FactEntry("origin", "yes", "VERIFIED", "SECONDARY"),)).duties[
        0
    ].amount == Decimal(5)


@pytest.mark.fast
def test_T_L02_0234_adjusted_basis() -> None:
    """
    id: T-L02-0234
    title: Adjusted basis
    purpose: Adjusted basis
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Adjusted basis
    risk: HZ-03
    capability: L02
    """
    goods = replace(
        GOODS, adjustments={"freight": Adjustment(Money(Decimal(20), "USD"), SRC, "DERIVED")}
    )
    assert goods.adjustments["freight"].amount.amount == Decimal(20) and cost(goods).duties[
        0
    ].basis.amount.amount == Decimal(100)


@pytest.mark.fast
def test_T_L02_0235_zero_goods_value() -> None:
    """
    id: T-L02-0235
    title: Zero goods value
    purpose: Zero goods value
    level: fast
    requirement: P16-T05, Part 5 section 5.L02, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Zero goods value
    risk: HZ-03
    capability: L02
    """
    assert cost(replace(GOODS, value=Money(Decimal(0), "USD"))).duties[0].amount == Decimal(0)


@pytest.mark.fast
def test_T_L02_0520_invalid_range_rejected() -> None:
    """
    id: T-L02-0520
    title: Invalid range rejected
    purpose: Invalid range rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid range rejected
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="ordered"):
        Range(Decimal(2), Decimal(1), Decimal(3))


@pytest.mark.fast
def test_T_L02_0521_negative_component_rejected() -> None:
    """
    id: T-L02-0521
    title: Negative component rejected
    purpose: Negative component rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Negative component rejected
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="nonnegative"):
        component("FREIGHT", "-1")


@pytest.mark.fast
def test_T_L02_0522_assumption_requires_its_label() -> None:
    """
    id: T-L02-0522
    title: Assumption requires its label
    purpose: Assumption requires its label
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Assumption requires its label
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="evidence label"):
        replace(component("FREIGHT"), kind=Kind.ASSUMPTION)


@pytest.mark.fast
def test_T_L02_0523_specific_per_piece() -> None:
    """
    id: T-L02-0523
    title: Specific per piece
    purpose: Specific per piece
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Specific per piece
    risk: HZ-03
    capability: L02
    """
    mode = replace(AD, kind=DutyKind.SPECIFIC, specific=Decimal(2), unit="piece")
    assert cost(rate=mode).duties[0].amount == Decimal(20)


@pytest.mark.fast
def test_T_L02_0524_unsupported_weight_unit() -> None:
    """
    id: T-L02-0524
    title: Unsupported weight unit
    purpose: Unsupported weight unit
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Unsupported weight unit
    risk: HZ-03
    capability: L02
    """
    mode = replace(AD, kind=DutyKind.SPECIFIC, specific=Decimal(2))
    assert Reason.UPSTREAM in cost(replace(GOODS, weight_unit="unsupported"), mode).reason_codes


@pytest.mark.fast
def test_T_L02_0525_negative_preference_rejected() -> None:
    """
    id: T-L02-0525
    title: Negative preference rejected
    purpose: Negative preference rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Negative preference rejected
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="nonnegative"):
        Preference("origin", "yes", Decimal(-1))


@pytest.mark.fast
def test_T_L02_0526_invalid_duty_rate_rejected() -> None:
    """
    id: T-L02-0526
    title: Invalid duty rate rejected
    purpose: Invalid duty rate rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid duty rate rejected
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="invalid duty rate"):
        replace(AD, specific=Decimal(-1))


@pytest.mark.fast
def test_T_L02_0527_invalid_pack_rejected() -> None:
    """
    id: T-L02-0527
    title: Invalid pack rejected
    purpose: Invalid pack rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid pack rejected
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="invalid duty pack"):
        DutyPack("", SRC, FROM, TO, (AD,))


@pytest.mark.fast
def test_T_L02_0528_invalid_tax_rate_rejected() -> None:
    """
    id: T-L02-0528
    title: Invalid tax rate rejected
    purpose: Invalid tax rate rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid tax rate rejected
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="invalid tax rate"):
        replace(TAX, base_codes=())


@pytest.mark.fast
def test_T_L02_0529_overlapping_tax_rates_need_review() -> None:
    """
    id: T-L02-0529
    title: Overlapping tax rates need review
    purpose: Overlapping tax rates need review
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Overlapping tax rates need review
    risk: HZ-03
    capability: L02
    """
    result = cost(taxes=(TAX, replace(TAX, id="second")))
    assert Reason.CONFLICT in result.reason_codes and result.total is None


@pytest.mark.fast
def test_T_L02_0530_unknown_duty_currency() -> None:
    """
    id: T-L02-0530
    title: Unknown duty currency
    purpose: Unknown duty currency
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Unknown duty currency
    risk: HZ-03
    capability: L02
    """
    assert Reason.CURRENCY in cost(rate=replace(AD, currency="ZZZ")).reason_codes


@pytest.mark.fast
def test_T_L02_0531_tax_rounding_honors_pack() -> None:
    """
    id: T-L02-0531
    title: Tax rounding honors pack
    purpose: Tax rounding honors pack
    level: fast
    requirement: P16-T09, Part 5 section 5.L02, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Tax rounding honors pack
    risk: HZ-03
    capability: L02
    """
    rounding = RoundingRule(RoundAt.LINE, ROUND_HALF_UP, SRC)
    report = cost(taxes=(replace(TAX, rate=Decimal("0.001"), rounding=rounding),))
    assert actual(report) == Decimal("105.11")

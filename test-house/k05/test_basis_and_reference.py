"""K05 valuation basis and reference statistics properties and differentials."""

from datetime import date, timedelta
from decimal import Context, Decimal, localcontext
from fractions import Fraction
from itertools import accumulate
from math import ceil

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.k05.reference import (
    ReferenceGroup,
    Unit,
    normalize_line,
    reference_statistics,
)
from kernel.lib.conformal import calibrate
from kernel.lib.money import CurrencyTable, Money, RateDatum
from kernel.lib.valuation import (
    Adjustment,
    BasisUnavailable,
    FxPack,
    ValuationRule,
    valuation_basis,
)

DAY = date.fromisoformat("2026-11-01")
CONTEXT = Context(prec=60)
SYNTHETIC = "SYNTHETIC"
SOURCE = "SRC-SYNTHETIC-K05"
TABLE = CurrencyTable({"USD": 2, "EUR": 2, "AED": 2}, SOURCE)
FX = FxPack(
    "synthetic-fx",
    TABLE,
    {
        (DAY, "USD", "AED"): RateDatum("USD", "AED", Decimal("3.67"), SOURCE, SYNTHETIC),
        (DAY, "EUR", "AED"): RateDatum("EUR", "AED", Decimal("4.25"), SOURCE, SYNTHETIC),
    },
    SYNTHETIC,
)
RULES = {
    "FOB": ValuationRule("synthetic-rule-fob", ("freight", "insurance"), SYNTHETIC),
    "CIF": ValuationRule("synthetic-rule-cif", (), SYNTHETIC),
}
UNITS = {
    "kg": Unit("mass", Decimal(1)),
    "t": Unit("mass", Decimal(1000)),
    "g": Unit("mass", Decimal("0.001")),
    "piece": Unit("count", Decimal(1)),
    "l": Unit("volume", Decimal(1)),
}


def basis(
    invoice: Money,
    adjustments: dict[str, Adjustment],
    *,
    day: date = DAY,
    incoterm: str = "FOB",
) -> Decimal:
    return valuation_basis(
        invoice,
        invoice_label=SYNTHETIC,
        target_currency="AED",
        declared_date=day,
        incoterm=incoterm,
        fx=FX,
        rules=RULES,
        adjustments=adjustments,
        context=CONTEXT,
    ).amount.amount


def normalized(value: Money, quantity: Decimal, unit: str) -> Decimal:
    return normalize_line(
        value,
        quantity,
        unit=unit,
        basis_unit="kg",
        basis_currency="AED",
        units=UNITS,
        label=SYNTHETIC,
        fx=FX,
        declared_date=DAY,
        context=CONTEXT,
    ).unit_value(CONTEXT)


@pytest.mark.fast
@given(amount=st.integers(1, 10**12), quantity=st.integers(1, 10**9))
def test_T_K05_0201_exact_unit_conversion(amount: int, quantity: int) -> None:
    """
    id: T-K05-0201
    title: Exact unit conversion
    purpose: Exact unit conversion
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    value = Money(Decimal(amount), "AED")
    assert normalized(value, Decimal(quantity), "t") == normalized(
        value, Decimal(quantity * 1000), "kg"
    )


@pytest.mark.fast
@given(amount=st.integers(1, 10**12), quantity=st.integers(1, 10**9))
def test_T_K05_0202_exact_currency_conversion(amount: int, quantity: int) -> None:
    """
    id: T-K05-0202
    title: Exact currency conversion
    purpose: Exact currency conversion
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    assert normalized(Money(Decimal(amount), "USD"), Decimal(quantity), "kg") == normalized(
        Money(Decimal(amount) * Decimal("3.67"), "AED"), Decimal(quantity), "kg"
    )


@pytest.mark.fast
@given(
    invoice=st.integers(1, 10**10),
    freight=st.integers(0, 10**7),
    insurance=st.integers(0, 10**7),
)
def test_T_K05_0203_documentary_basis_fraction_oracle(
    invoice: int, freight: int, insurance: int
) -> None:
    """
    id: T-K05-0203
    title: Documentary basis fraction oracle
    purpose: Documentary basis fraction oracle
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    adjustments = {
        "freight": Adjustment(Money(Decimal(freight), "EUR"), "fact-freight", SYNTHETIC),
        "insurance": Adjustment(Money(Decimal(insurance), "AED"), "fact-insurance", SYNTHETIC),
    }
    expected = invoice * Fraction(367, 100) + freight * Fraction(425, 100) + insurance
    assert Fraction(basis(Money(Decimal(invoice), "USD"), adjustments)) == expected


def oracle_median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


@pytest.mark.fast
@pytest.mark.parametrize(
    ("test_id", "sample"),
    [
        ("0204", tuple(range(1, 31))),
        ("0205", tuple(range(1, 32))),
        ("0206", (17,) * 30),
        ("0207", (7,) * 29 + (10**18,)),
        ("0208", (1,) * 15 + (10**18,) * 15),
        ("0209", tuple(range(31, 0, -1))),
        ("0210", tuple(accumulate(range(1, 81)))),
        ("0211", (20, 30, 10) * 10),
    ],
    ids=[
        "T-K05-0204",
        "T-K05-0205",
        "T-K05-0206",
        "T-K05-0207",
        "T-K05-0208",
        "T-K05-0209",
        "T-K05-0210",
        "T-K05-0211",
    ],
)
def test_reference_median_and_mad(test_id: str, sample: tuple[int, ...]) -> None:
    """
    id: T-K05-0204
    title: Reference median and mad
    purpose: Reference median and mad
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    values = tuple(map(Decimal, sample))
    group = ReferenceGroup("20", "kg", "AED", values)
    stats = reference_statistics("20", groups={"20": group}, parent=None, context=CONTEXT)
    assert stats is not None, test_id
    with localcontext(CONTEXT):
        logs = [value.ln() for value in values]
        median = oracle_median(logs)
        mad = oracle_median([abs(value - median) for value in logs])
        assert (stats.center, stats.scale) == (
            median,
            max(Decimal("0.05"), mad * Decimal("1.4826")),
        )


@pytest.mark.fast
@pytest.mark.parametrize(
    ("size", "parent_size", "expected"),
    [
        (12, 80, "20"),
        (29, 30, "20"),
        (30, 80, "2001"),
        (29, 29, None),
        (0, 30, "20"),
        (0, 0, None),
        (31, 0, "2001"),
    ],
    ids=[f"T-K05-{number:04}" for number in range(212, 219)],
)
def test_reference_sample_boundaries(size: int, parent_size: int, expected: str | None) -> None:
    """
    id: T-K05-0212
    title: Reference sample boundaries
    purpose: Reference sample boundaries
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    groups = {
        code: ReferenceGroup(code, "kg", "AED", (Decimal(10),) * count)
        for code, count in (("2001", size), ("20", parent_size))
        if count
    }
    stats = reference_statistics("2001", groups=groups, parent="20", context=CONTEXT)
    assert (stats.group.code if stats else None) == expected
    if stats:
        assert stats.fallback is (expected == "20")
        assert stats.scale == Decimal("0.05")


@pytest.mark.fast
@pytest.mark.parametrize(
    ("values", "alpha"),
    [
        ([i / 500 for i in range(500)], 0.1),
        ([0.0] * 499 + [1.0], 0.1),
        ([0.2] * 300 + [0.4] * 200, 0.1),
        ([0.0, 0.5, 1.0] * 200, 0.2),
        ([1.0, 0.5, 0.0] * 200, 0.01),
        ([0.0, 1.0], 0.1),
    ],
    ids=[f"T-K05-{number:04}" for number in range(219, 225)],
)
def test_split_quantile_matches_rank(values: list[float], alpha: float) -> None:
    """
    id: T-K05-0219
    title: Split quantile matches rank
    purpose: Split quantile matches rank
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    rank = ceil((len(values) + 1) * (1 - Fraction(str(alpha))))
    threshold = next(
        (
            candidate
            for candidate in sorted(set(values))
            if sum(score <= candidate for score in values) >= rank
        ),
        None,
    )
    artifact = calibrate({"reference": values}, alpha=alpha, version="v1", source_id=SOURCE)
    assert artifact.thresholds[0].threshold == threshold


@pytest.mark.fast
@pytest.mark.parametrize(
    ("currency", "day", "incoterm", "issue"),
    [
        ("USD", DAY, "FOB", "ADJUSTMENT_MISSING"),
        ("USD", DAY + timedelta(days=1), "CIF", "FX_UNAVAILABLE"),
        ("GBP", DAY, "CIF", "FX_UNAVAILABLE"),
        ("USD", DAY, "unknown", "VALUATION_RULE_UNAVAILABLE"),
    ],
    ids=[f"T-K05-{number:04}" for number in range(225, 229)],
)
def test_unavailable_inputs_abstain(currency: str, day: date, incoterm: str, issue: str) -> None:
    """
    id: T-K05-0225
    title: Unavailable inputs abstain
    purpose: Unavailable inputs abstain
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    with pytest.raises(BasisUnavailable, match=issue):
        basis(Money(Decimal(12), currency), {}, day=day, incoterm=incoterm)


@pytest.mark.fast
def test_T_K05_0229_grams_scale_exactly() -> None:
    """
    id: T-K05-0229
    title: Grams scale exactly
    purpose: Grams scale exactly
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    amount = Money(Decimal("3.67"), "AED")
    assert normalized(amount, Decimal(1200), "g") == normalized(amount, Decimal("1.2"), "kg")


@pytest.mark.fast
def test_T_K05_0230_currency_and_unit_conversion_compose() -> None:
    """
    id: T-K05-0230
    title: Currency and unit conversion compose
    purpose: Currency and unit conversion compose
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    assert normalized(Money(Decimal("0.1"), "USD"), Decimal("0.000001"), "t") == normalized(
        Money(Decimal("0.367"), "AED"), Decimal(1), "g"
    )

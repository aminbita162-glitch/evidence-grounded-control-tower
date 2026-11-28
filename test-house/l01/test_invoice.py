"""Exercise basis precedence, exact arithmetic and duplicate invariants."""

from dataclasses import replace
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.l01 import (
    Basis,
    BasisSource,
    HeaderTotal,
    Invoice,
    InvoiceAudit,
    InvoiceLine,
    LineClass,
    Policy,
    Quantity,
    Reason,
    evaluate,
)
from kernel.lib.money import CurrencyTable, RoundAt, RoundingRule
from kernel.lib.taxonomy import ChargeName, LineKind, Taxonomy
from kernel.types.decision import DecisionValue

SRC = "SRC-SYNTHETIC-L01"
DAY = date(2024, 3, 1)
ONE = Decimal(1)
TAXONOMY = Taxonomy(
    SRC,
    "1",
    "SYNTHETIC",
    DAY - timedelta(days=30),
    DAY + timedelta(days=30),
    (
        ChargeName("HANDLING", LineKind.OTHER, ("Handling fee", "رسوم المناولة")),
        ChargeName("DETENTION", LineKind.TIME_BASED, ("Detention", "احتجاز")),
        ChargeName("TAX", LineKind.TAX, ("VAT", "ضريبة")),
    ),
)
CURRENCIES = CurrencyTable({"USD": 2, "EUR": 2}, SRC)
BASIS = Basis(
    "quote-1",
    "HANDLING",
    BasisSource.QUOTE,
    Decimal(100),
    "USD",
    "kg",
    TAXONOMY.valid_from,
    TAXONOMY.valid_until,
    SRC,
    "SYNTHETIC",
    "1",
)
LINE = InvoiceLine(
    "1",
    "Handling fee",
    "SYN-1",
    "USD",
    Quantity(ONE, "kg"),
    Decimal(100),
    Decimal(100),
    SRC,
    label="SYNTHETIC",
)
INVOICE = Invoice("INV-1", "Synthetic Carrier", DAY, "USD", (LINE,), "SYNTHETIC", SRC)


def audit(
    bill: Invoice = INVOICE,
    bases: tuple[Basis, ...] = (BASIS,),
    *,
    policy: Policy | None = None,
    quantities: dict[str, Quantity] | None = None,
    previous: tuple[Invoice, ...] = (),
) -> InvoiceAudit:
    return evaluate(
        bill,
        at=DAY,
        taxonomy=TAXONOMY,
        bases=bases,
        currencies=CURRENCIES,
        synthetic=True,
        policy=policy or Policy(),
        verified_quantities=quantities,
        previous=previous,
    )


def line(**changes: object) -> Invoice:
    from dataclasses import fields

    values = {field.name: getattr(LINE, field.name) for field in fields(LINE)}
    return replace(INVOICE, lines=(InvoiceLine(**(values | changes)),))


def duplicate(other: InvoiceLine) -> Invoice:
    return replace(INVOICE, lines=(LINE, replace(other, id="2")))


def category(bill: Invoice = INVOICE, *bases: Basis) -> LineClass:
    return audit(bill, bases or (BASIS,)).lines[0].classification


@pytest.mark.fast
@given(rate=st.integers(0, 10**12), qty=st.integers(1, 10**8))
def test_T_L01_0201_corrected_invoice_allows(rate: int, qty: int) -> None:
    """
    id: T-L01-0201
    title: Corrected invoice allows
    purpose: Corrected invoice allows
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Corrected invoice allows
    risk: HZ-03
    capability: L01
    """
    expected = Decimal(rate) * Decimal(qty)
    rule = replace(BASIS, rate=Decimal(rate))
    fixed = line(rate=Decimal(rate), quantity=Quantity(Decimal(qty), "kg"), amount=expected)
    assert audit(fixed, (rule,)).outcome is DecisionValue.ALLOW


@pytest.mark.fast
@given(cents=st.integers(0, 10**9), grams=st.integers(1, 10**9))
def test_T_L01_0202_decimal_matches_fraction(cents: int, grams: int) -> None:
    """
    id: T-L01-0202
    title: Decimal matches fraction
    purpose: Decimal matches fraction
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Decimal matches fraction
    risk: HZ-03
    capability: L01
    """
    rate = Decimal(cents).scaleb(-2)
    quantity = Decimal(grams).scaleb(-3)
    bill = line(rate=rate, quantity=Quantity(quantity, "kg"), amount=rate * quantity)
    expected = audit(bill, (replace(BASIS, rate=rate),)).lines[0].expected
    assert expected is not None
    assert Fraction(expected) == Fraction(cents * grams, 100_000)


@pytest.mark.fast
@given(delta=st.integers(1, 500), width=st.integers(1, 500))
def test_T_L01_0203_widening_band_preserves_flags(delta: int, width: int) -> None:
    """
    id: T-L01-0203
    title: Widening band preserves flags
    purpose: Widening band preserves flags
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Widening band preserves flags
    risk: HZ-03
    capability: L01
    """
    other = replace(LINE, amount=LINE.amount + Decimal(delta).scaleb(-2))
    bill = duplicate(other)
    narrow = audit(bill, policy=Policy(near_band=Decimal(width).scaleb(-4)))
    wide = audit(bill, policy=Policy(near_band=Decimal(width + 100).scaleb(-4)))
    if Reason.POSSIBLE_DUPLICATE in narrow.reason_codes:
        assert Reason.POSSIBLE_DUPLICATE in wide.reason_codes


@pytest.mark.fast
@given(amount=st.integers(0, 1000))
def test_T_L01_0204_adding_duplicate_preserves_severity(amount: int) -> None:
    """
    id: T-L01-0204
    title: Adding duplicate preserves severity
    purpose: Adding duplicate preserves severity
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Adding duplicate preserves severity
    risk: HZ-03
    capability: L01
    """
    value = Decimal(amount)
    row = replace(LINE, amount=value, name="Unquoted" if amount % 2 else LINE.name)
    initial = replace(INVOICE, lines=(row,))
    repeated = replace(initial, lines=(row, replace(row, id="2")))
    assert audit(repeated).outcome >= audit(initial).outcome


@pytest.mark.fast
def test_T_L01_0205_line_permutation_preserves_output() -> None:
    """
    id: T-L01-0205
    title: Line permutation preserves output
    purpose: Line permutation preserves output
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Line permutation preserves output
    risk: HZ-03
    capability: L01
    """
    bill = duplicate(replace(LINE, amount=Decimal("101.50")))
    assert audit(bill) == audit(replace(bill, lines=bill.lines[::-1]))


@pytest.mark.fast
def test_T_L01_0206_unit_conversion_preserves_outcome() -> None:
    """
    id: T-L01-0206
    title: Unit conversion preserves outcome
    purpose: Unit conversion preserves outcome
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Unit conversion preserves outcome
    risk: HZ-03
    capability: L01
    """
    changed = line(quantity=Quantity(Decimal(1000), "g"), rate=Decimal("0.1"))
    assert audit(changed).outcome == audit().outcome
    assert audit(changed).lines[0].expected == audit().lines[0].expected


@pytest.mark.fast
def test_T_L01_0207_arabic_synonym_preserves_outcome() -> None:
    """
    id: T-L01-0207
    title: Arabic synonym preserves outcome
    purpose: Arabic synonym preserves outcome
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Arabic synonym preserves outcome
    risk: HZ-03
    capability: L01
    """
    expected = audit().lines[0]
    actual = audit(line(name="رسوم المناولة")).lines[0]
    assert (actual.kind, actual.classification) == (expected.kind, expected.classification)


@pytest.mark.fast
def test_T_L01_0208_exact_duplicate() -> None:
    """
    id: T-L01-0208
    title: Exact duplicate
    purpose: Exact duplicate
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Exact duplicate
    risk: HZ-03
    capability: L01
    """
    assert category(duplicate(LINE)) is LineClass.DUPLICATE


@pytest.mark.fast
def test_T_L01_0209_near_duplicate() -> None:
    """
    id: T-L01-0209
    title: Near duplicate
    purpose: Near duplicate
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Near duplicate
    risk: HZ-03
    capability: L01
    """
    assert (
        category(duplicate(replace(LINE, amount=Decimal("101.50")))) is LineClass.POSSIBLE_DUPLICATE
    )


@pytest.mark.fast
def test_T_L01_0210_zero_band() -> None:
    """
    id: T-L01-0210
    title: Zero band
    purpose: Zero band
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Zero band
    risk: HZ-03
    capability: L01
    """
    assert (
        audit(
            duplicate(replace(LINE, amount=Decimal("101.50"))), policy=Policy(near_band=Decimal(0))
        )
        .lines[0]
        .classification
        is LineClass.MATCH
    )


@pytest.mark.fast
def test_T_L01_0211_unknown_charge() -> None:
    """
    id: T-L01-0211
    title: Unknown charge
    purpose: Unknown charge
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Unknown charge
    risk: HZ-03
    capability: L01
    """
    assert category(line(name="Unmapped")) is LineClass.UNQUOTED


@pytest.mark.fast
def test_T_L01_0212_confusable_charge() -> None:
    """
    id: T-L01-0212
    title: Confusable charge
    purpose: Confusable charge
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Confusable charge
    risk: HZ-03
    capability: L01
    """
    assert category(line(name="Нandling fee")) is LineClass.UNQUOTED


@pytest.mark.fast
def test_T_L01_0213_ambiguous_quote() -> None:
    """
    id: T-L01-0213
    title: Ambiguous quote
    purpose: Ambiguous quote
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Ambiguous quote
    risk: HZ-03
    capability: L01
    """
    assert (
        category(INVOICE, BASIS, replace(BASIS, id="quote-2", rate=Decimal(10)))
        is LineClass.AMBIGUOUS
    )


@pytest.mark.fast
def test_T_L01_0214_agreeing_quotes() -> None:
    """
    id: T-L01-0214
    title: Agreeing quotes
    purpose: Agreeing quotes
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Agreeing quotes
    risk: HZ-03
    capability: L01
    """
    assert category(INVOICE, BASIS, replace(BASIS, id="quote-2")) is LineClass.MATCH


@pytest.mark.fast
def test_T_L01_0215_accepted_quote_wins() -> None:
    """
    id: T-L01-0215
    title: Accepted quote wins
    purpose: Accepted quote wins
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Accepted quote wins
    risk: HZ-03
    capability: L01
    """
    assert (
        audit(
            INVOICE, (replace(BASIS, id="terms", source=BasisSource.TERMS, rate=Decimal(1)), BASIS)
        )
        .lines[0]
        .basis
        == BASIS
    )


@pytest.mark.fast
def test_T_L01_0216_contract_fallback() -> None:
    """
    id: T-L01-0216
    title: Contract fallback
    purpose: Contract fallback
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Contract fallback
    risk: HZ-03
    capability: L01
    """
    assert (
        category(
            INVOICE,
            replace(BASIS, accepted=False),
            replace(BASIS, id="terms", source=BasisSource.TERMS),
        )
        is LineClass.MATCH
    )


@pytest.mark.fast
def test_T_L01_0217_tariff_fallback() -> None:
    """
    id: T-L01-0217
    title: Tariff fallback
    purpose: Tariff fallback
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Tariff fallback
    risk: HZ-03
    capability: L01
    """
    assert (
        category(
            INVOICE,
            replace(BASIS, accepted=False),
            replace(BASIS, id="tariff", source=BasisSource.TARIFF),
        )
        is LineClass.MATCH
    )


@pytest.mark.fast
def test_T_L01_0218_invalid_surcharge() -> None:
    """
    id: T-L01-0218
    title: Invalid surcharge
    purpose: Invalid surcharge
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Invalid surcharge
    risk: HZ-03
    capability: L01
    """
    assert (
        category(INVOICE, replace(BASIS, surcharge=True, valid_until=DAY))
        is LineClass.SURCHARGE_VALIDITY
    )


@pytest.mark.fast
def test_T_L01_0219_validity_start() -> None:
    """
    id: T-L01-0219
    title: Validity start
    purpose: Validity start
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Validity start
    risk: HZ-03
    capability: L01
    """
    assert category(INVOICE, replace(BASIS, valid_from=DAY)) is LineClass.MATCH


@pytest.mark.fast
def test_T_L01_0220_validity_end() -> None:
    """
    id: T-L01-0220
    title: Validity end
    purpose: Validity end
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Validity end
    risk: HZ-03
    capability: L01
    """
    assert category(INVOICE, replace(BASIS, valid_until=DAY)) is LineClass.UNQUOTED


@pytest.mark.fast
def test_T_L01_0221_currency_mismatch() -> None:
    """
    id: T-L01-0221
    title: Currency mismatch
    purpose: Currency mismatch
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Currency mismatch
    risk: HZ-03
    capability: L01
    """
    assert category(line(currency="EUR")) is LineClass.CURRENCY_MISMATCH


@pytest.mark.fast
def test_T_L01_0222_anchor_quantity() -> None:
    """
    id: T-L01-0222
    title: Anchor quantity
    purpose: Anchor quantity
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Anchor quantity
    risk: HZ-03
    capability: L01
    """
    assert (
        audit(
            line(quantity=Quantity(Decimal(2), "kg")), quantities={"SYN-1:kg": Quantity(ONE, "kg")}
        )
        .lines[0]
        .classification
        is LineClass.QUANTITY_MISMATCH
    )


@pytest.mark.fast
def test_T_L01_0223_above_rate() -> None:
    """
    id: T-L01-0223
    title: Above rate
    purpose: Above rate
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Above rate
    risk: HZ-03
    capability: L01
    """
    assert category(line(rate=Decimal(101), amount=Decimal(101))) is LineClass.RATE_ABOVE_BASIS


@pytest.mark.fast
def test_T_L01_0224_arithmetic_mismatch() -> None:
    """
    id: T-L01-0224
    title: Arithmetic mismatch
    purpose: Arithmetic mismatch
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Arithmetic mismatch
    risk: HZ-03
    capability: L01
    """
    assert category(line(amount=Decimal(101))) is LineClass.ARITHMETIC


@pytest.mark.fast
def test_T_L01_0225_freight_terms_conflict() -> None:
    """
    id: T-L01-0225
    title: Freight terms conflict
    purpose: Freight terms conflict
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Freight terms conflict
    risk: HZ-03
    capability: L01
    """
    assert (
        category(line(freight_conflict=True), replace(BASIS, freight=True))
        is LineClass.FREIGHT_CONFLICT
    )


@pytest.mark.fast
def test_T_L01_0226_under_basis() -> None:
    """
    id: T-L01-0226
    title: Under basis
    purpose: Under basis
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Under basis
    risk: HZ-03
    capability: L01
    """
    assert category(line(rate=Decimal(99), amount=Decimal(99))) is LineClass.BELOW_BASIS


@pytest.mark.fast
def test_T_L01_0227_exact_basis() -> None:
    """
    id: T-L01-0227
    title: Exact basis
    purpose: Exact basis
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Exact basis
    risk: HZ-03
    capability: L01
    """
    assert category() is LineClass.MATCH


@pytest.mark.fast
def test_T_L01_0228_header_sum_includes_tax() -> None:
    """
    id: T-L01-0228
    title: Header sum includes tax
    purpose: Header sum includes tax
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Header sum includes tax
    risk: HZ-03
    capability: L01
    """
    bill = duplicate(replace(LINE, tax=True, amount=Decimal(5)))
    assert audit(replace(bill, total=Decimal(105))).header == HeaderTotal(
        Decimal(105), Decimal(105), True
    )


@pytest.mark.fast
def test_T_L01_0229_header_exposes_minor_unit() -> None:
    """
    id: T-L01-0229
    title: Header exposes minor unit
    purpose: Header exposes minor unit
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Header exposes minor unit
    risk: HZ-03
    capability: L01
    """
    assert Reason.HEADER in audit(replace(INVOICE, total=Decimal("100.01"))).reason_codes


@pytest.mark.fast
def test_T_L01_0230_subminor_difference() -> None:
    """
    id: T-L01-0230
    title: Subminor difference
    purpose: Subminor difference
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Subminor difference
    risk: HZ-03
    capability: L01
    """
    assert category(line(amount=Decimal("100.004"))) is LineClass.MATCH


@pytest.mark.fast
def test_T_L01_0231_independent_issuers() -> None:
    """
    id: T-L01-0231
    title: Independent issuers
    purpose: Independent issuers
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Independent issuers
    risk: HZ-03
    capability: L01
    """
    prior = replace(INVOICE, number="INV-2", issuer="Different Carrier")
    assert audit(previous=(prior,)).outcome is DecisionValue.ALLOW


@pytest.mark.fast
def test_T_L01_0232_previous_in_window() -> None:
    """
    id: T-L01-0232
    title: Previous in window
    purpose: Previous in window
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Previous in window
    risk: HZ-03
    capability: L01
    """
    prior = replace(INVOICE, number="INV-2", issued_on=DAY - timedelta(days=30))
    assert audit(previous=(prior,)).lines[0].classification is LineClass.DUPLICATE


@pytest.mark.fast
def test_T_L01_0233_previous_outside_window() -> None:
    """
    id: T-L01-0233
    title: Previous outside window
    purpose: Previous outside window
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Previous outside window
    risk: HZ-03
    capability: L01
    """
    prior = replace(INVOICE, number="INV-2", issued_on=DAY - timedelta(days=31))
    assert audit(previous=(prior,)).outcome is DecisionValue.ALLOW


@pytest.mark.fast
def test_T_L01_0234_other_shipment_basis() -> None:
    """
    id: T-L01-0234
    title: Other shipment basis
    purpose: Other shipment basis
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Other shipment basis
    risk: HZ-03
    capability: L01
    """
    assert category(INVOICE, replace(BASIS, shipment="OTHER")) is LineClass.UNQUOTED


@pytest.mark.fast
def test_T_L01_0235_rounded_line_trace() -> None:
    """
    id: T-L01-0235
    title: Rounded line trace
    purpose: Rounded line trace
    level: fast
    requirement: P16-T03, Part 5 section 5.L01, DoD 7
    input: Synthetic invoice and exact-decimal charge basis
    expected: Rounded line trace
    risk: HZ-03
    capability: L01
    """
    assert audit().lines[0].trace is not None


@pytest.mark.fast
def test_T_L01_0520_taxonomy_rejects_invalid_dates() -> None:
    """
    id: T-L01-0520
    title: Taxonomy rejects invalid dates
    purpose: Taxonomy rejects invalid dates
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Taxonomy rejects invalid dates
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="ordered validity"):
        replace(TAXONOMY, valid_until=TAXONOMY.valid_from)


@pytest.mark.fast
def test_T_L01_0521_taxonomy_rejects_duplicate_codes() -> None:
    """
    id: T-L01-0521
    title: Taxonomy rejects duplicate codes
    purpose: Taxonomy rejects duplicate codes
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Taxonomy rejects duplicate codes
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="unique"):
        replace(TAXONOMY, entries=(TAXONOMY.entries[0],) * 2)


@pytest.mark.fast
def test_T_L01_0522_taxonomy_rejects_shared_synonym() -> None:
    """
    id: T-L01-0522
    title: Taxonomy rejects shared synonym
    purpose: Taxonomy rejects shared synonym
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Taxonomy rejects shared synonym
    risk: HZ-03
    capability: L01
    """
    entry = replace(TAXONOMY.entries[0], code="OTHER")
    with pytest.raises(ValueError, match="more than one"):
        replace(TAXONOMY, entries=(TAXONOMY.entries[0], entry))


@pytest.mark.fast
def test_T_L01_0523_invalid_invoice_identity() -> None:
    """
    id: T-L01-0523
    title: Invalid invoice identity
    purpose: Invalid invoice identity
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid invoice identity
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="identifier"):
        replace(INVOICE, number="")


@pytest.mark.fast
def test_T_L01_0524_invalid_duplicate_line_id() -> None:
    """
    id: T-L01-0524
    title: Invalid duplicate line id
    purpose: Invalid duplicate line id
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid duplicate line id
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="unique"):
        replace(INVOICE, lines=(LINE, LINE))


@pytest.mark.fast
def test_T_L01_0525_invalid_nonfinite_header() -> None:
    """
    id: T-L01-0525
    title: Invalid nonfinite header
    purpose: Invalid nonfinite header
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid nonfinite header
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="finite"):
        replace(INVOICE, total=Decimal("NaN"))


@pytest.mark.fast
def test_T_L01_0526_basis_reject_negative_rate() -> None:
    """
    id: T-L01-0526
    title: Basis reject negative rate
    purpose: Basis reject negative rate
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Basis reject negative rate
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="invalid invoice charge"):
        replace(BASIS, rate=Decimal(-1))


@pytest.mark.fast
def test_T_L01_0527_incommensurate_quantity_abstains() -> None:
    """
    id: T-L01-0527
    title: Incommensurate quantity abstains
    purpose: Incommensurate quantity abstains
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Incommensurate quantity abstains
    risk: HZ-03
    capability: L01
    """
    assert category(line(quantity=Quantity(ONE, "piece"))) is LineClass.UNVERIFIED


@pytest.mark.fast
def test_T_L01_0528_basis_uses_declared_rounding() -> None:
    """
    id: T-L01-0528
    title: Basis uses declared rounding
    purpose: Basis uses declared rounding
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Basis uses declared rounding
    risk: HZ-03
    capability: L01
    """
    rule = RoundingRule(RoundAt.LINE, ROUND_HALF_UP, SRC)
    basis = replace(BASIS, rate=Decimal("1.005"), rounding=rule)
    bill = line(rate=basis.rate, amount=Decimal("1.01"))
    item = audit(bill, (basis,)).lines[0]
    assert item.classification is LineClass.MATCH and item.expected == Decimal("1.01")


@pytest.mark.fast
def test_T_L01_0529_negative_duplicate_window_rejected() -> None:
    """
    id: T-L01-0529
    title: Negative duplicate window rejected
    purpose: Negative duplicate window rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Negative duplicate window rejected
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="duplicate window"):
        Policy(duplicate_days=-1)


@pytest.mark.fast
def test_T_L01_0530_negative_duplicate_band_rejected() -> None:
    """
    id: T-L01-0530
    title: Negative duplicate band rejected
    purpose: Negative duplicate band rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Negative duplicate band rejected
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValueError, match="near-duplicate band"):
        Policy(near_band=Decimal(-1))


@pytest.mark.fast
def test_T_L01_0531_unverified_invoice_abstains() -> None:
    """
    id: T-L01-0531
    title: Unverified invoice abstains
    purpose: Unverified invoice abstains
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Unverified invoice abstains
    risk: HZ-03
    capability: L01
    """
    assert Reason.INVOICE in audit(replace(INVOICE, verified=False)).reason_codes


@pytest.mark.fast
def test_T_L01_0532_weak_invoice_fails_closed() -> None:
    """
    id: T-L01-0532
    title: Weak invoice fails closed
    purpose: Weak invoice fails closed
    level: fast
    requirement: P16-T09, Part 5 section 5.L01, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Weak invoice fails closed
    risk: HZ-03
    capability: L01
    """
    assert Reason.LABEL in audit(replace(INVOICE, label="UNVERIFIED")).reason_codes

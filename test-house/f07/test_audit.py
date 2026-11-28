"""Exercise F07 recomputation, discrepancy ordering and stable exports."""

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.f03 import ContainerClock, Event
from capabilities.f07 import (
    Audit,
    Classification,
    Reason,
    TariffClock,
    evaluate,
)
from capabilities.f07.dossier import export
from capabilities.l01 import Basis, BasisSource, Invoice, InvoiceLine, Quantity
from capabilities.l01 import evaluate as l01
from kernel.hashing import domain_hash
from kernel.lib.clock import Clock, DayBasis, DayOne, PartialDay, Terms, Tier
from kernel.lib.money import CurrencyTable, RoundAt, RoundingRule
from kernel.lib.taxonomy import ChargeName, LineKind, Taxonomy
from kernel.types.decision import DecisionValue

SRC = "SRC-SYNTHETIC-F07"
AT = datetime(2024, 3, 10, tzinfo=UTC)
START = datetime(2024, 3, 1, tzinfo=UTC)
DAY = timedelta(days=1)
CONTAINER = "SYN-CONT-1"
TABLE = CurrencyTable({"USD": 2, "EUR": 2}, SRC)
TAX = Taxonomy(
    SRC,
    "1",
    "SYNTHETIC",
    date(2024, 1, 1),
    date(2025, 1, 1),
    (
        ChargeName("DEMURRAGE", LineKind.TIME_BASED, ("Demurrage",)),
        ChargeName("TAX", LineKind.TAX, ("VAT",)),
        ChargeName("HANDLING", LineKind.OTHER, ("Handling",)),
    ),
)
BASIS = Basis(
    "B1",
    "DEMURRAGE",
    BasisSource.TARIFF,
    Decimal(5),
    "USD",
    "day",
    TAX.valid_from,
    TAX.valid_until,
    SRC,
    "SYNTHETIC",
    "1",
)
TERMS = Terms(
    SRC,
    "1",
    "SYNTHETIC",
    START - DAY,
    AT + DAY,
    True,
    "DISCHARGED",
    "GATED_OUT_FULL",
    1,
    DayBasis.CALENDAR,
    ZoneInfo("UTC"),
    DayOne.INCLUDE,
    time(),
    PartialDay.STARTED,
    "USD",
    RoundingRule(RoundAt.TOTAL, ROUND_HALF_EVEN, SRC),
    (Tier(None, Decimal(5)),),
)
EVENT = Event("DISCHARGED", START, SRC, SRC, "SYNTHETIC", True)
MODEL = ContainerClock(CONTAINER, "DEMURRAGE", (EVENT,), TERMS)
CLOCK = TariffClock(BASIS.id, MODEL)
LINE = InvoiceLine(
    "L1",
    "Demurrage",
    "SYN-1",
    "USD",
    Quantity(Decimal(2), "day"),
    Decimal(5),
    Decimal(10),
    SRC,
    container=CONTAINER,
    period_start=START + DAY,
    period_end=START + 3 * DAY,
    label="SYNTHETIC",
)
INVOICE = Invoice("INV-1", "Synthetic Carrier", AT.date(), "USD", (LINE,), "SYNTHETIC", SRC)


def report(
    lines: tuple[InvoiceLine, ...] = (LINE,),
    clocks: tuple[TariffClock, ...] = (CLOCK,),
    bases: tuple[Basis, ...] = (BASIS,),
    *,
    missing_matches: bool = False,
    synthetic: bool = True,
) -> Audit:
    bill = replace(INVOICE, lines=lines)
    audited = l01(
        bill, at=AT.date(), taxonomy=TAX, bases=bases, currencies=TABLE, synthetic=synthetic
    )
    if missing_matches:
        audited = replace(audited, matches=())
    return evaluate(
        bill,
        audited,
        clocks,
        canonical_containers=frozenset({CONTAINER}),
        currencies=TABLE,
        at=AT,
        synthetic=synthetic,
    )


def root(*args: InvoiceLine) -> Classification:
    return report(args).lines[0].classification


@pytest.mark.fast
@given(days=st.integers(1, 8), rate=st.integers(1, 1000))
def test_T_F07_0201_exact_clock_equivalence(days: int, rate: int) -> None:
    """
    id: T-F07-0201
    title: Recomputed amounts match F03
    purpose: Compare time-charge audits with the shared accrual engine
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Generated tariff rates and billed periods
    expected: Expected amounts and tier progression agree
    risk: HZ-03
    capability: F07
    """
    start, end = START + DAY, START + (days + 1) * DAY
    terms = replace(TERMS, tiers=(Tier(None, Decimal(rate)),))
    clock = replace(CLOCK, clock=replace(MODEL, terms=terms))
    row = replace(LINE, period_start=start, period_end=end)
    expected = Clock(terms, None, (), TABLE).charge(START, end, period_start=start)
    assert report((row,), (clock,)).lines[0].expected == expected.amount.amount


@pytest.mark.fast
@given(days=st.integers(1, 8), rate=st.integers(1, 1000))
def test_T_F07_0202_corrected_invoice_allows(days: int, rate: int) -> None:
    """
    id: T-F07-0202
    title: A corrected supported invoice allows
    purpose: Check amount and rate agreement at the minor unit
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Generated exact tariff and corrected billed line
    expected: Matching supported charge yields ALLOW
    risk: HZ-03
    capability: F07
    """
    terms = replace(TERMS, tiers=(Tier(None, Decimal(rate)),))
    clock = replace(CLOCK, clock=replace(MODEL, terms=terms))
    row = replace(
        LINE,
        period_end=START + (days + 1) * DAY,
        quantity=Quantity(Decimal(days), "day"),
        rate=Decimal(rate),
        amount=Decimal(rate * days),
    )
    assert report((row,), (clock,)).outcome is DecisionValue.ALLOW


@pytest.mark.fast
@given(extension=st.integers(0, 7))
def test_T_F07_0203_verified_extension_changes_difference(extension: int) -> None:
    """
    id: T-F07-0203
    title: More verified free time lowers expected charge
    purpose: Check the approved fixed-billed difference invariant
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Generated verified terms and unchanged billed line
    expected: Billed minus expected never decreases
    risk: HZ-03
    capability: F07
    """
    terms = replace(TERMS, free_days=TERMS.free_days + extension)
    extended = replace(CLOCK, clock=replace(MODEL, terms=terms))
    earlier, later = report().lines[0], report(clocks=(extended,)).lines[0]
    assert earlier.expected is not None and later.expected is not None
    assert earlier.difference is not None and later.difference is not None
    assert later.expected <= earlier.expected and later.difference >= earlier.difference


@pytest.mark.fast
def test_T_F07_0204_line_order_independent() -> None:
    """
    id: T-F07-0204
    title: Line order independent
    purpose: Line order independent
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Line order independent
    risk: HZ-03
    capability: F07
    """
    lines = (LINE, replace(LINE, id="L2", amount=Decimal("10.01")))
    assert report(lines) == report(lines[::-1])


@pytest.mark.fast
def test_T_F07_0205_dossier_hash_deterministic() -> None:
    """
    id: T-F07-0205
    title: Dossier hash deterministic
    purpose: Dossier hash deterministic
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Dossier hash deterministic
    risk: HZ-03
    capability: F07
    """
    row = replace(LINE, amount=Decimal(11))
    assert export(report((row,))).digest == export(report((row,))).digest


@pytest.mark.fast
def test_T_F07_0206_dossier_hash_covers_artifacts() -> None:
    """
    id: T-F07-0206
    title: Dossier hash covers artifacts
    purpose: Dossier hash covers artifacts
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Dossier hash covers artifacts
    risk: HZ-03
    capability: F07
    """
    dossier = export(report((replace(LINE, amount=Decimal(11)),)))
    assert dossier.digest == domain_hash("ctc/payload/v1", [dossier.json, dossier.html])


@pytest.mark.fast
def test_T_F07_0207_duplicate_precedes_period() -> None:
    """
    id: T-F07-0207
    title: Duplicate precedes period
    purpose: Duplicate precedes period
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Duplicate precedes period
    risk: HZ-03
    capability: F07
    """
    item = replace(LINE, period_start=START)
    assert root(item, replace(item, id="L2")) is Classification.DUPLICATE


@pytest.mark.fast
def test_T_F07_0208_period_precedes_rate() -> None:
    """
    id: T-F07-0208
    title: Period precedes rate
    purpose: Period precedes rate
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Period precedes rate
    risk: HZ-03
    capability: F07
    """
    assert (
        root(replace(LINE, period_start=START, rate=Decimal(20), amount=Decimal(40)))
        is Classification.NOT_BILLABLE
    )


@pytest.mark.fast
def test_T_F07_0209_rate_precedes_days() -> None:
    """
    id: T-F07-0209
    title: Rate precedes days
    purpose: Rate precedes days
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Rate precedes days
    risk: HZ-03
    capability: F07
    """
    assert (
        root(
            replace(LINE, rate=Decimal(6), quantity=Quantity(Decimal(3), "day"), amount=Decimal(18))
        )
        is Classification.RATE
    )


@pytest.mark.fast
def test_T_F07_0210_days_precede_arithmetic() -> None:
    """
    id: T-F07-0210
    title: Days precede arithmetic
    purpose: Days precede arithmetic
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Days precede arithmetic
    risk: HZ-03
    capability: F07
    """
    assert (
        root(replace(LINE, quantity=Quantity(Decimal(3), "day"), amount=Decimal(16)))
        is Classification.DAYS
    )


@pytest.mark.fast
def test_T_F07_0211_arithmetic_precedes_outcome() -> None:
    """
    id: T-F07-0211
    title: Arithmetic precedes outcome
    purpose: Arithmetic precedes outcome
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Arithmetic precedes outcome
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, amount=Decimal(11))) is Classification.ARITHMETIC


@pytest.mark.fast
def test_T_F07_0212_unsupported_basis() -> None:
    """
    id: T-F07-0212
    title: Unsupported basis
    purpose: Unsupported basis
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Unsupported basis
    risk: HZ-03
    capability: F07
    """
    assert report(bases=()).lines[0].classification is Classification.UNSUPPORTED


@pytest.mark.fast
def test_T_F07_0213_ambiguous_basis() -> None:
    """
    id: T-F07-0213
    title: Ambiguous basis
    purpose: Ambiguous basis
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Ambiguous basis
    risk: HZ-03
    capability: F07
    """
    assert (
        report(bases=(BASIS, replace(BASIS, id="B2", rate=Decimal(9)))).lines[0].classification
        is Classification.AMBIGUOUS
    )


@pytest.mark.fast
def test_T_F07_0214_missing_clock() -> None:
    """
    id: T-F07-0214
    title: Missing clock
    purpose: Missing clock
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Missing clock
    risk: HZ-03
    capability: F07
    """
    assert report(clocks=()).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0215_missing_match() -> None:
    """
    id: T-F07-0215
    title: Missing match
    purpose: Missing match
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Missing match
    risk: HZ-03
    capability: F07
    """
    assert report(missing_matches=True).lines[0].classification is Classification.MATCHING


@pytest.mark.fast
def test_T_F07_0216_undercharge_observed() -> None:
    """
    id: T-F07-0216
    title: Undercharge observed
    purpose: Undercharge observed
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Undercharge observed
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, rate=Decimal(4), amount=Decimal(8))) is Classification.UNDERCHARGE


@pytest.mark.fast
def test_T_F07_0217_below_minor_unit_matches() -> None:
    """
    id: T-F07-0217
    title: Below minor unit matches
    purpose: Below minor unit matches
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Below minor unit matches
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, amount=Decimal("10.004"))) is Classification.MATCH


@pytest.mark.fast
def test_T_F07_0218_tax_not_evaluated() -> None:
    """
    id: T-F07-0218
    title: Tax not evaluated
    purpose: Tax not evaluated
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Tax not evaluated
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, name="VAT", tax=True)) is Classification.TAX


@pytest.mark.fast
def test_T_F07_0219_flat_charge_passes_to_l01() -> None:
    """
    id: T-F07-0219
    title: Flat charge passes to l01
    purpose: Flat charge passes to l01
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Flat charge passes to l01
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, name="Handling")) is Classification.OUT_OF_SCOPE


@pytest.mark.fast
def test_T_F07_0220_currency_mismatch() -> None:
    """
    id: T-F07-0220
    title: Currency mismatch
    purpose: Currency mismatch
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Currency mismatch
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, currency="EUR")) is Classification.UNSUPPORTED


@pytest.mark.fast
def test_T_F07_0221_missing_period() -> None:
    """
    id: T-F07-0221
    title: Missing period
    purpose: Missing period
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Missing period
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, period_start=None)) is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0222_step_carries_exact_days() -> None:
    """
    id: T-F07-0222
    title: Step carries exact days
    purpose: Step carries exact days
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Step carries exact days
    risk: HZ-03
    capability: F07
    """
    assert report().lines[0].steps[0].days == Fraction(2)


@pytest.mark.fast
def test_T_F07_0223_weak_label_indicative() -> None:
    """
    id: T-F07-0223
    title: Weak label indicative
    purpose: Weak label indicative
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Weak label indicative
    risk: HZ-03
    capability: F07
    """
    assert export(report()).strength == "INDICATIVE"


@pytest.mark.fast
def test_T_F07_0224_after_stop_not_billable() -> None:
    """
    id: T-F07-0224
    title: After stop not billable
    purpose: After stop not billable
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: After stop not billable
    risk: HZ-03
    capability: F07
    """
    stop = Event("GATED_OUT_FULL", START + 2 * DAY, SRC, SRC, "SYNTHETIC", True)
    clock = replace(CLOCK, clock=replace(MODEL, events=(EVENT, stop)))
    assert report(clocks=(clock,)).lines[0].reason is Reason.PERIOD


@pytest.mark.fast
def test_T_F07_0225_adjacent_periods_are_distinct() -> None:
    """
    id: T-F07-0225
    title: Adjacent periods are distinct
    purpose: Adjacent periods are distinct
    level: fast
    requirement: P16-T07, Part 5 section 5.F07, DoD 7
    input: Versioned synthetic case and referenced packs
    expected: Adjacent periods are distinct
    risk: HZ-03
    capability: F07
    """
    adjacent = replace(LINE, id="L2", period_start=START + 3 * DAY, period_end=START + 5 * DAY)
    assert report((LINE, adjacent)).outcome is DecisionValue.ALLOW


@pytest.mark.fast
def test_T_F07_0520_overlapping_clock_versions_ambiguous() -> None:
    """
    id: T-F07-0520
    title: Overlapping clock versions ambiguous
    purpose: Overlapping clock versions ambiguous
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Overlapping clock versions ambiguous
    risk: HZ-03
    capability: F07
    """
    overlap = replace(CLOCK, clock=replace(MODEL, terms=replace(TERMS, version="2")))
    assert report(clocks=(CLOCK, overlap)).lines[0].classification is Classification.AMBIGUOUS


@pytest.mark.fast
def test_T_F07_0521_unverified_clock_terms() -> None:
    """
    id: T-F07-0521
    title: Unverified clock terms
    purpose: Unverified clock terms
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Unverified clock terms
    risk: HZ-03
    capability: F07
    """
    weak = replace(CLOCK, clock=replace(MODEL, terms=replace(TERMS, verified=False)))
    assert report(clocks=(weak,)).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0522_gap_before_tariff() -> None:
    """
    id: T-F07-0522
    title: Gap before tariff
    purpose: Gap before tariff
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Gap before tariff
    risk: HZ-03
    capability: F07
    """
    late = replace(CLOCK, clock=replace(MODEL, terms=replace(TERMS, valid_from=START + 2 * DAY)))
    assert report(clocks=(late,)).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0523_gap_after_tariff() -> None:
    """
    id: T-F07-0523
    title: Gap after tariff
    purpose: Gap after tariff
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Gap after tariff
    risk: HZ-03
    capability: F07
    """
    early = replace(CLOCK, clock=replace(MODEL, terms=replace(TERMS, valid_until=START + 2 * DAY)))
    assert report(clocks=(early,)).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0524_duplicated_event_rejected() -> None:
    """
    id: T-F07-0524
    title: Duplicated event rejected
    purpose: Duplicated event rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Duplicated event rejected
    risk: HZ-03
    capability: F07
    """
    duplicates = replace(CLOCK, clock=replace(MODEL, events=(EVENT, EVENT)))
    assert report(clocks=(duplicates,)).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0525_missing_start_event_rejected() -> None:
    """
    id: T-F07-0525
    title: Missing start event rejected
    purpose: Missing start event rejected
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Missing start event rejected
    risk: HZ-03
    capability: F07
    """
    no_events = replace(CLOCK, clock=replace(MODEL, events=()))
    assert report(clocks=(no_events,)).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0526_future_event_not_in_evidence() -> None:
    """
    id: T-F07-0526
    title: Future event not in evidence
    purpose: Future event not in evidence
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Future event not in evidence
    risk: HZ-03
    capability: F07
    """
    late = replace(EVENT, kind="GATED_OUT_FULL", instant=AT + DAY)
    future = replace(CLOCK, clock=replace(MODEL, events=(EVENT, late)))
    assert report(clocks=(future,)).lines[0].events == (EVENT,)


@pytest.mark.fast
def test_T_F07_0527_invalid_movement_order() -> None:
    """
    id: T-F07-0527
    title: Invalid movement order
    purpose: Invalid movement order
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Invalid movement order
    risk: HZ-03
    capability: F07
    """
    stop = replace(EVENT, kind="GATED_OUT_FULL", instant=START - DAY)
    wrong = replace(CLOCK, clock=replace(MODEL, events=(EVENT, stop)))
    assert report(clocks=(wrong,)).lines[0].classification is Classification.CLOCK


@pytest.mark.fast
def test_T_F07_0528_no_invoice_rows_abstains() -> None:
    """
    id: T-F07-0528
    title: No invoice rows abstains
    purpose: No invoice rows abstains
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: No invoice rows abstains
    risk: HZ-03
    capability: F07
    """
    assert report(lines=()).outcome is DecisionValue.ABSTAIN


@pytest.mark.fast
def test_T_F07_0529_unverified_invoice_line_abstains() -> None:
    """
    id: T-F07-0529
    title: Unverified invoice line abstains
    purpose: Unverified invoice line abstains
    level: fast
    requirement: P16-T09, Part 5 section 5.F07, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Unverified invoice line abstains
    risk: HZ-03
    capability: F07
    """
    assert root(replace(LINE, verified=False)) is Classification.MATCHING

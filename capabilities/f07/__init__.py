"""Audit time-based invoice charges using the matched tariff and shared clock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal
from enum import StrEnum
from fractions import Fraction

from capabilities.f03 import ContainerClock, Event
from capabilities.l01 import AuditedLine, Invoice, InvoiceAudit, InvoiceLine, MatchRecord
from capabilities.l01 import Reason as InvoiceReason
from kernel.lib.clock import Clock, aware
from kernel.lib.money import CurrencyTable, Money, within_tolerance
from kernel.lib.taxonomy import LineKind
from kernel.types.decision import DecisionValue
from kernel.types.label import is_allow_eligible, weakest_of

_CONTEXT = Context(prec=128)
_ZERO = Decimal(0)


class Reason(StrEnum):
    MATCH = "F07.OK.MATCH"
    UNDERCHARGE = "F07.OBS.UNDERCHARGE"
    OUT_OF_SCOPE = "F07.OBS.OUT_OF_SCOPE"
    DUPLICATE = "F07.OVERCHARGE.DUPLICATE"
    PERIOD = "F07.OVERCHARGE.NOT_BILLABLE_PERIOD"
    RATE = "F07.OVERCHARGE.RATE_MISMATCH"
    DAYS = "F07.OVERCHARGE.DAY_COUNT"
    ARITHMETIC = "F07.OVERCHARGE.ARITHMETIC"
    UNSUPPORTED = "F07.UNSUPPORTED.NO_TARIFF_BASIS"
    AMBIGUOUS = "F07.AMBIGUOUS.TARIFF"
    CLOCK = "F07.ABSTAIN.CLOCK_MISSING"
    MATCHING = "F07.ABSTAIN.MATCHING_MISSING"
    LABEL = "F07.ABSTAIN.LABEL_INSUFFICIENT"


class Classification(StrEnum):
    MATCH = "MATCH"
    UNDERCHARGE = "UNDERCHARGE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    TAX = "TAX_NOT_EVALUATED"
    DUPLICATE = "DUPLICATE"
    NOT_BILLABLE = "NOT_BILLABLE_PERIOD"
    UNSUPPORTED = "UNSUPPORTED"
    AMBIGUOUS = "AMBIGUOUS_TARIFF"
    RATE = "RATE_MISMATCH"
    DAYS = "DAY_COUNT_MISMATCH"
    ARITHMETIC = "ARITHMETIC"
    CLOCK = "CLOCK_MISSING"
    MATCHING = "MATCHING_MISSING"
    LABEL = "LABEL_INSUFFICIENT"


_CODES = {
    Classification.MATCH: (Reason.MATCH, DecisionValue.ALLOW),
    Classification.UNDERCHARGE: (Reason.UNDERCHARGE, DecisionValue.ALLOW),
    Classification.OUT_OF_SCOPE: (Reason.OUT_OF_SCOPE, DecisionValue.ALLOW),
    Classification.TAX: (None, DecisionValue.ALLOW),
    Classification.DUPLICATE: (Reason.DUPLICATE, DecisionValue.HOLD),
    Classification.NOT_BILLABLE: (Reason.PERIOD, DecisionValue.HOLD),
    Classification.UNSUPPORTED: (Reason.UNSUPPORTED, DecisionValue.ESCALATE),
    Classification.AMBIGUOUS: (Reason.AMBIGUOUS, DecisionValue.ESCALATE),
    Classification.RATE: (Reason.RATE, DecisionValue.HOLD),
    Classification.DAYS: (Reason.DAYS, DecisionValue.HOLD),
    Classification.ARITHMETIC: (Reason.ARITHMETIC, DecisionValue.HOLD),
    Classification.CLOCK: (Reason.CLOCK, DecisionValue.ABSTAIN),
    Classification.MATCHING: (Reason.MATCHING, DecisionValue.ABSTAIN),
    Classification.LABEL: (Reason.LABEL, DecisionValue.ABSTAIN),
}


@dataclass(frozen=True, slots=True)
class TariffClock:
    basis_id: str
    clock: ContainerClock


@dataclass(frozen=True, slots=True)
class TariffStep:
    terms_id: str
    version: str
    label: str
    valid_from: datetime
    valid_until: datetime
    period_from: datetime
    period_until: datetime
    free_expiry: datetime
    days: Fraction
    rates: tuple[Decimal, ...]
    amount: Decimal


@dataclass(frozen=True, slots=True)
class ChargeLine:
    line_id: str
    charge_kind: str
    container: str | None
    classification: Classification
    reason: Reason | None
    outcome: DecisionValue
    currency: str
    billed: Decimal
    expected: Decimal | None
    difference: Decimal | None
    remainder: Decimal | None
    citation: str
    label: str
    events: tuple[Event, ...] = ()
    steps: tuple[TariffStep, ...] = ()


@dataclass(frozen=True, slots=True)
class Total:
    billed: Decimal
    expected: Decimal | None
    difference: Decimal | None


@dataclass(frozen=True, slots=True)
class Audit:
    invoice_number: str
    issuer: str
    invoice_citation: str
    outcome: DecisionValue
    reason_codes: tuple[Reason, ...]
    lines: tuple[ChargeLine, ...]
    totals: dict[str, Total]
    label: str


@dataclass(frozen=True, slots=True)
class Comparison:
    expected: Decimal
    days: Fraction
    rates: tuple[Decimal, ...]
    non_billable: bool
    events: tuple[Event, ...]
    steps: tuple[TariffStep, ...]
    label: str


def _eligible(label: str, synthetic: bool) -> bool:
    return is_allow_eligible(label) or synthetic and label == "SYNTHETIC"


def _equal(a: Decimal, b: Decimal, currency: str, currencies: CurrencyTable) -> bool:
    return within_tolerance(
        Money(a, currency),
        Money(b, currency),
        tolerance_units=0,
        rounding=ROUND_HALF_EVEN,
        currencies=currencies,
        context=_CONTEXT,
    )


def _period(line: InvoiceLine) -> tuple[datetime, datetime] | None:
    if line.period_start is None or line.period_end is None:
        return None
    try:
        start, end = aware(line.period_start), aware(line.period_end)
    except ValueError:
        return None
    return (start, end) if start < end else None


def _duplicates(rows: tuple[AuditedLine, ...]) -> set[str]:
    groups: dict[tuple[str, str], list[tuple[datetime, datetime, str]]] = {}
    for row in rows:
        period = _period(row.line)
        if row.line.container and row.kind.kind == LineKind.TIME_BASED and period is not None:
            groups.setdefault((row.line.container, row.kind.code), []).append(
                (*period, row.line.id)
            )
    found: set[str] = set()
    for group in groups.values():
        ordered = sorted(group)
        for index, (start, _, id_) in enumerate(ordered):
            for _, end, other in ordered[:index]:
                if start < end:
                    found.update((id_, other))
    return found


def recompute(
    line: InvoiceLine,
    match: MatchRecord,
    clocks: tuple[TariffClock, ...],
    canonical_containers: frozenset[str],
    currencies: CurrencyTable,
    at: datetime,
) -> Comparison | Classification:
    """Recompute billed increments on the same tariff-clock timeline as F03."""
    period = _period(line)
    if period is None or line.container not in canonical_containers or match.basis is None:
        return Classification.CLOCK
    left, right = period
    if right > at:
        return Classification.CLOCK
    relevant = [
        item.clock
        for item in clocks
        if item.basis_id == match.basis.id
        and item.clock.container == line.container
        and item.clock.charge_kind == match.kind
    ]
    if not relevant:
        return Classification.CLOCK
    windows = [
        (aware(clock.terms.valid_from), aware(clock.terms.valid_until), clock)
        for clock in relevant
        if clock.terms is not None
        and aware(clock.terms.valid_from) < right
        and aware(clock.terms.valid_until) > left
    ]
    windows.sort(key=lambda window: (window[0], window[1]))
    if any(windows[i][1] > windows[i + 1][0] for i in range(len(windows) - 1)):
        return Classification.AMBIGUOUS
    if line.currency != match.basis.currency or line.currency not in currencies.minor_units:
        return Classification.UNSUPPORTED

    cursor = left
    total = _ZERO
    days = Fraction(0)
    non_billable = False
    rates: set[Decimal] = set()
    evidence: dict[tuple[str, datetime, str], Event] = {}
    steps = []
    label = weakest_of(line.label, match.basis.label)
    for window_start, window_end, data in windows:
        terms = data.terms
        if terms is None or not terms.verified or terms.currency != line.currency:
            return Classification.CLOCK
        begin, finish = max(left, window_start), min(right, window_end)
        if cursor != begin:
            return Classification.CLOCK
        by_kind = {event.kind: event for event in data.events}
        if len(by_kind) != len(data.events):
            return Classification.CLOCK
        start_event, stop_event = by_kind.get(terms.start_event), by_kind.get(terms.stop_event)
        if (
            start_event is None
            or not start_event.verified
            or (stop_event and not stop_event.verified)
        ):
            return Classification.CLOCK
        for event in data.events:
            if aware(event.instant) <= at:
                evidence[(event.kind, aware(event.instant), event.source_id)] = event
        label = weakest_of(weakest_of(label, terms.label), start_event.label)
        if stop_event:
            label = weakest_of(label, stop_event.label)
        if data.calendar is not None:
            label = weakest_of(label, data.calendar.label)
        try:
            clock = Clock(terms, data.calendar, data.suspensions, currencies)
            start = aware(start_event.instant)
            stop = aware(stop_event.instant) if stop_event else at
            if start > stop:
                return Classification.CLOCK
            expiry = clock.expiry(start)
            billable_end = min(stop, finish)
            charge = clock.charge(start, billable_end, period_start=begin)
        except ValueError, OverflowError, ArithmeticError:
            return Classification.CLOCK
        non_billable |= begin < expiry or finish > stop
        total = _CONTEXT.add(total, charge.amount.amount)
        days += charge.days
        rates.update(charge.rates)
        steps.append(
            TariffStep(
                terms.source_id,
                terms.version,
                terms.label,
                window_start,
                window_end,
                begin,
                finish,
                expiry,
                charge.days,
                charge.rates,
                charge.amount.amount,
            )
        )
        cursor = finish
    if cursor != right:
        return Classification.CLOCK
    return Comparison(
        total,
        days,
        tuple(sorted(rates)),
        non_billable,
        tuple(evidence[k] for k in sorted(evidence)),
        tuple(steps),
        label,
    )


def _classify(
    line: InvoiceLine,
    calculated: Comparison,
    currencies: CurrencyTable,
    *,
    duplicate: bool,
    synthetic: bool,
) -> tuple[Classification, Decimal | None]:
    if duplicate:
        return Classification.DUPLICATE, None
    if calculated.non_billable and line.quantity.value > 0:
        return Classification.NOT_BILLABLE, None
    currency = line.currency
    if not _eligible(calculated.label, synthetic):
        return Classification.LABEL, None
    if _equal(line.amount, calculated.expected, currency, currencies):
        return Classification.MATCH, _ZERO
    if line.amount < calculated.expected:
        return Classification.UNDERCHARGE, None

    if any(not _equal(line.rate, rate, currency, currencies) for rate in calculated.rates):
        if len(calculated.rates) != 1:
            return Classification.RATE, None
        corrected = _CONTEXT.multiply(calculated.rates[0], line.quantity.value)
        return Classification.RATE, _CONTEXT.subtract(corrected, calculated.expected)
    if Fraction(line.quantity.value) != calculated.days:
        billed_at_rate = _CONTEXT.multiply(line.rate, line.quantity.value)
        return Classification.DAYS, _CONTEXT.subtract(line.amount, billed_at_rate)
    if not _equal(
        _CONTEXT.multiply(line.rate, line.quantity.value), line.amount, currency, currencies
    ):
        return Classification.ARITHMETIC, _ZERO
    return Classification.RATE, None


def _row(
    item: AuditedLine,
    classification: Classification,
    *,
    computed: Comparison | None = None,
    remainder: Decimal | None = None,
) -> ChargeLine:
    reason, outcome = _CODES[classification]
    line = item.line
    expected = computed.expected if computed else None
    difference = _CONTEXT.subtract(line.amount, expected) if expected is not None else None
    return ChargeLine(
        line.id,
        item.kind.code,
        line.container,
        classification,
        reason,
        outcome,
        line.currency,
        line.amount,
        expected,
        difference,
        remainder,
        line.citation,
        computed.label if computed else line.label,
        computed.events if computed else (),
        computed.steps if computed else (),
    )


def evaluate(
    invoice: Invoice,
    audit: InvoiceAudit,
    clocks: tuple[TariffClock, ...],
    *,
    canonical_containers: frozenset[str],
    currencies: CurrencyTable,
    at: datetime,
    synthetic: bool = False,
) -> Audit:
    """Classify matched time charges and retain the first explaining root cause."""
    at = aware(at)
    matches = {match.line_id: match for match in audit.matches}
    dups = _duplicates(audit.lines)
    rows = []
    for item in audit.lines:
        if item.kind.kind == LineKind.TAX:
            rows.append(_row(item, Classification.TAX))
            continue
        if item.kind.kind != LineKind.TIME_BASED:
            rows.append(_row(item, Classification.OUT_OF_SCOPE))
            continue
        match = matches.get(item.line.id)
        duplicate = item.line.id in dups
        if match is None:
            rows.append(
                _row(item, Classification.DUPLICATE if duplicate else Classification.MATCHING)
            )
            continue
        if match.basis is None:
            code = (
                Classification.AMBIGUOUS
                if match.reason == InvoiceReason.AMBIGUOUS
                else Classification.UNSUPPORTED
            )
            rows.append(_row(item, Classification.DUPLICATE if duplicate else code))
            continue
        calculated = recompute(item.line, match, clocks, canonical_containers, currencies, at)
        if isinstance(calculated, Classification):
            rows.append(_row(item, Classification.DUPLICATE if duplicate else calculated))
            continue
        code, remainder = _classify(
            item.line,
            calculated,
            currencies,
            duplicate=duplicate,
            synthetic=synthetic,
        )
        rows.append(_row(item, code, computed=calculated, remainder=remainder))
    rows.sort(key=lambda row: row.line_id)
    totals = {}
    by_currency: dict[str, list[ChargeLine]] = {}
    label = invoice.label
    for row in rows:
        if row.classification in (Classification.TAX, Classification.OUT_OF_SCOPE):
            continue
        label = weakest_of(label, row.label)
        by_currency.setdefault(row.currency, []).append(row)
    for currency, group in sorted(by_currency.items()):
        billed = _ZERO
        expected: Decimal | None = _ZERO
        for row in group:
            billed = _CONTEXT.add(billed, row.billed)
            expected = (
                _CONTEXT.add(expected, row.expected)
                if expected is not None and row.expected is not None
                else None
            )
        totals[currency] = Total(
            billed,
            expected,
            _CONTEXT.subtract(billed, expected) if expected is not None else None,
        )
    outcome = max((row.outcome for row in rows), default=DecisionValue.ABSTAIN)
    reasons = {row.reason for row in rows if row.reason is not None}
    if not rows:
        reasons.add(Reason.MATCHING)
    if outcome == DecisionValue.ALLOW and not _eligible(label, synthetic):
        outcome = DecisionValue.ABSTAIN
        reasons.add(Reason.LABEL)
    return Audit(
        invoice.number,
        invoice.issuer,
        invoice.citation,
        outcome,
        tuple(sorted(reasons)),
        tuple(rows),
        totals,
        label,
    )

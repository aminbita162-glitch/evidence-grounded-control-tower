"""Evaluate container clocks using recorded terms, events, and local calendars."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction

from kernel.lib.calctrace import DecimalSettings, Formula, Operand, Operation, calculate
from kernel.lib.clock import Calendar, Clock, DayBasis, Suspension, Terms, aware
from kernel.lib.money import CurrencyTable
from kernel.types.decision import DecisionValue
from kernel.types.label import is_allow_eligible

_WARNING = timedelta(hours=48)
_PROJECTION_DAYS = (1, 3, 7)
_MOVEMENT = ("DISCHARGED", "GATED_OUT_FULL", "GATED_IN_EMPTY")


class State(StrEnum):
    STOPPED = "STOPPED"
    ACCRUING = "ACCRUING"
    ENDING = "ENDING"
    WITHIN_FREE = "WITHIN_FREE"
    UNKNOWN = "UNKNOWN"


class Reason(StrEnum):
    WITHIN_FREE = "F03.OK.WITHIN_FREE"
    STOPPED = "F03.OK.STOPPED"
    ENDING = "F03.WARN.FREE_TIME_ENDING"
    ACCRUING = "F03.CHARGES.ACCRUING"
    ORDER = "F03.EVENT.ORDER_INVALID"
    EVENT = "F03.ABSTAIN.EVENT_MISSING"
    TARIFF = "F03.ABSTAIN.TARIFF_TERMS_MISSING"
    RULE = "F03.ABSTAIN.DAY_RULE_UNSPECIFIED"
    CALENDAR = "F03.ABSTAIN.CALENDAR_UNAVAILABLE"
    CONTAINER = "F03.ABSTAIN.CONTAINER_UNMATCHED"
    LABEL = "F03.ABSTAIN.LABEL_INSUFFICIENT"


@dataclass(frozen=True, slots=True)
class Event:
    kind: str
    instant: datetime
    source_id: str
    zone_source: str
    label: str
    verified: bool

    def __post_init__(self) -> None:
        aware(self.instant)
        if not self.kind or not self.source_id or not self.zone_source:
            raise ValueError("movement event requires a kind, citation and zone source")


@dataclass(frozen=True, slots=True)
class ContainerClock:
    container: str
    charge_kind: str
    events: tuple[Event, ...]
    terms: Terms | None
    calendar: Calendar | None = None
    suspensions: tuple[Suspension, ...] = ()
    document_note: str | None = None


@dataclass(frozen=True, slots=True)
class Projection:
    days_ahead: int
    through: datetime
    charge: Decimal
    action: str
    latest_effective: datetime
    savings: Decimal


@dataclass(frozen=True, slots=True)
class ClockReport:
    container: str
    charge_kind: str
    state: State
    reason: Reason
    decision: DecisionValue
    evaluated_at: datetime
    start: datetime | None = None
    stop: datetime | None = None
    free_expiry: datetime | None = None
    remaining: timedelta | None = None
    suspended: timedelta | None = None
    chargeable_days: Fraction | None = None
    charge: Decimal | None = None
    currency: str | None = None
    projections: tuple[Projection, ...] = ()
    terms: Terms | None = None
    calendar_version: str | None = None
    timeline: tuple[Event, ...] = ()
    suspensions: tuple[Suspension, ...] = ()
    charge_trace: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class CaseClocks:
    decision: DecisionValue
    clocks: tuple[ClockReport, ...]
    totals: dict[str, Decimal]


def _eligible(label: str, synthetic: bool) -> bool:
    return is_allow_eligible(label) or synthetic and label == "SYNTHETIC"


def evaluate_clock(
    data: ContainerClock,
    at: datetime,
    currencies: CurrencyTable,
    canonical_containers: frozenset[str],
    *,
    synthetic: bool = False,
) -> ClockReport:
    """Evaluate a container and charge kind as of the supplied instant."""
    at = aware(at)
    terms = data.terms

    def unknown(reason: Reason) -> ClockReport:
        decision = DecisionValue.HOLD if reason == Reason.ORDER else DecisionValue.ABSTAIN
        return ClockReport(data.container, data.charge_kind, State.UNKNOWN, reason, decision, at)

    if data.container not in canonical_containers:
        return unknown(Reason.CONTAINER)
    if terms is None or not terms.verified or not terms.valid_at(at):
        return unknown(Reason.TARIFF)
    if None in (terms.day_one, terms.cutoff, terms.partial):
        return unknown(Reason.RULE)
    calendar = data.calendar if terms.basis == DayBasis.WORKING else None
    if terms.basis == DayBasis.WORKING and (
        calendar is None or calendar.source_id != terms.calendar_id
    ):
        return unknown(Reason.CALENDAR)

    events = tuple(sorted(data.events, key=lambda event: (aware(event.instant), event.source_id)))
    counts = Counter(event.kind for event in events)
    if any(count > 1 for count in counts.values()):
        return unknown(Reason.ORDER)
    by_kind = {event.kind: event for event in events}
    start_event, stop_event = by_kind.get(terms.start_event), by_kind.get(terms.stop_event)
    if start_event is None or not start_event.verified or (stop_event and not stop_event.verified):
        return unknown(Reason.EVENT)
    start = aware(start_event.instant)
    stop = aware(stop_event.instant) if stop_event else None
    movement = [aware(by_kind[kind].instant) for kind in _MOVEMENT if kind in by_kind]
    if start > at or (stop is not None and stop < start) or movement != sorted(movement):
        return unknown(Reason.ORDER)
    if stop is not None and stop > at:
        stop = None
    end = stop if stop is not None else at
    if not all(
        _eligible(label, synthetic)
        for label in (
            terms.label,
            start_event.label,
            *((stop_event.label,) if stop_event is not None and stop is not None else ()),
            *((calendar.label,) if calendar is not None else ()),
        )
    ):
        return unknown(Reason.LABEL)

    windows = tuple(
        sorted(
            (s for s in data.suspensions if s.verified),
            key=lambda s: (aware(s.start), aware(s.end), s.source_id),
        )
    )
    try:
        clock = Clock(terms, calendar, windows, currencies)
        expiry = clock.expiry(start)
        accrued = clock.charge(start, end)
        projections = []
        for days in _PROJECTION_DAYS:
            if stop is not None:
                break
            horizon = at + timedelta(days=days)
            baseline = clock.charge(start, horizon).amount.amount
            latest = max(at, min(expiry, horizon))
            acted = clock.charge(start, latest).amount.amount
            projections.append(
                Projection(
                    days,
                    horizon,
                    baseline,
                    terms.stop_event,
                    latest,
                    baseline - acted,
                )
            )
    except ValueError, OverflowError, ArithmeticError:
        return unknown(Reason.TARIFF)

    trace = calculate(
        Formula("F03.TIERED_CHARGE_ROUNDING", 1, Operation.QUANTIZE, terms.rounding.source_id),
        DecimalSettings(len(accrued.unrounded.as_tuple().digits) + 12, terms.rounding.mode),
        Operand(
            f"{terms.source_id}:{terms.version}:tier-sum",
            accrued.unrounded,
            terms.currency,
            terms.label,
        ),
        Operand(
            currencies.source_id, currencies.quantum(terms.currency), terms.currency, terms.label
        ),
        unit=terms.currency,
    )
    remaining = max(timedelta(), expiry - at)
    if stop is not None:
        state, reason, decision = State.STOPPED, Reason.STOPPED, DecisionValue.ALLOW
    elif accrued.days >= 1:
        state, reason, decision = State.ACCRUING, Reason.ACCRUING, DecisionValue.ESCALATE
    elif timedelta() < remaining <= _WARNING:
        state, reason, decision = State.ENDING, Reason.ENDING, DecisionValue.HOLD
    else:
        state, reason, decision = State.WITHIN_FREE, Reason.WITHIN_FREE, DecisionValue.ALLOW

    return ClockReport(
        data.container,
        data.charge_kind,
        state,
        reason,
        decision,
        at,
        start,
        stop,
        expiry,
        remaining,
        clock.suspended(start, end),
        accrued.days,
        accrued.amount.amount,
        terms.currency,
        tuple(projections),
        terms,
        calendar.version if calendar else None,
        tuple(event for event in events if event.instant.astimezone(UTC) <= at),
        windows,
        trace.payload(),
    )


def evaluate(
    clocks: tuple[ContainerClock, ...],
    at: datetime,
    currencies: CurrencyTable,
    canonical_containers: frozenset[str],
    *,
    synthetic: bool = False,
) -> CaseClocks:
    """Combine clocks in stable order while keeping each currency separate."""
    reports = tuple(
        evaluate_clock(clock, at, currencies, canonical_containers, synthetic=synthetic)
        for clock in sorted(clocks, key=lambda clock: (clock.container, clock.charge_kind))
    )
    totals: dict[str, Decimal] = {}
    for report in reports:
        if report.charge is not None and report.currency is not None:
            totals[report.currency] = totals.get(report.currency, Decimal(0)) + report.charge
    decision = max((report.decision for report in reports), default=DecisionValue.ABSTAIN)
    return CaseClocks(decision, reports, totals)

"""Compute tariff days from local boundaries and recorded clock suspensions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Context, Decimal
from enum import StrEnum
from fractions import Fraction
from itertools import pairwise
from zoneinfo import ZoneInfo

from kernel.lib.money import CurrencyTable, Money, RoundingRule, round_at

_DAY = timedelta(days=1)
_ZERO = timedelta()
_MAX_DAYS = 36_600


class DayBasis(StrEnum):
    CALENDAR = "CALENDAR"
    WORKING = "WORKING"


class DayOne(StrEnum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"


class PartialDay(StrEnum):
    STARTED = "STARTED"
    COMPLETE = "COMPLETE"
    PRORATED = "PRORATED"


@dataclass(frozen=True, slots=True)
class Calendar:
    source_id: str
    version: str
    label: str
    weekend: frozenset[int]
    holidays: frozenset[date]

    def __post_init__(self) -> None:
        if not self.source_id or not self.version or not self.weekend < frozenset(range(7)):
            raise ValueError("a calendar requires a version, source and working weekdays")

    def works(self, day: date) -> bool:
        return day.weekday() not in self.weekend and day not in self.holidays


@dataclass(frozen=True, slots=True)
class Suspension:
    start: datetime
    end: datetime
    source_id: str
    verified: bool

    def __post_init__(self) -> None:
        if aware(self.start) >= aware(self.end) or not self.source_id:
            raise ValueError("a suspension requires an ordered period and source")


@dataclass(frozen=True, slots=True)
class Tier:
    through_day: int | None
    rate: Decimal

    def __post_init__(self) -> None:
        if not self.rate.is_finite() or self.rate < 0:
            raise ValueError("a tier rate must be finite and nonnegative")
        if self.through_day is not None and self.through_day < 1:
            raise ValueError("a finite tier must end at a positive day")


@dataclass(frozen=True, slots=True)
class Terms:
    source_id: str
    version: str
    label: str
    valid_from: datetime
    valid_until: datetime
    verified: bool
    start_event: str
    stop_event: str
    free_days: int
    basis: DayBasis
    zone: ZoneInfo
    day_one: DayOne | None
    cutoff: time | None
    partial: PartialDay | None
    currency: str
    rounding: RoundingRule
    tiers: tuple[Tier, ...]
    calendar_id: str | None = None

    def __post_init__(self) -> None:
        limits = [tier.through_day for tier in self.tiers[:-1]]
        if (
            not self.source_id
            or not self.version
            or not self.start_event
            or not self.stop_event
            or aware(self.valid_from) >= aware(self.valid_until)
            or not 0 <= self.free_days <= _MAX_DAYS
            or not self.tiers
            or self.tiers[-1].through_day is not None
            or any(limit is None for limit in limits)
            or any(a >= b for a, b in pairwise(limit for limit in limits if limit is not None))
            or (self.cutoff is not None and self.cutoff.tzinfo is not None)
        ):
            raise ValueError("invalid tariff terms")

    def valid_at(self, instant: datetime) -> bool:
        return aware(self.valid_from) <= aware(instant) < aware(self.valid_until)


@dataclass(frozen=True, slots=True)
class Charge:
    days: Fraction
    amount: Money
    rates: tuple[Decimal, ...]
    unrounded: Decimal


def aware(instant: datetime) -> datetime:
    """Return a recorded instant on the UTC timeline."""
    if instant.utcoffset() is None:
        raise ValueError("a recorded instant requires a time zone")
    return instant.astimezone(UTC)


def _merged(windows: tuple[Suspension, ...]) -> tuple[tuple[datetime, datetime], ...]:
    periods: list[tuple[datetime, datetime]] = []
    for start, end in sorted((aware(w.start), aware(w.end)) for w in windows if w.verified):
        if periods and start <= periods[-1][1]:
            periods[-1] = (periods[-1][0], max(periods[-1][1], end))
        else:
            periods.append((start, end))
    return tuple(periods)


@dataclass(frozen=True, slots=True)
class Clock:
    terms: Terms
    calendar: Calendar | None
    suspensions: tuple[Suspension, ...]
    currencies: CurrencyTable

    def __post_init__(self) -> None:
        if None in (self.terms.day_one, self.terms.cutoff, self.terms.partial):
            raise ValueError("tariff day rule is required")
        if self.terms.basis == DayBasis.WORKING and (
            self.calendar is None or self.calendar.source_id != self.terms.calendar_id
        ):
            raise ValueError("the recorded working calendar is required")
        self.currencies.exponent(self.terms.currency)

    def boundary(self, day: date) -> datetime:
        cutoff = self.terms.cutoff
        if cutoff is None:
            raise ValueError("tariff cut-off is required")
        local = datetime.combine(day, cutoff, tzinfo=self.terms.zone)
        return aware(local)

    def day_at(self, instant: datetime) -> date:
        point = aware(instant)
        day = point.astimezone(self.terms.zone).date()
        return day if point >= self.boundary(day) else day - _DAY

    def _counts(self, day: date) -> bool:
        return (
            self.terms.basis == DayBasis.CALENDAR
            or self.calendar is not None
            and self.calendar.works(day)
        )

    def _count_dates(self, start: date, end: date) -> int:
        span = (end - start).days
        if self.calendar is None or self.terms.basis == DayBasis.CALENDAR:
            return span
        weeks, days = divmod(span, 7)
        return (
            weeks * (7 - len(self.calendar.weekend))
            + sum(
                (start.weekday() + offset) % 7 not in self.calendar.weekend
                for offset in range(days)
            )
            - sum(
                start <= day < end and day.weekday() not in self.calendar.weekend
                for day in self.calendar.holidays
            )
        )

    def _first_day(self, start: datetime) -> date:
        day = self.day_at(start)
        return day + _DAY if self.terms.day_one == DayOne.EXCLUDE else day

    def _suspended_days(self) -> tuple[tuple[date, date], ...]:
        spans = []
        for start, end in _merged(self.suspensions):
            first = self.day_at(start)
            if start > self.boundary(first):
                first += _DAY
            last = self.day_at(end)
            if first < last:
                spans.append((first, last))
        return tuple(spans)

    def _whole_days(self, start: date, end: date) -> int:
        return self._count_dates(start, end) - sum(
            self._count_dates(max(start, left), min(end, right))
            for left, right in self._suspended_days()
            if max(start, left) < min(end, right)
        )

    def expiry(self, start: datetime) -> datetime:
        """Find the end of the last free tariff day by searching cumulative counts."""
        start = aware(start)
        free_days = self.terms.free_days
        if free_days == 0:
            return start
        first = self._first_day(start)
        lo, hi = 0, free_days
        while self._whole_days(first, first + hi * _DAY) < free_days:
            if hi == _MAX_DAYS:
                raise ValueError("free period exceeds the supported calendar horizon")
            hi = min(2 * hi, _MAX_DAYS)
        while hi - lo > 1:
            middle = (lo + hi) // 2
            if self._whole_days(first, first + middle * _DAY) < free_days:
                lo = middle
            else:
                hi = middle
        return self.boundary(first + hi * _DAY)

    def suspended(self, start: datetime, end: datetime) -> timedelta:
        return sum(
            (
                max(_ZERO, min(end, right) - max(start, left))
                for left, right in _merged(self.suspensions)
            ),
            _ZERO,
        )

    def _day_units(
        self,
        day: date,
        start: datetime,
        end: datetime,
        windows: tuple[tuple[datetime, datetime], ...],
    ) -> Fraction:
        if not self._counts(day):
            return Fraction(0)
        left, right = self.boundary(day), self.boundary(day + _DAY)
        begin, finish = max(left, start), min(right, end)
        duration = (
            finish
            - begin
            - sum(
                (max(_ZERO, min(finish, b) - max(begin, a)) for a, b in windows),
                _ZERO,
            )
        )
        if duration <= _ZERO:
            return Fraction(0)
        if self.terms.partial == PartialDay.STARTED:
            return Fraction(1)
        if self.terms.partial == PartialDay.COMPLETE:
            return Fraction(duration == right - left)
        return Fraction(
            duration // timedelta(microseconds=1), (right - left) // timedelta(microseconds=1)
        )

    def _units(self, start: datetime, end: datetime) -> Fraction:
        if end <= start:
            return Fraction(0)
        first, last = self.day_at(start), self.day_at(end)
        if (last - first).days > _MAX_DAYS:
            raise ValueError("charge period exceeds the supported calendar horizon")
        windows = _merged(self.suspensions)
        affected = {first, last}
        for left, right in windows:
            affected.update((self.day_at(left), self.day_at(right)))
        middle = self._whole_days(first + _DAY, last) if first < last else 0
        for day in affected:
            if first < day < last and self._whole_days(day, day + _DAY):
                middle -= 1
        return Fraction(middle) + sum(
            (self._day_units(day, start, end, windows) for day in affected if first <= day <= last),
            Fraction(0),
        )

    def _cost(self, units: Fraction, after: Fraction = Fraction(0)) -> Charge:
        remaining, skip = units, after
        amount = Fraction(0)
        previous = 0
        rates = []
        for tier in self.terms.tiers:
            size = remaining + skip if tier.through_day is None else tier.through_day - previous
            offset = min(skip, size)
            skip -= offset
            portion = min(remaining, size - offset)
            if portion > 0:
                rates.append(tier.rate)
                amount += portion * Fraction(tier.rate)
                remaining -= portion
            if not remaining or tier.through_day is None:
                break
            previous = tier.through_day
        places = self.currencies.exponent(self.terms.currency)
        context = Context(
            prec=len(str(abs(amount.numerator))) + len(str(amount.denominator)) + places + 8
        )
        value = context.divide(Decimal(amount.numerator), Decimal(amount.denominator))
        money = Money(value, self.terms.currency, self.terms.rounding.mode)
        posted = round_at(
            money,
            self.terms.rounding.point,
            currencies=self.currencies,
            context=context,
            rule=self.terms.rounding,
        )
        return Charge(units, posted.money, tuple(rates), value)

    def charge(
        self, start: datetime, end: datetime, *, period_start: datetime | None = None
    ) -> Charge:
        """Price cumulative tariff units or their increment over a billed period."""
        expiry, finish = self.expiry(start), aware(end)
        total = self._units(expiry, finish)
        prior = (
            self._units(expiry, min(aware(period_start), finish))
            if period_start is not None
            else Fraction(0)
        )
        if not prior:
            return self._cost(total)
        through = self._cost(total)
        before = self._cost(prior)
        incremental = self._cost(total - prior, prior)
        amount = through.amount.amount - before.amount.amount
        return Charge(
            incremental.days,
            Money(amount, through.amount.currency, through.amount.rounding),
            incremental.rates,
            incremental.unrounded,
        )

    def simulate(self, start: datetime, end: datetime) -> Charge:
        """Reference calculation that visits and accounts for each tariff day."""
        start, end = aware(start), aware(end)
        day = self._first_day(start) if self.terms.free_days else self.day_at(start)
        last = self.day_at(end)
        if (last - day).days > _MAX_DAYS:
            raise ValueError("charge period exceeds the supported calendar horizon")
        free = self.terms.free_days
        units = Fraction(0)
        windows = _merged(self.suspensions)
        while day <= last:
            begin, finish = self.boundary(day), self.boundary(day + _DAY)
            if free:
                if self._counts(day) and self.suspended(begin, finish) < finish - begin:
                    free -= 1
            else:
                units += self._day_units(day, start, end, windows)
            day += _DAY
        return self._cost(units)

"""Fixed-point operations using explicit currency, rounding and rate data."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import (
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Context,
    Decimal,
    Inexact,
)
from enum import StrEnum
from fractions import Fraction
from types import MappingProxyType

from kernel.types.label import Label, label_rank, weakest_of
from kernel.types.money import Money

__all__ = [
    "CurrencyTable",
    "Money",
    "RateDatum",
    "RateResult",
    "RoundAt",
    "RoundedMoney",
    "RoundingRule",
    "add",
    "allocate",
    "convert",
    "round_at",
    "within_tolerance",
]

_MODES = frozenset(
    (
        ROUND_05UP,
        ROUND_CEILING,
        ROUND_DOWN,
        ROUND_FLOOR,
        ROUND_HALF_DOWN,
        ROUND_HALF_EVEN,
        ROUND_HALF_UP,
        ROUND_UP,
    )
)


def _exact(context: Context) -> Context:
    exact = context.copy()
    exact.traps[Inexact] = True
    return exact


@dataclass(frozen=True, slots=True)
class CurrencyTable:
    """Minor-unit exponents from one recorded FX pack edition."""

    minor_units: Mapping[str, int]
    source_id: str

    def __post_init__(self) -> None:
        """Freeze the supplied table and validate the shape of every entry."""
        if not self.source_id:
            raise ValueError("currency table source is required")
        for currency, places in self.minor_units.items():
            if not re.fullmatch(r"[A-Z]{3}", currency) or type(places) is not int or places < 0:
                raise ValueError(f"invalid currency table entry: {currency}")
        object.__setattr__(self, "minor_units", MappingProxyType(dict(self.minor_units)))

    def exponent(self, currency: str) -> int:
        """Return the exponent, failing closed for an unrecorded currency."""
        if currency not in self.minor_units:
            raise ValueError(f"currency absent from the FX pack: {currency}")
        return self.minor_units[currency]

    def quantum(self, currency: str) -> Decimal:
        """Return one minor unit of currency without ambient rounding."""
        return Decimal((0, (1,), -self.exponent(currency)))


class RoundAt(StrEnum):
    """The operation point to which a pack rule applies."""

    LINE = "LINE"
    TOTAL = "TOTAL"
    PRESENTATION = "PRESENTATION"


@dataclass(frozen=True, slots=True)
class RoundingRule:
    """The pack's approved rounding rule."""

    point: RoundAt
    mode: str
    source_id: str

    def __post_init__(self) -> None:
        """Validate the recorded rounding rule."""
        if self.mode not in _MODES or not self.source_id:
            raise ValueError("rounding requires a known mode and source")


@dataclass(frozen=True, slots=True)
class RoundedMoney:
    """Amount and provenance of any applied rounding."""

    money: Money
    source_id: str | None = None
    label: Label | None = None


@dataclass(frozen=True, slots=True)
class RateDatum:
    """A positively valued FX rate from an identified datum."""

    source_currency: str
    target_currency: str
    value: Decimal
    source_id: str
    label: Label

    def __post_init__(self) -> None:
        """Require an exact rate and recorded provenance."""
        if not isinstance(self.value, Decimal):
            raise TypeError("rate must be a Decimal")
        if not self.value.is_finite() or self.value <= 0 or not self.source_id:
            raise ValueError("rate must be positive, finite and recorded")
        label_rank(self.label)


@dataclass(frozen=True, slots=True)
class RateResult:
    """Exact converted amount with its rate datum and propagated label."""

    money: Money
    rate: RateDatum
    label: Label


def _validate(money: Money, currencies: CurrencyTable) -> None:
    currencies.exponent(money.currency)
    if not money.amount.is_finite() or money.rounding not in _MODES:
        raise ValueError("amount must be finite and carry a known rounding mode")


def _same_currency(left: Money, right: Money, currencies: CurrencyTable) -> None:
    _validate(left, currencies)
    _validate(right, currencies)
    if left.currency != right.currency:
        raise ValueError("mixed currencies require recorded conversion")


def add(left: Money, right: Money, *, currencies: CurrencyTable, context: Context) -> Money:
    """Add equal-currency amounts exactly within the supplied context."""
    _same_currency(left, right, currencies)
    value = _exact(context).add(left.amount, right.amount)
    return Money(value, left.currency, left.rounding)


def convert(
    money: Money,
    rate: RateDatum,
    *,
    label: Label,
    currencies: CurrencyTable,
    context: Context,
) -> RateResult:
    """Multiply by a recorded rate, preserving the weakest input label."""
    _validate(money, currencies)
    currencies.exponent(rate.target_currency)
    if money.currency != rate.source_currency:
        raise ValueError("rate does not apply to the amount currency")
    value = _exact(context).multiply(money.amount, rate.value)
    return RateResult(
        Money(value, rate.target_currency, money.rounding),
        rate,
        weakest_of(label, rate.label),
    )


def round_at(
    money: Money,
    point: RoundAt,
    *,
    currencies: CurrencyTable,
    context: Context,
    rule: RoundingRule | None = None,
) -> RoundedMoney:
    """Round at the declared point, or use labelled half-even presentation."""
    _validate(money, currencies)
    if rule is not None and point == rule.point:
        mode, source_id, label = rule.mode, rule.source_id, None
    elif rule is None and point == RoundAt.PRESENTATION:
        mode, source_id, label = ROUND_HALF_EVEN, currencies.source_id, "ASSUMPTION"
    else:
        return RoundedMoney(money)
    value = money.amount.quantize(
        currencies.quantum(money.currency), rounding=mode, context=context.copy()
    )
    return RoundedMoney(Money(value, money.currency, mode), source_id, label)


def within_tolerance(
    left: Money,
    right: Money,
    *,
    tolerance_units: int,
    rounding: str,
    currencies: CurrencyTable,
    context: Context,
) -> bool:
    """Compare rounded minor units against an explicit nonnegative tolerance."""
    _same_currency(left, right, currencies)
    if type(tolerance_units) is not int or tolerance_units < 0 or rounding not in _MODES:
        raise ValueError("comparison requires a validated tolerance and rounding mode")
    quantum = currencies.quantum(left.currency)
    local = context.copy()
    a = left.amount.quantize(quantum, rounding=rounding, context=local)
    b = right.amount.quantize(quantum, rounding=rounding, context=local)
    return abs(Fraction(a) - Fraction(b)) <= Fraction(quantum) * tolerance_units


def allocate(
    money: Money,
    weights: Mapping[str, int],
    *,
    currencies: CurrencyTable,
    context: Context,
) -> dict[str, Money]:
    """Allocate exact minor units by largest remainder with stable tie ordering."""
    _validate(money, currencies)
    if not weights or any(type(value) is not int or value < 0 for value in weights.values()):
        raise ValueError("allocation requires integer nonnegative weights")
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("allocation requires positive total weight")
    quantum = currencies.quantum(money.currency)
    units = Fraction(money.amount) / Fraction(quantum)
    if units.denominator != 1:
        raise ValueError("allocation requires a whole number of minor units")
    unsigned = abs(units.numerator)
    shares = {key: divmod(unsigned * value, total_weight) for key, value in weights.items()}
    remaining = unsigned - sum(share[0] for share in shares.values())
    order = sorted(shares, key=lambda key: (-shares[key][1], key))
    bumped = set(order[:remaining])
    direction = -1 if units < 0 else 1
    exact = _exact(context)
    return {
        key: Money(
            exact.multiply(Decimal(direction * (shares[key][0] + (key in bumped))), quantum),
            money.currency,
            money.rounding,
        )
        for key in sorted(shares)
    }

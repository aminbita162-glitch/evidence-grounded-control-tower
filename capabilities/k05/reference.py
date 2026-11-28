"""Normalize case lines and compute robust statistics for their reference group."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal, Inexact
from statistics import median

from kernel.lib.money import Money, convert
from kernel.lib.valuation import FxPack
from kernel.types.label import Label

MINIMUM_SAMPLE = 30
SCALE_FLOOR = Decimal("0.05")
MAD_FACTOR = Decimal("1.4826")


@dataclass(frozen=True, slots=True)
class Unit:
    dimension: str
    factor: Decimal

    def __post_init__(self) -> None:
        if not self.dimension or not self.factor.is_finite() or self.factor <= 0:
            raise ValueError("unit needs a dimension and positive conversion factor")


@dataclass(frozen=True, slots=True)
class NormalizedLine:
    value: Decimal
    quantity: Decimal
    label: Label

    def unit_value(self, context: Context) -> Decimal:
        return context.divide(self.value, self.quantity)


def normalize_line(
    amount: Money,
    quantity: Decimal,
    *,
    unit: str,
    basis_unit: str,
    basis_currency: str,
    units: Mapping[str, Unit],
    label: Label,
    fx: FxPack,
    declared_date: date,
    context: Context,
) -> NormalizedLine:
    """Convert a positive line into the units and currency of its reference group."""
    source = units.get(unit)
    target = units.get(basis_unit)
    if source is None or target is None or source.dimension != target.dimension:
        raise ValueError("UNIT_UNSUPPORTED")
    if not quantity.is_finite() or quantity <= 0:
        raise ValueError("UNIT_UNSUPPORTED")
    if not amount.amount.is_finite() or amount.amount <= 0:
        raise ValueError("REFERENCE_INSUFFICIENT")
    exact = context.copy()
    exact.traps[Inexact] = True
    converted_quantity = exact.divide(exact.multiply(quantity, source.factor), target.factor)
    rate = fx.rate(declared_date, amount.currency, basis_currency)
    converted = convert(amount, rate, label=label, currencies=fx.currencies, context=context)
    return NormalizedLine(converted.money.amount, converted_quantity, converted.label)


@dataclass(frozen=True, slots=True)
class ReferenceGroup:
    code: str
    unit: str
    currency: str
    values: tuple[Decimal, ...]


@dataclass(frozen=True, slots=True)
class ReferenceStatistics:
    group: ReferenceGroup
    requested_code: str
    center: Decimal
    scale: Decimal

    @property
    def fallback(self) -> bool:
        return self.group.code != self.requested_code


def _median(values: list[Decimal], context: Context) -> Decimal:
    # Decimal's division in statistics.median uses the active decimal context.
    from decimal import localcontext

    with localcontext(context):
        return median(values)


def reference_statistics(
    code: str,
    *,
    groups: Mapping[str, ReferenceGroup],
    parent: str | None,
    context: Context,
) -> ReferenceStatistics | None:
    """Use the exact group or its declared parent when at least 30 samples exist."""
    group = groups.get(code)
    if group is None or len(group.values) < MINIMUM_SAMPLE:
        group = groups.get(parent) if parent is not None else None
    if group is None or len(group.values) < MINIMUM_SAMPLE:
        return None
    if any(not value.is_finite() or value <= 0 for value in group.values):
        raise ValueError("REFERENCE_INSUFFICIENT")
    logged = [context.ln(value) for value in group.values]
    center = _median(logged, context)
    deviations = [context.abs(context.subtract(value, center)) for value in logged]
    scale = max(context.multiply(MAD_FACTOR, _median(deviations, context)), SCALE_FLOOR)
    return ReferenceStatistics(group, code, center, scale)

"""Compare audit observations with the corresponding estimate components."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal

from capabilities.l01 import InvoiceAudit
from capabilities.l02 import Estimate
from kernel.lib.money import Money, convert
from kernel.lib.taxonomy import LineKind
from kernel.lib.valuation import BasisUnavailable, FxPack
from kernel.types.label import weakest_of

_CONTEXT = Context(prec=128)
_ZERO = Decimal(0)


@dataclass(frozen=True, slots=True)
class Difference:
    charge_kind: str
    actual: Decimal
    estimated: Decimal
    difference: Decimal
    percent: Decimal | None
    actual_citations: tuple[str, ...]
    estimate_citations: tuple[str, ...]
    label: str


@dataclass(frozen=True, slots=True)
class Variance:
    currency: str
    components: tuple[Difference, ...]
    total: Difference | None
    unestimated: tuple[str, ...]
    unconverted: tuple[str, ...]
    observation_only: bool = True


def _compare(
    kind: str,
    actual: Decimal,
    estimated: Decimal,
    actual_sources: set[str],
    estimate_sources: set[str],
    label: str,
) -> Difference:
    gap = _CONTEXT.subtract(actual, estimated)
    return Difference(
        kind,
        actual,
        estimated,
        gap,
        _CONTEXT.divide(_CONTEXT.multiply(gap, Decimal(100)), estimated) if estimated else None,
        tuple(sorted(actual_sources)),
        tuple(sorted(estimate_sources)),
        label,
    )


def compare(estimate: Estimate, audit: InvoiceAudit, fx: FxPack, day: date) -> Variance:
    """Return observed differences and identify actual charges outside the estimate."""
    planned: dict[str, Decimal] = {}
    actual: dict[str, Decimal] = {}
    estimate_sources: dict[str, set[str]] = {}
    actual_sources: dict[str, set[str]] = {}
    labels: dict[str, str] = {}
    unestimated: set[str] = set()
    unconverted: set[str] = set()
    for item in estimate.components:
        name = item.component.code
        if item.converted is None:
            unconverted.add(name)
            continue
        planned[name] = _CONTEXT.add(planned.get(name, _ZERO), item.converted.base)
        estimate_sources.setdefault(name, set()).add(item.component.source_id)
        labels[name] = weakest_of(labels.get(name, item.label), item.label)
    for line in audit.lines:
        name = line.kind.code
        if not line.line.verified or line.kind.kind == LineKind.TAX:
            continue
        if name not in planned:
            if name not in unconverted:
                unestimated.add(name)
            continue
        try:
            rate = fx.rate(day, line.line.currency, estimate.currency)
        except BasisUnavailable:
            unconverted.add(name)
            continue
        value = convert(
            Money(line.billed, line.line.currency),
            rate,
            label=line.line.label,
            currencies=fx.currencies,
            context=_CONTEXT,
        )
        actual[name] = _CONTEXT.add(actual.get(name, _ZERO), value.money.amount)
        actual_sources.setdefault(name, set()).update((line.line.citation, rate.source_id))
        labels[name] = weakest_of(labels[name], value.label)
    rows = tuple(
        _compare(
            name,
            actual[name],
            planned[name],
            actual_sources[name],
            estimate_sources[name],
            labels[name],
        )
        for name in sorted(actual.keys() - unconverted)
    )
    total = None
    if rows and not unconverted and not unestimated:
        sum_estimate, sum_actual = _ZERO, _ZERO
        label = "OFFICIAL"
        for difference in rows:
            sum_estimate = _CONTEXT.add(sum_estimate, difference.estimated)
            sum_actual = _CONTEXT.add(sum_actual, difference.actual)
            label = weakest_of(label, difference.label)
        total = _compare(
            "COMPARED_CHARGES",
            sum_actual,
            sum_estimate,
            {source for row in rows for source in row.actual_citations},
            {source for row in rows for source in row.estimate_citations},
            label,
        )
    return Variance(
        estimate.currency, rows, total, tuple(sorted(unestimated)), tuple(sorted(unconverted))
    )

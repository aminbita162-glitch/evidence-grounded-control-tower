"""Calculate the documentary valuation basis using dated, recorded pack inputs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Context, Decimal
from enum import StrEnum

from kernel.lib.money import CurrencyTable, Money, RateDatum, add, convert, within_tolerance
from kernel.types.label import Label, weakest_of

__all__ = [
    "Adjustment",
    "Basis",
    "BasisUnavailable",
    "FxPack",
    "ValuationIssue",
    "ValuationRule",
    "valuation_basis",
]


class ValuationIssue(StrEnum):
    FX_UNAVAILABLE = "FX_UNAVAILABLE"
    VALUATION_RULE_UNAVAILABLE = "VALUATION_RULE_UNAVAILABLE"
    ADJUSTMENT_MISSING = "ADJUSTMENT_MISSING"


class BasisUnavailable(ValueError):
    """A required pack entry or verified adjustment is unavailable."""

    def __init__(self, issue: ValuationIssue) -> None:
        self.issue = issue
        super().__init__(issue.value)


@dataclass(frozen=True, slots=True)
class Adjustment:
    amount: Money
    fact_id: str
    label: Label


@dataclass(frozen=True, slots=True)
class FxPack:
    version_hash: str
    currencies: CurrencyTable
    rates: Mapping[tuple[date, str, str], RateDatum]
    label: Label

    def rate(self, day: date, source: str, target: str) -> RateDatum:
        if source not in self.currencies.minor_units or target not in self.currencies.minor_units:
            raise BasisUnavailable(ValuationIssue.FX_UNAVAILABLE)
        if source == target:
            return RateDatum(source, target, Decimal(1), self.currencies.source_id, self.label)
        rate = self.rates.get((day, source, target))
        if rate is None or (rate.source_currency, rate.target_currency) != (source, target):
            raise BasisUnavailable(ValuationIssue.FX_UNAVAILABLE)
        return rate


@dataclass(frozen=True, slots=True)
class ValuationRule:
    rule_id: str
    required_adjustments: tuple[str, ...]
    label: Label


@dataclass(frozen=True, slots=True)
class Basis:
    amount: Money
    label: Label
    rule_id: str
    fx_version_hash: str
    rates: tuple[RateDatum, ...]
    adjustment_fact_ids: tuple[str, ...]

    def agrees_with(self, declared: Money, *, currencies: CurrencyTable, context: Context) -> bool:
        """Compare the declared and computed values at the currency's minor unit."""
        return within_tolerance(
            self.amount,
            declared,
            tolerance_units=0,
            rounding=self.amount.rounding,
            currencies=currencies,
            context=context,
        )


def valuation_basis(
    invoice: Money,
    *,
    invoice_label: Label,
    target_currency: str,
    declared_date: date,
    incoterm: str,
    fx: FxPack,
    rules: Mapping[str, ValuationRule],
    adjustments: Mapping[str, Adjustment],
    context: Context,
) -> Basis:
    """Convert the invoice and add every adjustment required by the recorded rule."""
    rule = rules.get(incoterm)
    if rule is None:
        raise BasisUnavailable(ValuationIssue.VALUATION_RULE_UNAVAILABLE)
    if len(set(rule.required_adjustments)) != len(rule.required_adjustments):
        raise ValueError("duplicate adjustment in valuation rule")
    if any(not adjustments.get(name) for name in rule.required_adjustments):
        raise BasisUnavailable(ValuationIssue.ADJUSTMENT_MISSING)

    invoice_rate = fx.rate(declared_date, invoice.currency, target_currency)
    converted = convert(
        invoice, invoice_rate, label=invoice_label, currencies=fx.currencies, context=context
    )
    amount = converted.money
    label = weakest_of(weakest_of(converted.label, fx.label), rule.label)
    rates = [invoice_rate]
    fact_ids = []
    for name in rule.required_adjustments:
        adjustment = adjustments[name]
        if not adjustment.fact_id:
            raise BasisUnavailable(ValuationIssue.ADJUSTMENT_MISSING)
        rate = fx.rate(declared_date, adjustment.amount.currency, target_currency)
        converted = convert(
            adjustment.amount,
            rate,
            label=adjustment.label,
            currencies=fx.currencies,
            context=context,
        )
        amount = add(amount, converted.money, currencies=fx.currencies, context=context)
        label = weakest_of(label, converted.label)
        rates.append(rate)
        fact_ids.append(adjustment.fact_id)
    return Basis(amount, label, rule.rule_id, fx.version_hash, tuple(rates), tuple(fact_ids))

"""Estimate landed cost using the documented valuation basis and declared code."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal
from enum import StrEnum

from kernel.decision import FactEntry
from kernel.lib.calctrace import (
    Calculation,
    DecimalSettings,
    Formula,
    Operand,
    Operation,
    calculate,
)
from kernel.lib.money import Money, RoundAt, RoundingRule, convert, round_at
from kernel.lib.unblock import Requirement, RequirementKind, open_items, requirements_for
from kernel.lib.valuation import (
    Adjustment,
    Basis,
    BasisUnavailable,
    FxPack,
    ValuationIssue,
    ValuationRule,
    valuation_basis,
)
from kernel.types.decision import DecisionValue
from kernel.types.label import is_allow_eligible, weakest_of

_CONTEXT = Context(prec=128)
_SETTINGS = DecimalSettings(128, ROUND_HALF_EVEN)
_ZERO = Decimal(0)
_ONE = Decimal(1)
_WEIGHT = {"g": Decimal("0.001"), "kg": _ONE, "t": Decimal(1000)}


class Kind(StrEnum):
    DOCUMENT = "DOCUMENT"
    PACK = "PACK"
    ASSUMPTION = "ASSUMPTION"


class DutyKind(StrEnum):
    AD_VALOREM = "AD_VALOREM"
    SPECIFIC = "SPECIFIC"
    COMPOUND = "COMPOUND"


class Status(StrEnum):
    PROVIDED = "PROVIDED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ABSTAINED = "ABSTAINED"


class Reason(StrEnum):
    PROVIDED = "L02.ESTIMATE.PROVIDED"
    INDICATIVE = "L02.ESTIMATE.INDICATIVE"
    INCOMPLETE = "L02.ESTIMATE.INCOMPLETE"
    VARIANCE = "L02.OBS.VARIANCE_REPORTED"
    CONFLICT = "L02.NEEDS_REVIEW.RATE_CONFLICT"
    UPSTREAM = "L02.ABSTAIN.UPSTREAM"
    RULE = "L02.ABSTAIN.VALUATION_RULE_UNAVAILABLE"
    DUTY_PACK = "L02.ABSTAIN.DUTY_PACK_MISSING"
    CODE = "L02.ABSTAIN.CODE_NOT_IN_PACK"
    FX = "L02.ABSTAIN.FX_UNAVAILABLE"
    CURRENCY = "L02.ABSTAIN.CURRENCY_UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class Range:
    minimum: Decimal
    base: Decimal
    maximum: Decimal

    def __post_init__(self) -> None:
        if (
            not all(
                value.is_finite() and len(value.as_tuple().digits) <= 128
                for value in (self.minimum, self.base, self.maximum)
            )
            or not self.minimum <= self.base <= self.maximum
        ):
            raise ValueError("component range requires finite ordered exact decimals")

    @classmethod
    def exact(cls, value: Decimal) -> Range:
        return cls(value, value, value)

    def plus(self, other: Range) -> Range:
        return Range(
            _CONTEXT.add(self.minimum, other.minimum),
            _CONTEXT.add(self.base, other.base),
            _CONTEXT.add(self.maximum, other.maximum),
        )


@dataclass(frozen=True, slots=True)
class Component:
    code: str
    interval: Range
    currency: str
    kind: Kind
    label: str
    source_id: str

    def __post_init__(self) -> None:
        if not self.code or not self.source_id or self.interval.minimum < 0:
            raise ValueError("component requires nonnegative amounts and recorded provenance")
        if self.kind == Kind.ASSUMPTION and self.label != "ASSUMPTION":
            raise ValueError("assumption requires its evidence label")


@dataclass(frozen=True, slots=True)
class Goods:
    id: str
    code: str
    value: Money
    label: str
    source_id: str
    incoterm: str
    declared_on: date
    adjustments: dict[str, Adjustment]
    quantity: Decimal | None = None
    weight: Decimal | None = None
    weight_unit: str = "kg"
    quantities_verified: bool = False
    verified: bool = True

    def __post_init__(self) -> None:
        for value in (self.value.amount, self.quantity, self.weight):
            if value is not None and (
                not value.is_finite()
                or value < 0
                or not -30 <= value.adjusted() <= 30
                or len(value.as_tuple().digits) > 60
            ):
                raise ValueError("goods values and quantities must be bounded nonnegative decimals")

    def units(self, unit: str) -> Decimal | None:
        if not self.quantities_verified:
            return None
        if unit == "piece":
            return self.quantity
        if self.weight is None or self.weight_unit not in _WEIGHT or unit not in _WEIGHT:
            return None
        return _CONTEXT.divide(
            _CONTEXT.multiply(self.weight, _WEIGHT[self.weight_unit]), _WEIGHT[unit]
        )


@dataclass(frozen=True, slots=True)
class Preference:
    fact_key: str
    expected: str
    rate: Decimal

    def __post_init__(self) -> None:
        if not self.rate.is_finite() or self.rate < 0:
            raise ValueError("preference rate must be a nonnegative exact decimal")

    def applies(self, facts: tuple[FactEntry, ...], *, synthetic: bool) -> bool:
        matches = [fact for fact in facts if fact.key == self.fact_key]
        return len(matches) == 1 and all(
            fact.status == "VERIFIED"
            and fact.value == self.expected
            and (is_allow_eligible(fact.label) or synthetic and fact.label == "SYNTHETIC")
            for fact in matches
        )


@dataclass(frozen=True, slots=True)
class DutyRate:
    id: str
    code: str
    kind: DutyKind
    currency: str
    label: str
    valid_from: date
    valid_until: date
    ad_valorem: Decimal = _ZERO
    specific: Decimal = _ZERO
    unit: str = "kg"
    preference: Preference | None = None
    rounding: RoundingRule | None = None

    def __post_init__(self) -> None:
        if (
            not self.id
            or not self.code
            or self.valid_from >= self.valid_until
            or any(not v.is_finite() or v < 0 for v in (self.ad_valorem, self.specific))
        ):
            raise ValueError("invalid duty rate")

    def valid_at(self, at: date) -> bool:
        return self.valid_from <= at < self.valid_until


@dataclass(frozen=True, slots=True)
class DutyPack:
    version: str
    source_id: str
    valid_from: date
    valid_until: date
    rates: tuple[DutyRate, ...]

    def __post_init__(self) -> None:
        if not self.version or not self.source_id or self.valid_from >= self.valid_until:
            raise ValueError("invalid duty pack")

    def valid_at(self, at: date) -> bool:
        return self.valid_from <= at < self.valid_until


@dataclass(frozen=True, slots=True)
class TaxRate:
    id: str
    code: str
    label: str
    rate: Decimal
    base_codes: tuple[str, ...]
    valid_from: date
    valid_until: date
    rounding: RoundingRule | None = None

    def __post_init__(self) -> None:
        if (
            not self.id
            or not self.code
            or self.valid_from >= self.valid_until
            or not self.rate.is_finite()
            or self.rate < 0
            or not self.base_codes
            or len(set(self.base_codes)) != len(self.base_codes)
        ):
            raise ValueError("invalid tax rate")

    def valid_at(self, at: date) -> bool:
        return self.valid_from <= at < self.valid_until


@dataclass(frozen=True, slots=True)
class CostLine:
    component: Component
    converted: Range | None
    fx_rate: Decimal | None
    fx_source: str | None
    rate_day: date
    label: str
    trace: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class DutyLine:
    goods_id: str
    code: str
    basis: Basis
    rate_id: str
    amount: Decimal
    currency: str
    label: str
    preferred: bool
    trace: dict[str, object]


@dataclass(frozen=True, slots=True)
class UnitCosts:
    per_piece: Decimal | None
    per_kg: Decimal | None
    per_line: Decimal
    context_precision: int


@dataclass(frozen=True, slots=True)
class Estimate:
    status: Status
    reason_codes: tuple[Reason, ...]
    currency: str
    components: tuple[CostLine, ...] = ()
    duties: tuple[DutyLine, ...] = ()
    total: Range | None = None
    label: str | None = None
    unit_costs: UnitCosts | None = None
    missing: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    unblock: tuple[dict[str, object], ...] = ()


def _formula(
    id_: str,
    source: str,
    operation: Operation,
    left: Operand | Calculation,
    right: Operand | Calculation,
    currency: str,
    settings: DecimalSettings = _SETTINGS,
) -> Calculation:
    return calculate(Formula(id_, 1, operation, source), settings, left, right, unit=currency)


def _rounded(
    trace: Calculation,
    rule: RoundingRule | None,
    fx: FxPack,
    currency: str,
) -> Calculation:
    if rule is None or rule.point not in (RoundAt.LINE, RoundAt.TOTAL):
        return trace
    return _formula(
        "L02.PACK_ROUNDING",
        rule.source_id,
        Operation.QUANTIZE,
        trace,
        Operand(
            fx.currencies.source_id, fx.currencies.quantum(currency), currency, trace.result.label
        ),
        currency,
        DecimalSettings(_SETTINGS.precision, rule.mode),
    )


def _basis(goods: Goods, currency: str, fx: FxPack, rules: Mapping[str, ValuationRule]) -> Basis:
    return valuation_basis(
        goods.value,
        invoice_label=goods.label,
        target_currency=currency,
        declared_date=goods.declared_on,
        incoterm=goods.incoterm,
        fx=fx,
        rules=rules,
        adjustments=goods.adjustments,
        context=_CONTEXT,
    )


def _duty(
    goods: Goods,
    rate: DutyRate,
    base: Basis,
    facts: tuple[FactEntry, ...],
    fx: FxPack,
    *,
    synthetic: bool,
) -> DutyLine | None:
    selected = rate.preference
    preferred = selected is not None and selected.applies(facts, synthetic=synthetic)
    percentage = selected.rate if selected is not None and preferred else rate.ad_valorem
    currency = rate.currency
    parts: list[Calculation] = []
    if rate.kind != DutyKind.SPECIFIC:
        parts.append(
            _formula(
                "L02.AD_VALOREM",
                rate.id,
                Operation.MULTIPLY,
                Operand(base.rule_id, base.amount.amount, currency, base.label),
                Operand(rate.id, percentage, "ratio", rate.label),
                currency,
            )
        )
    if rate.kind != DutyKind.AD_VALOREM:
        units = goods.units(rate.unit)
        if units is None:
            return None
        parts.append(
            _formula(
                "L02.SPECIFIC",
                rate.id,
                Operation.MULTIPLY,
                Operand(goods.source_id, units, rate.unit, goods.label),
                Operand(rate.id, rate.specific, f"{currency}/{rate.unit}", rate.label),
                currency,
            )
        )
    trace = parts[0]
    if len(parts) == 2:
        trace = _formula("L02.COMPOUND", rate.id, Operation.ADD, trace, parts[1], currency)
    trace = _rounded(trace, rate.rounding, fx, currency)
    return DutyLine(
        goods.id,
        goods.code,
        base,
        rate.id,
        trace.result.value,
        currency,
        trace.result.label,
        preferred,
        trace.payload(),
    )


def _convert(
    component: Component,
    target: str,
    day: date,
    fx: FxPack,
    trace: tuple[dict[str, object], ...] = (),
) -> CostLine:
    try:
        rate = fx.rate(day, component.currency, target)
    except BasisUnavailable:
        return CostLine(component, None, None, None, day, component.label, trace)
    bases = (component.interval.minimum, component.interval.base, component.interval.maximum)
    amounts = tuple(
        convert(
            Money(value, component.currency),
            rate,
            label=component.label,
            currencies=fx.currencies,
            context=_CONTEXT,
        )
        for value in bases
    )
    conversion = _formula(
        "L02.FX_CONVERSION",
        rate.source_id,
        Operation.MULTIPLY,
        Operand(component.source_id, component.interval.base, component.currency, component.label),
        Operand(rate.source_id, rate.value, "fx_rate", rate.label),
        target,
    )
    return CostLine(
        component,
        Range(*(amount.money.amount for amount in amounts)),
        rate.value,
        rate.source_id,
        day,
        weakest_of(amounts[1].label, fx.label),
        (*trace, conversion.payload()),
    )


def _sum_ranges(lines: Iterable[Range]) -> Range:
    result = Range.exact(_ZERO)
    for line in lines:
        result = result.plus(line)
    return result


def _tax(
    rate: TaxRate,
    bases: dict[str, Range],
    labels: dict[str, str],
    currency: str,
    fx: FxPack,
) -> tuple[Component, dict[str, object]]:
    values = _sum_ranges(bases[name] for name in rate.base_codes)
    evidence_label = rate.label
    for name in rate.base_codes:
        evidence_label = weakest_of(evidence_label, labels[name])
    trace = _formula(
        "L02.TAX",
        rate.id,
        Operation.MULTIPLY,
        Operand(":".join(rate.base_codes), values.base, currency, evidence_label),
        Operand(rate.id, rate.rate, "ratio", rate.label),
        currency,
    )
    trace = _rounded(trace, rate.rounding, fx, currency)
    limits = []
    for value in (values.minimum, values.maximum):
        amount = Money(_CONTEXT.multiply(value, rate.rate), currency)
        if rate.rounding is not None:
            amount = round_at(
                amount,
                rate.rounding.point,
                currencies=fx.currencies,
                context=_CONTEXT,
                rule=rate.rounding,
            ).money
        limits.append(amount.amount)
    return (
        Component(
            rate.code,
            Range(limits[0], trace.result.value, limits[1]),
            currency,
            Kind.PACK,
            trace.result.label,
            rate.id,
        ),
        trace.payload(),
    )


def _unblock(
    reasons: tuple[Reason, ...],
    missing: tuple[str, ...],
) -> tuple[dict[str, object], ...]:
    names = {
        Reason.CONFLICT: "unambiguous effective rates",
        Reason.UPSTREAM: "verified canonical shipment facts",
        Reason.RULE: "applicable valuation rule",
        Reason.DUTY_PACK: "effective duty-rate pack",
        Reason.CODE: "registered rate for the declared code",
        Reason.FX: "dated FX rate for goods value",
        Reason.CURRENCY: "currency minor-unit table",
        Reason.INDICATIVE: "evidence at DERIVED or stronger",
    }
    rules: dict[str, tuple[tuple[Requirement, ...], ...]] = {
        reason.value: ((Requirement(RequirementKind.PACK, name),),)
        for reason, name in names.items()
    }
    rules[Reason.INCOMPLETE.value] = (
        tuple(Requirement(RequirementKind.FACT, name) for name in missing),
    )
    needs = requirements_for(DecisionValue.ABSTAIN, (r for r in reasons if r in rules), rules)
    return tuple(dict(item) for item in open_items(needs))


def _failure(currency: str, reason: Reason) -> Estimate:
    status = Status.NEEDS_REVIEW if reason == Reason.CONFLICT else Status.ABSTAINED
    return Estimate(status, (reason,), currency, unblock=_unblock((reason,), ()))


def _unit_costs(goods: tuple[Goods, ...], total: Decimal) -> UnitCosts | None:
    if not all(row.quantities_verified for row in goods):
        return None
    piece = _ZERO
    weight = _ZERO
    for row in goods:
        piece = _CONTEXT.add(piece, row.quantity or _ZERO)
        weight = _CONTEXT.add(weight, row.units("kg") or _ZERO)
    return UnitCosts(
        _CONTEXT.divide(total, piece) if piece else None,
        _CONTEXT.divide(total, weight) if weight else None,
        _CONTEXT.divide(total, Decimal(len(goods))),
        _CONTEXT.prec,
    )


def evaluate(
    goods: tuple[Goods, ...],
    *,
    components: tuple[Component, ...],
    rates: DutyPack | None,
    taxes: tuple[TaxRate, ...],
    fx: FxPack,
    valuation_rules: Mapping[str, ValuationRule],
    currency: str,
    at: date,
    facts: tuple[FactEntry, ...] = (),
    required_components: frozenset[str] = frozenset(),
    synthetic: bool = False,
) -> Estimate:
    """Compute complete totals only when every required component can be converted."""

    def fail(reason: Reason) -> Estimate:
        return _failure(currency, reason)

    if not goods or any(not row.verified or not row.code or not row.source_id for row in goods):
        return fail(Reason.UPSTREAM)
    if rates is None or not rates.valid_at(at):
        return fail(Reason.DUTY_PACK)
    if currency not in fx.currencies.minor_units or any(
        row.value.currency not in fx.currencies.minor_units for row in goods
    ):
        return fail(Reason.CURRENCY)

    costs: list[CostLine] = []
    duties: list[DutyLine] = []
    bases: dict[str, Range] = {}
    labels: dict[str, str] = {}
    notes: list[str] = []
    missing = required_components.difference(component.code for component in components)
    unavailable_bases = set(missing)

    def include(cost: CostLine) -> None:
        nonlocal missing
        costs.append(cost)
        code = cost.component.code
        if cost.converted is None:
            unavailable_bases.add(code)
            missing = missing.union((f"{code}:{cost.component.currency}/{currency}",))
            return
        bases[code] = bases.get(code, Range.exact(_ZERO)).plus(cost.converted)
        labels[code] = weakest_of(labels.get(code, cost.label), cost.label)

    for item in sorted(goods, key=lambda item: item.id):
        applicable = [rate for rate in rates.rates if rate.code == item.code and rate.valid_at(at)]
        if not applicable:
            return fail(Reason.CODE)
        if len(applicable) > 1:
            return fail(Reason.CONFLICT)
        rate = applicable[0]
        if rate.currency not in fx.currencies.minor_units:
            return fail(Reason.CURRENCY)
        try:
            valuation = _basis(item, rate.currency, fx, valuation_rules)
        except BasisUnavailable as error:
            return fail(
                {
                    ValuationIssue.FX_UNAVAILABLE: Reason.FX,
                    ValuationIssue.VALUATION_RULE_UNAVAILABLE: Reason.RULE,
                    ValuationIssue.ADJUSTMENT_MISSING: Reason.UPSTREAM,
                }[error.issue]
            )
        duty = _duty(item, rate, valuation, facts, fx, synthetic=synthetic)
        if duty is None:
            return fail(Reason.UPSTREAM)
        duties.append(duty)
        if rate.preference is not None and not duty.preferred:
            notes.append(f"{item.id}: preferential rate did not apply")
        include(
            _convert(
                Component(
                    "GOODS",
                    Range.exact(item.value.amount),
                    item.value.currency,
                    Kind.DOCUMENT,
                    item.label,
                    item.source_id,
                ),
                currency,
                at,
                fx,
            )
        )
        include(
            _convert(
                Component(
                    "DUTY",
                    Range.exact(duty.amount),
                    duty.currency,
                    Kind.PACK,
                    duty.label,
                    duty.rate_id,
                ),
                currency,
                at,
                fx,
                (duty.trace,),
            )
        )
        try:
            fx_basis = fx.rate(item.declared_on, valuation.amount.currency, currency)
        except BasisUnavailable:
            return fail(Reason.FX)
        base_in_currency = convert(
            valuation.amount,
            fx_basis,
            label=valuation.label,
            currencies=fx.currencies,
            context=_CONTEXT,
        )
        key = "VALUATION"
        bases[key] = bases.get(key, Range.exact(_ZERO)).plus(
            Range.exact(base_in_currency.money.amount)
        )
        labels[key] = weakest_of(labels.get(key, base_in_currency.label), base_in_currency.label)
    for component in sorted(components, key=lambda row: (row.code, row.source_id)):
        include(_convert(component, currency, at, fx))

    active = sorted((tax for tax in taxes if tax.valid_at(at)), key=lambda tax: (tax.code, tax.id))
    if len({rate.code for rate in active}) != len(active):
        return fail(Reason.CONFLICT)
    for tax in active:
        if any(name not in bases or name in unavailable_bases for name in tax.base_codes):
            unavailable_bases.add(tax.code)
            missing = missing.union((tax.code,))
            continue
        component, trace = _tax(tax, bases, labels, currency, fx)
        include(_convert(component, currency, at, fx, (trace,)))

    label = "OFFICIAL"
    for cost in costs:
        label = weakest_of(label, cost.label)
    total = (
        None
        if missing
        else _sum_ranges(cost.converted for cost in costs if cost.converted is not None)
    )
    if missing:
        reason = Reason.INCOMPLETE
    elif is_allow_eligible(label):
        reason = Reason.PROVIDED
    else:
        reason = Reason.INDICATIVE
    reasons = (reason,)
    gaps = tuple(sorted(missing))
    return Estimate(
        Status.PROVIDED,
        reasons,
        currency,
        tuple(costs),
        tuple(duties),
        total,
        label,
        _unit_costs(goods, total.base) if total is not None else None,
        gaps,
        tuple(notes),
        _unblock(reasons, gaps),
    )

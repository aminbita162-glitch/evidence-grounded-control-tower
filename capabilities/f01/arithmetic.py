"""Fixed-point arithmetic and independently checked interval constraints."""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from decimal import Decimal, getcontext

from capabilities.f01 import (
    Edge,
    Fact,
    Finding,
    Interval,
    Workflow,
    _finding,
    decimal_amount,
    quantity,
)
from kernel.lib.money import CurrencyTable, RoundAt, round_at
from kernel.lib.solve import Constraint, IntegerModel, Settings, Term, Variable, solve_z3
from kernel.types.money import Money

_SETTINGS = Settings(seed=0, workers=1, seconds=0.2)


def _minor(amount: Decimal, currency: str, currencies: Mapping[str, int]) -> Decimal:
    if currency not in currencies or not 0 <= currencies[currency] <= 12:
        raise ValueError("CURRENCY_PRECISION_UNAVAILABLE")
    table = CurrencyTable(currencies, "F01-WORKFLOW")
    money = round_at(
        Money(amount, currency), RoundAt.PRESENTATION, currencies=table, context=getcontext()
    ).money
    return money.amount.scaleb(table.exponent(currency))


def money_minor(fact: Fact, currencies: Mapping[str, int]) -> Decimal:
    return _minor(decimal_amount(fact), fact.currency or "", currencies)


def _point(value: Decimal) -> Interval:
    return Interval(value, value)


def _solve(
    bounds: Sequence[Interval],
    weights: tuple[int, ...],
    rule: str,
    upper_only: bool,
) -> tuple[bool | None, tuple[int, ...]]:
    scale = max(0, max(-int(v.as_tuple().exponent) for b in bounds for v in (b.low, b.high)))
    limits = tuple((int(b.low.scaleb(scale)), int(b.high.scaleb(scale))) for b in bounds)
    # Fixed domains express the evidence. With any domain removed, the associated
    # operand is free over the largest sum of magnitudes and can satisfy the rule.
    wide = sum(max(abs(lo), abs(hi)) for lo, hi in limits) + 1
    variables = tuple(Variable(f"x{i}", -wide, wide) for i in range(len(bounds)))
    terms = tuple(Term(var.name, weight) for var, weight in zip(variables, weights, strict=True))
    equation = Constraint(rule, terms, lower=None if upper_only else 0, upper=0)
    evidence = tuple(
        Constraint(f"fact{i}", (Term(var.name, 1),), lo, hi)
        for i, (var, (lo, hi)) in enumerate(zip(variables, limits, strict=True))
    )
    result = solve_z3(IntegerModel(variables, (equation, *evidence)), _SETTINGS)
    if result.status != "INFEASIBLE":
        return (True if result.status == "SOLVED" else None), ()
    # A tracked core is a sufficient subset. Minimize it by testing each removal.
    indices = [i for i in range(len(evidence)) if f"fact{i}" in result.evidence]
    for index in tuple(indices):
        subset = tuple(evidence[i] for i in indices if i != index)
        check = solve_z3(IntegerModel(variables, (equation, *subset)), _SETTINGS)
        if check.status == "ABSTAIN":
            return None, ()
        if check.status == "INFEASIBLE":
            indices.remove(index)
    return False, tuple(indices)


def check(
    rule: str,
    code: str,
    facts: Sequence[Fact],
    bounds: Sequence[Interval],
    *,
    upper_only: bool = False,
) -> tuple[Finding | None, Edge]:
    weights = (1,) * (len(bounds) - 1) + (-1,)
    left = Interval(
        sum((x.low for x in bounds[:-1]), Decimal(0)),
        sum((x.high for x in bounds[:-1]), Decimal(0)),
    )
    primary = left.low <= bounds[-1].high if upper_only else left.overlaps(bounds[-1])
    independent, core = _solve(bounds, weights, rule, upper_only)
    ids = tuple(f.fact_id for f in facts)
    edge = Edge("ARITHMETIC", rule, ids)
    if primary != independent:
        return _finding(
            "ESCALATE.SOLVER_DISAGREEMENT",
            "ESCALATE",
            facts,
            f"Independent constraint check could not confirm {rule}.",
        ), edge
    if not primary:
        return _finding(
            code, "HOLD", facts, f"The cited values violate {rule}.", tuple(ids[i] for i in core)
        ), edge
    return None, edge


def _measurements(facts: Sequence[Fact]) -> list[Interval]:
    values = [quantity(fact) for fact in facts]
    if len({unit for unit, _ in values}) != 1:
        raise ValueError("UNITS_INCOMPARABLE")
    return [interval for _, interval in values]


def _checks(
    fields: Mapping[str, Fact],
    workflow: Workflow,
) -> Iterator[tuple[str, str, Sequence[Fact], Sequence[Interval], bool]]:
    currencies = dict(workflow.currency_precision)
    lines = sorted({name.rsplit(".", 1)[0] for name in fields if name.startswith("line_items.")})
    weights = sorted(name for name in fields if name.startswith("package_gross_weight."))
    for rule, code, members, target in (
        ("ARI-1", "ARITH.SUM_VALUE", [f"{key}.line_amount" for key in lines], "invoice_total"),
        ("ARI-3", "ARITH.SUM_WEIGHT", weights, "gross_weight"),
        ("ARI-5", "ARITH.SUM_QUANTITY", [f"{key}.quantity" for key in lines], "total_quantity"),
    ):
        if not members or any(name not in fields for name in (*members, target)):
            continue
        facts = [fields[name] for name in (*members, target)]
        if rule == "ARI-1":
            if len({fact.currency for fact in facts}) != 1:
                continue
            yield rule, code, facts, [_point(money_minor(f, currencies)) for f in facts], False
        else:
            yield rule, code, facts, _measurements(facts), False
    for key in lines:
        keys = tuple(f"{key}.{name}" for name in ("quantity", "unit_price", "line_amount"))
        if any(name not in fields for name in keys):
            continue
        count, price, total = (fields[name] for name in keys)
        if price.currency != total.currency:
            continue
        product = decimal_amount(count) * decimal_amount(price)
        yield (
            "ARI-2",
            "ARITH.LINE_AMOUNT",
            (count, price, total),
            (
                _point(_minor(product, price.currency or "", currencies)),
                _point(money_minor(total, currencies)),
            ),
            False,
        )
    if "net_weight" in fields and "gross_weight" in fields:
        pair = (fields["net_weight"], fields["gross_weight"])
        yield "ARI-4", "ARITH.NET_GT_GROSS", pair, _measurements(pair), True
    if weights and "package_count" in fields:
        package_count = fields["package_count"]
        facts = [fields[name] for name in weights] + [package_count]
        bounds = [_point(Decimal(1)) for _ in weights] + [_point(decimal_amount(package_count))]
        yield "ARI-6", "ARITH.PACKAGES", facts, bounds, False


def arithmetic_findings(
    facts: Sequence[Fact],
    workflow: Workflow,
) -> Iterator[tuple[Finding | None, Edge]]:
    documents: dict[str, dict[str, Fact]] = {}
    conflicted: set[tuple[str, str]] = set()
    for fact in facts:
        if fact.status == "VERIFIED":
            fields = documents.setdefault(fact.document_id, {})
            old = fields.get(fact.field)
            if old and (old.value, old.unit, old.currency) != (
                fact.value,
                fact.unit,
                fact.currency,
            ):
                conflicted.add((fact.document_id, fact.field))
            fields[fact.field] = fact
    for document, fields in documents.items():
        eligible = {
            name: fact for name, fact in fields.items() if (document, name) not in conflicted
        }
        try:
            for rule, code, selected, bounds, upper_only in _checks(eligible, workflow):
                yield check(rule, code, selected, bounds, upper_only=upper_only)
        except ValueError:
            affected = list(eligible.values())
            yield (
                _finding(
                    "ABSTAIN.FACT_NOT_VERIFIED",
                    "ABSTAIN",
                    affected,
                    "A cited arithmetic operand cannot be evaluated.",
                ),
                Edge("ARITHMETIC", "NOT_EVALUABLE", tuple(f.fact_id for f in affected)),
            )

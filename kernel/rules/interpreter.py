"""Reference interpreter for the rule engine (Part 3 §3.6, P06-T03).

Evaluates rules whose validity window contains the explicit evaluation time
over VERIFIED facts only.  Records every rule considered with state APPLIED,
NOT_APPLICABLE or SKIPPED (with reason).  A missing fact gives ABSTAIN; a
CONFLICTED fact gives ESCALATE with both citations.  Decimal arithmetic uses
an explicit context.  No clock, no network.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from typing import Literal

from kernel.rules.dsl.types import (
    Add,
    All,
    And,
    AnyExpr,
    BoolLit,
    CountExpr,
    DateAdd,
    DateDiff,
    DateLit,
    DecimalLit,
    Div,
    Eq,
    Expr,
    FieldRef,
    Ge,
    Gt,
    In,
    IntLit,
    Le,
    Lt,
    Mul,
    Ne,
    Not,
    Or,
    StringEq,
    StringLit,
    Sub,
)

__all__ = [
    "RuleResult",
    "InterpreterError",
    "MissingFactError",
    "ConflictedFactError",
    "interpret",
    "evaluate_condition",
]


@dataclass(frozen=True)
class RuleResult:
    """A single rule evaluation result.

    Attributes:
        rule_id: The rule's identifier.
        rule_version: The rule's version.
        state: APPLIED, NOT_APPLICABLE or SKIPPED.
        outcome: The effective outcome (ALLOW, ABSTAIN, HOLD, ESCALATE).
        reason_code: A stable code explaining the state.
        citations: Citations for ESCALATE (both conflicting citations).
    """

    rule_id: str
    rule_version: str
    state: Literal["APPLIED", "NOT_APPLICABLE", "SKIPPED"]
    outcome: str
    reason_code: str
    citations: tuple[str, ...] = field(default_factory=tuple)


class InterpreterError(Exception):
    """Base interpreter error."""


class MissingFactError(InterpreterError):
    """A referenced fact is missing or not VERIFIED."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"missing fact: {key!r}")


class ConflictedFactError(InterpreterError):
    """A referenced fact is CONFLICTED."""

    def __init__(self, key: str, citations: tuple[str, ...]) -> None:
        self.key = key
        self.citations = citations
        super().__init__(f"conflicted fact: {key!r}")


#: Fact set type: key -> (value, status, citations).
FactSet = Mapping[str, tuple[str, str, tuple[str, ...]]]


def _get_fact(facts: FactSet, key: str) -> str:
    """Look up a fact by key.  Only VERIFIED facts are returned.

    Raises:
        MissingFactError: If the fact is absent or not VERIFIED.
        ConflictedFactError: If the fact is CONFLICTED.
    """
    entry = facts.get(key)
    if entry is None:
        raise MissingFactError(key)
    value, status, citations = entry
    if status == "CONFLICTED":
        raise ConflictedFactError(key, citations)
    if status != "VERIFIED":
        raise MissingFactError(key)
    return value


def _eval(expr: Expr, facts: FactSet) -> object:
    """Evaluate an expression against the fact set.

    Returns:
        The evaluated value (bool, int, Decimal, str, or list).

    Raises:
        MissingFactError: If a referenced fact is missing.
        ConflictedFactError: If a referenced fact is CONFLICTED.
    """
    if isinstance(expr, BoolLit):
        return expr.value
    if isinstance(expr, IntLit):
        return expr.value
    if isinstance(expr, DecimalLit):
        return expr.value
    if isinstance(expr, StringLit):
        return expr.value
    if isinstance(expr, DateLit):
        return f"{expr.year:04d}-{expr.month:02d}-{expr.day:02d}"
    if isinstance(expr, FieldRef):
        return _get_fact(facts, expr.name)
    if isinstance(expr, And):
        return all(_eval(operand, facts) for operand in expr.operands)
    if isinstance(expr, Or):
        return any(_eval(operand, facts) for operand in expr.operands)
    if isinstance(expr, Not):
        return not _eval(expr.operand, facts)
    if isinstance(expr, Eq):
        return str(_eval(expr.left, facts)) == str(_eval(expr.right, facts))
    if isinstance(expr, Ne):
        return str(_eval(expr.left, facts)) != str(_eval(expr.right, facts))
    if isinstance(expr, Lt):
        return _to_decimal(_eval(expr.left, facts)) < _to_decimal(_eval(expr.right, facts))
    if isinstance(expr, Le):
        return _to_decimal(_eval(expr.left, facts)) <= _to_decimal(_eval(expr.right, facts))
    if isinstance(expr, Gt):
        return _to_decimal(_eval(expr.left, facts)) > _to_decimal(_eval(expr.right, facts))
    if isinstance(expr, Ge):
        return _to_decimal(_eval(expr.left, facts)) >= _to_decimal(_eval(expr.right, facts))
    if isinstance(expr, Add):
        ctx = getcontext()
        return ctx.add(_to_decimal(_eval(expr.left, facts)), _to_decimal(_eval(expr.right, facts)))
    if isinstance(expr, Sub):
        ctx = getcontext()
        return ctx.subtract(
            _to_decimal(_eval(expr.left, facts)), _to_decimal(_eval(expr.right, facts))
        )
    if isinstance(expr, Mul):
        ctx = getcontext()
        return ctx.multiply(
            _to_decimal(_eval(expr.left, facts)), _to_decimal(_eval(expr.right, facts))
        )
    if isinstance(expr, Div):
        ctx = getcontext()
        return ctx.divide(
            _to_decimal(_eval(expr.left, facts)), _to_decimal(_eval(expr.right, facts))
        )
    if isinstance(expr, In):
        item = _eval(expr.item, facts)
        collection = _eval(expr.collection, facts)
        if isinstance(collection, str):
            return str(item) in collection.split(",")
        if isinstance(collection, list):
            return item in collection
        return False
    if isinstance(expr, StringEq):
        left = str(_eval(expr.left, facts)).strip().casefold()
        right = str(_eval(expr.right, facts)).strip().casefold()
        return left == right
    if isinstance(expr, DateAdd):
        date_val = str(_eval(expr.date, facts))
        days = int(str(_eval(expr.days, facts)))
        from datetime import datetime, timedelta

        dt = datetime.fromisoformat(date_val)
        result = dt + timedelta(days=days)
        return result.date().isoformat()
    if isinstance(expr, DateDiff):
        start = str(_eval(expr.start, facts))
        end = str(_eval(expr.end, facts))
        from datetime import datetime

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        return (end_dt - start_dt).days
    if isinstance(expr, All):
        collection = _eval(expr.collection, facts)
        if isinstance(collection, list):
            return all(_eval_with_item(expr.predicate, facts, item) for item in collection)
        return False
    if isinstance(expr, AnyExpr):
        collection = _eval(expr.collection, facts)
        if isinstance(collection, list):
            return any(_eval_with_item(expr.predicate, facts, item) for item in collection)
        return False
    if isinstance(expr, CountExpr):
        collection = _eval(expr.collection, facts)
        if isinstance(collection, list):
            return len(collection)
        return 0
    raise InterpreterError(f"unhandled expression type: {type(expr).__name__}")


def _eval_with_item(predicate: Expr, facts: FactSet, item: object) -> bool:
    """Evaluate a predicate with an item bound to '_item_'."""
    extended: dict[str, tuple[str, str, tuple[str, ...]]] = dict(facts)
    extended["_item_"] = (str(item), "VERIFIED", ())
    result = _eval(predicate, extended)
    return bool(result)


def _to_decimal(value: object) -> Decimal:
    """Convert a value to Decimal for arithmetic."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str):
        return Decimal(value)
    return Decimal(str(value))


def evaluate_condition(
    condition: Expr,
    facts: FactSet,
) -> tuple[bool, str]:
    """Evaluate a rule condition.

    Returns:
        A tuple of (result, reason).  If evaluation succeeds, result is the
        boolean condition result and reason is "OK".  If a fact is missing,
        returns (False, "ABSTAIN").  If a fact is CONFLICTED, returns
        (False, "ESCALATE").

    Raises:
        ConflictedFactError: If a fact is CONFLICTED (caller handles ESCALATE).
    """
    try:
        result = bool(_eval(condition, facts))
        return result, "OK"
    except MissingFactError:
        return False, "ABSTAIN"


def interpret(
    rules: Sequence[Mapping[str, object]],
    facts: FactSet,
    evaluation_time: str,
) -> list[RuleResult]:
    """Interpret a list of rules against a fact set at a given time.

    Args:
        rules: The list of rule definitions (each a Mapping).
        facts: The fact set (key -> (value, status, citations)).
        evaluation_time: ISO 8601 UTC timestamp.

    Returns:
        A list of :class:`RuleResult` for every rule considered.
    """
    from kernel.rules.dsl.parser import parse_expr

    results: list[RuleResult] = []
    for rule in rules:
        rule_id = str(rule.get("id", ""))
        rule_version = str(rule.get("version", ""))
        valid_from = str(rule.get("valid_from", ""))
        valid_to = str(rule.get("valid_to", ""))
        declared_outcome = str(rule.get("outcome", "ABSTAIN"))
        reason_code = str(rule.get("reason_code", ""))
        condition_raw = rule.get("condition", {})

        # Window check
        if not (valid_from <= evaluation_time <= valid_to):
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    rule_version=rule_version,
                    state="SKIPPED",
                    outcome="ABSTAIN",
                    reason_code="RULE.SKIPPED.OUTSIDE_WINDOW",
                    citations=(),
                )
            )
            continue

        # Parse condition
        condition = parse_expr(dict(condition_raw) if isinstance(condition_raw, Mapping) else {})

        # Evaluate
        try:
            result, reason = evaluate_condition(condition, facts)
        except ConflictedFactError as exc:
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    rule_version=rule_version,
                    state="NOT_APPLICABLE",
                    outcome="ESCALATE",
                    reason_code=f"RULE.ESCALATE.CONFLICTED_FACT:{exc.key}",
                    citations=exc.citations,
                )
            )
            continue

        if reason == "ABSTAIN":
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    rule_version=rule_version,
                    state="NOT_APPLICABLE",
                    outcome="ABSTAIN",
                    reason_code="RULE.ABSTAIN.MISSING_FACT",
                    citations=(),
                )
            )
        elif result:
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    rule_version=rule_version,
                    state="APPLIED",
                    outcome=declared_outcome,
                    reason_code=reason_code,
                    citations=(),
                )
            )
        else:
            results.append(
                RuleResult(
                    rule_id=rule_id,
                    rule_version=rule_version,
                    state="NOT_APPLICABLE",
                    outcome="ABSTAIN",
                    reason_code="RULE.NOT_APPLICABLE.CONDITION_FALSE",
                    citations=(),
                )
            )

    return results

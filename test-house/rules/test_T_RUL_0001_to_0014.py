"""Tests for the Pack DSL types and parser (P06-T01).

Test IDs: T-RUL-0001 to T-RUL-0014.
Covers: every allowed construct parses; every forbidden construct is
rejected with a stable error code; every expression terminates (checked
by structural bound).

Spec: Part 3 §3.6; kernel/rules/dsl/types.py; kernel/rules/dsl/parser.py.
"""

from __future__ import annotations

import pytest

from kernel.rules.dsl.parser import ParseError, parse_expr
from kernel.rules.dsl.types import MAX_DEPTH, And, BoolLit, Eq, FieldRef, IntLit

# ---------------------------------------------------------------------------
# T-RUL-0001 — A boolean literal parses
# ---------------------------------------------------------------------------
# id: T-RUL-0001
# title: A boolean literal parses
# purpose: Verify that the bool literal type parses correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "bool" and value true
# expected: parse_expr returns a BoolLit with value True
# risk: boolean values misinterpreted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0001_bool_literal_parses() -> None:
    """A boolean literal parses into a BoolLit."""
    result = parse_expr({"type": "bool", "value": True})
    assert isinstance(result, BoolLit)
    assert result.value is True


# ---------------------------------------------------------------------------
# T-RUL-0002 — An integer literal parses
# ---------------------------------------------------------------------------
# id: T-RUL-0002
# title: An integer literal parses
# purpose: Verify that the int literal type parses correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "int" and value 42
# expected: parse_expr returns an IntLit with value 42
# risk: integer values misinterpreted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0002_int_literal_parses() -> None:
    """An integer literal parses into an IntLit."""
    result = parse_expr({"type": "int", "value": 42})
    assert isinstance(result, IntLit)
    assert result.value == 42


# ---------------------------------------------------------------------------
# T-RUL-0003 — A decimal literal parses
# ---------------------------------------------------------------------------
# id: T-RUL-0003
# title: A decimal literal parses
# purpose: Verify that the decimal literal type parses correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "decimal" and value "100.50"
# expected: parse_expr returns a DecimalLit with Decimal("100.50")
# risk: decimal values misinterpreted or floating point introduced
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0003_decimal_literal_parses() -> None:
    """A decimal literal parses into a DecimalLit."""
    from decimal import Decimal

    from kernel.rules.dsl.types import DecimalLit

    result = parse_expr({"type": "decimal", "value": "100.50"})
    assert isinstance(result, DecimalLit)
    assert result.value == Decimal("100.50")


# ---------------------------------------------------------------------------
# T-RUL-0004 — A string literal parses
# ---------------------------------------------------------------------------
# id: T-RUL-0004
# title: A string literal parses
# purpose: Verify that the string literal type parses correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "string" and value "hello"
# expected: parse_expr returns a StringLit with value "hello"
# risk: string values misinterpreted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0004_string_literal_parses() -> None:
    """A string literal parses into a StringLit."""
    from kernel.rules.dsl.types import StringLit

    result = parse_expr({"type": "string", "value": "hello"})
    assert isinstance(result, StringLit)
    assert result.value == "hello"


# ---------------------------------------------------------------------------
# T-RUL-0005 — A field reference parses
# ---------------------------------------------------------------------------
# id: T-RUL-0005
# title: A field reference parses
# purpose: Verify that field access (field reference) parses correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "field" and name "hs_code"
# expected: parse_expr returns a FieldRef with name "hs_code"
# risk: field references misresolved
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0005_field_ref_parses() -> None:
    """A field reference parses into a FieldRef."""
    result = parse_expr({"type": "field", "name": "hs_code"})
    assert isinstance(result, FieldRef)
    assert result.name == "hs_code"


# ---------------------------------------------------------------------------
# T-RUL-0006 — Boolean operators (and, or, not) parse
# ---------------------------------------------------------------------------
# id: T-RUL-0006
# title: Boolean operators parse
# purpose: Verify that and, or, and not parse correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: dicts with type "and", "or", and "not"
# expected: parse_expr returns And, Or, and Not respectively
# risk: boolean logic misconstructed
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0006_boolean_operands_parse() -> None:
    """Boolean operators and, or, not parse correctly."""
    from kernel.rules.dsl.types import Not, Or

    result_and = parse_expr(
        {
            "type": "and",
            "operands": [
                {"type": "bool", "value": True},
                {"type": "bool", "value": False},
            ],
        }
    )
    assert isinstance(result_and, And)
    assert len(result_and.operands) == 2

    result_or = parse_expr(
        {
            "type": "or",
            "operands": [
                {"type": "bool", "value": True},
                {"type": "bool", "value": False},
            ],
        }
    )
    assert isinstance(result_or, Or)
    assert len(result_or.operands) == 2

    result_not = parse_expr(
        {
            "type": "not",
            "operand": {"type": "bool", "value": True},
        }
    )
    assert isinstance(result_not, Not)
    assert isinstance(result_not.operand, BoolLit)


# ---------------------------------------------------------------------------
# T-RUL-0007 — Comparisons (eq, ne, lt, le, gt, ge) parse
# ---------------------------------------------------------------------------
# id: T-RUL-0007
# title: Comparison operators parse
# purpose: Verify that all six comparison types parse correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: dicts with each comparison type
# expected: parse_expr returns the corresponding typed expression
# risk: comparison logic misconstructed
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0007_comparisons_parse() -> None:
    """All comparison operators parse correctly."""
    from kernel.rules.dsl.types import Ge, Gt, Le, Lt, Ne

    for type_name, cls in [
        ("eq", Eq),
        ("ne", Ne),
        ("lt", Lt),
        ("le", Le),
        ("gt", Gt),
        ("ge", Ge),
    ]:
        result = parse_expr(
            {
                "type": type_name,
                "left": {"type": "int", "value": 1},
                "right": {"type": "int", "value": 2},
            }
        )
        assert isinstance(result, cls), f"{type_name} did not parse to {cls.__name__}"


# ---------------------------------------------------------------------------
# T-RUL-0008 — Decimal arithmetic (add, sub, mul, div) parse
# ---------------------------------------------------------------------------
# id: T-RUL-0008
# title: Decimal arithmetic operators parse
# purpose: Verify that add, sub, mul, div parse correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: dicts with each arithmetic type
# expected: parse_expr returns the corresponding typed expression
# risk: arithmetic logic misconstructed
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0008_arithmetic_parse() -> None:
    """Decimal arithmetic operators parse correctly."""
    from kernel.rules.dsl.types import Add, Div, Mul, Sub

    for type_name, cls in [
        ("add", Add),
        ("sub", Sub),
        ("mul", Mul),
        ("div", Div),
    ]:
        result = parse_expr(
            {
                "type": type_name,
                "left": {"type": "decimal", "value": "10.0"},
                "right": {"type": "decimal", "value": "2.0"},
            }
        )
        assert isinstance(result, cls), f"{type_name} did not parse to {cls.__name__}"


# ---------------------------------------------------------------------------
# T-RUL-0009 — Set membership (in) parses
# ---------------------------------------------------------------------------
# id: T-RUL-0009
# title: Set membership parses
# purpose: Verify that the in operator (set membership) parses correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "in", item, and collection
# expected: parse_expr returns an In expression
# risk: membership checks misconstructed
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0009_in_parses() -> None:
    """Set membership (in) parses correctly."""
    from kernel.rules.dsl.types import In

    result = parse_expr(
        {
            "type": "in",
            "item": {"type": "field", "name": "hs_code"},
            "collection": {"type": "string", "value": "0101.21"},
        }
    )
    assert isinstance(result, In)


# ---------------------------------------------------------------------------
# T-RUL-0010 — Normalized string equality (string_eq) parses
# ---------------------------------------------------------------------------
# id: T-RUL-0010
# title: Normalized string equality parses
# purpose: Verify that string_eq (normalized string equality) parses.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a dict with type "string_eq", left, and right
# expected: parse_expr returns a StringEq expression
# risk: string normalization misapplied
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0010_string_eq_parses() -> None:
    """Normalized string equality (string_eq) parses correctly."""
    from kernel.rules.dsl.types import StringEq

    result = parse_expr(
        {
            "type": "string_eq",
            "left": {"type": "field", "name": "description"},
            "right": {"type": "string", "value": "FREE TRADE ZONE"},
        }
    )
    assert isinstance(result, StringEq)


# ---------------------------------------------------------------------------
# T-RUL-0011 — Date arithmetic (date_add, date_diff) parses
# ---------------------------------------------------------------------------
# id: T-RUL-0011
# title: Date arithmetic parses
# purpose: Verify that date_add and date_diff parse correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: dicts with type "date_add" and "date_diff"
# expected: parse_expr returns DateAdd and DateDiff respectively
# risk: date arithmetic misconstructed
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0011_date_arithmetic_parses() -> None:
    """Date arithmetic (date_add, date_diff) parses correctly."""
    from kernel.rules.dsl.types import DateAdd, DateDiff

    result_add = parse_expr(
        {
            "type": "date_add",
            "date": {"type": "date", "year": 2026, "month": 1, "day": 15},
            "days": {"type": "int", "value": 30},
        }
    )
    assert isinstance(result_add, DateAdd)

    result_diff = parse_expr(
        {
            "type": "date_diff",
            "start": {"type": "date", "year": 2026, "month": 1, "day": 1},
            "end": {"type": "date", "year": 2026, "month": 2, "day": 1},
        }
    )
    assert isinstance(result_diff, DateDiff)


# ---------------------------------------------------------------------------
# T-RUL-0012 — Quantifiers (all, any, count) parse
# ---------------------------------------------------------------------------
# id: T-RUL-0012
# title: Quantifiers parse
# purpose: Verify that all, any, and count parse correctly.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: dicts with type "all", "any", and "count"
# expected: parse_expr returns All, AnyExpr, and CountExpr respectively
# risk: quantifier logic misconstructed
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0012_quantifiers_parse() -> None:
    """Quantifiers (all, any, count) parse correctly."""
    from kernel.rules.dsl.types import All, AnyExpr, CountExpr

    result_all = parse_expr(
        {
            "type": "all",
            "collection": {"type": "field", "name": "items"},
            "predicate": {"type": "bool", "value": True},
        }
    )
    assert isinstance(result_all, All)

    result_any = parse_expr(
        {
            "type": "any",
            "collection": {"type": "field", "name": "items"},
            "predicate": {"type": "bool", "value": True},
        }
    )
    assert isinstance(result_any, AnyExpr)

    result_count = parse_expr(
        {
            "type": "count",
            "collection": {"type": "field", "name": "items"},
        }
    )
    assert isinstance(result_count, CountExpr)


# ---------------------------------------------------------------------------
# T-RUL-0013 — Forbidden constructs rejected with stable error codes
# ---------------------------------------------------------------------------
# id: T-RUL-0013
# title: Forbidden constructs rejected with stable error codes
# purpose: Verify that loops, recursion, I/O, randomness, clock, and
#          user-defined functions are rejected with stable error codes.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: dicts with forbidden construct types
# expected: parse_expr raises ParseError with a stable error code for each
# risk: non-determinism or side effects in rule evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0013_forbidden_constructs_rejected() -> None:
    """Forbidden constructs are rejected with stable error codes."""
    forbidden_cases: list[tuple[dict[str, object], str]] = [
        ({"type": "while"}, "DSL_FORBIDDEN_LOOP"),
        ({"type": "for"}, "DSL_FORBIDDEN_LOOP"),
        ({"type": "loop"}, "DSL_FORBIDDEN_LOOP"),
        ({"type": "call", "name": "my_func"}, "DSL_FORBIDDEN_USER_FUNCTION"),
        ({"type": "lambda"}, "DSL_FORBIDDEN_USER_FUNCTION"),
        ({"type": "random"}, "DSL_FORBIDDEN_RANDOM"),
        ({"type": "now"}, "DSL_FORBIDDEN_CLOCK"),
        ({"type": "time"}, "DSL_FORBIDDEN_CLOCK"),
        ({"type": "exec", "code": "print(1)"}, "DSL_FORBIDDEN_IO"),
        ({"type": "eval", "expr": "1+1"}, "DSL_FORBIDDEN_IO"),
    ]
    for data, expected_code in forbidden_cases:
        with pytest.raises(ParseError) as exc_info:
            parse_expr(data)
        assert exc_info.value.code == expected_code, (
            f"forbidden construct {data['type']!r} got code "
            f"{exc_info.value.code!r}, expected {expected_code!r}"
        )

    # Unknown type also rejected
    with pytest.raises(ParseError) as exc_info:
        parse_expr({"type": "nonexistent_type", "value": 1})
    assert exc_info.value.code == "DSL_UNKNOWN_TYPE"


# ---------------------------------------------------------------------------
# T-RUL-0014 — Structural depth bound enforced
# ---------------------------------------------------------------------------
# id: T-RUL-0014
# title: Structural depth bound enforced
# purpose: Verify that expressions exceeding the maximum depth are rejected.
# level: fast
# requirement: P06-T01, Part 3 §3.6
# input: a deeply nested expression exceeding MAX_DEPTH
# expected: parse_expr raises ParseError with code DSL_DEPTH_EXCEEDED
# risk: non-terminating expression evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0014_depth_bound_enforced() -> None:
    """An expression exceeding the structural depth bound is rejected."""
    # Build a chain of Not(Not(Not(...))) deeper than MAX_DEPTH
    nested: dict[str, object] = {"type": "bool", "value": True}
    for _ in range(MAX_DEPTH + 5):
        nested = {"type": "not", "operand": nested}
    with pytest.raises(ParseError) as exc_info:
        parse_expr(nested)
    assert exc_info.value.code == "DSL_DEPTH_EXCEEDED"

    # An expression within bounds should parse fine
    shallow = {"type": "not", "operand": {"type": "bool", "value": True}}
    result = parse_expr(shallow)
    assert isinstance(result, type(parse_expr(shallow)))

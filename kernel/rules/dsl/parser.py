"""Parser for the Pack DSL expression language (Part 3 §3.6, P06-T01).

Parses JSON dictionaries into typed :mod:`kernel.rules.dsl.types` expression
objects.  Every allowed construct parses; every forbidden construct is
rejected with a stable error code; every expression terminates (checked by
structural bound).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import NoReturn

from kernel.rules.dsl.types import (
    MAX_DEPTH,
    MAX_OPERANDS,
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


class ParseError(Exception):
    """A DSL parse error with a stable error code.

    Attributes:
        code: Stable error code (e.g. ``DSL_UNKNOWN_TYPE``).
        message: Human-readable description.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


#: Expression types that take a left/right pair.
_PAIR_TYPES: frozenset[str] = frozenset(
    {
        "eq",
        "ne",
        "lt",
        "le",
        "gt",
        "ge",
        "add",
        "sub",
        "mul",
        "div",
        "string_eq",
    }
)

#: Forbidden expression types (loops, recursion, I/O, randomness, clock,
#: user-defined functions).  Each maps to a stable error code.
_FORBIDDEN_TYPES: dict[str, str] = {
    "while": "DSL_FORBIDDEN_LOOP",
    "for": "DSL_FORBIDDEN_LOOP",
    "loop": "DSL_FORBIDDEN_LOOP",
    "recurse": "DSL_FORBIDDEN_RECURSION",
    "call": "DSL_FORBIDDEN_USER_FUNCTION",
    "lambda": "DSL_FORBIDDEN_USER_FUNCTION",
    "function": "DSL_FORBIDDEN_USER_FUNCTION",
    "def": "DSL_FORBIDDEN_USER_FUNCTION",
    "eval": "DSL_FORBIDDEN_IO",
    "exec": "DSL_FORBIDDEN_IO",
    "read": "DSL_FORBIDDEN_IO",
    "write": "DSL_FORBIDDEN_IO",
    "print": "DSL_FORBIDDEN_IO",
    "input": "DSL_FORBIDDEN_IO",
    "random": "DSL_FORBIDDEN_RANDOM",
    "rand": "DSL_FORBIDDEN_RANDOM",
    "choice": "DSL_FORBIDDEN_RANDOM",
    "now": "DSL_FORBIDDEN_CLOCK",
    "today": "DSL_FORBIDDEN_CLOCK",
    "time": "DSL_FORBIDDEN_CLOCK",
    "clock": "DSL_FORBIDDEN_CLOCK",
    "date_func": "DSL_FORBIDDEN_CLOCK",
    "uuid": "DSL_FORBIDDEN_RANDOM",
}


def _fail(code: str, message: str) -> NoReturn:
    """Raise a :class:`ParseError` with the given code and message."""
    raise ParseError(code, message)


def _get_type(data: dict[str, object]) -> str:
    """Extract and validate the ``type`` field from a JSON dict."""
    if "type" not in data:
        _fail("DSL_MISSING_TYPE", "expression dict missing 'type' field")
    raw = data["type"]
    if not isinstance(raw, str):
        _fail("DSL_INVALID_TYPE", "'type' must be a string")
    return raw


def _get_required(data: dict[str, object], key: str) -> object:
    """Get a required field from the dict or fail."""
    if key not in data:
        _fail("DSL_MISSING_FIELD", f"missing required field: {key!r}")
    return data[key]


def parse_expr(data: object, depth: int = 0) -> Expr:
    """Parse a JSON dict into a typed expression.

    Args:
        data: The JSON dict (or scalar) to parse.
        depth: Current recursion depth (for structural bound).

    Returns:
        A typed :data:`Expr` expression.

    Raises:
        ParseError: If the expression is malformed, uses a forbidden
            construct, or exceeds the structural depth bound.
    """
    if depth > MAX_DEPTH:
        _fail("DSL_DEPTH_EXCEEDED", f"expression depth exceeds maximum of {MAX_DEPTH}")

    if isinstance(data, bool):
        return BoolLit(value=data)
    if isinstance(data, int) and not isinstance(data, bool):
        return IntLit(value=data)
    if isinstance(data, str):
        return StringLit(value=data)
    if not isinstance(data, dict):
        _fail("DSL_INVALID_EXPR", f"expected dict or scalar, got {type(data).__name__}")

    type_name = _get_type(data)

    if type_name in _FORBIDDEN_TYPES:
        _fail(_FORBIDDEN_TYPES[type_name], f"forbidden construct: {type_name!r}")

    if type_name == "bool":
        val = _get_required(data, "value")
        if not isinstance(val, bool):
            _fail("DSL_INVALID_VALUE", "bool value must be a boolean")
        return BoolLit(value=val)

    if type_name == "int":
        val = _get_required(data, "value")
        if isinstance(val, bool) or not isinstance(val, int):
            _fail("DSL_INVALID_VALUE", "int value must be an integer")
        return IntLit(value=val)

    if type_name == "decimal":
        val = _get_required(data, "value")
        if isinstance(val, (int, float, str)) and not isinstance(val, bool):
            try:
                return DecimalLit(value=Decimal(str(val)))
            except InvalidOperation, ValueError:
                _fail("DSL_INVALID_VALUE", f"invalid decimal: {val!r}")
        _fail("DSL_INVALID_VALUE", "decimal value must be a number or string")

    if type_name == "string":
        val = _get_required(data, "value")
        if not isinstance(val, str):
            _fail("DSL_INVALID_VALUE", "string value must be a string")
        return StringLit(value=val)

    if type_name == "date":
        year = _get_required(data, "year")
        month = _get_required(data, "month")
        day = _get_required(data, "day")
        if not isinstance(year, int) or not isinstance(month, int) or not isinstance(day, int):
            _fail("DSL_INVALID_VALUE", "date fields must be integers")
        return DateLit(year=year, month=month, day=day)

    if type_name == "field":
        name = _get_required(data, "name")
        if not isinstance(name, str):
            _fail("DSL_INVALID_VALUE", "field name must be a string")
        return FieldRef(name=name)

    if type_name == "and":
        operands = _parse_operands(data, depth)
        return And(operands=operands)

    if type_name == "or":
        operands = _parse_operands(data, depth)
        return Or(operands=operands)

    if type_name == "not":
        operand = _get_required(data, "operand")
        return Not(operand=parse_expr(operand, depth + 1))

    if type_name in _PAIR_TYPES:
        left = _get_required(data, "left")
        right = _get_required(data, "right")
        left_expr = parse_expr(left, depth + 1)
        right_expr = parse_expr(right, depth + 1)
        if type_name == "eq":
            return Eq(left=left_expr, right=right_expr)
        if type_name == "ne":
            return Ne(left=left_expr, right=right_expr)
        if type_name == "lt":
            return Lt(left=left_expr, right=right_expr)
        if type_name == "le":
            return Le(left=left_expr, right=right_expr)
        if type_name == "gt":
            return Gt(left=left_expr, right=right_expr)
        if type_name == "ge":
            return Ge(left=left_expr, right=right_expr)
        if type_name == "add":
            return Add(left=left_expr, right=right_expr)
        if type_name == "sub":
            return Sub(left=left_expr, right=right_expr)
        if type_name == "mul":
            return Mul(left=left_expr, right=right_expr)
        if type_name == "div":
            return Div(left=left_expr, right=right_expr)
        return StringEq(left=left_expr, right=right_expr)

    if type_name == "in":
        item = _get_required(data, "item")
        collection = _get_required(data, "collection")
        return In(
            item=parse_expr(item, depth + 1),
            collection=parse_expr(collection, depth + 1),
        )

    if type_name == "date_add":
        date = _get_required(data, "date")
        days = _get_required(data, "days")
        return DateAdd(
            date=parse_expr(date, depth + 1),
            days=parse_expr(days, depth + 1),
        )

    if type_name == "date_diff":
        start = _get_required(data, "start")
        end = _get_required(data, "end")
        return DateDiff(
            start=parse_expr(start, depth + 1),
            end=parse_expr(end, depth + 1),
        )

    if type_name == "all":
        collection = _get_required(data, "collection")
        predicate = _get_required(data, "predicate")
        return All(
            collection=parse_expr(collection, depth + 1),
            predicate=parse_expr(predicate, depth + 1),
        )

    if type_name == "any":
        collection = _get_required(data, "collection")
        predicate = _get_required(data, "predicate")
        return AnyExpr(
            collection=parse_expr(collection, depth + 1),
            predicate=parse_expr(predicate, depth + 1),
        )

    if type_name == "count":
        collection = _get_required(data, "collection")
        return CountExpr(collection=parse_expr(collection, depth + 1))

    _fail("DSL_UNKNOWN_TYPE", f"unknown expression type: {type_name!r}")


def _parse_operands(data: dict[str, object], depth: int) -> tuple[Expr, ...]:
    """Parse the ``operands`` list for variadic expressions."""
    raw = _get_required(data, "operands")
    if not isinstance(raw, list):
        _fail("DSL_INVALID_VALUE", "operands must be a list")
    if len(raw) > MAX_OPERANDS:
        _fail(
            "DSL_TOO_MANY_OPERANDS",
            f"at most {MAX_OPERANDS} operands, got {len(raw)}",
        )
    if len(raw) == 0:
        _fail("DSL_EMPTY_OPERANDS", "operands must not be empty")
    return tuple(parse_expr(o, depth + 1) for o in raw)

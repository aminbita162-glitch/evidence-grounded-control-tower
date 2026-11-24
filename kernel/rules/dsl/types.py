"""Expression language types for the Pack DSL (Part 3 §3.6, P06-T01).

A restricted, typed expression language for rule conditions:
- Boolean operators: and, or, not
- Comparisons: eq, ne, lt, le, gt, ge
- Decimal arithmetic: add, sub, mul, div
- Set membership: in
- Normalized string equality: string_eq
- Calendar-pack date arithmetic: date_add, date_diff
- Field access: field
- Quantifiers: all, any, count over finite collections
- Literals: bool, int, decimal, string, date

No loops, recursion, I/O, randomness, clock access, or user-defined
functions.  Every expression terminates (checked by structural bound).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

#: Maximum nesting depth for any expression tree.  This structural bound
#: guarantees termination: the parser rejects any expression whose depth
#: exceeds this value.
MAX_DEPTH: int = 50

#: Maximum number of operands in a variadic expression (and, or).
MAX_OPERANDS: int = 32


@dataclass(frozen=True)
class BoolLit:
    """A boolean literal."""

    value: bool


@dataclass(frozen=True)
class IntLit:
    """An integer literal."""

    value: int


@dataclass(frozen=True)
class DecimalLit:
    """A fixed-point decimal literal."""

    value: Decimal


@dataclass(frozen=True)
class StringLit:
    """A string literal."""

    value: str


@dataclass(frozen=True)
class DateLit:
    """A calendar date literal (year, month, day)."""

    year: int
    month: int
    day: int


@dataclass(frozen=True)
class FieldRef:
    """A reference to a fact field by name."""

    name: str


@dataclass(frozen=True)
class And:
    """Logical conjunction of one or more operands."""

    operands: tuple[Expr, ...]


@dataclass(frozen=True)
class Or:
    """Logical disjunction of one or more operands."""

    operands: tuple[Expr, ...]


@dataclass(frozen=True)
class Not:
    """Logical negation."""

    operand: Expr


@dataclass(frozen=True)
class Eq:
    """Equality comparison."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Ne:
    """Inequality comparison."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Lt:
    """Less-than comparison."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Le:
    """Less-than-or-equal comparison."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Gt:
    """Greater-than comparison."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Ge:
    """Greater-than-or-equal comparison."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Add:
    """Decimal addition."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Sub:
    """Decimal subtraction."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Mul:
    """Decimal multiplication."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class Div:
    """Decimal division."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class In:
    """Set membership: ``item`` is in ``collection``."""

    item: Expr
    collection: Expr


@dataclass(frozen=True)
class StringEq:
    """Normalized string equality (after NFC and whitespace collapse)."""

    left: Expr
    right: Expr


@dataclass(frozen=True)
class DateAdd:
    """Add a number of days to a date using the calendar pack."""

    date: Expr
    days: Expr


@dataclass(frozen=True)
class DateDiff:
    """Difference in days between two dates using the calendar pack."""

    start: Expr
    end: Expr


@dataclass(frozen=True)
class All:
    """Universal quantifier: every element of ``collection`` satisfies
    ``predicate``.  ``predicate`` is an expression evaluated with the
    element bound to the field ``_item_``."""

    collection: Expr
    predicate: Expr


@dataclass(frozen=True)
class AnyExpr:
    """Existential quantifier: at least one element of ``collection``
    satisfies ``predicate``."""

    collection: Expr
    predicate: Expr


@dataclass(frozen=True)
class CountExpr:
    """Count of elements in ``collection`` (returns an integer)."""

    collection: Expr


#: The union of all expression types.
type Expr = (
    BoolLit
    | IntLit
    | DecimalLit
    | StringLit
    | DateLit
    | FieldRef
    | And
    | Or
    | Not
    | Eq
    | Ne
    | Lt
    | Le
    | Gt
    | Ge
    | Add
    | Sub
    | Mul
    | Div
    | In
    | StringEq
    | DateAdd
    | DateDiff
    | All
    | AnyExpr
    | CountExpr
)


def _depth_pair(a: Expr, b: Expr) -> int:
    """Depth of a two-sub-expression node."""
    return 1 + max(expr_depth(a), expr_depth(b))


def expr_depth(expr: Expr) -> int:
    """Compute the maximum nesting depth of an expression tree.

    A literal or field reference has depth 1; a compound expression has
    depth equal to one plus the maximum depth of its sub-expressions.
    """
    if isinstance(expr, BoolLit | IntLit | DecimalLit | StringLit | DateLit | FieldRef):
        return 1
    if isinstance(expr, And | Or):
        return 1 + max((expr_depth(o) for o in expr.operands), default=0)
    if isinstance(expr, Not):
        return 1 + expr_depth(expr.operand)
    if isinstance(expr, Eq | Ne | Lt | Le | Gt | Ge | Add | Sub | Mul | Div | StringEq):
        return _depth_pair(expr.left, expr.right)
    if isinstance(expr, In):
        return _depth_pair(expr.item, expr.collection)
    if isinstance(expr, DateAdd):
        return _depth_pair(expr.date, expr.days)
    if isinstance(expr, DateDiff):
        return _depth_pair(expr.start, expr.end)
    if isinstance(expr, All | AnyExpr):
        return _depth_pair(expr.collection, expr.predicate)
    if isinstance(expr, CountExpr):
        return 1 + expr_depth(expr.collection)
    return 1

"""Replayable calculation trees with canonical hashes and labelled inputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Context, Decimal, Inexact
from enum import StrEnum

from kernel.contracts._generated.decision import Decision
from kernel.hashing import ALGORITHM, domain_hash
from kernel.types.label import Label, label_rank, weakest_of

__all__ = [
    "Calculation",
    "DecimalSettings",
    "Formula",
    "Operand",
    "Operation",
    "calculate",
    "with_calculations",
]


class Operation(StrEnum):
    """Supported version-one decimal formulas."""

    ADD = "ADD"
    SUBTRACT = "SUBTRACT"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    QUANTIZE = "QUANTIZE"


@dataclass(frozen=True, slots=True)
class DecimalSettings:
    """Serializable decimal context for deterministic replay."""

    precision: int
    rounding: str
    minimum_exponent: int = -999999
    maximum_exponent: int = 999999

    def context(self, *, exact: bool) -> Context:
        """Build a fresh context without using process defaults."""
        ctx = Context(
            prec=self.precision,
            rounding=self.rounding,
            Emin=self.minimum_exponent,
            Emax=self.maximum_exponent,
            clamp=0,
        )
        ctx.clear_traps()
        if exact:
            ctx.traps[Inexact] = True
        return ctx


@dataclass(frozen=True, slots=True)
class Formula:
    """Versioned formula and exact rule or source that selected it."""

    identifier: str
    version: int
    operation: Operation
    rule_or_source: str

    def __post_init__(self) -> None:
        """Require a recorded version and rule reference."""
        if not self.identifier or self.version != 1 or not self.rule_or_source:
            raise ValueError("formula requires an identifier, version one and a recorded rule")


@dataclass(frozen=True, slots=True)
class Operand:
    """A decimal input with its fact or pack-line reference."""

    reference: str
    value: Decimal
    unit: str
    label: Label

    def __post_init__(self) -> None:
        """Reject unrecorded, nonfinite or unlabelled inputs."""
        if not self.reference or not self.unit:
            raise ValueError("operand reference and unit are required")
        if not isinstance(self.value, Decimal) or not self.value.is_finite():
            raise ValueError("operand must be a finite Decimal")
        label_rank(self.label)

    def payload(self) -> dict[str, object]:
        """Return the exact serialized operand."""
        return {
            "reference": self.reference,
            "decimal": format(self.value, "f"),
            "unit": self.unit,
            "label": self.label,
        }


@dataclass(frozen=True, slots=True)
class Calculation:
    """A computed decimal quantity or amount with all inputs needed for replay."""

    formula: Formula
    settings: DecimalSettings
    operands: tuple[Operand | Calculation, Operand | Calculation]
    result: Operand

    def payload(self) -> dict[str, object]:
        """Serialize the typed tree as a record payload."""
        return {
            "type": "CALCULATION_TRACE",
            "formula": {
                "id": self.formula.identifier,
                "version": self.formula.version,
                "operation": self.formula.operation,
                "rule_or_source": self.formula.rule_or_source,
            },
            "context": {
                "precision": self.settings.precision,
                "rounding": self.settings.rounding,
                "minimum_exponent": self.settings.minimum_exponent,
                "maximum_exponent": self.settings.maximum_exponent,
            },
            "operands": [_operand_payload(operand) for operand in self.operands],
            "result": self.result.payload(),
        }

    def digest(self) -> str:
        """Hash the canonical trace in the registered record-payload domain."""
        return domain_hash("ctc/payload/v1", self.payload())

    def replay(self) -> Operand:
        """Recalculate the whole tree, checking each recorded result."""
        left, right = self.operands
        rebuilt = _evaluate(
            self.formula,
            self.settings,
            left.replay() if isinstance(left, Calculation) else left,
            right.replay() if isinstance(right, Calculation) else right,
            self.result.unit,
        )
        if rebuilt.payload() != self.result.payload():
            raise ValueError("calculation trace does not reproduce its recorded result")
        return rebuilt


def _operand_payload(operand: Operand | Calculation) -> dict[str, object]:
    payload = operand.payload()
    if isinstance(operand, Calculation):
        return {"trace_hash": domain_hash("ctc/payload/v1", payload), "trace": payload}
    return payload


def _evaluate(
    formula: Formula,
    settings: DecimalSettings,
    left: Operand,
    right: Operand,
    unit: str,
) -> Operand:
    if formula.operation in {Operation.ADD, Operation.SUBTRACT, Operation.QUANTIZE} and (
        left.unit != right.unit or unit != left.unit
    ):
        raise ValueError("formula requires matching units")
    ctx = settings.context(exact=formula.operation != Operation.QUANTIZE)
    operations = {
        Operation.ADD: ctx.add,
        Operation.SUBTRACT: ctx.subtract,
        Operation.MULTIPLY: ctx.multiply,
        Operation.DIVIDE: ctx.divide,
        Operation.QUANTIZE: ctx.quantize,
    }
    result = operations[formula.operation](left.value, right.value)
    return Operand(formula.identifier, result, unit, weakest_of(left.label, right.label))


def calculate(
    formula: Formula,
    settings: DecimalSettings,
    left: Operand | Calculation,
    right: Operand | Calculation,
    *,
    unit: str,
) -> Calculation:
    """Calculate a result and retain the ordered input tree."""
    result = _evaluate(
        formula,
        settings,
        left.replay() if isinstance(left, Calculation) else left,
        right.replay() if isinstance(right, Calculation) else right,
        unit,
    )
    return Calculation(formula, settings, (left, right), result)


def with_calculations(decision: Decision, *calculations: Calculation) -> Decision:
    """Add stable, deduplicated trace references to a Decision."""
    existing = decision.calculation_trace_hashes or []
    if any(re.fullmatch(r"[0-9a-f]{64}", value) is None for value in existing):
        raise ValueError(f"expected {ALGORITHM} calculation trace references")
    for calculation in calculations:
        calculation.replay()
    references = sorted(set(existing).union(trace.digest() for trace in calculations))
    return decision.model_copy(update={"calculation_trace_hashes": references})

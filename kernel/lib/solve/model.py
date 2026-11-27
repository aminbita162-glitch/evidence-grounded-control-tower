"""Immutable solver-neutral integer constraints and assignments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from kernel.hashing import domain_hash


@dataclass(frozen=True, slots=True)
class Variable:
    """One integer variable with a closed domain."""

    name: str
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        """Require an explicit integral domain."""
        if (
            not self.name
            or type(self.minimum) is not int
            or type(self.maximum) is not int
            or self.minimum > self.maximum
        ):
            raise ValueError("invalid integer variable")


@dataclass(frozen=True, slots=True)
class Term:
    """A coefficient and a variable reference."""

    variable: str
    weight: int

    def __post_init__(self) -> None:
        """Require an integer coefficient."""
        if not self.variable or type(self.weight) is not int:
            raise ValueError("invalid linear term")


@dataclass(frozen=True, slots=True)
class Constraint:
    """A named linear expression with one or two inclusive bounds."""

    reference: str
    terms: tuple[Term, ...]
    lower: int | None = None
    upper: int | None = None

    def __post_init__(self) -> None:
        """Validate the bounds without solving the model."""
        if not self.reference or self.lower is None and self.upper is None:
            raise ValueError("linear constraint requires a name and bound")
        if any(bound is not None and type(bound) is not int for bound in (self.lower, self.upper)):
            raise ValueError("constraint bounds must be integers")
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError("constraint lower bound exceeds upper bound")


@dataclass(frozen=True, slots=True)
class IntegerModel:
    """Encoding shared by solver adapters and the plain assignment checker."""

    variables: tuple[Variable, ...]
    constraints: tuple[Constraint, ...]
    minimize: tuple[Term, ...] = ()

    def __post_init__(self) -> None:
        """Check symbol and constraint references before any solver call."""
        names = {variable.name for variable in self.variables}
        references = {constraint.reference for constraint in self.constraints}
        if (
            not names
            or len(names) != len(self.variables)
            or len(references) != len(self.constraints)
        ):
            raise ValueError("variable and constraint identifiers must be unique")
        groups = (*[constraint.terms for constraint in self.constraints], self.minimize)
        if any(term.variable not in names for terms in groups for term in terms):
            raise ValueError("linear term references an unknown variable")

    def digest(self) -> str:
        """Hash the exact ordered encoding, retaining full precision for integers."""

        def terms(values: tuple[Term, ...]) -> list[tuple[str, str]]:
            return [(term.variable, str(term.weight)) for term in values]

        return domain_hash(
            "ctc/payload/v1",
            {
                "type": "ENCODED_INTEGER_MODEL",
                "variables": [
                    [variable.name, str(variable.minimum), str(variable.maximum)]
                    for variable in self.variables
                ],
                "constraints": [
                    [
                        constraint.reference,
                        terms(constraint.terms),
                        str(constraint.lower) if constraint.lower is not None else None,
                        str(constraint.upper) if constraint.upper is not None else None,
                    ]
                    for constraint in self.constraints
                ],
                "minimize": terms(self.minimize),
            },
        )


type Assignment = tuple[tuple[str, int], ...]
type Status = Literal["SOLVED", "INFEASIBLE", "ABSTAIN"]

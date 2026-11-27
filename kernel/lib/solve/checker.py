"""Independently check a candidate assignment using ordinary integer arithmetic."""

from collections.abc import Mapping

from kernel.lib.solve.model import IntegerModel, Term


def evaluate(terms: tuple[Term, ...], values: Mapping[str, int]) -> int:
    """Evaluate a linear expression without a solver."""
    return sum(term.weight * values[term.variable] for term in terms)


def violations(model: IntegerModel, values: Mapping[str, int]) -> tuple[str, ...]:
    """Return violations of symbol, domain and constraint requirements."""
    if set(values) != {variable.name for variable in model.variables}:
        return ("ASSIGNMENT_VARIABLES",)
    invalid = [
        f"domain:{variable.name}"
        for variable in model.variables
        if type(values[variable.name]) is not int
        or not variable.minimum <= values[variable.name] <= variable.maximum
    ]
    if invalid:
        return tuple(invalid)
    for constraint in model.constraints:
        actual = evaluate(constraint.terms, values)
        if (constraint.lower is not None and actual < constraint.lower) or (
            constraint.upper is not None and actual > constraint.upper
        ):
            invalid.append(constraint.reference)
    return tuple(invalid)

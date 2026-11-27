"""Reproducible solver calls with independently checked assignments."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from importlib import import_module
from typing import Literal

from kernel.lib.solve.checker import evaluate, violations
from kernel.lib.solve.model import Assignment, Constraint, IntegerModel, Status, Term, Variable

__all__ = [
    "Constraint",
    "IntegerModel",
    "Result",
    "Settings",
    "Term",
    "Variable",
    "check_candidate",
    "solve_consistent",
    "solve_cp_sat",
    "solve_z3",
]


@dataclass(frozen=True, slots=True)
class Settings:
    """Fixed controls applied to every call in a solver run."""

    seed: int
    workers: int
    seconds: float

    def __post_init__(self) -> None:
        """Reject controls that would leave the worker count or time unbounded."""
        if (
            type(self.seed) is not int
            or not 0 <= self.seed <= 2**31 - 1
            or type(self.workers) is not int
            or self.workers < 1
            or not math.isfinite(self.seconds)
            or self.seconds < 0
        ):
            raise ValueError("invalid solver settings")


@dataclass(frozen=True, slots=True)
class Result:
    """Status qualified by the exact encoded model and run settings."""

    status: Status
    model_hash: str
    backend: str
    settings: Settings
    reason: str
    assignment: Assignment = ()
    objective: int | None = None
    evidence: tuple[str, ...] = ()
    scope: Literal["ENCODED_MODEL_ONLY"] = "ENCODED_MODEL_ONLY"


def check_candidate(
    model: IntegerModel, candidate: Mapping[str, int], *, backend: str, settings: Settings
) -> Result:
    """Reject any assignment that does not satisfy the original constraints."""
    violations_found = violations(model, candidate)
    if violations_found:
        return Result(
            "ABSTAIN",
            model.digest(),
            backend,
            settings,
            "INVALID_ASSIGNMENT",
            evidence=violations_found,
        )
    return Result(
        "SOLVED",
        model.digest(),
        backend,
        settings,
        "VERIFIED_ASSIGNMENT",
        tuple(sorted(candidate.items())),
        evaluate(model.minimize, candidate),
    )


def solve_z3(model: IntegerModel, settings: Settings) -> Result:
    """Check satisfiability with Z3 and report the recorded unsatisfiable core."""
    backend = "Z3"
    model_hash = model.digest()
    if settings.seconds < 0.001:
        return Result("ABSTAIN", model_hash, backend, settings, "TIME_LIMIT")
    z3 = import_module("z3")
    context = z3.Context()
    solver = z3.Solver(ctx=context)
    solver.set(
        timeout=int(min(settings.seconds, (2**32 - 1) / 1000) * 1000),
        random_seed=settings.seed,
        threads=settings.workers,
    )
    variables = {
        variable.name: z3.Int(f"v{index}", ctx=context)
        for index, variable in enumerate(model.variables)
    }
    references: dict[str, str] = {}
    for index, variable in enumerate(model.variables):
        symbol = variables[variable.name]
        key = f"domain{index}"
        references[key] = f"domain:{variable.name}"
        solver.assert_and_track(z3.And(symbol >= variable.minimum, symbol <= variable.maximum), key)
    for index, constraint in enumerate(model.constraints):
        expr = sum(
            (variables[term.variable] * term.weight for term in constraint.terms),
            z3.IntVal(0, ctx=context),
        )
        bounds = []
        if constraint.lower is not None:
            bounds.append(expr >= constraint.lower)
        if constraint.upper is not None:
            bounds.append(expr <= constraint.upper)
        key = f"rule{index}"
        references[key] = constraint.reference
        solver.assert_and_track(z3.And(*bounds), key)
    status = solver.check()
    if status == z3.sat:
        answer = solver.model()
        candidate = {name: int(answer.eval(symbol).as_long()) for name, symbol in variables.items()}
        return check_candidate(model, candidate, backend=backend, settings=settings)
    if status == z3.unsat:
        core = tuple(sorted(references[str(item)] for item in solver.unsat_core()))
        return Result(
            "INFEASIBLE",
            model_hash,
            backend,
            settings,
            "Z3_UNSAT",
            evidence=core or ("Z3 returned unsat for the encoded constraints",),
        )
    detail = str(solver.reason_unknown())
    reason = "TIME_LIMIT" if "timeout" in detail or "canceled" in detail else "SOLVER_UNKNOWN"
    return Result("ABSTAIN", model_hash, backend, settings, reason, evidence=(detail,))


def solve_cp_sat(model: IntegerModel, settings: Settings) -> Result:
    """Solve and verify an optimum or justify infeasibility with Z3."""
    backend = "CP-SAT"
    module = import_module("ortools.sat.python.cp_model")
    encoded = module.CpModel()
    variables = {
        variable.name: encoded.new_int_var(variable.minimum, variable.maximum, variable.name)
        for variable in model.variables
    }
    for constraint in model.constraints:
        expression = module.LinearExpr.weighted_sum(
            [variables[term.variable] for term in constraint.terms],
            [term.weight for term in constraint.terms],
        )
        if constraint.lower is not None:
            encoded.add(expression >= constraint.lower)
        if constraint.upper is not None:
            encoded.add(expression <= constraint.upper)
    if model.minimize:
        encoded.minimize(
            module.LinearExpr.weighted_sum(
                [variables[term.variable] for term in model.minimize],
                [term.weight for term in model.minimize],
            )
        )
    solver = module.CpSolver()
    solver.parameters.num_search_workers = settings.workers
    solver.parameters.random_seed = settings.seed
    solver.parameters.max_time_in_seconds = settings.seconds / 2
    status = solver.solve(encoded)
    model_hash = model.digest()
    if status == module.OPTIMAL:
        values = {name: int(solver.value(symbol)) for name, symbol in variables.items()}
        return check_candidate(model, values, backend=backend, settings=settings)
    if status == module.INFEASIBLE:
        proof = solve_z3(model, replace(settings, seconds=settings.seconds / 2))
        if proof.status == "INFEASIBLE":
            return Result(
                "INFEASIBLE", model_hash, backend, settings, proof.reason, evidence=proof.evidence
            )
        return Result(
            "ABSTAIN",
            model_hash,
            backend,
            settings,
            "INFEASIBILITY_UNCONFIRMED",
            evidence=(proof.reason,),
        )
    if status in {module.UNKNOWN, module.FEASIBLE}:
        return Result("ABSTAIN", model_hash, backend, settings, "TIME_LIMIT")
    return Result(
        "ABSTAIN",
        model_hash,
        backend,
        settings,
        "INVALID_MODEL",
        evidence=(str(solver.status_name(status)),),
    )


def solve_consistent(model: IntegerModel, settings: Settings, *, other_workers: int) -> Result:
    """Accept a CP-SAT result only when an alternate fixed worker count agrees."""
    if other_workers == settings.workers:
        raise ValueError("stability check requires a different worker count")
    primary = solve_cp_sat(model, replace(settings, seconds=settings.seconds / 2))
    if primary.status == "ABSTAIN":
        return primary
    alternate = solve_cp_sat(model, replace(primary.settings, workers=other_workers))
    if alternate.status == "ABSTAIN" and alternate.reason == "TIME_LIMIT":
        return alternate
    if (primary.status, primary.assignment, primary.objective) != (
        alternate.status,
        alternate.assignment,
        alternate.objective,
    ):
        return Result(
            "ABSTAIN",
            model.digest(),
            "CP-SAT",
            settings,
            "THREAD_INSTABILITY",
            evidence=(str(settings.workers), str(other_workers)),
        )
    return replace(primary, settings=settings)

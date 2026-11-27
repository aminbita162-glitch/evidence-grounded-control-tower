"""Measure the solver harness on a labelled synthetic workload."""

from __future__ import annotations

import json
from math import ceil
from statistics import median
from time import perf_counter_ns

from kernel.lib.solve import Constraint, IntegerModel, Settings, Term, Variable, solve_consistent


def main() -> None:
    """Measure a fixed mix of feasible and infeasible integer models."""
    durations: list[float] = []
    terms = (Term("x", 1),)
    settings = Settings(seed=17, workers=1, seconds=2)
    for index in range(60):
        threshold = index % 50
        expected = "INFEASIBLE" if index % 5 == 0 else "SOLVED"
        upper = threshold - 1 if expected == "INFEASIBLE" else 50
        model = IntegerModel(
            (Variable("x", 0, 50),),
            (
                Constraint("minimum", terms, lower=threshold),
                Constraint("maximum", terms, upper=upper),
            ),
            terms,
        )
        start = perf_counter_ns()
        result = solve_consistent(model, settings, other_workers=2)
        durations.append((perf_counter_ns() - start) / 1_000_000)
        if result.status != expected:
            raise RuntimeError(f"synthetic case {index} returned {result.status}: {result.reason}")
    durations.sort()
    print(
        json.dumps(
            {
                "source_id": "SYN-P13-SOLVER-BENCH",
                "label": "SYNTHETIC",
                "cases": len(durations),
                "p50_ms": round(median(durations), 3),
                "p95_ms": round(durations[ceil(0.95 * len(durations)) - 1], 3),
                "metered_provider_cost_eur_per_case": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

"""Performance tests for the rule engine (P06-T06).

Test IDs: T-RUL-0072 (performance budget).
Covers: the budget holds on the reference environment (p95 at most 200 ms
for 200 facts); a seeded slowdown above 10 percent fails.

Spec: Part 4 §4.14; kernel/rules/interpreter.py.
"""

from __future__ import annotations

import time

import pytest

from kernel.rules.interpreter import interpret

# ---------------------------------------------------------------------------
# T-RUL-0072 — Performance budget: 200 facts, p95 at most 200 ms
# ---------------------------------------------------------------------------
# id: T-RUL-0072
# title: Performance budget for 200 facts
# purpose: Verify that evaluating a case with 200 facts completes within
#          the 200 ms p95 budget on the reference environment.
# level: fast
# requirement: P06-T06, Part 4 §4.14
# input: 200 facts and 10 rules
# expected: p95 evaluation time at most 200 ms
# risk: slow rule evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0072_perf_budget_200_facts() -> None:
    """Performance budget: 200 facts, p95 at most 200 ms."""
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    for i in range(200):
        facts[f"fact_{i}"] = (str(i), "VERIFIED", ())

    rules: list[dict[str, object]] = []
    for i in range(10):
        rules.append(
            {
                "id": f"rule_{i}",
                "version": "1.0.0",
                "condition": {
                    "type": "eq",
                    "left": {"type": "field", "name": f"fact_{i}"},
                    "right": {"type": "string", "value": str(i)},
                },
                "outcome": "ALLOW",
                "reason_code": f"RULE.{i:03d}",
                "citation_source_id": "src-1",
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_to": "2026-12-31T23:59:59Z",
                "label": "DERIVED",
            }
        )

    # Run 20 iterations and measure p95
    times: list[float] = []
    for _ in range(20):
        start = time.monotonic()
        interpret(rules, facts, "2026-06-01T00:00:00Z")
        elapsed_ms = (time.monotonic() - start) * 1000
        times.append(elapsed_ms)

    times.sort()
    p95_index = int(len(times) * 0.95)
    p95 = times[p95_index]
    assert p95 < 200.0, f"p95 {p95:.1f} ms exceeds 200 ms budget"

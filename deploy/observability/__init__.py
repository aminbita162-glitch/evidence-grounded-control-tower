"""Deploy observability — collector config and dashboards-as-code (P10-T06, T07).

Service objectives and error budgets declared as data.  The canary case
runs through the whole pipeline on demand and on a schedule.

Spec: Part 3 §3.14; P10-T06, P10-T07.
"""

from __future__ import annotations

__all__ = ["OBJECTIVES", "ERROR_BUDGETS"]

OBJECTIVES = [
    {"name": "availability", "target": 0.999, "window": "28d"},
    {"name": "latency_p99", "target": 0.5, "window": "7d", "unit": "seconds"},
    {"name": "canary_pass_rate", "target": 1.0, "window": "1h"},
]

ERROR_BUDGETS = [
    {"name": "api_errors", "budget": 0.001, "window": "28d"},
    {"name": "canary_failures", "budget": 0.0, "window": "1h"},
]

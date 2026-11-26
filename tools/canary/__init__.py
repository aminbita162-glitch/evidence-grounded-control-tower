"""Canary case — a synthetic end-to-end pipeline run (P10-T07).

A synthetic canary case runs through the whole pipeline on demand and on a
schedule setting (every 5 minutes, D-32 section 3).  Service objectives
and error budgets are declared as data.  An automatic reconciliation
compares trace records with ledger records and raises an alert on any gap.

Spec: Part 3 §3.14; P10-T07.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from kernel.skeleton import run_skeleton

__all__ = [
    "CanaryResult",
    "ReconciliationResult",
    "run_canary",
    "reconcile",
    "evaluate_objectives",
    "OBJECTIVES",
    "ERROR_BUDGETS",
    "CANARY_INTERVAL_SECONDS",
]

OBJECTIVES: list[dict[str, Any]] = [
    {"name": "availability", "target": 0.999, "window": "28d"},
    {"name": "latency_p99", "target": 0.5, "window": "7d", "unit": "seconds"},
    {"name": "canary_pass_rate", "target": 1.0, "window": "1h"},
]

ERROR_BUDGETS: list[dict[str, Any]] = [
    {"name": "api_errors", "budget": 0.001, "window": "28d"},
    {"name": "canary_failures", "budget": 0.0, "window": "1h"},
]

CANARY_INTERVAL_SECONDS = 300  # 5 minutes (D-32 section 3)


@dataclass
class CanaryResult:
    """The result of a canary run."""

    passed: bool = False
    case_id: str = ""
    decision: str = ""
    passport_hash: str = ""
    duration_seconds: float = 0.0
    label: str = "SYNTHETIC"
    error: str = ""


def run_canary(seed: int = 42) -> CanaryResult:
    """Run the canary case through the whole pipeline.

    Returns a :class:`CanaryResult` with ``passed=True`` on a healthy stack.
    """
    t0 = time.perf_counter()
    try:
        result = run_skeleton(seed)
        duration = time.perf_counter() - t0
        return CanaryResult(
            passed=result.structural_ok and result.bundle_ok,
            case_id=result.case_id,
            decision=result.decision,
            passport_hash=result.passport_hash,
            duration_seconds=duration,
            label="SYNTHETIC",
        )
    except Exception as exc:
        duration = time.perf_counter() - t0
        return CanaryResult(
            passed=False,
            duration_seconds=duration,
            label="SYNTHETIC",
            error=str(exc),
        )


@dataclass
class ReconciliationResult:
    """The result of a trace-vs-ledger reconciliation."""

    gaps: list[str] = field(default_factory=list)
    ok: bool = True


def reconcile(
    trace_records: list[dict[str, Any]],
    ledger_records: list[dict[str, Any]],
) -> ReconciliationResult:
    """Compare trace records with ledger records and report gaps.

    A gap is a trace record that has no matching ledger record by
    sequence number.  A deleted span is reported as a gap.
    """
    ledger_seqs = {r.get("seq") for r in ledger_records if "seq" in r}
    gaps: list[str] = []
    for trace in trace_records:
        seq = trace.get("seq")
        if seq is not None and seq not in ledger_seqs:
            gaps.append(f"trace record seq={seq} has no ledger record")
    return ReconciliationResult(gaps=gaps, ok=len(gaps) == 0)


def evaluate_objectives(results: list[CanaryResult]) -> dict[str, bool]:
    """Evaluate service objectives against canary results."""
    if not results:
        return {str(obj["name"]): True for obj in OBJECTIVES}
    pass_rate = sum(1 for r in results if r.passed) / len(results)
    return {
        "availability": pass_rate >= float(OBJECTIVES[0]["target"]),
        "latency_p99": all(r.duration_seconds < float(OBJECTIVES[1]["target"]) for r in results),
        "canary_pass_rate": pass_rate >= float(OBJECTIVES[2]["target"]),
    }

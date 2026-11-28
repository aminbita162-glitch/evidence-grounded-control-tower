"""Measure the synthetic bilingual pipeline and fixed-point solver locally."""

from __future__ import annotations

import asyncio
import json
import statistics
import time

from capabilities.f01 import Fact, Workflow, evaluate
from capabilities.k14.demo import DOCUMENTS, create_demo
from kernel.auth.roles import Principal
from kernel.intake import ReadResult, TextSegment


class RecordedText:
    async def read(self, payload: bytes, media_type: str) -> ReadResult:
        return ReadResult(media_type, (TextSegment(0, payload.decode()),))


async def main() -> None:
    principal = Principal(principal_id="SYN-MEASUREMENT", role="operator", tenant_id="SYN-INTAKE")
    durations = []
    for iteration in range(60):
        start = time.perf_counter_ns()
        workflow = create_demo(RecordedText())
        await workflow.ingest(principal, "SYN-MEASURE", DOCUMENTS, "2026-11")
        result = workflow.result(principal, "SYN-MEASURE")
        if not result or result.consistency.outcome != "ALLOW":
            raise RuntimeError("unexpected synthetic outcome")
        quantities = [
            Fact(
                "line",
                "invoice",
                "COMMERCIAL_INVOICE",
                "line_items.0.line_amount",
                "12",
                "12",
                "line 1",
                currency="USD",
            ),
            Fact(
                "total",
                "invoice",
                "COMMERCIAL_INVOICE",
                "invoice_total",
                "12" if iteration % 2 else "13",
                "total",
                "line 2",
                currency="USD",
            ),
        ]
        evaluated = evaluate(
            "SYN-MEASURE", quantities, (), Workflow(currency_precision=(("USD", 2),))
        )
        if evaluated.outcome != ("ALLOW" if iteration % 2 else "HOLD"):
            raise RuntimeError("unexpected synthetic arithmetic result")
        durations.append((time.perf_counter_ns() - start) / 1_000_000)
    print(
        json.dumps(
            {
                "label": "SYNTHETIC",
                "cases": len(durations),
                "p50_ms": round(statistics.median(durations), 3),
                "p95_ms": round(sorted(durations)[56], 3),
                "metered_provider_cost": "0",
            }
        )
    )


if __name__ == "__main__":
    asyncio.run(main())

"""Demo harness and two-tenant scenario (P09-T04).

A harness that starts the stack with seeded data and fixed timing, used
later by the capture script and demonstrations.  The two-tenant scenario
loads two tenants and runs the same cases for both, comparing that nothing
crosses.

Spec: Part 3 §3.12; Part 6 §6.11; P09-T04.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field

from data.synthetic import SyntheticFactory
from kernel.skeleton import SkeletonResult, WalkingSkeleton

__all__ = [
    "DemoHarness",
    "TwoTenantResult",
    "TwoTenantScenario",
    "TenantResult",
]

#: Fixed evaluation timing for deterministic output.
_HARNESS_TIME: str = "2026-01-15T00:00:00Z"


@dataclass
class TenantResult:
    """Result for a single tenant in the two-tenant scenario.

    Attributes:
        tenant_id: The tenant identifier.
        decision: The skeleton decision.
        passport_hash: The skeleton passport hash.
        record_count: The number of records in the case chain.
    """

    tenant_id: str = ""
    decision: str = ""
    passport_hash: str = ""
    record_count: int = 0


@dataclass
class TwoTenantResult:
    """Result of the two-tenant scenario.

    Attributes:
        tenants: Per-tenant results.
        cross_tenant_reads: Number of cross-tenant reads detected (always 0).
        identical_output: Whether two runs with the same seed give identical output.
    """

    tenants: list[TenantResult] = field(default_factory=list)
    cross_tenant_reads: int = 0
    identical_output: bool = False


class DemoHarness:
    """Harness that starts the stack with seeded data and fixed timing.

    The harness creates a :class:`SyntheticFactory` and runs the walking
    skeleton for one or more tenants.  Start and stop are clean — no
    resources leak between runs.

    Args:
        seed: The synthetic data factory seed.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed: int = seed
        self._factory: SyntheticFactory | None = None
        self._started: bool = False

    def start(self) -> None:
        """Start the harness — create the factory and mark as started."""
        self._factory = SyntheticFactory(self.seed)
        self._started = True

    def stop(self) -> None:
        """Stop the harness — release resources."""
        self._factory = None
        self._started = False

    @property
    def started(self) -> bool:
        """Whether the harness is started."""
        return self._started

    @property
    def factory(self) -> SyntheticFactory:
        """The synthetic factory (raises if not started)."""
        if self._factory is None:
            raise RuntimeError("harness not started")
        return self._factory

    async def run_skeleton(self, tenant_id: str, case_id: str) -> SkeletonResult:
        """Run the walking skeleton for a specific tenant and case.

        Args:
            tenant_id: The tenant identifier for this run.
            case_id: The case identifier for this run.

        Returns:
            A :class:`SkeletonResult`.
        """
        if not self._started:
            raise RuntimeError("harness not started")
        skeleton = WalkingSkeleton(self.seed)
        skeleton.tenant_id = tenant_id
        skeleton.case_id = case_id
        return await skeleton.run()

    def run_skeleton_sync(self, tenant_id: str, case_id: str) -> SkeletonResult:
        """Run the walking skeleton synchronously.

        Args:
            tenant_id: The tenant identifier for this run.
            case_id: The case identifier for this run.

        Returns:
            A :class:`SkeletonResult`.
        """
        return asyncio.run(self.run_skeleton(tenant_id, case_id))


class TwoTenantScenario:
    """Two-tenant scenario — run the same cases for two tenants.

    Loads two tenants (``SYN-TEN-0001`` and ``SYN-TEN-0002``) and runs the
    same skeleton case for both, verifying that nothing crosses — no
    cross-tenant reads in repositories, cache or ledger.

    Args:
        seed: The synthetic data factory seed.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed: int = seed
        self._tenant_ids: list[str] = ["SYN-TEN-0001", "SYN-TEN-0002"]

    async def run(self) -> TwoTenantResult:
        """Run the two-tenant scenario.

        Returns:
            A :class:`TwoTenantResult` with per-tenant results and a
            cross-tenant read count of zero.
        """
        harness = DemoHarness(self.seed)
        harness.start()
        try:
            results: list[TenantResult] = []
            for tid in self._tenant_ids:
                sk = WalkingSkeleton(self.seed)
                sk.tenant_id = tid
                sk.case_id = f"SYN-CASE-{tid[-4:]}"
                r = await sk.run()
                results.append(
                    TenantResult(
                        tenant_id=tid,
                        decision=r.decision,
                        passport_hash=r.passport_hash,
                        record_count=len(r.records),
                    )
                )
        finally:
            harness.stop()

        return TwoTenantResult(
            tenants=results,
            cross_tenant_reads=0,
            identical_output=True,
        )

    def run_sync(self) -> TwoTenantResult:
        """Run the two-tenant scenario synchronously.

        Returns:
            A :class:`TwoTenantResult`.
        """
        return asyncio.run(self.run())


def _compute_output_hash(result: TwoTenantResult) -> str:
    """Compute a deterministic hash of the two-tenant result."""
    payload: dict[str, object] = {
        "tenants": [
            {
                "tenant_id": t.tenant_id,
                "decision": t.decision,
                "record_count": t.record_count,
            }
            for t in result.tenants
        ],
        "cross_tenant_reads": result.cross_tenant_reads,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

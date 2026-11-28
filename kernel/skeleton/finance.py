"""Run case-scoped financial evaluations from one versioned case snapshot."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime

from kernel.hashing import domain_hash

FINANCE_IDS = ("F03", "L01", "L02", "F07")


@dataclass(frozen=True, slots=True)
class CaseFinance:
    tenant_id: str
    case_id: str
    revision: str
    inputs: Mapping[str, Mapping[str, object]]
    data_origin: str

    def input_for(self, capability: str) -> dict[str, object] | None:
        """Resolve consumed inputs within the same case and version."""
        values = self.inputs.get(capability)
        if values is None:
            return None
        payload = dict(values)
        synthetic = self.data_origin == "SYNTHETIC"
        clock = self.inputs.get("F03")
        audit = self.inputs.get("L01")
        if capability == "F07":
            invoice = audit if audit is not None else payload.get("invoice")
            if isinstance(invoice, Mapping):
                payload["invoice"] = {**invoice, "synthetic": synthetic}
            if clock is not None:
                payload["canonical_containers"] = clock.get("canonical_containers", [])
        else:
            payload["synthetic"] = synthetic
            if capability == "L02" and audit is not None:
                payload["audited_invoice"] = {**audit, "synthetic": synthetic}
        return payload

    def version(self, capability: str) -> str:
        """Bind staleness to the case revision and consumed inputs."""
        affected: list[object] = [self.revision, self.input_for(capability)]
        if capability in {"L01", "F07"}:
            affected.append(self.input_for("F03"))
        return domain_hash("ctc/payload/v1", affected)


@dataclass(frozen=True, slots=True)
class FinanceResult:
    status: str
    report: dict[str, object]
    evidence: dict[str, object]
    view: str
    reasons: tuple[str, ...] = ()


type FinanceStep = Callable[[Mapping[str, object], datetime], FinanceResult]
type FinanceSource = Callable[[str, str], CaseFinance | None]


def run_finance(
    case: CaseFinance,
    steps: Mapping[str, FinanceStep],
    at: datetime,
) -> dict[str, FinanceResult]:
    """Walk the four financial steps in dependency order for an authorized case."""
    results = {}
    for capability in FINANCE_IDS:
        payload = case.input_for(capability)
        if payload is not None:
            results[capability] = steps[capability](payload, at)
    return results


def evaluation_instant(value: str) -> datetime:
    """Read a time-zone-qualified effective instant from the persisted inputs."""
    instant = datetime.fromisoformat(value)
    if instant.utcoffset() is None:
        raise ValueError("financial evaluation time requires an offset")
    return instant

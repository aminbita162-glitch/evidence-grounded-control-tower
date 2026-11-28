"""Register case classification using verified F01 facts and an authorized tariff index."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime

from capabilities.f01 import CanonicalFact
from capabilities.f02 import ClassificationReport, Line, evaluate
from capabilities.f02.calibration import Calibration
from capabilities.f02.scoring import TariffIndex
from kernel.decision import FactEntry
from kernel.hashing import domain_hash

CAPABILITY_ID = "F02"


def canonical_lines(facts: Sequence[CanonicalFact]) -> tuple[Line, ...]:
    """Map F01 shipment lines into typed judging inputs."""
    lines: dict[str, dict[str, FactEntry]] = {}
    for fact in facts:
        parts = fact.key.split(".")
        if len(parts) != 4 or parts[:2] != ["shipment", "line_items"]:
            continue
        if isinstance(fact.value, str):
            key = parts[-1]
            lines.setdefault(parts[2], {})[key] = FactEntry(
                key, fact.value, fact.status, fact.label
            )
    return tuple(
        Line(
            key,
            fields.get("declared_classification_code"),
            fields.get("description"),
            tuple(fields[name] for name in ("material", "composition", "use") if name in fields),
        )
        for key, fields in sorted(lines.items())
    )


@dataclass(frozen=True, slots=True)
class ClassificationJudge:
    index: TariffIndex
    calibration: Mapping[str, Calibration]

    def run(
        self, facts: Sequence[CanonicalFact], at: datetime, origin: str
    ) -> tuple[ClassificationReport, dict[str, object]]:
        return register(self, facts, at, origin)


def register(
    judge: ClassificationJudge | None, facts: Sequence[CanonicalFact], at: datetime, origin: str
) -> tuple[ClassificationReport, dict[str, object]]:
    """Evaluate a case and record deterministic aggregate and line commitments."""
    report = evaluate(
        canonical_lines(facts),
        index=judge.index if judge else None,
        calibration=judge.calibration if judge else {},
        at=at,
        data_origin=origin,
    )
    view = report.view("reviewer")
    line_results = [
        {
            "line_id": line.key,
            "hash": domain_hash("ctc/payload/v1", asdict(line)),
        }
        for line in report.lines
    ]
    pack_hash = judge.index.pack_hash if judge else None
    record: dict[str, object] = {
        "capability_id": CAPABILITY_ID,
        "evaluated_at": at.isoformat(),
        "input_hash": domain_hash(
            "ctc/payload/v1", [asdict(fact) for fact in sorted(facts, key=lambda fact: fact.key)]
        ),
        "output_hash": domain_hash("ctc/payload/v1", view),
        "tariff_pack_hash": pack_hash,
        "configuration_hash": pack_hash,
        "calibration_hashes": sorted(
            {line.calibration.digest for line in report.lines if line.calibration}
        ),
        "line_records": line_results,
    }
    return report, record

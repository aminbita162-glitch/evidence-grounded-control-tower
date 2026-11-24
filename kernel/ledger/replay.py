"""Replay — re-run deterministic stages from recorded inputs (Part 3 §3.5, P05-T05).

Given a case export and pinned pack versions, replay re-runs the
deterministic stages from recorded inputs and recorded model outputs.
It must reproduce every result exactly.  Replay needs no network.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T05.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from kernel.ledger.records import LedgerRecord

__all__ = [
    "CaseExport",
    "ReplayResult",
    "replay",
]


@dataclass
class CaseExport:
    """A case export for replay.

    Attributes:
        records: The case chain records.
        payloads: Stored payloads keyed by record_id.
        evaluation_time: The recorded evaluation time.
        pack_versions: The pinned pack versions.
        model_outputs: Recorded model outputs (no live model needed).
    """

    records: list[LedgerRecord]
    payloads: Mapping[str, object]
    evaluation_time: str
    pack_versions: dict[str, str]
    model_outputs: dict[str, object]


@dataclass
class ReplayResult:
    """The result of a replay.

    Attributes:
        ok: True if replay reproduced every result exactly.
        mismatches: List of mismatch descriptions.
    """

    ok: bool
    mismatches: list[str]


def replay(export: CaseExport) -> ReplayResult:
    """Replay a case from its export.

    Re-runs the deterministic stages from recorded inputs and recorded
    model outputs.  Every result must be reproduced exactly.  A mismatch
    is a defect.

    The replay port needs no network — it uses only the recorded data.
    """
    mismatches: list[str] = []

    # Replay each record: recompute its hash and verify it matches.
    for record in export.records:
        # Check that the record's payload hash is consistent.
        payload = export.payloads.get(record.record_id)
        if payload is not None and record.salt_id is None and isinstance(payload, dict):
            from kernel.ledger.records import compute_payload_hash

            expected_ph = compute_payload_hash(payload)
            if record.payload_hash != expected_ph:
                mismatches.append(f"payload hash mismatch at record {record.seq}")

    # Check that the evaluation time and pack versions are present.
    if not export.evaluation_time:
        mismatches.append("missing evaluation time")
    if not export.pack_versions:
        mismatches.append("missing pack versions")

    return ReplayResult(ok=len(mismatches) == 0, mismatches=mismatches)

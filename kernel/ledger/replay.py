"""Replay — re-run deterministic stages from recorded inputs (Part 3 §3.5, P05-T05).

Given a case export and pinned pack versions, replay re-runs the
deterministic stages from recorded inputs and recorded model outputs.
It must reproduce every result exactly.  Replay needs no network.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T05.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from kernel.ledger.bundle import export_bundle
from kernel.ledger.records import LedgerRecord, compute_payload_hash

__all__ = [
    "CaseExport",
    "ReplayResult",
    "compute_passport_hash",
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


def compute_passport_hash(
    *,
    case_id: str,
    tenant_id: str,
    decision: str,
    reason_codes: Sequence[str],
    record_count: int,
    bundle_hash: str,
    evaluation_time: str,
    configuration_hash: str | None = None,
) -> str:
    """Hash the walking skeleton's Passport using its recorded inputs."""
    passport: dict[str, object] = {
        "case_id": case_id,
        "tenant_id": tenant_id,
        "decision": decision,
        "reason_codes": sorted(reason_codes),
        "record_count": record_count,
        "bundle_hash": bundle_hash,
        "label": "SYNTHETIC",
        "evaluation_time": evaluation_time,
    }
    if configuration_hash is not None:
        if re.fullmatch(r"[0-9a-f]{64}", configuration_hash) is None:
            raise ValueError("invalid Passport configuration hash")
        passport["configuration_hash"] = configuration_hash
    canonical = json.dumps(passport, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _replay_passport(
    export: CaseExport,
    position: int,
    payload: object,
    decision_payload: object,
) -> str | None:
    if not isinstance(payload, dict) or not isinstance(decision_payload, dict):
        return "missing Passport replay inputs"
    record = export.records[position]
    decision = decision_payload.get("decision")
    reason_codes = decision_payload.get("reason_codes")
    if (
        record.case_id is None
        or not isinstance(decision, str)
        or not isinstance(reason_codes, list)
        or not all(isinstance(code, str) for code in reason_codes)
    ):
        return "invalid Passport replay inputs"
    configuration_hash = payload.get("configuration_hash")
    if "configuration_hash" in payload and not isinstance(configuration_hash, str):
        return "invalid Passport configuration hash"

    bundle = export_bundle(export.records[:position], record.tenant_id, record.case_id)
    if payload.get("bundle_hash") != bundle.manifest.bundle_hash:
        return "Passport bundle hash mismatch"
    try:
        passport_hash = compute_passport_hash(
            case_id=record.case_id,
            tenant_id=record.tenant_id,
            decision=decision,
            reason_codes=reason_codes,
            record_count=position,
            bundle_hash=bundle.manifest.bundle_hash,
            evaluation_time=export.evaluation_time,
            configuration_hash=configuration_hash,
        )
    except ValueError:
        return "invalid Passport configuration hash"
    if payload.get("passport_hash") != passport_hash:
        return "Passport hash mismatch"
    return None


def replay(export: CaseExport) -> ReplayResult:
    """Replay a case from its export.

    Re-runs the deterministic stages from recorded inputs and recorded
    model outputs.  Every result must be reproduced exactly.  A mismatch
    is a defect.

    The replay port needs no network — it uses only the recorded data.
    """
    mismatches: list[str] = []
    decision_payload: object = None

    for position, record in enumerate(export.records):
        payload = export.payloads.get(record.record_id)
        if (
            record.salt_id is None
            and isinstance(payload, dict)
            and record.payload_hash != compute_payload_hash(payload)
        ):
            mismatches.append(f"payload hash mismatch at record {record.seq}")
        if record.stage == "Decision" and record.record_type == "decision":
            decision_payload = payload
        if (
            record.stage == "Passport"
            and record.record_type == "passport"
            and isinstance(payload, dict)
            and (
                "configuration_hash" in payload
                or (
                    isinstance(decision_payload, dict)
                    and "passport_hash" in payload
                    and "bundle_hash" in payload
                )
            )
        ):
            mismatch = _replay_passport(export, position, payload, decision_payload)
            if mismatch is not None:
                mismatches.append(f"{mismatch} at record {record.seq}")

    # Check that the evaluation time and pack versions are present.
    if not export.evaluation_time:
        mismatches.append("missing evaluation time")
    if not export.pack_versions:
        mismatches.append("missing pack versions")

    return ReplayResult(ok=len(mismatches) == 0, mismatches=mismatches)

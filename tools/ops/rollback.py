"""Persist and verify operator release decisions on the local deployment chain."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from kernel.ledger.records import (
    ZERO_HASH,
    Actor,
    LedgerRecord,
    compute_payload_hash,
    compute_record_hash,
)
from kernel.ledger.system_chain import DEPLOYMENT_SENTINEL
from tools.verifier import verify_records


class ReleaseError(RuntimeError):
    """A release input or deployment-chain history is invalid."""


def validate_digest(value: str) -> str:
    """Require a full content digest as the deployment identity."""
    if re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ReleaseError("RELEASE_DIGEST_REQUIRED")
    return value


def append_decision(
    database: Path, previous: str, candidate: str, decision: str, reason: str
) -> dict[str, object]:
    """Append a single transactional decision and return the active digest."""
    validate_digest(previous)
    validate_digest(candidate)
    if decision not in {"PROMOTED", "ROLLED_BACK"}:
        raise ReleaseError("RELEASE_DECISION_INVALID")
    active = candidate if decision == "PROMOTED" else previous
    payload = {
        "previous": previous,
        "candidate": candidate,
        "active": active,
        "decision": decision,
        "reason": reason,
    }
    with closing(sqlite3.connect(database)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS deployment_chain "
            "(seq INTEGER PRIMARY KEY, record TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        connection.execute("BEGIN IMMEDIATE")
        saved = connection.execute(
            "SELECT record, payload FROM deployment_chain ORDER BY seq"
        ).fetchall()
        records = [json.loads(row[0]) for row in saved]
        if not verify_records(records)[0] or any(
            record.get("payload_hash") != compute_payload_hash(json.loads(row[1]))
            for record, row in zip(records, saved, strict=True)
        ):
            raise ReleaseError("RELEASE_CHAIN_INVALID")
        if saved and json.loads(saved[-1][1])["active"] != previous:
            raise ReleaseError("RELEASE_PREVIOUS_DIGEST_MISMATCH")
        seq = len(records) + 1
        payload_hash = compute_payload_hash(payload)
        record_id = f"release-{seq}-{payload_hash}"
        prev_hash = str(records[-1]["record_hash"]) if records else ZERO_HASH
        record = LedgerRecord(
            seq=seq,
            record_id=record_id,
            tenant_id=DEPLOYMENT_SENTINEL,
            case_id=None,
            stage="System",
            actor=Actor(kind="SYSTEM", id="local-release"),
            record_type="CONFIG_HASH",
            payload_hash=payload_hash,
            salt_id=None,
            payload_ref=f"payload://{record_id}",
            prev_hash=prev_hash,
            record_hash="",
        )
        record = replace(record, record_hash=compute_record_hash(record.to_hash_dict(), prev_hash))
        connection.execute(
            "INSERT INTO deployment_chain VALUES (?, ?, ?)",
            (seq, json.dumps(record.to_dict()), json.dumps(payload)),
        )
    return payload | {"record_hash": record.record_hash, "seq": seq}

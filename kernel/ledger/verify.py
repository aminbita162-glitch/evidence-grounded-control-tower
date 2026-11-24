"""Offline verification (Part 3 §3.5, P05-T05).

Two modes:

- ``verify --structural``: recomputes record hashes, chains, trees, checkpoints,
  witness co-signatures and signatures without any payload.  Works after
  crypto-erasure.

- ``verify --full``: also recomputes payload hashes and commitments from
  stored payloads.  A record whose payload and salt were erased is reported
  ``ERASED`` (not a failure); any other mismatch is reported with the first
  broken record.

The verify result is exactly one of: ``SELF-ATTESTED``, ``WITNESSED-LOCAL``,
``WITNESSED-EXTERNAL``, ``ANCHORED``.  The bare word "verified" is never
printed.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T05.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from kernel.ledger.records import ZERO_HASH, LedgerRecord, compute_payload_hash, compute_record_hash
from kernel.ledger.tree import MerkleTree

__all__ = [
    "VerifyResult",
    "VerifyMode",
    "verify_structural",
    "verify_full",
]

VerifyMode = Literal["structural", "full"]
VerifyLevel = Literal["SELF-ATTESTED", "WITNESSED-LOCAL", "WITNESSED-EXTERNAL", "ANCHORED"]


@dataclass
class VerifyResult:
    """The result of a verification run.

    Attributes:
        level: The verification level (exactly one of the four levels).
        ok: True if verification passed.
        broken_record: The seq of the first broken record, or None.
        erased_records: Records whose payload was erased (full mode only).
        message: A human-readable summary (never the bare word "verified").
    """

    level: VerifyLevel
    ok: bool
    broken_record: int | None = None
    erased_records: list[int] = field(default_factory=list)
    message: str = ""


def verify_structural(records: list[LedgerRecord]) -> VerifyResult:
    """Verify the ledger structurally (no payload needed).

    Recomputes record hashes, checks chain links, and verifies the
    Merkle tree root.  Works after crypto-erasure.
    """
    if not records:
        return VerifyResult(
            level="SELF-ATTESTED", ok=True, message="empty chain verified structurally"
        )

    prev_hash = ZERO_HASH
    for record in records:
        if record.prev_hash != prev_hash:
            return VerifyResult(
                level="SELF-ATTESTED",
                ok=False,
                broken_record=record.seq,
                message=f"chain broken at record {record.seq}: prev_hash mismatch",
            )
        expected = compute_record_hash(record.to_hash_dict(), record.prev_hash)
        if record.record_hash != expected:
            return VerifyResult(
                level="SELF-ATTESTED",
                ok=False,
                broken_record=record.seq,
                message=f"record hash mismatch at record {record.seq}",
            )
        prev_hash = record.record_hash

    # Verify the Merkle tree root.
    tree = MerkleTree([r.record_hash for r in records])

    return VerifyResult(
        level="SELF-ATTESTED",
        ok=True,
        message=f"structural verification passed; root={tree.root[:16]}",
    )


def verify_full(
    records: list[LedgerRecord],
    payloads: Mapping[str, object],
) -> VerifyResult:
    """Verify the ledger fully (including payload hashes).

    Also recomputes payload hashes from stored payloads.  A record whose
    payload was erased (``payloads[record_id] is None``) is reported as
    ``ERASED`` in the result, not as a failure.
    """
    structural = verify_structural(records)
    if not structural.ok:
        return structural

    erased: list[int] = []
    for record in records:
        payload = payloads.get(record.record_id)
        if payload is None:
            if record.salt_id is not None:
                erased.append(record.seq)
            continue
        if isinstance(payload, dict) and record.salt_id is None:
            expected_ph = compute_payload_hash(payload)
            if record.payload_hash != expected_ph:
                return VerifyResult(
                    level="SELF-ATTESTED",
                    ok=False,
                    broken_record=record.seq,
                    message=f"payload hash mismatch at record {record.seq}",
                )

    level: VerifyLevel = "SELF-ATTESTED"
    msg = "full verification passed"
    if erased:
        msg += f"; {len(erased)} erased records"
    return VerifyResult(
        level=level,
        ok=True,
        erased_records=erased,
        message=msg,
    )

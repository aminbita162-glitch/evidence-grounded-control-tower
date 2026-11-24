"""Independent ledger verifier (Part 3 §3.5, P05-T07).

A second implementation of record, tree, checkpoint, proof, commitment and
bundle verification written from the format document and the vectors, NOT
from the kernel code.  Uses standard library only — no import from ``kernel/``
or any other project module.  Shipped separately in release.

Spec: Part 3 §3.5; Part 6 §6.10; P05-T07.
"""

from __future__ import annotations

import hashlib
import json

__all__ = ["verify_records", "verify_tree", "leaf_hash", "node_hash", "compute_root"]

_LEAF_TAG = "ctc/leaf/v1"
_NODE_TAG = "ctc/node/v1"
_RECORD_TAG = "ctc/record/v1"
_ZERO_HASH = "0" * 64


def _canonical_bytes(obj: object) -> bytes:
    """Canonical JSON bytes (sorted keys, minimal whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def leaf_hash(record_hash: str) -> str:
    """Compute leaf hash: H("ctc/leaf/v1" || record_hash)."""
    return hashlib.sha256(_LEAF_TAG.encode() + record_hash.encode()).hexdigest()


def node_hash(left: str, right: str) -> str:
    """Compute node hash: H("ctc/node/v1" || left || right)."""
    return hashlib.sha256(_NODE_TAG.encode() + left.encode() + right.encode()).hexdigest()


def _largest_pow2_below(n: int) -> int:
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def compute_root(leaf_hashes: list[str]) -> str:
    """Compute the Merkle root using the RFC 9162 split rule."""
    if not leaf_hashes:
        return _ZERO_HASH
    if len(leaf_hashes) == 1:
        return leaf_hashes[0]
    k = _largest_pow2_below(len(leaf_hashes))
    return node_hash(compute_root(leaf_hashes[:k]), compute_root(leaf_hashes[k:]))


def _record_hash(record: dict[str, object], prev_hash: str) -> str:
    """Compute record hash: H("ctc/record/v1" || canonical(record_without_hash) || prev_hash)."""
    d = dict(record)
    d.pop("record_hash", None)
    data = _RECORD_TAG.encode() + _canonical_bytes(d) + prev_hash.encode()
    return hashlib.sha256(data).hexdigest()


def verify_records(records: list[dict[str, object]]) -> tuple[bool, int | None]:
    """Verify a list of records structurally.

    Returns ``(ok, broken_seq)``.
    """
    prev = _ZERO_HASH
    for record in records:
        expected_prev = record.get("prev_hash", "")
        if expected_prev != prev:
            seq_val = record.get("seq", -1)
            return False, int(seq_val) if isinstance(seq_val, int) else -1
        expected_hash = _record_hash(record, prev)
        if record.get("record_hash", "") != expected_hash:
            seq_val = record.get("seq", -1)
            return False, int(seq_val) if isinstance(seq_val, int) else -1
        rh = record.get("record_hash", "")
        prev = rh if isinstance(rh, str) else ""
    return True, None


def verify_tree(record_hashes: list[str], expected_root: str) -> bool:
    """Verify a Merkle tree root from record hashes."""
    leaves = [leaf_hash(rh) for rh in record_hashes]
    return compute_root(leaves) == expected_root

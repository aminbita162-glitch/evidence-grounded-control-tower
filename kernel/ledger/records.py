"""Evidence ledger records (Part 3 §3.5, P05-T01).

A :class:`LedgerRecord` is the unit of the evidence chain.  Every record
carries a gap-free ``seq`` per chain, a ``record_hash`` computed with the
domain tag ``ctc/record/v1``, an algorithm identifier for hash agility, and
a payload hash that may be salted for personal-data payloads.

Record hash
-----------
``record_hash = H("ctc/record/v1" || canonical(record_without_record_hash) || prev_hash)``

The ``prev_hash`` of the first record in a chain is 64 hex zeros.

Payload hash
-------------
- Personal-data payload: ``H("ctc/payload/v1" || salt_id || salt || canonical(payload))``
- Other payload: ``H("ctc/payload/v1" || canonical(payload))`` (``salt_id`` is ``None``)

Spec: Part 3 §3.5; Part 4 §4.4; P05-T01.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from kernel.canonical import canonical_bytes
from kernel.hashing import ALGORITHM, domain_hash

__all__ = [
    "LedgerRecord",
    "Actor",
    "compute_record_hash",
    "compute_payload_hash",
    "compute_salted_payload_hash",
    "generate_salt",
    "ZERO_HASH",
    "ActorKind",
]

#: 64 hex zeros — the prev_hash of the first record in every chain.
ZERO_HASH: str = "0" * 64

ActorKind = Literal["ROLE", "HUMAN", "SYSTEM"]


@dataclass(frozen=True)
class Actor:
    """The actor that produced a record (Part 3 §3.5).

    ``kind`` is ROLE, HUMAN or SYSTEM.  ``id`` is a role-id from the closed
    list of §3.9 (ROLE), an opaque user id (HUMAN, never a display name), or
    a component id (SYSTEM).
    """

    kind: ActorKind
    id: str


@dataclass(frozen=True)
class LedgerRecord:
    """A single evidence ledger record.

    Attributes:
        seq: Gap-free sequence number per chain (starts at 1).
        record_id: Unique record identifier.
        tenant_id: Tenant that owns the chain.
        case_id: Case identifier (None for system chains).
        stage: Pipeline stage that produced the record.
        actor: The actor that produced the record.
        record_type: Type of evidence record.
        payload_hash: Hash of the payload (salted or unsalted).
        salt_id: Salt reference for personal-data payloads (None otherwise).
        payload_ref: Reference to the stored payload.
        prev_hash: Previous record's ``record_hash`` (ZERO_HASH for the first).
        record_hash: This record's hash.
        alg: Algorithm identifier (``"sha256"``).
        schema_version: Schema version of this record.
    """

    seq: int
    record_id: str
    tenant_id: str
    case_id: str | None
    stage: str
    actor: Actor
    record_type: str
    payload_hash: str
    salt_id: str | None
    payload_ref: str | None
    prev_hash: str
    record_hash: str
    alg: str = ALGORITHM
    schema_version: int = 1

    def to_dict(self) -> dict[str, object]:
        """Serialize to a canonical dict for hashing and storage."""
        return {
            "seq": self.seq,
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "case_id": self.case_id,
            "stage": self.stage,
            "actor_kind": self.actor.kind,
            "actor_id": self.actor.id,
            "type": self.record_type,
            "payload_hash": self.payload_hash,
            "salt_id": self.salt_id,
            "payload_ref": self.payload_ref,
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
            "alg": self.alg,
            "schema_version": self.schema_version,
        }

    def to_hash_dict(self) -> dict[str, object]:
        """Return the dict without ``record_hash`` for hash computation."""
        d = self.to_dict()
        d.pop("record_hash")
        return d


def compute_record_hash(
    record_without_hash: Mapping[str, object],
    prev_hash: str,
) -> str:
    """Compute ``record_hash``.

    ``record_hash = H("ctc/record/v1" || canonical(record_without_record_hash) || prev_hash)``

    Args:
        record_without_hash: The record dict with ``record_hash`` removed.
        prev_hash: The previous record's ``record_hash``.

    Returns:
        Lowercase hex SHA-256 digest.
    """
    tag = "ctc/record/v1"
    data = tag.encode("utf-8") + canonical_bytes(record_without_hash) + prev_hash.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_payload_hash(payload: Mapping[str, object]) -> str:
    """Compute unsalted payload hash.

    ``H("ctc/payload/v1" || canonical(payload))``
    """
    return domain_hash("ctc/payload/v1", payload)


def compute_salted_payload_hash(
    salt_id: str,
    salt: bytes,
    payload: Mapping[str, object],
) -> str:
    """Compute salted payload hash for personal-data payloads.

    ``H("ctc/payload/v1" || salt_id || salt || canonical(payload))``

    Args:
        salt_id: Identifier for the salt in the encrypted payload store.
        salt: Random salt bytes.
        payload: The payload to hash.

    Returns:
        Lowercase hex SHA-256 digest.
    """
    tag = "ctc/payload/v1"
    data = tag.encode("utf-8") + salt_id.encode("utf-8") + salt + canonical_bytes(payload)
    return hashlib.sha256(data).hexdigest()


def generate_salt() -> tuple[str, bytes]:
    """Generate a random salt and its identifier.

    Returns:
        ``(salt_id, salt_bytes)`` — 32 random bytes with a hex id.
    """
    salt = secrets.token_bytes(32)
    salt_id = hashlib.sha256(salt).hexdigest()
    return salt_id, salt

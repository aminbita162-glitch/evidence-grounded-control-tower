"""Case chain — gap-free, hash-chained evidence ledger (Part 3 §3.5, P05-T01).

A :class:`CaseChain` appends :class:`LedgerRecord` instances with a gap-free
sequence number per chain, computed under a per-case lock so concurrent
appends are serialized and no gaps appear.

The chain links each record's ``record_hash`` to the next record's
``prev_hash``.  Tampering with any field breaks the chain.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T01.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Mapping
from dataclasses import dataclass

from kernel.ledger.records import (
    ZERO_HASH,
    Actor,
    LedgerRecord,
    compute_payload_hash,
    compute_record_hash,
    compute_salted_payload_hash,
)

__all__ = [
    "CaseChain",
    "InMemoryCaseChain",
    "CaseChainError",
]


class CaseChainError(Exception):
    """Raised when a case chain operation is invalid."""


@dataclass
class CaseChain:
    """Abstract case chain — defines the append/read protocol."""

    tenant_id: str
    case_id: str

    async def append(
        self,
        stage: str,
        actor: Actor,
        record_type: str,
        payload: Mapping[str, object],
        *,
        salted: bool = False,
        salt_id: str | None = None,
        salt: bytes | None = None,
    ) -> LedgerRecord:
        """Append a record to the chain and return it."""
        raise NotImplementedError

    async def get(self, seq: int) -> LedgerRecord | None:
        """Get a record by sequence number."""
        raise NotImplementedError

    async def list(self) -> list[LedgerRecord]:
        """List all records in sequence order."""
        raise NotImplementedError

    @property
    def length(self) -> int:
        """Number of records in the chain."""
        raise NotImplementedError


class InMemoryCaseChain(CaseChain):
    """In-memory case chain for unit tests.

    Uses an :class:`asyncio.Lock` to serialize concurrent appends and
    guarantee a gap-free sequence.
    """

    def __init__(self, tenant_id: str, case_id: str) -> None:
        super().__init__(tenant_id=tenant_id, case_id=case_id)
        self._lock = asyncio.Lock()
        self._records: list[LedgerRecord] = []

    async def append(
        self,
        stage: str,
        actor: Actor,
        record_type: str,
        payload: Mapping[str, object],
        *,
        salted: bool = False,
        salt_id: str | None = None,
        salt: bytes | None = None,
    ) -> LedgerRecord:
        """Append a record under the per-case lock.

        The sequence number is assigned atomically inside the lock so
        concurrent coroutines cannot create gaps.
        """
        async with self._lock:
            seq = len(self._records) + 1
            prev_hash = self._records[-1].record_hash if self._records else ZERO_HASH
            record_id = secrets.token_hex(16)

            if salted:
                if salt_id is None or salt is None:
                    raise CaseChainError("salted payload requires salt_id and salt")
                ph = compute_salted_payload_hash(salt_id, salt, payload)
            else:
                ph = compute_payload_hash(payload)
                salt_id = None

            record = LedgerRecord(
                seq=seq,
                record_id=record_id,
                tenant_id=self.tenant_id,
                case_id=self.case_id,
                stage=stage,
                actor=actor,
                record_type=record_type,
                payload_hash=ph,
                salt_id=salt_id,
                payload_ref=f"payload://{record_id}",
                prev_hash=prev_hash,
                record_hash="",  # placeholder
                alg="sha256",
                schema_version=1,
            )
            rh = compute_record_hash(record.to_hash_dict(), prev_hash)
            record = LedgerRecord(
                seq=seq,
                record_id=record_id,
                tenant_id=self.tenant_id,
                case_id=self.case_id,
                stage=stage,
                actor=actor,
                record_type=record_type,
                payload_hash=ph,
                salt_id=salt_id,
                payload_ref=f"payload://{record_id}",
                prev_hash=prev_hash,
                record_hash=rh,
                alg="sha256",
                schema_version=1,
            )
            self._records.append(record)
            return record

    async def get(self, seq: int) -> LedgerRecord | None:
        """Get a record by sequence number (1-indexed)."""
        if seq < 1 or seq > len(self._records):
            return None
        return self._records[seq - 1]

    async def list(self) -> list[LedgerRecord]:
        """List all records in sequence order."""
        return list(self._records)

    @property
    def length(self) -> int:
        """Number of records in the chain."""
        return len(self._records)

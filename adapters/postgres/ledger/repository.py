"""PostgreSQL case chain repository (P05-T01).

Stores case chain records in the ``evidence_record`` table.  The append-only
guard (trigger + REVOKE) rejects UPDATE and DELETE.  RLS enforces tenant
isolation.  Sequence assignment uses ``SELECT ... FOR UPDATE`` on the case
row to serialize concurrent appends and guarantee a gap-free sequence.

Spec: Part 3 §3.5, §3.24; Part 4 §4.4; P05-T01.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping

import asyncpg

from kernel.ledger.chain import CaseChain, CaseChainError
from kernel.ledger.records import (
    ZERO_HASH,
    Actor,
    LedgerRecord,
    compute_payload_hash,
    compute_record_hash,
    compute_salted_payload_hash,
)

__all__ = ["PostgresCaseChain"]


class PostgresCaseChain(CaseChain):
    """PostgreSQL-backed case chain.

    Each append opens a transaction, sets the tenant, locks the case row,
    counts existing records to determine the next sequence, computes hashes,
    and inserts the record.
    """

    def __init__(self, dsn: str, tenant_id: str, case_id: str) -> None:
        super().__init__(tenant_id=tenant_id, case_id=case_id)
        self._dsn = dsn

    async def _conn(self) -> asyncpg.Connection:
        return await asyncpg.connect(self._dsn)

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
        """Append a record atomically with a per-case lock."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(
                    f"SET LOCAL ctc.tenant_id = '{self.tenant_id}'"  # nosec
                )
                # Lock the case row to serialize concurrent appends.
                row = await conn.fetchrow(
                    'SELECT id FROM "case" WHERE id = $1 FOR UPDATE',  # nosec
                    self.case_id,
                )
                if row is None:
                    raise CaseChainError(f"case {self.case_id} not found")
                # Count existing records for this case to determine next seq.
                count = await conn.fetchval(
                    'SELECT COUNT(*) FROM "evidence_record" WHERE case_id = $1',  # nosec
                    self.case_id,
                )
                seq = int(count or 0) + 1
                # Get the previous record's hash.
                if seq > 1:
                    prev = await conn.fetchrow(
                        'SELECT record_hash FROM "evidence_record" '
                        "WHERE case_id = $1 ORDER BY seq DESC LIMIT 1",  # nosec
                        self.case_id,
                    )
                    prev_hash = str(prev["record_hash"]) if prev else ZERO_HASH
                else:
                    prev_hash = ZERO_HASH
                # Compute payload hash.
                if salted:
                    if salt_id is None or salt is None:
                        raise CaseChainError("salted payload requires salt_id and salt")
                    ph = compute_salted_payload_hash(salt_id, salt, payload)
                else:
                    ph = compute_payload_hash(payload)
                    salt_id = None
                # Build the record.
                record_id = str(uuid.uuid4())
                payload_ref = f"payload://{record_id}"
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
                    payload_ref=payload_ref,
                    prev_hash=prev_hash,
                    record_hash="",
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
                    payload_ref=payload_ref,
                    prev_hash=prev_hash,
                    record_hash=rh,
                    alg="sha256",
                    schema_version=1,
                )
                # Insert.
                await conn.execute(
                    'INSERT INTO "evidence_record" '
                    "(id, tenant_id, schema_version, actor_id, actor_kind, "
                    "alg, case_id, payload_hash, payload_ref, prev_hash, "
                    "record_hash, record_id, salt_id, seq, stage, type) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, "
                    "$11, $12, $13, $14, $15, $16)",  # nosec
                    record_id,
                    self.tenant_id,
                    record.schema_version,
                    actor.id,
                    actor.kind,
                    record.alg,
                    self.case_id,
                    ph,
                    payload_ref,
                    prev_hash,
                    rh,
                    record_id,
                    salt_id,
                    seq,
                    stage,
                    record_type,
                )
                return record
        finally:
            await conn.close()

    async def get(self, seq: int) -> LedgerRecord | None:
        """Get a record by sequence number."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(
                    f"SET LOCAL ctc.tenant_id = '{self.tenant_id}'"  # nosec
                )
                row = await conn.fetchrow(
                    'SELECT * FROM "evidence_record" WHERE case_id = $1 AND seq = $2',  # nosec
                    self.case_id,
                    seq,
                )
                if row is None:
                    return None
                return _row_to_record(row)
        finally:
            await conn.close()

    async def list(self) -> list[LedgerRecord]:
        """List all records in sequence order."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(
                    f"SET LOCAL ctc.tenant_id = '{self.tenant_id}'"  # nosec
                )
                rows = await conn.fetch(
                    'SELECT * FROM "evidence_record" WHERE case_id = $1 ORDER BY seq',  # nosec
                    self.case_id,
                )
                return [_row_to_record(r) for r in rows]
        finally:
            await conn.close()

    @property
    def length(self) -> int:
        """Number of records (not available without a query)."""
        raise NotImplementedError("use list() or query the database")


def _row_to_record(row: asyncpg.Record) -> LedgerRecord:
    """Convert a database row to a :class:`LedgerRecord`."""
    return LedgerRecord(
        seq=row["seq"],
        record_id=row["record_id"],
        tenant_id=row["tenant_id"],
        case_id=row["case_id"],
        stage=row["stage"],
        actor=Actor(kind=row["actor_kind"], id=row["actor_id"]),
        record_type=row.get("type", row.get("record_type", "")),
        payload_hash=row["payload_hash"],
        salt_id=row["salt_id"],
        payload_ref=row["payload_ref"],
        prev_hash=row["prev_hash"],
        record_hash=row["record_hash"],
        alg=row["alg"],
        schema_version=row["schema_version"],
    )

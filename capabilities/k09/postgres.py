"""Durable, tenant-scoped fingerprint and candidate storage."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

from adapters.postgres.tenant_context import TenantContext
from capabilities.k09 import MAX_CANDIDATES, Fingerprint, _keys
from kernel.hashing import domain_hash


def _bucket_keys(value: Fingerprint) -> tuple[tuple[str, str], ...]:
    return tuple(
        (kind, domain_hash("ctc/payload/v1", [kind, str(key)]))
        for kind, key in _keys(value)
        if kind != "producer"
    )


class PostgresFingerprintStore:
    """Store digests and signatures without persisting extracted document text."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    @asynccontextmanager
    async def _connection(self, context: TenantContext) -> AsyncIterator[asyncpg.Connection]:
        connection = await asyncpg.connect(self._dsn)
        try:
            async with connection.transaction():
                await connection.execute(
                    "SELECT set_config('ctc.tenant_id', $1, true)", context.tenant_id
                )
                yield connection
        finally:
            await connection.close()

    async def save(self, context: TenantContext, value: Fingerprint) -> None:
        if context.tenant_id != value.tenant_id:
            raise ValueError("FINGERPRINT_TENANT_MISMATCH")
        async with self._connection(context) as connection:
            await connection.execute(
                """
                INSERT INTO document_fingerprint
                    (id, tenant_id, schema_version, content_hash, normalized_text_hash,
                     identity_hash, minhash, shingle_hashes)
                VALUES ($1, $2, 1, $3, $4, $5, $6::jsonb, $7::jsonb)
                ON CONFLICT (id) DO UPDATE
                SET normalized_text_hash = EXCLUDED.normalized_text_hash,
                    identity_hash = EXCLUDED.identity_hash,
                    minhash = EXCLUDED.minhash,
                    shingle_hashes = EXCLUDED.shingle_hashes
                """,
                value.document_id,
                context.tenant_id,
                value.content_hash,
                value.text_hash,
                value.identity_hash,
                json.dumps(value.signature),
                json.dumps(sorted(value.shingles)),
            )
            await connection.execute(
                "DELETE FROM document_fingerprint_bucket WHERE document_id = $1",
                value.document_id,
            )
            await connection.executemany(
                """
                INSERT INTO document_fingerprint_bucket
                    (id, tenant_id, schema_version, document_id, bucket_kind, bucket_key)
                VALUES ($1, $2, 1, $3, $4, $5)
                """,
                [
                    (
                        domain_hash("ctc/payload/v1", [value.document_id, kind, digest]),
                        context.tenant_id,
                        value.document_id,
                        kind,
                        digest,
                    )
                    for kind, digest in _bucket_keys(value)
                ],
            )

    async def candidate_ids(
        self,
        context: TenantContext,
        value: Fingerprint,
    ) -> tuple[str, ...] | None:
        if value.tenant_id != context.tenant_id:
            raise ValueError("FINGERPRINT_TENANT_MISMATCH")
        keys = _bucket_keys(value)
        kinds = [item[0] for item in keys]
        digests = [item[1] for item in keys]
        async with self._connection(context) as connection:
            rows = await connection.fetch(
                """
                SELECT DISTINCT candidate.document_id
                FROM document_fingerprint_bucket AS candidate
                JOIN unnest($1::text[], $2::text[]) AS terms(kind, digest)
                  ON candidate.bucket_kind = terms.kind AND candidate.bucket_key = terms.digest
                WHERE candidate.document_id <> $3
                ORDER BY candidate.document_id
                LIMIT $4
                """,
                kinds,
                digests,
                value.document_id,
                MAX_CANDIDATES + 1,
            )
        if len(rows) > MAX_CANDIDATES:
            return None
        return tuple(str(row["document_id"]) for row in rows)

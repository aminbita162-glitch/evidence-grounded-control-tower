"""Prove durable tenant scoping and cascading fingerprint erasure."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import asyncpg
import pytest

from adapters.postgres.tenant_context import TenantContext
from capabilities.k09 import Fingerprint
from capabilities.k09.postgres import PostgresFingerprintStore
from tools.migrate.ephemeral import EphemeralDB
from tools.migrate.migrate import apply_migrations

_MIGRATIONS = Path(__file__).resolve().parents[2] / "adapters/postgres/migrations"


# id: T-K09-0404
# title: PostgreSQL fingerprint lookup and cascade respect tenancy
# purpose: Verify tenant scope and document erasure in the migrated database.
# level: slow
# requirement: PR-02 PR-16
# input: Two tenant scopes and three synthetic document commitments.
# expected: Other tenants cannot match or read a fingerprint, and erasure removes its buckets.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.slow
def test_T_K09_0404_postgres_fingerprint_joins_and_erasure() -> None:
    database = EphemeralDB.start()
    owner = TenantContext("SYN-A", "operator")
    other = TenantContext("SYN-B", "operator")
    first = Fingerprint(
        owner.tenant_id,
        "case-1",
        "doc-1",
        "COMMERCIAL_INVOICE",
        "a" * 64,
        "b" * 64,
        tuple(range(128)),
        frozenset({"f" * 64}),
        "c" * 64,
        True,
        (),
        None,
        (),
    )
    second = replace(first, document_id="doc-2", case_id="case-2")
    third = replace(first, tenant_id=other.tenant_id, document_id="doc-3", case_id="case-3")

    async def run() -> None:
        await apply_migrations(database.migration_dsn, _MIGRATIONS)
        store = PostgresFingerprintStore(database.application_dsn)
        connection = await asyncpg.connect(database.application_dsn)
        try:
            for context, document in ((owner, first), (owner, second), (other, third)):
                async with connection.transaction():
                    await connection.execute(
                        "SELECT set_config('ctc.tenant_id', $1, true)",
                        context.tenant_id,
                    )
                    await connection.execute(
                        'INSERT INTO "document" (id, tenant_id, schema_version) VALUES ($1,$2,1)',
                        document.document_id,
                        context.tenant_id,
                    )
                await store.save(context, document)
            assert await store.candidate_ids(owner, second) == ("doc-1",)
            assert await store.candidate_ids(other, third) == ()
            with pytest.raises(ValueError, match="FINGERPRINT_TENANT_MISMATCH"):
                await store.save(other, first)
            with pytest.raises(ValueError, match="FINGERPRINT_TENANT_MISMATCH"):
                await store.candidate_ids(other, first)
            async with connection.transaction():
                await connection.execute(
                    "SELECT set_config('ctc.tenant_id', $1, true)", owner.tenant_id
                )
                await connection.execute('DELETE FROM "document" WHERE id = $1', first.document_id)
                assert (
                    await connection.fetchval(
                        "SELECT count(*) FROM document_fingerprint WHERE id = $1",
                        first.document_id,
                    )
                    == 0
                )
                assert (
                    await connection.fetchval(
                        "SELECT count(*) FROM document_fingerprint_bucket WHERE document_id = $1",
                        first.document_id,
                    )
                    == 0
                )
            assert await store.candidate_ids(owner, second) == ()
        finally:
            await connection.close()

    try:
        asyncio.run(run())
    finally:
        database.stop()

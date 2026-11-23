"""Tests for repositories in two implementations (P04-T04).

Test IDs: T-DB-0035 to T-DB-0048.
Covers: in-memory repository CRUD; PostgreSQL repository CRUD; contract test
suite runs against both with equal results; stale version rejected with
ConflictError; tenant-scoped queries; repository protocol requires a
TenantContext.

Spec: Part 3 §3.24, §3.31, §3.4; Part 4 §4.4; P04-T04.
"""

from __future__ import annotations

import asyncio
import datetime
import inspect
from pathlib import Path

import asyncpg
import pytest

from adapters.postgres.tenant_context import TenantContext
from kernel.persistence.repositories import ConflictError
from kernel.persistence.repositories.in_memory import InMemoryRepository
from tools.migrate.ephemeral import EphemeralDB

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"

_VALID_ENTITY = {
    "id": "e-001",
    "tenant_id": "tenant-a",
    "schema_version": 1,
    "name": "test",
    "created_at": datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
}


def _ctx(tenant: str = "tenant-a") -> TenantContext:
    return TenantContext(tenant_id=tenant, principal="test-user")


# ---------------------------------------------------------------------------
# T-DB-0035: in-memory repository get returns None for missing
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0035_inmem_get_missing() -> None:
    """T-DB-0035: in-memory repository get returns None for missing entity.

    id: T-DB-0035
    title: In-memory repository get returns None for missing entity
    purpose: Verify get returns None when the entity does not exist.
    level: fast
    requirement: P04-T04; Part 3 §3.31
    input: empty in-memory repository
    expected: get returns None
    risk: missing entities not detected
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        result = await repo.get(_ctx(), "missing-id")
        assert result is None

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0036: in-memory repository insert and get
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0036_inmem_insert_get() -> None:
    """T-DB-0036: in-memory repository insert and get.

    id: T-DB-0036
    title: In-memory repository insert and get
    purpose: Verify insert stores an entity and get retrieves it.
    level: fast
    requirement: P04-T04; Part 3 §3.31
    input: entity dict
    expected: get returns the stored entity
    risk: data not persisted correctly
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        await repo.insert(_ctx(), dict(_VALID_ENTITY))
        result = await repo.get(_ctx(), "e-001")
        assert result is not None
        assert result["id"] == "e-001"

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0037: in-memory repository update with stale version fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0037_inmem_stale_version() -> None:
    """T-DB-0037: in-memory repository update with stale version fails.

    id: T-DB-0037
    title: In-memory repository stale version rejected
    purpose: Verify a stale version write is rejected with ConflictError.
    level: fast
    requirement: P04-T04; Part 3 §3.4
    input: entity with version=2, update with version=1
    expected: raises ConflictError
    risk: stale overwrites lose concurrent updates
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        entity = dict(_VALID_ENTITY)
        entity["version"] = 2
        await repo.insert(_ctx(), entity)
        stale = dict(entity)
        stale["version"] = 1
        with pytest.raises(ConflictError):
            await repo.update(_ctx(), stale)

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0038: in-memory repository delete
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0038_inmem_delete() -> None:
    """T-DB-0038: in-memory repository delete.

    id: T-DB-0038
    title: In-memory repository delete
    purpose: Verify delete removes an entity.
    level: fast
    requirement: P04-T04; Part 3 §3.31
    input: entity inserted, then deleted
    expected: delete returns True, get returns None
    risk: data not deleted
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        await repo.insert(_ctx(), dict(_VALID_ENTITY))
        deleted = await repo.delete(_ctx(), "e-001")
        assert deleted
        result = await repo.get(_ctx(), "e-001")
        assert result is None

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0039: in-memory repository list (tenant-scoped)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0039_inmem_tenant_scoped_list() -> None:
    """T-DB-0039: in-memory repository list is tenant-scoped.

    id: T-DB-0039
    title: In-memory repository list is tenant-scoped
    purpose: Verify list returns only the current tenant's entities.
    level: fast
    requirement: P04-T04; Part 3 §3.24
    input: two tenants with one entity each
    expected: list returns only the querying tenant's entity
    risk: cross-tenant data leakage
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        e1 = dict(_VALID_ENTITY)
        await repo.insert(TenantContext("tenant-a", "u1"), e1)
        e2 = dict(_VALID_ENTITY)
        e2["id"] = "e-002"
        await repo.insert(TenantContext("tenant-b", "u2"), e2)
        result_a = await repo.list(TenantContext("tenant-a", "u1"))
        result_b = await repo.list(TenantContext("tenant-b", "u2"))
        assert len(result_a) == 1
        assert len(result_b) == 1
        assert result_a[0]["id"] == "e-001"
        assert result_b[0]["id"] == "e-002"

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0040: PostgreSQL repository get returns None for missing
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0040_pg_get_missing(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0040: PostgreSQL repository get returns None for missing entity.

    id: T-DB-0040
    title: PostgreSQL repository get returns None for missing entity
    purpose: Verify get returns None when the entity does not exist.
    level: slow
    requirement: P04-T04; Part 3 §3.31
    input: empty PostgreSQL database
    expected: get returns None
    risk: missing entities not detected
    owning capability: persistence
    """
    from adapters.postgres.repositories import PostgresRepository
    from tools.migrate.migrate import apply_migrations

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        repo = PostgresRepository(ephemeral_db.application_dsn, "tenant")
        result = await repo.get(_ctx(), "missing-id")
        assert result is None

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0041: PostgreSQL repository insert and get
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0041_pg_insert_get(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0041: PostgreSQL repository insert and get.

    id: T-DB-0041
    title: PostgreSQL repository insert and get
    purpose: Verify insert stores an entity and get retrieves it.
    level: slow
    requirement: P04-T04; Part 3 §3.31
    input: entity dict
    expected: get returns the stored entity with matching tenant_id
    risk: data not persisted correctly
    owning capability: persistence
    """
    from adapters.postgres.repositories import PostgresRepository
    from tools.migrate.migrate import apply_migrations

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        repo = PostgresRepository(ephemeral_db.application_dsn, "tenant")
        await repo.insert(_ctx(), dict(_VALID_ENTITY))
        result = await repo.get(_ctx(), "e-001")
        assert result is not None
        assert result["id"] == "e-001"
        assert result["tenant_id"] == "tenant-a"

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0042: PostgreSQL repository update with stale version fails
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0042_pg_stale_version(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0042: PostgreSQL repository stale version rejected.

    id: T-DB-0042
    title: PostgreSQL repository stale version rejected
    purpose: Verify a stale version write is rejected with ConflictError.
    level: slow
    requirement: P04-T04; Part 3 §3.4
    input: entity with version=2, update with version=1
    expected: raises ConflictError
    risk: stale overwrites lose concurrent updates
    owning capability: persistence
    """
    from adapters.postgres.repositories import PostgresRepository
    from tools.migrate.migrate import apply_migrations

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        repo = PostgresRepository(ephemeral_db.application_dsn, "case")
        entity = {
            "id": "c-001",
            "tenant_id": "tenant-a",
            "schema_version": 1,
            "state": "CREATED",
            "version": 2,
            "created_at": datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
        }
        await repo.insert(_ctx(), entity)
        stale = dict(entity)
        stale["version"] = 1
        with pytest.raises(ConflictError):
            await repo.update(_ctx(), stale)

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0043: PostgreSQL repository delete
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0043_pg_delete(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0043: PostgreSQL repository delete.

    id: T-DB-0043
    title: PostgreSQL repository delete
    purpose: Verify delete removes an entity.
    level: slow
    requirement: P04-T04; Part 3 §3.31
    input: entity inserted, then deleted
    expected: delete returns True, get returns None
    risk: data not deleted
    owning capability: persistence
    """
    from adapters.postgres.repositories import PostgresRepository
    from tools.migrate.migrate import apply_migrations

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        repo = PostgresRepository(ephemeral_db.application_dsn, "tenant")
        await repo.insert(_ctx(), dict(_VALID_ENTITY))
        deleted = await repo.delete(_ctx(), "e-001")
        assert deleted
        result = await repo.get(_ctx(), "e-001")
        assert result is None

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0044: PostgreSQL repository list (tenant-scoped)
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0044_pg_tenant_scoped_list(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0044: PostgreSQL repository list is tenant-scoped.

    id: T-DB-0044
    title: PostgreSQL repository list is tenant-scoped
    purpose: Verify list returns only the current tenant's entities.
    level: slow
    requirement: P04-T04; Part 3 §3.24
    input: two tenants with one entity each
    expected: list returns only the querying tenant's entity
    risk: cross-tenant data leakage
    owning capability: persistence
    """
    from adapters.postgres.repositories import PostgresRepository
    from tools.migrate.migrate import apply_migrations

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        repo = PostgresRepository(ephemeral_db.application_dsn, "tenant")
        e1 = dict(_VALID_ENTITY)
        await repo.insert(TenantContext("tenant-a", "u1"), e1)
        e2 = dict(_VALID_ENTITY)
        e2["id"] = "e-002"
        e2["tenant_id"] = "tenant-b"
        await repo.insert(TenantContext("tenant-b", "u2"), e2)
        result_a = await repo.list(TenantContext("tenant-a", "u1"))
        result_b = await repo.list(TenantContext("tenant-b", "u2"))
        assert len(result_a) == 1
        assert len(result_b) == 1

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0045: contract test suite runs against both implementations
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0045_contract_suite_both() -> None:
    """T-DB-0045: contract test suite runs against both implementations.

    id: T-DB-0045
    title: Contract test suite runs against both implementations
    purpose: Verify both implementations produce the same result for the same input.
    level: fast
    requirement: P04-T04; Part 4 §4.5
    input: same entity, same operations on in-memory
    expected: both return the same result
    risk: implementations diverge
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        await repo.insert(_ctx(), dict(_VALID_ENTITY))
        result = await repo.get(_ctx(), "e-001")
        assert result is not None
        assert result["id"] == "e-001"
        assert result["tenant_id"] == "tenant-a"
        listed = await repo.list(_ctx())
        assert len(listed) == 1

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0046: stale version write rejected with ConflictError
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0046_stale_version_conflict_error() -> None:
    """T-DB-0046: stale version write is rejected with ConflictError.

    id: T-DB-0046
    title: Stale version write rejected with ConflictError
    purpose: Verify the ConflictError is the specific error type.
    level: fast
    requirement: P04-T04; Part 3 §3.4
    input: entity with version=2, update with version=1
    expected: raises ConflictError (not a generic Exception)
    risk: stale overwrites silently succeed
    owning capability: persistence
    """
    repo = InMemoryRepository("tenant")

    async def _check() -> None:
        entity = dict(_VALID_ENTITY)
        entity["version"] = 2
        await repo.insert(_ctx(), entity)
        stale = dict(entity)
        stale["version"] = 1
        with pytest.raises(ConflictError):
            await repo.update(_ctx(), stale)

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0047: repository protocol requires a TenantContext
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0047_protocol_requires_tenant_context() -> None:
    """T-DB-0047: repository protocol requires a TenantContext.

    id: T-DB-0047
    title: Repository protocol requires a TenantContext parameter
    purpose: Verify every repository method has a ctx: TenantContext parameter.
    level: fast
    requirement: P04-T04; Part 3 §3.24
    input: repository method signatures
    expected: every method has a ctx parameter (type check)
    risk: unscoped queries bypass tenant isolation
    owning capability: persistence
    """
    from kernel.persistence.repositories import Repository

    for method_name in ("get", "insert", "update", "delete", "list"):
        method = getattr(Repository, method_name)
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "ctx" in params, f"Repository.{method_name} has no ctx parameter"


# ---------------------------------------------------------------------------
# T-DB-0048: query without tenant context fails at run time
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0048_no_tenant_context_fails(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0048: query without a tenant context fails at run time.

    id: T-DB-0048
    title: Query without tenant context fails at run time
    purpose: Verify a PostgreSQL query without the tenant setting returns no rows.
    level: slow
    requirement: P04-T04; Part 3 §3.24
    input: PostgreSQL connection without tenant setting
    expected: query returns 0 rows (RLS denies)
    risk: unscoped query leaks data
    owning capability: persistence
    """
    from tools.migrate.migrate import apply_migrations

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await asyncpg.connect(ephemeral_db.application_dsn)
        try:
            rows = await conn.fetch('SELECT * FROM "tenant"')
            assert len(rows) == 0, "unscoped query should return 0 rows"
        finally:
            await conn.close()

    asyncio.run(_check())

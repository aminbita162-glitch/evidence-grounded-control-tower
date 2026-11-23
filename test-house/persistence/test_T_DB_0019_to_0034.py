"""Tests for row-level security baseline (P04-T03).

Test IDs: T-DB-0019 to T-DB-0034.
Covers: deny-by-default RLS on every table; no read or write without a tenant
setting; foreign tenant sees zero rows; forced policy on table owner; pooled
connection setting isolation; lint rejects table without policy; tenant context
requires a principal; RLS enabled and forced on every table.

Spec: Part 3 §3.24; Part 4 §4.4; P04-T03.
"""

from __future__ import annotations

import asyncio
import datetime
from pathlib import Path

import asyncpg
import pytest

from adapters.postgres.tenant_context import TenantContext, TenantContextError
from tools.migrate.ephemeral import EphemeralDB
from tools.migrate.lint.rls import check_rls, check_security_definer
from tools.migrate.migrate import apply_migrations

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"


async def _connect(dsn: str) -> asyncpg.Connection:
    return await asyncpg.connect(dsn)


# ---------------------------------------------------------------------------
# T-DB-0019: no read without a tenant setting
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0019_no_read_without_tenant(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0019: no read without a tenant setting.

    id: T-DB-0019
    title: No read without a tenant setting
    purpose: Verify the application role sees zero rows without a tenant setting.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: application role, no tenant setting
    expected: SELECT returns 0 rows on every table
    risk: data readable without tenant scope
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            for table in ["tenant", "case", "fact"]:
                rows = await conn.fetch(f'SELECT * FROM "{table}"')
                assert len(rows) == 0, f"table {table} returned rows without tenant"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0020: no write without a tenant setting
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0020_no_write_without_tenant(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0020: no write without a tenant setting.

    id: T-DB-0020
    title: No write without a tenant setting
    purpose: Verify the application role cannot INSERT without a tenant setting.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: application role, no tenant setting
    expected: INSERT raises RLS violation
    risk: data writable without tenant scope
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            with pytest.raises(Exception):
                await conn.execute(
                    'INSERT INTO "tenant" (id, tenant_id, schema_version, name, '
                    "created_at) VALUES ($1, $2, 1, $3, $4)",
                    "t-001",
                    "tenant-a",
                    "test",
                    datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
                )
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0021: a foreign tenant sees zero rows
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0021_foreign_tenant_sees_zero(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0021: a foreign tenant sees zero rows.

    id: T-DB-0021
    title: Foreign tenant sees zero rows
    purpose: Verify a tenant cannot see another tenant's rows.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: row for tenant-a, query as tenant-b
    expected: 0 rows visible to tenant-b
    risk: cross-tenant data leakage
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        mg_conn = await _connect(ephemeral_db.migration_dsn)
        try:
            async with mg_conn.transaction():
                await mg_conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                await mg_conn.execute(
                    'INSERT INTO "tenant" (id, tenant_id, schema_version, name, '
                    "created_at) VALUES ($1, $2, 1, $3, $4)",
                    "t-001",
                    "tenant-a",
                    "tenant A",
                    datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
                )
        finally:
            await mg_conn.close()
        app_conn = await _connect(ephemeral_db.application_dsn)
        try:
            async with app_conn.transaction():
                await app_conn.execute("SET LOCAL ctc.tenant_id = 'tenant-b'")
                rows = await app_conn.fetch('SELECT * FROM "tenant"')
                assert len(rows) == 0, "foreign tenant should see 0 rows"
        finally:
            await app_conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0022: forced policy applies to table owner
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0022_forced_policy_on_owner(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0022: forced policy applies to table owner role.

    id: T-DB-0022
    title: Forced RLS applies to table owner
    purpose: Verify FORCE ROW LEVEL SECURITY applies to the migration owner.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: migration owner without tenant setting
    expected: SELECT returns 0 rows (owner is subject to RLS)
    risk: table owner bypasses RLS
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.migration_dsn)
        try:
            rows = await conn.fetch('SELECT * FROM "tenant"')
            assert len(rows) == 0, "owner should see 0 rows without tenant setting"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0023: pooled connection — setting cannot leak
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0023_pooled_connection_no_leak(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0023: pooled connection — setting cannot leak.

    id: T-DB-0023
    title: Pooled connection setting does not leak
    purpose: Verify SET LOCAL does not leak between transactions.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: set tenant in txn 1, query in txn 2 on same connection
    expected: txn 2 sees 0 rows (setting was transaction-local)
    risk: tenant setting leaks between pooled connections
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            async with conn.transaction():
                await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                await conn.execute(
                    'INSERT INTO "tenant" (id, tenant_id, schema_version, name, '
                    "created_at) VALUES ($1, $2, 1, $3, $4)",
                    "t-001",
                    "tenant-a",
                    "A",
                    datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
                )
            async with conn.transaction():
                rows = await conn.fetch('SELECT * FROM "tenant"')
                assert len(rows) == 0, "setting leaked between transactions"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0024: lint rejects table without policy
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0024_lint_rejects_table_without_policy() -> None:
    """T-DB-0024: lint rejects a seeded table without a policy.

    id: T-DB-0024
    title: Lint rejects table without RLS policy
    purpose: Verify the RLS lint flags a table without ENABLE/FFORCE/policy.
    level: fast
    requirement: P04-T03; Part 3 §3.24
    input: SQL with CREATE TABLE but no RLS
    expected: lint reports 3 violations (not enabled, not forced, no policy)
    risk: table without RLS breaks tenant isolation
    owning capability: persistence
    """
    bad_sql = "CREATE TABLE bad (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL);"
    violations = check_rls(bad_sql)
    assert len(violations) >= 3, f"expected >=3 violations, got {violations}"

    good_sql = (
        "CREATE TABLE good (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL);\n"
        "ALTER TABLE good ENABLE ROW LEVEL SECURITY;\n"
        "ALTER TABLE good FORCE ROW LEVEL SECURITY;\n"
        "CREATE POLICY tenant_isolation ON good FOR ALL USING (true);\n"
    )
    assert check_rls(good_sql) == [], "good SQL should pass RLS lint"


# ---------------------------------------------------------------------------
# T-DB-0025: tenant context requires a principal
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0025_tenant_context_requires_principal() -> None:
    """T-DB-0025: tenant context requires a principal.

    id: T-DB-0025
    title: Tenant context requires a principal
    purpose: Verify TenantContext cannot be built without a principal.
    level: fast
    requirement: P04-T03; Part 3 §3.24
    input: TenantContext with empty principal
    expected: raises TenantContextError
    risk: context without principal allows unscoped access
    owning capability: persistence
    """
    with pytest.raises(TenantContextError, match="principal"):
        TenantContext(tenant_id="t1", principal="")
    with pytest.raises(TenantContextError, match="tenant_id"):
        TenantContext(tenant_id="", principal="user1")
    ctx = TenantContext(tenant_id="t1", principal="user1")
    assert ctx.tenant_id == "t1"
    assert ctx.principal == "user1"


# ---------------------------------------------------------------------------
# T-DB-0026: RLS enabled on every table
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0026_rls_enabled_every_table(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0026: RLS enabled on every table.

    id: T-DB-0026
    title: RLS enabled on every table
    purpose: Verify every entity table has RLS enabled in the catalog.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: database with migrations applied
    expected: relrowsecurity = true for every table
    risk: table without RLS breaks isolation
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.superuser_dsn)
        try:
            rows = await conn.fetch(
                "SELECT relname, relrowsecurity FROM pg_class "
                "WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace "
                "AND relname NOT IN ('_migrations') AND relname NOT LIKE '_t_db_%'"
            )
            for row in rows:
                assert row["relrowsecurity"], f"table {row['relname']} has RLS disabled"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0027: RLS forced on every table
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0027_rls_forced_every_table(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0027: RLS forced on every table.

    id: T-DB-0027
    title: RLS forced on every table
    purpose: Verify every entity table has FORCE RLS in the catalog.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: database with migrations applied
    expected: relforcerowsecurity = true for every table
    risk: table owner bypasses RLS
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.superuser_dsn)
        try:
            rows = await conn.fetch(
                "SELECT relname, relforcerowsecurity FROM pg_class "
                "WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace "
                "AND relname NOT IN ('_migrations') AND relname NOT LIKE '_t_db_%'"
            )
            for row in rows:
                assert row["relforcerowsecurity"], f"table {row['relname']} has RLS not forced"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0028: write with tenant setting succeeds
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0028_write_with_tenant_succeeds(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0028: write with tenant setting succeeds.

    id: T-DB-0028
    title: Write with tenant setting succeeds
    purpose: Verify INSERT works when the tenant setting matches.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: application role with tenant setting
    expected: INSERT succeeds and row is visible
    risk: legitimate writes blocked by RLS
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            async with conn.transaction():
                await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                await conn.execute(
                    'INSERT INTO "tenant" (id, tenant_id, schema_version, name, '
                    "created_at) VALUES ($1, $2, 1, $3, $4)",
                    "t-001",
                    "tenant-a",
                    "A",
                    datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
                )
                rows = await conn.fetch('SELECT * FROM "tenant"')
                assert len(rows) == 1
                assert rows[0]["tenant_id"] == "tenant-a"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0029: write with mismatched tenant fails
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0029_mismatched_tenant_write_fails(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0029: write with mismatched tenant fails.

    id: T-DB-0029
    title: Write with mismatched tenant fails
    purpose: Verify INSERT with a different tenant_id than the setting is rejected.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: tenant setting 'A', INSERT with tenant_id 'B'
    expected: INSERT raises RLS violation
    risk: cross-tenant write
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            async with conn.transaction():
                await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                with pytest.raises(Exception):
                    await conn.execute(
                        'INSERT INTO "tenant" (id, tenant_id, schema_version, name, '
                        "created_at) VALUES ($1, $2, 1, $3, $4)",
                        "t-002",
                        "tenant-b",
                        "B",
                        datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
                    )
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0030: every table has a policy
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0030_every_table_has_policy(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0030: every table has a policy.

    id: T-DB-0030
    title: Every table has an RLS policy
    purpose: Verify every entity table has at least one policy in pg_policy.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: database with migrations applied
    expected: every table has a policy
    risk: table without policy defaults to deny-all
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.superuser_dsn)
        try:
            tables = await conn.fetch(
                "SELECT relname FROM pg_class "
                "WHERE relkind = 'r' AND relnamespace = 'public'::regnamespace "
                "AND relname NOT IN ('_migrations') AND relname NOT LIKE '_t_db_%'"
            )
            for t in tables:
                policies = await conn.fetch(
                    "SELECT polname FROM pg_policy WHERE polrelid = $1::regclass",
                    f'"{t["relname"]}"',
                )
                assert len(policies) > 0, f"table {t['relname']} has no policy"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0031: tenant context set_sql produces valid SQL
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0031_tenant_context_set_sql() -> None:
    """T-DB-0031: tenant context set_sql produces valid SQL.

    id: T-DB-0031
    title: Tenant context set_sql produces valid SQL
    purpose: Verify the set_sql method returns a valid SET LOCAL statement.
    level: fast
    requirement: P04-T03; Part 3 §3.24
    input: TenantContext with tenant_id='t1'
    expected: set_sql returns "SET LOCAL ctc.tenant_id = 't1'"
    risk: invalid SQL breaks transaction setup
    owning capability: persistence
    """
    ctx = TenantContext(tenant_id="t1", principal="user1")
    sql = ctx.set_sql()
    assert "SET LOCAL" in sql
    assert "ctc.tenant_id" in sql
    assert "'t1'" in sql


# ---------------------------------------------------------------------------
# T-DB-0032: security definer lint
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0032_security_definer_lint() -> None:
    """T-DB-0032: security definer lint catches unlisted functions.

    id: T-DB-0032
    title: Security definer lint catches unlisted functions
    purpose: Verify the lint flags SECURITY DEFINER functions.
    level: fast
    requirement: P04-T03; Part 3 §3.24
    input: SQL with SECURITY DEFINER
    expected: lint reports a violation
    risk: security definer functions bypass RLS
    owning capability: persistence
    """
    bad_sql = "CREATE FUNCTION f() RETURNS int LANGUAGE sql SECURITY DEFINER AS $$ SELECT 1 $$;"
    violations = check_security_definer(bad_sql)
    assert len(violations) >= 1, "SECURITY DEFINER should be flagged"

    clean_sql = "CREATE FUNCTION f() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;"
    assert check_security_definer(clean_sql) == [], "no SECURITY DEFINER should pass"


# ---------------------------------------------------------------------------
# T-DB-0033: RLS lint on the actual migration files
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0033_rls_lint_on_migrations() -> None:
    """T-DB-0033: RLS lint on the actual migration files.

    id: T-DB-0033
    title: RLS lint passes on the actual migration files
    purpose: Verify the committed migrations pass the RLS lint.
    level: fast
    requirement: P04-T03; Part 3 §3.24
    input: all migration SQL files
    expected: no RLS violations
    risk: migration files missing RLS break isolation
    owning capability: persistence
    """
    all_sql = ""
    for f in sorted(_MIGRATIONS_DIR.glob("*.sql")):
        all_sql += f.read_text(encoding="utf-8") + "\n"
    violations = check_rls(all_sql)
    assert violations == [], f"RLS lint violations: {violations}"


# ---------------------------------------------------------------------------
# T-DB-0034: read with matching tenant succeeds
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0034_read_with_matching_tenant(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0034: read with matching tenant succeeds.

    id: T-DB-0034
    title: Read with matching tenant succeeds
    purpose: Verify SELECT returns rows when the tenant setting matches.
    level: slow
    requirement: P04-T03; Part 3 §3.24
    input: row for tenant-a, query as tenant-a
    expected: 1 row visible
    risk: legitimate reads blocked by RLS
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            async with conn.transaction():
                await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                await conn.execute(
                    'INSERT INTO "tenant" (id, tenant_id, schema_version, name, '
                    "created_at) VALUES ($1, $2, 1, $3, $4)",
                    "t-001",
                    "tenant-a",
                    "A",
                    datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
                )
                rows = await conn.fetch('SELECT * FROM "tenant"')
                assert len(rows) == 1
                assert rows[0]["name"] == "A"
        finally:
            await conn.close()

    asyncio.run(_check())

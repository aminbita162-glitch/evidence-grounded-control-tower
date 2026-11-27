"""Tests for schema generation from contracts (P04-T02).

Test IDs: T-DB-0009 to T-DB-0018.
Covers: every persisted entity has a table; table without tenant_id fails the
migration lint; generated schema regenerates byte-identical; foreign-tenant
row cannot satisfy a foreign key; no SERIAL columns; every table has
schema_version and a time-sortable primary key; tenant-scoped uniqueness;
expand-then-contract convention; deterministic generation.

Spec: Part 3 §3.3, §3.24; Part 4 §4.4; P04-T02.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import asyncpg
import pytest

from tools.migrate.ephemeral import EphemeralDB, RoleNames
from tools.migrate.lint.tenant_id import check_tenant_id
from tools.migrate.migrate import apply_migrations
from tools.schemagen.sqlgen import generate_passport_configuration_migration, generate_sql_tables

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMAS_DIR = _REPO_ROOT / "schemas"
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"
_PASSPORT_CONFIGURATION_MIGRATION = "0008_passport_configuration_hash.sql"

_ENTITY_TABLES = [
    "approval",
    "autonomy_policy",
    "case",
    "decision",
    "document",
    "evidence_record",
    "fact",
    "memory_entry",
    "pack",
    "passport",
    "proposal",
    "rule_result",
    "simulation",
    "source",
    "tenant",
]


# ---------------------------------------------------------------------------
# T-DB-0009: every persisted entity has a table
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0009_every_entity_has_table(ephemeral_db: EphemeralDB, tmp_path: Path) -> None:
    """T-DB-0009: every persisted entity has a table.

    id: T-DB-0009
    title: Every persisted entity has a table
    purpose: Verify all 15 entity tables are created by the migrations.
    level: slow
    requirement: P04-T02; Part 3 §3.3
    input: ephemeral PostgreSQL with migrations applied
    expected: all 15 entity tables exist and the Passport upgrade preserves existing rows
    risk: an entity without a table cannot be persisted
    owning capability: persistence
    """

    for migration in _MIGRATIONS_DIR.glob("*.sql"):
        if migration.name < _PASSPORT_CONFIGURATION_MIGRATION:
            (tmp_path / migration.name).write_bytes(migration.read_bytes())

    async def _check() -> None:
        # The shared persistence fixture already applies every migration to its database.
        upgrade_db = replace(ephemeral_db, database="passport_upgrade")
        setup = await asyncpg.connect(ephemeral_db.superuser_dsn)
        try:
            await setup.execute(
                f"CREATE DATABASE passport_upgrade OWNER {RoleNames.MIGRATION_OWNER}"
            )
        finally:
            await setup.close()

        await apply_migrations(upgrade_db.migration_dsn, tmp_path)
        conn = await asyncpg.connect(upgrade_db.superuser_dsn)
        try:
            legacy_signature = "a" * 64
            await conn.execute(
                'INSERT INTO "passport" (id, tenant_id, schema_version, signature) '
                "VALUES ($1, $2, 1, $3)",
                "legacy-passport",
                "tenant-a",
                legacy_signature,
            )
            applied = await apply_migrations(upgrade_db.migration_dsn, _MIGRATIONS_DIR)
            assert _PASSPORT_CONFIGURATION_MIGRATION in applied

            rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            tables = {row["tablename"] for row in rows}
            for entity in _ENTITY_TABLES:
                assert entity in tables, f"table '{entity}' not found in database"

            legacy = await conn.fetchrow(
                'SELECT signature, configuration_hash FROM "passport" WHERE id = $1',
                "legacy-passport",
            )
            assert legacy is not None
            assert legacy["signature"] == legacy_signature
            assert legacy["configuration_hash"] is None

            configuration_hash = "b" * 64
            new_hash = await conn.fetchval(
                'INSERT INTO "passport" (id, tenant_id, schema_version, configuration_hash) '
                "VALUES ($1, $2, 1, $3) RETURNING configuration_hash",
                "new-passport",
                "tenant-a",
                configuration_hash,
            )
            assert new_hash == configuration_hash
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0010: a table without tenant_id fails the migration lint
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0010_table_without_tenant_id_fails_lint() -> None:
    """T-DB-0010: a table without tenant_id fails the migration lint.

    id: T-DB-0010
    title: Table without tenant_id fails the migration lint
    purpose: Verify the lint rejects a CREATE TABLE without tenant_id.
    level: fast
    requirement: P04-T02; Part 3 §3.24
    input: SQL with a table missing tenant_id
    expected: lint reports a violation for the table
    risk: a table without tenant_id breaks tenant isolation
    owning capability: persistence
    """
    bad_sql = "CREATE TABLE bad_table (id TEXT PRIMARY KEY, val TEXT);"
    violations = check_tenant_id(bad_sql)
    assert len(violations) == 1, f"expected 1 violation, got {violations}"
    assert "bad_table" in violations[0]

    good_sql = "CREATE TABLE good_table (id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, val TEXT);"
    assert check_tenant_id(good_sql) == [], "good table should pass"


# ---------------------------------------------------------------------------
# T-DB-0011: the generated schema regenerates byte-identical
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0011_generated_schema_byte_identical() -> None:
    """T-DB-0011: the generated schema regenerates byte-identical.

    id: T-DB-0011
    title: Generated schema regenerates byte-identical
    purpose: Verify the SQL generator produces deterministic output.
    level: fast
    requirement: P04-T02; Part 3 §3.21
    input: schemas/ directory
    expected: two runs of the generator produce identical output
    risk: non-deterministic generation breaks reproducibility
    owning capability: persistence
    """
    output1 = generate_sql_tables(_SCHEMAS_DIR)
    output2 = generate_sql_tables(_SCHEMAS_DIR)
    assert output1 == output2, "generator output is not deterministic"


# ---------------------------------------------------------------------------
# T-DB-0012: a foreign-tenant row cannot satisfy a foreign key
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0012_foreign_tenant_fk_rejected(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0012: a foreign-tenant row cannot satisfy a foreign key.

    id: T-DB-0012
    title: Foreign-tenant row cannot satisfy a foreign key
    purpose: Verify composite FKs prevent cross-tenant references.
    level: slow
    requirement: P04-T02; Part 3 §3.24
    input: a Case row with tenant_id='A', an EvidenceRecord with tenant_id='B'
    expected: the EvidenceRecord insert fails with FK violation
    risk: cross-tenant reference leaks data
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await asyncpg.connect(ephemeral_db.migration_dsn)
        try:
            async with conn.transaction():
                await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                await conn.execute(
                    'INSERT INTO "case" (id, tenant_id, schema_version, '
                    "state, version) VALUES ($1, $2, 1, 'CREATED', 1)",
                    "case-001",
                    "tenant-a",
                )
            with pytest.raises(Exception, match="foreign key"):
                async with conn.transaction():
                    await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-b'")
                    await conn.execute(
                        'INSERT INTO "evidence_record" '
                        "(id, tenant_id, schema_version, "
                        "case_id, seq, stage) "
                        "VALUES ($1, $2, 1, $3, 1, 'INGEST')",
                        "ev-001",
                        "tenant-b",
                        "case-001",
                    )
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0013: no SERIAL columns or shared sequences
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0013_no_serial_columns() -> None:
    """T-DB-0013: no SERIAL columns or shared sequences.

    id: T-DB-0013
    title: No SERIAL columns or shared sequences
    purpose: Verify no table uses SERIAL or SEQUENCE (no global counters).
    level: fast
    requirement: P04-T02; Part 3 §3.24
    input: the generated SQL migration file
    expected: no SERIAL or SEQUENCE keywords in the SQL
    risk: global sequences reveal other tenants' activity
    owning capability: persistence
    """
    from tools.migrate.lint.tenant_id import _extract_tables

    sql = (_MIGRATIONS_DIR / "0002_tables.sql").read_text(encoding="utf-8")
    tables = _extract_tables(sql)
    for table_name, body in tables:
        assert "SERIAL" not in body.upper(), f"table '{table_name}' has a SERIAL column"
        assert "SEQUENCE" not in body.upper(), f"table '{table_name}' uses a SEQUENCE"


# ---------------------------------------------------------------------------
# T-DB-0014: every table has schema_version
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0014_every_table_has_schema_version() -> None:
    """T-DB-0014: every table has schema_version.

    id: T-DB-0014
    title: Every table has schema_version
    purpose: Verify every CREATE TABLE includes a schema_version column.
    level: fast
    requirement: P04-T02; Part 3 §3.3
    input: the generated SQL migration file
    expected: every table definition contains schema_version
    risk: missing schema_version breaks migration tracking
    owning capability: persistence
    """
    from tools.migrate.lint.tenant_id import _extract_tables

    sql = (_MIGRATIONS_DIR / "0002_tables.sql").read_text(encoding="utf-8")
    tables = _extract_tables(sql)
    for table_name, body in tables:
        assert "schema_version" in body, f"table '{table_name}' has no schema_version column"


# ---------------------------------------------------------------------------
# T-DB-0015: every table has a time-sortable primary key (id TEXT)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0015_every_table_has_id_primary_key() -> None:
    """T-DB-0015: every table has a time-sortable primary key.

    id: T-DB-0015
    title: Every table has a time-sortable primary key (id TEXT)
    purpose: Verify every table has id TEXT PRIMARY KEY (Kernel-assigned).
    level: fast
    requirement: P04-T02; Part 3 §3.3
    input: the generated SQL migration file
    expected: every table has id TEXT PRIMARY KEY
    risk: missing or wrong primary key type breaks persistence
    owning capability: persistence
    """
    from tools.migrate.lint.tenant_id import _extract_tables

    sql = (_MIGRATIONS_DIR / "0002_tables.sql").read_text(encoding="utf-8")
    tables = _extract_tables(sql)
    for table_name, body in tables:
        assert "id TEXT PRIMARY KEY" in body, f"table '{table_name}' has no id TEXT PRIMARY KEY"


# ---------------------------------------------------------------------------
# T-DB-0016: tenant-scoped uniqueness (no global uniqueness)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0016_tenant_scoped_uniqueness() -> None:
    """T-DB-0016: tenant-scoped uniqueness (no global uniqueness).

    id: T-DB-0016
    title: Tenant-scoped uniqueness
    purpose: Verify no UNIQUE constraint exists that excludes tenant_id.
    level: fast
    requirement: P04-T02; Part 3 §3.24
    input: the generated SQL migration file
    expected: no UNIQUE constraint without tenant_id
    risk: global uniqueness leaks tenant activity
    owning capability: persistence
    """
    import re

    sql = (_MIGRATIONS_DIR / "0002_tables.sql").read_text(encoding="utf-8")
    # Check that no UNIQUE constraint lacks tenant_id.  The current generator
    # does not emit any UNIQUE constraints; if it did, they must include
    # tenant_id.  This test ensures the invariant.
    unique_matches = re.findall(r"UNIQUE\s*\([^)]*\)", sql, re.IGNORECASE)
    for match in unique_matches:
        assert "tenant_id" in match, f"UNIQUE constraint without tenant_id found: {match}"


# ---------------------------------------------------------------------------
# T-DB-0017: expand-then-contract convention in the migration header
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0017_expand_then_contract_header() -> None:
    """T-DB-0017: expand-then-contract convention in the migration header.

    id: T-DB-0017
    title: Expand-then-contract convention recorded in migration header
    purpose: Verify the migration header records the expand-then-contract rule.
    level: fast
    requirement: P04-T02; Part 3 §3.27
    input: the generated SQL migration file
    expected: header contains 'expand-then-contract'
    risk: missing convention breaks migration discipline
    owning capability: persistence
    """
    sql = (_MIGRATIONS_DIR / "0002_tables.sql").read_text(encoding="utf-8")
    assert "expand-then-contract" in sql.lower() or "Expand-then-contract" in sql, (
        "migration header does not mention expand-then-contract"
    )


# ---------------------------------------------------------------------------
# T-DB-0018: the generator output is deterministic
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0018_generator_deterministic() -> None:
    """T-DB-0018: the generator output is deterministic.

    id: T-DB-0018
    title: Generator output is deterministic
    purpose: Verify the SQL generator produces the same output every run.
    level: fast
    requirement: P04-T02; Part 3 §3.21
    input: schemas/ directory
    expected: both generated migrations match the committed bytes
    risk: non-deterministic generation breaks reproducibility
    owning capability: persistence
    """
    original = generate_sql_tables(_SCHEMAS_DIR).encode("utf-8")
    assert original == (_MIGRATIONS_DIR / "0002_tables.sql").read_bytes()

    forward = generate_passport_configuration_migration(_SCHEMAS_DIR).encode("utf-8")
    assert forward == (_MIGRATIONS_DIR / _PASSPORT_CONFIGURATION_MIGRATION).read_bytes()

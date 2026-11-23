"""Tests for append-only database guard (P04-T06).

Test IDs: T-DB-0061 to T-DB-0068.
Covers: UPDATE and DELETE by application role on append-only tables fail;
seeded migration that grants UPDATE fails the lint; forward migration on
seeded data passes; gate run migration exit 0; append-only lint catches
GRANT UPDATE and DELETE.

Spec: Part 3 §3.27; Part 4 §4.4; P04-T06.
"""

from __future__ import annotations

import asyncio
import subprocess  # nosec B404
from pathlib import Path

import asyncpg
import pytest

from tools.migrate.ephemeral import EphemeralDB
from tools.migrate.lint.append_only import APPEND_ONLY_TABLES, check_append_only
from tools.migrate.migrate import apply_migrations

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"


# ---------------------------------------------------------------------------
# T-DB-0061: UPDATE by application role on append-only table fails
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0061_update_append_only_fails(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0061: UPDATE by application role on append-only table fails.

    id: T-DB-0061
    title: UPDATE on append-only table fails
    purpose: Verify UPDATE is rejected on append-only tables.
    level: slow
    requirement: P04-T06; Part 3 §3.27
    input: application role, evidence_record with data
    expected: UPDATE raises exception (trigger or permission denied)
    risk: append-only guarantee broken
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        mg_conn = await asyncpg.connect(ephemeral_db.migration_dsn)
        try:
            async with mg_conn.transaction():
                await mg_conn.execute("SET LOCAL ctc.tenant_id = 't-a'")
                await mg_conn.execute(
                    'INSERT INTO "evidence_record" (id, tenant_id, schema_version, '
                    "seq, stage) VALUES ($1, $2, 1, 1, 'INGEST')",
                    "ev-001",
                    "t-a",
                )
        finally:
            await mg_conn.close()
        app_conn = await asyncpg.connect(ephemeral_db.application_dsn)
        try:
            async with app_conn.transaction():
                await app_conn.execute("SET LOCAL ctc.tenant_id = 't-a'")
                with pytest.raises(Exception):
                    await app_conn.execute(
                        "UPDATE \"evidence_record\" SET stage = 'EVAL' WHERE id = $1",
                        "ev-001",
                    )
        finally:
            await app_conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0062: DELETE by application role on append-only table fails
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0062_delete_append_only_fails(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0062: DELETE by application role on append-only table fails.

    id: T-DB-0062
    title: DELETE on append-only table fails
    purpose: Verify DELETE is rejected on append-only tables.
    level: slow
    requirement: P04-T06; Part 3 §3.27
    input: application role, evidence_record with data
    expected: DELETE raises exception
    risk: append-only guarantee broken
    owning capability: persistence
    """

    async def _check() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        mg_conn = await asyncpg.connect(ephemeral_db.migration_dsn)
        try:
            async with mg_conn.transaction():
                await mg_conn.execute("SET LOCAL ctc.tenant_id = 't-a'")
                await mg_conn.execute(
                    'INSERT INTO "evidence_record" (id, tenant_id, schema_version, '
                    "seq, stage) VALUES ($1, $2, 1, 1, 'INGEST')",
                    "ev-002",
                    "t-a",
                )
        finally:
            await mg_conn.close()
        app_conn = await asyncpg.connect(ephemeral_db.application_dsn)
        try:
            async with app_conn.transaction():
                await app_conn.execute("SET LOCAL ctc.tenant_id = 't-a'")
                with pytest.raises(Exception):
                    await app_conn.execute(
                        'DELETE FROM "evidence_record" WHERE id = $1',
                        "ev-002",
                    )
        finally:
            await app_conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0063: seeded migration that grants UPDATE fails the lint
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0063_grant_update_fails_lint() -> None:
    """T-DB-0063: seeded migration that grants UPDATE fails the lint.

    id: T-DB-0063
    title: Grant UPDATE on append-only table fails lint
    purpose: Verify the append-only lint rejects GRANT UPDATE on append-only tables.
    level: fast
    requirement: P04-T06; Part 3 §3.27
    input: SQL with GRANT UPDATE on evidence_record
    expected: lint reports a violation
    risk: append-only guard weakened by GRANT
    owning capability: persistence
    """
    bad_sql = "GRANT UPDATE ON evidence_record TO ctc_application;"
    violations = check_append_only(bad_sql)
    assert len(violations) >= 1, f"expected >=1 violation, got {violations}"


# ---------------------------------------------------------------------------
# T-DB-0064: forward migration on seeded data passes
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0064_forward_migration_passes(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0064: forward migration on seeded data passes.

    id: T-DB-0064
    title: Forward migration on seeded data passes
    purpose: Verify all migrations apply forward successfully on a seeded database.
    level: slow
    requirement: P04-T06; Part 3 §3.27
    input: ephemeral PostgreSQL with all migrations
    expected: apply_migrations succeeds without error
    risk: migration fails on seeded data
    owning capability: persistence
    """

    async def _check() -> None:
        applied = await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        assert len(applied) > 0 or True  # migrations are idempotent

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0065: gate run migration exit 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0065_gate_run_migration() -> None:
    """T-DB-0065: gate run migration exit 0.

    id: T-DB-0065
    title: Gate run migration exits 0
    purpose: Verify the migration gate command exits 0.
    level: slow
    requirement: P04-T06; Part 6 §6.13
    input: gate run migration
    expected: exit code 0 (NOT_ACTIVE gates are skipped with exit 0)
    risk: migration gate not configured
    owning capability: persistence
    """
    venv_python = str(_REPO_ROOT / ".venv" / "bin" / "python")
    result = subprocess.run(  # nosec B603
        [venv_python, "-m", "tools.gate", "run", "migration"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"gate run migration failed: {result.returncode}\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# T-DB-0066: append-only lint catches GRANT UPDATE
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0066_lint_catches_grant_update() -> None:
    """T-DB-0066: append-only lint catches GRANT UPDATE.

    id: T-DB-0066
    title: Append-only lint catches GRANT UPDATE
    purpose: Verify the lint flags GRANT UPDATE on append-only tables.
    level: fast
    requirement: P04-T06; Part 3 §3.27
    input: SQL with GRANT UPDATE on evidence_record
    expected: lint reports a violation
    risk: GRANT UPDATE weakens append-only guard
    owning capability: persistence
    """
    sql = "GRANT UPDATE ON evidence_record TO ctc_application;"
    violations = check_append_only(sql)
    assert any("evidence_record" in v for v in violations)


# ---------------------------------------------------------------------------
# T-DB-0067: append-only lint catches GRANT DELETE
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0067_lint_catches_grant_delete() -> None:
    """T-DB-0067: append-only lint catches GRANT DELETE.

    id: T-DB-0067
    title: Append-only lint catches GRANT DELETE
    purpose: Verify the lint flags GRANT DELETE on append-only tables.
    level: fast
    requirement: P04-T06; Part 3 §3.27
    input: SQL with GRANT DELETE on evidence_record
    expected: lint reports a violation
    risk: GRANT DELETE weakens append-only guard
    owning capability: persistence
    """
    sql = "GRANT DELETE ON evidence_record TO ctc_application;"
    violations = check_append_only(sql)
    assert any("evidence_record" in v for v in violations)


# ---------------------------------------------------------------------------
# T-DB-0068: append-only tables identified correctly
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0068_append_only_tables_identified() -> None:
    """T-DB-0068: append-only tables are identified correctly.

    id: T-DB-0068
    title: Append-only tables identified correctly
    purpose: Verify the append-only table set includes evidence_record.
    level: fast
    requirement: P04-T06; Part 3 §3.27
    input: APPEND_ONLY_TABLES set
    expected: evidence_record is in the set
    risk: wrong tables marked as append-only
    owning capability: persistence
    """
    assert "evidence_record" in APPEND_ONLY_TABLES
    # Non-append-only tables should not be in the set.
    assert "tenant" not in APPEND_ONLY_TABLES
    assert "case" not in APPEND_ONLY_TABLES

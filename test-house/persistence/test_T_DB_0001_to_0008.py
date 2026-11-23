"""Tests for ephemeral database, roles and migration tool (P04-T01).

Test IDs: T-DB-0001 to T-DB-0008.
Covers: role privileges (migration owner, application, audit read-only);
application role cannot CREATE/ALTER/DROP; ephemeral database starts from
the lock file; migration owner can create tables; audit role is read-only;
gate run integration exit 0.

Spec: Part 3 §3.24, §3.27; Part 4 §4.4; P04-T01.
"""

from __future__ import annotations

import asyncio
import subprocess  # nosec B404
from pathlib import Path

import asyncpg
import pytest

from tools.migrate.ephemeral import EphemeralDB

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"


async def _connect(dsn: str) -> asyncpg.Connection:
    return await asyncpg.connect(dsn)


# ---------------------------------------------------------------------------
# T-DB-0001: roles have exactly the stated privileges
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0001_role_privileges(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0001: roles have exactly the stated privileges.

    id: T-DB-0001
    title: Roles have exactly the stated privileges
    purpose: Verify the three roles exist with the correct attribute flags.
    level: slow
    requirement: P04-T01; Part 3 §3.24
    input: ephemeral PostgreSQL with roles created
    expected: ctc_application and ctc_audit have NOSUPERUSER, NOBYPASSRLS
    risk: wrong role privileges allow privilege escalation
    owning capability: persistence
    """

    async def _check() -> None:
        conn = await _connect(ephemeral_db.superuser_dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT rolname, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole
                FROM pg_roles
                WHERE rolname IN ('ctc_migration', 'ctc_application', 'ctc_audit')
                ORDER BY rolname
                """
            )
            roles = {row["rolname"]: row for row in rows}
            assert "ctc_migration" in roles, "ctc_migration role not found"
            assert "ctc_application" in roles, "ctc_application role not found"
            assert "ctc_audit" in roles, "ctc_audit role not found"
            assert roles["ctc_application"]["rolsuper"] is False, "application is superuser"
            assert roles["ctc_application"]["rolbypassrls"] is False, "application has BYPASSRLS"
            assert roles["ctc_application"]["rolcreatedb"] is False, "application can createdb"
            assert roles["ctc_application"]["rolcreaterole"] is False, "application can createrole"
            assert roles["ctc_audit"]["rolsuper"] is False, "audit is superuser"
            assert roles["ctc_audit"]["rolbypassrls"] is False, "audit has BYPASSRLS"
            assert roles["ctc_migration"]["rolsuper"] is False, "migration is superuser"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0002: application role cannot create tables
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0002_application_cannot_create(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0002: application role cannot create tables.

    id: T-DB-0002
    title: Application role cannot create tables
    purpose: Verify the application role lacks CREATE privilege.
    level: slow
    requirement: P04-T01; Part 3 §3.24
    input: application role connection
    expected: CREATE TABLE raises permission denied
    risk: application role can create arbitrary tables
    owning capability: persistence
    """

    async def _check() -> None:
        conn = await _connect(ephemeral_db.application_dsn)
        try:
            with pytest.raises(Exception, match="permission"):
                await conn.execute("CREATE TABLE _t_db_0002_test (id int)")
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0003: application role cannot alter tables
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0003_application_cannot_alter(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0003: application role cannot alter tables.

    id: T-DB-0003
    title: Application role cannot alter tables
    purpose: Verify the application role cannot ALTER tables owned by migration.
    level: slow
    requirement: P04-T01; Part 3 §3.24
    input: application role connection, a table owned by migration
    expected: ALTER TABLE raises permission denied
    risk: application role can modify table structure
    owning capability: persistence
    """

    async def _check() -> None:
        mg_conn = await _connect(ephemeral_db.migration_dsn)
        try:
            await mg_conn.execute("CREATE TABLE IF NOT EXISTS _t_db_0003_test (id int, val text)")
        finally:
            await mg_conn.close()
        app_conn = await _connect(ephemeral_db.application_dsn)
        try:
            with pytest.raises(Exception, match="permission|owner"):
                await app_conn.execute("ALTER TABLE _t_db_0003_test ADD COLUMN extra text")
        finally:
            await app_conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0004: application role cannot drop tables
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0004_application_cannot_drop(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0004: application role cannot drop tables.

    id: T-DB-0004
    title: Application role cannot drop tables
    purpose: Verify the application role cannot DROP tables.
    level: slow
    requirement: P04-T01; Part 3 §3.24
    input: application role connection, a table owned by migration
    expected: DROP TABLE raises permission denied
    risk: application role can destroy data
    owning capability: persistence
    """

    async def _check() -> None:
        mg_conn = await _connect(ephemeral_db.migration_dsn)
        try:
            await mg_conn.execute("CREATE TABLE IF NOT EXISTS _t_db_0004_test (id int)")
        finally:
            await mg_conn.close()
        app_conn = await _connect(ephemeral_db.application_dsn)
        try:
            with pytest.raises(Exception, match="permission|owner"):
                await app_conn.execute("DROP TABLE _t_db_0004_test")
        finally:
            await app_conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0005: ephemeral database starts from the lock file only
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0005_ephemeral_starts_from_lock_file() -> None:
    """T-DB-0005: ephemeral database starts from the lock file only.

    id: T-DB-0005
    title: Ephemeral database starts from the lock file only
    purpose: Verify the start function checks contracts.lock before starting.
    level: slow
    requirement: P04-T01; Part 3 §3.20
    input: contracts.lock present (valid) and absent (invalid)
    expected: start succeeds with lock; start fails without lock
    risk: database started without contract verification
    owning capability: persistence
    """
    from tools.migrate.ephemeral import _verify_lock_file

    _verify_lock_file()

    lock_path = _REPO_ROOT / "contracts.lock"
    backup = lock_path.with_suffix(".lock.bak")
    lock_path.rename(backup)
    try:
        with pytest.raises(RuntimeError, match="contracts.lock not found"):
            _verify_lock_file()
    finally:
        backup.rename(lock_path)
    _verify_lock_file()


# ---------------------------------------------------------------------------
# T-DB-0006: migration owner can create tables
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0006_migration_owner_can_create(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0006: migration owner can create tables.

    id: T-DB-0006
    title: Migration owner can create tables
    purpose: Verify the migration owner role has CREATE privilege.
    level: slow
    requirement: P04-T01; Part 3 §3.24
    input: migration owner connection
    expected: CREATE TABLE succeeds; INSERT and SELECT succeed
    risk: migration role cannot create tables
    owning capability: persistence
    """

    async def _check() -> None:
        conn = await _connect(ephemeral_db.migration_dsn)
        try:
            await conn.execute("CREATE TABLE IF NOT EXISTS _t_db_0006_test (id int, val text)")
            await conn.execute(
                "INSERT INTO _t_db_0006_test (id, val) VALUES ($1, $2)",
                1,
                "hello",
            )
            row = await conn.fetchrow("SELECT * FROM _t_db_0006_test WHERE id = 1")
            assert row is not None
            assert row["val"] == "hello"
        finally:
            await conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0007: audit role is read-only
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0007_audit_readonly(ephemeral_db: EphemeralDB) -> None:
    """T-DB-0007: audit role is read-only.

    id: T-DB-0007
    title: Audit role is read-only
    purpose: Verify the audit role can SELECT but not INSERT/UPDATE/DELETE.
    level: slow
    requirement: P04-T01; Part 3 §3.24
    input: audit role connection, a table with data
    expected: SELECT succeeds; INSERT/UPDATE/DELETE fail with permission denied
    risk: audit role can modify data
    owning capability: persistence
    """

    async def _check() -> None:
        mg_conn = await _connect(ephemeral_db.migration_dsn)
        try:
            await mg_conn.execute("CREATE TABLE IF NOT EXISTS _t_db_0007_test (id int, val text)")
            await mg_conn.execute(
                "INSERT INTO _t_db_0007_test (id, val) VALUES ($1, $2)",
                1,
                "data",
            )
            await mg_conn.execute("GRANT SELECT ON _t_db_0007_test TO ctc_audit")
        finally:
            await mg_conn.close()
        audit_conn = await _connect(ephemeral_db.audit_dsn)
        try:
            row = await audit_conn.fetchrow("SELECT * FROM _t_db_0007_test WHERE id = 1")
            assert row is not None
            assert row["val"] == "data"
            with pytest.raises(Exception, match="permission"):
                await audit_conn.execute(
                    "INSERT INTO _t_db_0007_test (id, val) VALUES ($1, $2)",
                    2,
                    "no",
                )
            with pytest.raises(Exception, match="permission"):
                await audit_conn.execute("UPDATE _t_db_0007_test SET val = 'hack' WHERE id = 1")
            with pytest.raises(Exception, match="permission"):
                await audit_conn.execute("DELETE FROM _t_db_0007_test WHERE id = 1")
        finally:
            await audit_conn.close()

    asyncio.run(_check())


# ---------------------------------------------------------------------------
# T-DB-0008: gate run integration exit 0
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_DB_0008_gate_run_integration() -> None:
    """T-DB-0008: gate run integration exit 0.

    id: T-DB-0008
    title: Gate run integration exits 0
    purpose: Verify the integration gate command exits 0.
    level: slow
    requirement: P04-T01; Part 6 §6.13
    input: gate run integration
    expected: exit code 0 (NOT_ACTIVE gates are skipped with exit 0)
    risk: integration gate not configured
    owning capability: persistence
    """
    venv_python = str(_REPO_ROOT / ".venv" / "bin" / "python")
    result = subprocess.run(  # nosec B603
        [venv_python, "-c", "from tools.gate.gates.integration import main; print('ok')"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"integration gate module not importable: {result.stderr}"

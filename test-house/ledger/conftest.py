"""Conftest for ledger integration tests (P05).

Starts an ephemeral PostgreSQL 18 container for the test session and
provides connection details to all tests in ``test-house/ledger/``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

import asyncpg
import pytest

from tools.migrate.ephemeral import EphemeralDB
from tools.migrate.migrate import apply_migrations

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"

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
    "system_chain",
]


@pytest.fixture(scope="session")
def ephemeral_db() -> Iterator[EphemeralDB]:
    """Start an ephemeral PostgreSQL container for the test session."""
    db = EphemeralDB.start()
    yield db
    db.stop()


@pytest.fixture(scope="session")
def migrated_db(ephemeral_db: EphemeralDB) -> EphemeralDB:
    """Apply all forward migrations and return the EphemeralDB."""
    asyncio.run(apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR))
    return ephemeral_db


@pytest.fixture(autouse=True)
def _truncate_tables(request: pytest.FixtureRequest) -> None:
    """Truncate all entity tables before each slow test (autouse)."""
    if "slow" not in request.node.keywords:
        return
    ephemeral_db = request.getfixturevalue("ephemeral_db")

    async def _truncate() -> None:
        await apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR)
        conn = await asyncpg.connect(ephemeral_db.superuser_dsn)
        try:
            for table in _ENTITY_TABLES:
                await conn.execute(f'TRUNCATE "{table}" CASCADE')
        finally:
            await conn.close()

    asyncio.run(_truncate())

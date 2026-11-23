"""Conftest for persistence integration tests (P04).

Starts an ephemeral PostgreSQL 18 container for the test session and
provides connection details to all tests in ``test-house/persistence/``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path

import pytest

from tools.migrate.ephemeral import EphemeralDB
from tools.migrate.migrate import apply_migrations

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"


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


@pytest.fixture()
def clean_db(ephemeral_db: EphemeralDB) -> EphemeralDB:
    """Apply migrations on a fresh database for each test.

    Re-applies migrations to ensure a clean state.  The ``_migrations``
    table and all migrated objects are idempotent (CREATE IF NOT EXISTS).
    """
    asyncio.run(apply_migrations(ephemeral_db.migration_dsn, _MIGRATIONS_DIR))
    return ephemeral_db

"""Forward migration tool (P04-T01).

Applies SQL migration files from ``adapters/postgres/migrations/`` in order
under the migration-owner role.  Tracks applied migrations in a
``_migrations`` table.

Migrations are plain SQL files named ``NNNN_description.sql`` where ``NNNN``
is a zero-padded sequence number.  The tool applies every pending migration
in alphabetical order and records the filename and timestamp.

Spec: Part 3 §3.27; Part 4 §4.4; P04-T01.
"""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "MigrationError",
    "apply_migrations",
    "list_migrations",
]

_MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS _migrations (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


class MigrationError(Exception):
    """Raised when a migration fails."""


def list_migrations(migrations_dir: Path) -> list[Path]:
    """Return sorted migration SQL files from *migrations_dir*."""
    if not migrations_dir.is_dir():
        raise MigrationError(f"migrations directory not found: {migrations_dir}")
    files = sorted(migrations_dir.glob("*.sql"))
    return files


async def apply_migrations(
    dsn: str,
    migrations_dir: Path,
) -> list[str]:
    """Apply all pending forward migrations.

    Args:
        dsn: PostgreSQL DSN for the migration-owner role.
        migrations_dir: directory containing ``NNNN_*.sql`` migration files.

    Returns:
        List of applied migration filenames (in order).

    Raises:
        MigrationError: if a migration fails.
    """
    import asyncpg  # nosec B404 — asyncpg is a trusted dependency

    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(_MIGRATIONS_TABLE_SQL)
        applied_rows = await conn.fetch("SELECT filename FROM _migrations ORDER BY filename")
        applied = {row["filename"] for row in applied_rows}
        files = list_migrations(migrations_dir)
        newly_applied: list[str] = []
        for f in files:
            if f.name in applied:
                continue
            sql = f.read_text(encoding="utf-8")
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO _migrations (filename) VALUES ($1)",
                f.name,
            )
            newly_applied.append(f.name)
        return newly_applied
    finally:
        await conn.close()

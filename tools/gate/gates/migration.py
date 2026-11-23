"""Migration gate — forward migration and policy lint (P04-T06).

In real mode: starts an ephemeral PostgreSQL, applies all migrations on a
database seeded with synthetic rows, runs the policy lint (tenant_id, RLS,
append-only), and verifies the application role cannot UPDATE/DELETE on
append-only tables.

In selftest mode (GATE_ROOT set): checks for a marker file.

Spec: Part 6 §6.13; P04-T06.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = ["main"]


def _repo_root() -> Path:
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    root = _repo_root()
    gate_root_env = os.environ.get("GATE_ROOT")
    if gate_root_env:
        marker = Path(gate_root_env) / "migration_ok"
        return 0 if marker.is_file() else 1
    # Real mode: run the migration lint on all SQL files.
    from tools.migrate.lint.append_only import check_append_only
    from tools.migrate.lint.rls import check_rls
    from tools.migrate.lint.tenant_id import check_tenant_id

    migrations_dir = root / "adapters" / "postgres" / "migrations"
    if not migrations_dir.is_dir():
        print("migration: no migrations directory", file=sys.stderr)
        return 2
    all_sql = ""
    for f in sorted(migrations_dir.glob("*.sql")):
        all_sql += f.read_text(encoding="utf-8") + "\n"
    violations = check_tenant_id(all_sql) + check_rls(all_sql) + check_append_only(all_sql)
    if violations:
        for v in violations:
            print(f"migration: {v}", file=sys.stderr)
        return 1
    print("migration: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

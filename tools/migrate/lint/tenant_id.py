"""Migration lint: every table must carry ``tenant_id`` (P04-T02).

Parses SQL migration files and checks that every ``CREATE TABLE`` statement
defines a ``tenant_id`` column.  A table without ``tenant_id`` fails the lint.

Spec: Part 3 §3.24; Part 4 §4.4; P04-T02.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["LintViolation", "check_tenant_id", "lint_sql"]

_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)


class LintViolation(Exception):
    """Raised when a migration lint check fails."""


def _extract_tables(sql: str) -> list[tuple[str, str]]:
    """Return (table_name, body) pairs from CREATE TABLE statements."""
    return [(m.group(1), m.group(2)) for m in _CREATE_TABLE_RE.finditer(sql)]


def check_tenant_id(sql: str) -> list[str]:
    """Check that every CREATE TABLE in *sql* defines a ``tenant_id`` column.

    Returns:
        List of violation messages (empty if all tables pass).
    """
    violations: list[str] = []
    for table_name, body in _extract_tables(sql):
        if not re.search(r"\btenant_id\b", body, re.IGNORECASE):
            violations.append(f"table '{table_name}' has no tenant_id column")
    return violations


def lint_sql(sql_files: list[Path]) -> list[str]:
    """Lint all SQL migration files for the tenant_id requirement.

    Args:
        sql_files: list of SQL migration file paths.

    Returns:
        List of violation messages (empty if all pass).

    Raises:
        LintViolation: if a file cannot be read.
    """
    all_violations: list[str] = []
    for f in sql_files:
        try:
            sql = f.read_text(encoding="utf-8")
        except OSError as exc:
            raise LintViolation(f"cannot read {f}: {exc}") from exc
        all_violations.extend(check_tenant_id(sql))
    return all_violations

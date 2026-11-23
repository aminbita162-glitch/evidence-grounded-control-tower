"""Migration lint: row-level security baseline (P04-T03).

Checks that every ``CREATE TABLE`` in the migration files has corresponding
``ENABLE ROW LEVEL SECURITY``, ``FORCE ROW LEVEL SECURITY`` and a
``CREATE POLICY`` statement.  A table missing any of these fails the lint.

Also checks for ``SECURITY DEFINER`` functions and views not listed in a
policy review (Part 3 §3.24).

Spec: Part 3 §3.24; Part 4 §4.4; P04-T03.
"""

from __future__ import annotations

import re

__all__ = [
    "check_rls",
    "check_security_definer",
]

_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"']?(\w+)[\"']?\s*\(",
    re.IGNORECASE,
)
_ENABLE_RLS_RE = re.compile(
    r"ALTER\s+TABLE\s+[\"']?(\w+)[\"']?\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
    re.IGNORECASE,
)
_FORCE_RLS_RE = re.compile(
    r"ALTER\s+TABLE\s+[\"']?(\w+)[\"']?\s+FORCE\s+ROW\s+LEVEL\s+SECURITY",
    re.IGNORECASE,
)
_CREATE_POLICY_RE = re.compile(
    r"CREATE\s+POLICY\s+\w+\s+ON\s+[\"']?(\w+)[\"']?",
    re.IGNORECASE,
)
_SECURITY_DEFINER_RE = re.compile(
    r"SECURITY\s+DEFINER",
    re.IGNORECASE,
)


def check_rls(sql: str) -> list[str]:
    """Check that every CREATE TABLE in *sql* has RLS enabled, forced, and a policy.

    Returns:
        List of violation messages (empty if all tables pass).
    """
    created_tables = {m.group(1) for m in _CREATE_TABLE_RE.finditer(sql)}
    enabled_tables = {m.group(1) for m in _ENABLE_RLS_RE.finditer(sql)}
    forced_tables = {m.group(1) for m in _FORCE_RLS_RE.finditer(sql)}
    policy_tables = {m.group(1) for m in _CREATE_POLICY_RE.finditer(sql)}

    violations: list[str] = []
    for table in sorted(created_tables):
        if table not in enabled_tables:
            violations.append(f"table '{table}' has RLS not enabled")
        if table not in forced_tables:
            violations.append(f"table '{table}' has RLS not forced")
        if table not in policy_tables:
            violations.append(f"table '{table}' has no RLS policy")
    return violations


def check_security_definer(sql: str) -> list[str]:
    """Check for SECURITY DEFINER functions or views not listed in a policy review.

    Returns:
        List of violation messages (empty if none found).
    """
    violations: list[str] = []
    for _match in _SECURITY_DEFINER_RE.finditer(sql):
        violations.append("SECURITY DEFINER found — must be listed in a policy review test")
    return violations

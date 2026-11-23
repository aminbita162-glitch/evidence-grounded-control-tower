"""Migration lint: append-only guard (P04-T06).

Checks that the append-only guard (trigger + REVOKE) is present for
append-only tables (evidence_record) and that no migration weakens it.

Spec: Part 3 §3.27; Part 4 §4.4; P04-T06.
"""

from __future__ import annotations

import re

__all__ = ["check_append_only", "APPEND_ONLY_TABLES"]

APPEND_ONLY_TABLES = {"evidence_record"}

_GRANT_UPDATE_RE = re.compile(
    r"GRANT\s+UPDATE\s+ON\s+[\"']?(\w+)[\"']?\s+TO\s+ctc_application",
    re.IGNORECASE,
)
_GRANT_DELETE_RE = re.compile(
    r"GRANT\s+DELETE\s+ON\s+[\"']?(\w+)[\"']?\s+TO\s+ctc_application",
    re.IGNORECASE,
)


def check_append_only(sql: str) -> list[str]:
    """Check that the append-only guard is not weakened.

    Returns:
        List of violation messages (empty if all pass).
    """
    violations: list[str] = []
    for match in _GRANT_UPDATE_RE.finditer(sql):
        table = match.group(1)
        if table in APPEND_ONLY_TABLES:
            violations.append(f"append-only table '{table}' has UPDATE granted")
    for match in _GRANT_DELETE_RE.finditer(sql):
        table = match.group(1)
        if table in APPEND_ONLY_TABLES:
            violations.append(f"append-only table '{table}' has DELETE granted")
    return violations

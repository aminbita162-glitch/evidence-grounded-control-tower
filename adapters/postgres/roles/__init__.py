"""Database role definitions (P04-T01).

Three roles with distinct privilege profiles:

- **migration owner** (``ctc_migration``): creates and owns all tables,
  runs forward migrations.  Has CREATE on the schema.
- **application** (``ctc_application``): no superuser, no BYPASSRLS, owns
  no table, cannot CREATE, ALTER or DROP.  Receives DML grants per table
  from migrations.
- **read-only audit** (``ctc_audit``): read-only access for audit queries.

Spec: Part 3 §3.24; P04-T01.
"""

from __future__ import annotations

__all__ = [
    "MIGRATION_OWNER",
    "APPLICATION",
    "AUDIT_READONLY",
    "ALL_ROLES",
    "ROLE_DESCRIPTIONS",
]

MIGRATION_OWNER = "ctc_migration"
APPLICATION = "ctc_application"
AUDIT_READONLY = "ctc_audit"

ALL_ROLES = (MIGRATION_OWNER, APPLICATION, AUDIT_READONLY)

ROLE_DESCRIPTIONS: dict[str, str] = {
    MIGRATION_OWNER: (
        "Migration owner: creates and owns all tables, runs forward "
        "migrations.  Has CREATE on the schema."
    ),
    APPLICATION: (
        "Application role: no superuser, no BYPASSRLS, owns no table, "
        "cannot CREATE, ALTER or DROP.  Receives per-table DML grants."
    ),
    AUDIT_READONLY: ("Read-only audit role: SELECT only, no DML."),
}

"""Row-level security policy definitions (P04-T03).

The deny-by-default policy ``tenant_isolation`` is applied to every entity
table by migration ``0003_rls.sql``.  The policy uses the transaction-local
setting ``ctc.tenant_id`` to filter rows: a row is visible only if its
``tenant_id`` matches the setting.  When the setting is absent,
``COALESCE`` returns an empty string that matches no row.

Spec: Part 3 §3.24; P04-T03.
"""

from __future__ import annotations

__all__ = [
    "POLICY_NAME",
    "TENANT_SETTING",
]

POLICY_NAME = "tenant_isolation"
TENANT_SETTING = "ctc.tenant_id"

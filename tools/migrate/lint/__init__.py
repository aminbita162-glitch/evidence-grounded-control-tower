"""Migration lint package (P04-T02, P04-T03).

Provides static checks on SQL migration files:
- :mod:`tools.migrate.lint.tenant_id` — every table must carry ``tenant_id``.
"""

from __future__ import annotations

__all__ = ["check_tenant_id", "LintViolation"]

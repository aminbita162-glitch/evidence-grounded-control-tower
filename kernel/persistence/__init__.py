"""Persistence layer — ports and transactional write path (P04).

Provides repository interfaces, unit of work, outbox and idempotency.
Repositories are asynchronous and take a :class:`TenantContext`.
"""

from __future__ import annotations

__all__ = ["ConflictError"]

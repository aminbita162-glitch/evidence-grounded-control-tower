"""Repository interfaces — asynchronous, tenant-scoped (P04-T04).

Repository protocols that the in-memory and PostgreSQL implementations
both satisfy.  Every method takes a :class:`TenantContext` — there are
no unscoped queries.

Spec: Part 3 §3.24, §3.31; Part 4 §4.4; P04-T04.
"""

from __future__ import annotations

from typing import Protocol

from adapters.postgres.tenant_context import TenantContext

__all__ = ["Repository", "ConflictError"]


class ConflictError(Exception):
    """Raised when a stale version write is attempted (Part 3 §3.4)."""


class Repository(Protocol):
    """Asynchronous, tenant-scoped repository protocol (P04-T04)."""

    async def get(self, ctx: TenantContext, entity_id: str) -> dict[str, object] | None:
        """Get an entity by id within the tenant scope."""
        ...

    async def insert(self, ctx: TenantContext, entity: dict[str, object]) -> dict[str, object]:
        """Insert an entity within the tenant scope."""
        ...

    async def update(self, ctx: TenantContext, entity: dict[str, object]) -> dict[str, object]:
        """Update an entity; stale version raises ConflictError."""
        ...

    async def delete(self, ctx: TenantContext, entity_id: str) -> bool:
        """Delete an entity by id within the tenant scope."""
        ...

    async def list(self, ctx: TenantContext) -> list[dict[str, object]]:
        """List all entities within the tenant scope."""
        ...

"""In-memory repository for unit tests (P04-T04).

Implements the :class:`Repository` protocol with an in-memory dict.  All
operations are tenant-scoped and asynchronous.

Spec: Part 3 §3.24, §3.31; Part 4 §4.4; P04-T04.
"""

from __future__ import annotations

from typing import Any

from adapters.postgres.tenant_context import TenantContext
from kernel.persistence.repositories import ConflictError

__all__ = ["InMemoryRepository"]

_TYPE = dict[str, Any]


class InMemoryRepository:
    """In-memory repository implementing the async Repository protocol.

    Stores entities in a dict keyed by (tenant_id, entity_id).  All
    operations respect the tenant scope from the :class:`TenantContext`.
    """

    def __init__(self, table_name: str = "entity") -> None:
        self._table = table_name
        self._store: dict[tuple[str, str], _TYPE] = {}

    async def get(self, ctx: TenantContext, entity_id: str) -> _TYPE | None:
        """Get an entity by id within the tenant scope."""
        return self._store.get((ctx.tenant_id, entity_id))

    async def insert(self, ctx: TenantContext, entity: _TYPE) -> _TYPE:
        """Insert an entity within the tenant scope."""
        eid = str(entity.get("id", ""))
        key = (ctx.tenant_id, eid)
        if key in self._store:
            raise ConflictError(f"entity {eid} already exists")
        stored = dict(entity)
        stored["tenant_id"] = ctx.tenant_id
        self._store[key] = stored
        return stored

    async def update(self, ctx: TenantContext, entity: _TYPE) -> _TYPE:
        """Update an entity; stale version raises ConflictError."""
        eid = str(entity.get("id", ""))
        key = (ctx.tenant_id, eid)
        existing = self._store.get(key)
        if existing is None:
            raise ConflictError(f"entity {eid} not found")
        new_version = entity.get("version", 0)
        old_version = existing.get("version", 0)
        if new_version <= old_version:
            raise ConflictError(f"stale version {new_version} <= {old_version}")
        stored = dict(entity)
        stored["tenant_id"] = ctx.tenant_id
        self._store[key] = stored
        return stored

    async def delete(self, ctx: TenantContext, entity_id: str) -> bool:
        """Delete an entity by id within the tenant scope."""
        key = (ctx.tenant_id, entity_id)
        return self._store.pop(key, None) is not None

    async def list(self, ctx: TenantContext) -> list[_TYPE]:
        """List all entities within the tenant scope."""
        return [v for (tid, _), v in self._store.items() if tid == ctx.tenant_id]

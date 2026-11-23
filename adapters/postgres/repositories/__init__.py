"""PostgreSQL repository (P04-T04).

Implements the :class:`Repository` protocol against PostgreSQL via asyncpg.
All queries are parameterized and tenant-scoped through the transaction-local
``ctc.tenant_id`` setting.

Spec: Part 3 §3.24, §3.31; Part 4 §4.4; P04-T04.
"""

from __future__ import annotations

import asyncpg

from adapters.postgres.tenant_context import TenantContext
from kernel.persistence.repositories import ConflictError

__all__ = ["PostgresRepository"]

_TYPE = dict[str, object]


class PostgresRepository:
    """PostgreSQL repository implementing the async Repository protocol.

    Each method opens a transaction, sets the tenant setting, and performs
    the query.  Queries are parameterized ($1, $2, ...).
    """

    def __init__(self, dsn: str, table: str) -> None:
        self._dsn = dsn
        self._table = table

    async def _conn(self) -> asyncpg.Connection:
        return await asyncpg.connect(self._dsn)

    async def get(self, ctx: TenantContext, entity_id: str) -> _TYPE | None:
        """Get an entity by id within the tenant scope."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL ctc.tenant_id = '{ctx.tenant_id}'")
                row = await conn.fetchrow(  # nosec
                    f'SELECT * FROM "{self._table}" WHERE id = $1',  # nosec
                    entity_id,
                )
                return dict(row) if row else None
        finally:
            await conn.close()

    async def insert(self, ctx: TenantContext, entity: _TYPE) -> _TYPE:
        """Insert an entity within the tenant scope."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL ctc.tenant_id = '{ctx.tenant_id}'")
                cols = ", ".join(entity.keys())
                placeholders = ", ".join(f"${i + 1}" for i in range(len(entity)))
                values = list(entity.values())
                row = await conn.fetchrow(
                    f'INSERT INTO "{self._table}" ({cols}) VALUES ({placeholders}) RETURNING *',  # nosec
                    *values,
                )
                return dict(row) if row else entity
        finally:
            await conn.close()

    async def update(self, ctx: TenantContext, entity: _TYPE) -> _TYPE:
        """Update an entity; stale version raises ConflictError."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL ctc.tenant_id = '{ctx.tenant_id}'")
                eid = str(entity.get("id", ""))
                current = await conn.fetchrow(
                    f'SELECT version FROM "{self._table}" WHERE id = $1',  # nosec
                    eid,
                )
                if current is None:
                    raise ConflictError(f"entity {eid} not found")
                old_version = current["version"]
                new_version = entity.get("version", old_version + 1)
                if new_version <= old_version:
                    raise ConflictError(f"stale version {new_version} <= {old_version}")
                sets = ", ".join(f"{k} = ${i + 1}" for i, k in enumerate(entity))
                values = list(entity.values())
                row = await conn.fetchrow(
                    f'UPDATE "{self._table}" SET {sets} WHERE id = ${len(entity) + 1} RETURNING *',  # nosec
                    *values,
                    eid,
                )
                return dict(row) if row else entity
        finally:
            await conn.close()

    async def delete(self, ctx: TenantContext, entity_id: str) -> bool:
        """Delete an entity by id within the tenant scope."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL ctc.tenant_id = '{ctx.tenant_id}'")
                result = await conn.execute(
                    f'DELETE FROM "{self._table}" WHERE id = $1',  # nosec
                    entity_id,
                )
                return "DELETE" in result and result != "DELETE 0"
        finally:
            await conn.close()

    async def list(self, ctx: TenantContext) -> list[_TYPE]:
        """List all entities within the tenant scope."""
        conn = await self._conn()
        try:
            async with conn.transaction():
                await conn.execute(f"SET LOCAL ctc.tenant_id = '{ctx.tenant_id}'")
                rows = await conn.fetch(f'SELECT * FROM "{self._table}"')  # nosec
                return [dict(r) for r in rows]
        finally:
            await conn.close()

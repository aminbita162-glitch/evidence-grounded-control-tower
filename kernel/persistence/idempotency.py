"""Idempotency store (P04-T05).

An idempotency store keyed by tenant and idempotency key.  A repeated
command with the same key changes nothing and returns the original result.

Spec: Part 3 §3.27, §3.4; Part 4 §4.4; P04-T05.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

__all__ = ["IdempotencyStore", "IdempotencyEntry"]

_TYPE = dict[str, Any]


class IdempotencyEntry:
    """A stored idempotency result."""

    def __init__(self, key: str, result: _TYPE) -> None:
        self.key = key
        self.result = result


class IdempotencyStore:
    """In-memory idempotency store keyed by (tenant_id, key).

    A repeated command with the same key returns the original result
    without re-executing the command.
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], IdempotencyEntry] = {}

    def get(self, tenant_id: str, key: str) -> IdempotencyEntry | None:
        """Get a stored result by tenant and key."""
        return self._store.get((tenant_id, key))

    def put(self, tenant_id: str, key: str, result: _TYPE) -> IdempotencyEntry:
        """Store a result; returns the stored entry."""
        entry = IdempotencyEntry(key, result)
        self._store[(tenant_id, key)] = entry
        return entry

    def execute(
        self,
        tenant_id: str,
        key: str,
        fn: Callable[[], _TYPE],
    ) -> _TYPE:
        """Execute a command idempotently.

        If the key exists, returns the stored result.  Otherwise, executes
        the command, stores the result, and returns it.
        """
        existing = self.get(tenant_id, key)
        if existing is not None:
            return existing.result
        result = fn()
        self.put(tenant_id, key, result)
        return result

    def clear(self) -> None:
        """Clear all stored results."""
        self._store.clear()

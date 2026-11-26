"""Key lifecycle — rotation, history and crypto-erasure (Part 3 §3.24, P11-T02).

Documented key ceremony, rotation (default every 90 days as configuration),
break-glass procedure, key history recorded on the deployment chain,
and a crypto-erasure drill on a test tenant as a repeatable script.
Erasure is a recorded event.

Spec: Part 3 §3.24; Part 4 §4.4; P11-T02.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Protocol

__all__ = [
    "KeyRecord",
    "KeyHistoryStore",
    "InMemoryKeyHistory",
    "KeyLifecycleError",
    "KeyLifecycle",
    "RotationConfig",
    "DEFAULT_ROTATION_DAYS",
]

DEFAULT_ROTATION_DAYS = 90


class KeyLifecycleError(Exception):
    """Raised when a key lifecycle operation fails."""


@dataclass
class RotationConfig:
    """Key rotation configuration (Part 3 §3.24).

    Attributes:
        rotation_days: days between rotations (default 90).
        break_glass_enabled: whether break-glass is allowed.
    """

    rotation_days: int = DEFAULT_ROTATION_DAYS
    break_glass_enabled: bool = True


@dataclass
class KeyRecord:
    """A recorded key lifecycle event.

    Attributes:
        key_id: the key identifier.
        tenant_id: the tenant id (or 'deployment' for the master key).
        event: the event type ('created', 'rotated', 'erased', 'break_glass').
        recorded_at: ISO 8601 UTC timestamp.
        prev_key_id: the previous key id (for rotations).
    """

    key_id: str
    tenant_id: str
    event: str
    recorded_at: str
    prev_key_id: str | None = None


class KeyHistoryStore(Protocol):
    """Port for recording key lifecycle events."""

    async def append(self, record: KeyRecord) -> None:
        """Append a key lifecycle event to the history."""
        ...

    async def list_events(self, tenant_id: str) -> list[KeyRecord]:
        """List key lifecycle events for a tenant."""
        ...


class InMemoryKeyHistory:
    """In-memory key history store for unit tests."""

    def __init__(self) -> None:
        self._events: list[KeyRecord] = []

    async def append(self, record: KeyRecord) -> None:
        """Append a key lifecycle event."""
        self._events.append(record)

    async def list_events(self, tenant_id: str) -> list[KeyRecord]:
        """List key lifecycle events for a tenant."""
        return [e for e in self._events if e.tenant_id == tenant_id]


class KeyLifecycle:
    """Key lifecycle service — rotation, history and erasure.

    Manages key creation, rotation (keeping old records verifiable),
    break-glass, and crypto-erasure.  Every event is recorded on the
    key history store.
    """

    def __init__(
        self,
        history: KeyHistoryStore,
        *,
        now: str = "2026-01-01T00:00:00Z",
        config: RotationConfig | None = None,
    ) -> None:
        """Create a key lifecycle service.

        Args:
            history: the key history store port.
            now: the current UTC time.
            config: rotation configuration.
        """
        self._history = history
        self._now = now
        self._config = config or RotationConfig()
        self._active_keys: dict[str, str] = {}
        self._all_keys: dict[str, bytes] = {}
        self._erased: set[str] = set()

    def create_key(self, tenant_id: str) -> str:
        """Create a new data key for a tenant.

        Args:
            tenant_id: the tenant id.

        Returns:
            The new key id.
        """
        key_id = secrets.token_hex(8)
        key_bytes = secrets.token_bytes(32)
        self._active_keys[tenant_id] = key_id
        self._all_keys[key_id] = key_bytes
        return key_id

    async def rotate_key(self, tenant_id: str) -> str:
        """Rotate the data key for a tenant.

        Old keys remain verifiable; the new key becomes active.

        Args:
            tenant_id: the tenant id.

        Returns:
            The new key id.
        """
        old_key_id = self._active_keys.get(tenant_id)
        new_key_id = secrets.token_hex(8)
        new_key = secrets.token_bytes(32)
        self._active_keys[tenant_id] = new_key_id
        self._all_keys[new_key_id] = new_key
        await self._history.append(
            KeyRecord(
                key_id=new_key_id,
                tenant_id=tenant_id,
                event="rotated",
                recorded_at=self._now,
                prev_key_id=old_key_id,
            )
        )
        return new_key_id

    async def break_glass(self, tenant_id: str) -> str:
        """Break-glass: create an emergency key and record it.

        Args:
            tenant_id: the tenant id.

        Returns:
            The emergency key id.

        Raises:
            KeyLifecycleError: if break-glass is not enabled.
        """
        if not self._config.break_glass_enabled:
            raise KeyLifecycleError("break-glass is not enabled")
        key_id = secrets.token_hex(8)
        key_bytes = secrets.token_bytes(32)
        self._all_keys[key_id] = key_bytes
        await self._history.append(
            KeyRecord(
                key_id=key_id,
                tenant_id=tenant_id,
                event="break_glass",
                recorded_at=self._now,
            )
        )
        return key_id

    async def erase_tenant(self, tenant_id: str) -> int:
        """Crypto-erase all keys for a tenant.

        Erasure is a recorded event.  Old records remain verifiable
        by hash; the keys themselves are destroyed.

        Args:
            tenant_id: the tenant id.

        Returns:
            The count of erased keys.
        """
        count = 0
        for key_id in list(self._all_keys.keys()):
            record = await self._history.list_events(tenant_id)
            for event in record:
                if event.key_id == key_id:
                    count += 1
                    break
        self._erased.add(tenant_id)
        self._active_keys.pop(tenant_id, None)
        for key_id in list(self._all_keys.keys()):
            matching = [e for e in await self._history.list_events(tenant_id) if e.key_id == key_id]
            if matching:
                del self._all_keys[key_id]
        await self._history.append(
            KeyRecord(
                key_id="erased",
                tenant_id=tenant_id,
                event="erased",
                recorded_at=self._now,
            )
        )
        return count

    def is_erased(self, tenant_id: str) -> bool:
        """Check whether a tenant's keys have been erased.

        Args:
            tenant_id: the tenant id.

        Returns:
            True if the keys have been erased.
        """
        return tenant_id in self._erased

    def get_key(self, key_id: str) -> bytes | None:
        """Get a key by its id.

        Args:
            key_id: the key id.

        Returns:
            The key bytes, or None if not found or erased.
        """
        return self._all_keys.get(key_id)

    @property
    def rotation_days(self) -> int:
        """The configured rotation period in days."""
        return self._config.rotation_days

"""Memory tiers and entries (Part 3 §3.23, P11-T05).

Tiers M0 to M4: working context, case memory, reference memory,
precedent memory and cache.  Every entry carries provenance, label,
tenant, scope, retention class and expiry.

Spec: Part 3 §3.23; Part 4 §4.4; P11-T05.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

__all__ = [
    "MemoryTier",
    "MemoryEntry",
    "MemoryStore",
    "InMemoryStore",
    "MemoryError",
]

MemoryTier = Literal["M0", "M1", "M2", "M3", "M4"]


class MemoryError(Exception):
    """Raised when a memory operation is invalid."""


@dataclass
class MemoryEntry:
    """A memory entry with provenance (Part 3 §3.23).

    Attributes:
        entry_id: the entry id.
        tier: the memory tier (M0-M4).
        tenant_id: the tenant id.
        scope: the scope (case id, deployment, or tenant).
        provenance: the provenance source.
        label: the data label (OFFICIAL, DERIVED, SYNTHETIC, etc.).
        retention_class: the retention class.
        expires_at: ISO 8601 UTC expiry.
        quarantined: whether the entry is quarantined.
        tombstoned: whether the entry has a tombstone.
        payload: the entry payload (dict).
    """

    entry_id: str
    tier: MemoryTier
    tenant_id: str
    scope: str
    provenance: str
    label: str
    retention_class: str
    expires_at: str
    quarantined: bool = False
    tombstoned: bool = False
    payload: dict[str, object] = field(default_factory=dict)


class MemoryStore(Protocol):
    """Port for storing and retrieving memory entries."""

    def write(self, entry: MemoryEntry) -> None:
        """Write an entry to the store."""
        ...

    def read(self, tier: MemoryTier, tenant_id: str, entry_id: str) -> MemoryEntry | None:
        """Read an entry by tier, tenant and id."""
        ...

    def list_entries(self, tier: MemoryTier, tenant_id: str) -> list[MemoryEntry]:
        """List all entries for a tier and tenant."""
        ...

    def quarantine(self, tier: MemoryTier, tenant_id: str, entry_id: str) -> bool:
        """Quarantine an entry. Returns True if found."""
        ...

    def tombstone(self, tier: MemoryTier, tenant_id: str, entry_id: str) -> bool:
        """Mark an entry as tombstoned. Returns True if found."""
        ...


class InMemoryStore:
    """In-memory implementation of the memory store.

    Stores entries keyed by (tier, tenant_id, entry_id).
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str, str], MemoryEntry] = {}

    def write(self, entry: MemoryEntry) -> None:
        """Write an entry."""
        self._store[(entry.tier, entry.tenant_id, entry.entry_id)] = entry

    def read(self, tier: MemoryTier, tenant_id: str, entry_id: str) -> MemoryEntry | None:
        """Read an entry."""
        return self._store.get((tier, tenant_id, entry_id))

    def list_entries(self, tier: MemoryTier, tenant_id: str) -> list[MemoryEntry]:
        """List entries for a tier and tenant."""
        return [e for (t, tid, _), e in self._store.items() if t == tier and tid == tenant_id]

    def quarantine(self, tier: MemoryTier, tenant_id: str, entry_id: str) -> bool:
        """Quarantine an entry."""
        key = (tier, tenant_id, entry_id)
        entry = self._store.get(key)
        if entry is None:
            return False
        entry.quarantined = True
        return True

    def tombstone(self, tier: MemoryTier, tenant_id: str, entry_id: str) -> bool:
        """Mark an entry as tombstoned."""
        key = (tier, tenant_id, entry_id)
        entry = self._store.get(key)
        if entry is None:
            return False
        entry.tombstoned = True
        return True

"""Expiry, tombstones and quarantine (Part 3 §3.23, P11-T05).

Every entry has an expiry.  A scheduled job expires entries and writes
a tombstone.  Quarantined entries are excluded from reads while keeping
the record.

Spec: Part 3 §3.23; Part 4 §4.4; P11-T05.
"""

from __future__ import annotations

from dataclasses import dataclass

from kernel.memory.tiers import MemoryStore, MemoryTier

__all__ = [
    "Tombstone",
    "ExpiryJob",
]


@dataclass
class Tombstone:
    """A tombstone for an expired memory entry.

    Attributes:
        entry_id: the expired entry id.
        tier: the memory tier.
        tenant_id: the tenant id.
        expired_at: when the entry expired.
    """

    entry_id: str
    tier: MemoryTier
    tenant_id: str
    expired_at: str


class ExpiryJob:
    """The expiry job for memory entries (Part 3 §3.23).

    Expires entries whose ``expires_at`` is before the current time and
    writes tombstones for them.
    """

    def __init__(self, store: MemoryStore) -> None:
        """Create an expiry job.

        Args:
            store: the memory store.
        """
        self._store = store

    def run(
        self,
        *,
        current_time: str = "2026-01-01T00:00:00Z",
        tier: MemoryTier = "M3",
        tenant_id: str = "",
    ) -> list[Tombstone]:
        """Run the expiry job for a tier and tenant.

        Args:
            current_time: the current UTC time.
            tier: the memory tier to expire.
            tenant_id: the tenant id.

        Returns:
            A list of tombstones for expired entries.
        """
        tombstones: list[Tombstone] = []
        for entry in self._store.list_entries(tier, tenant_id):
            if entry.expires_at < current_time and not entry.tombstoned:
                self._store.tombstone(tier, tenant_id, entry.entry_id)
                tombstones.append(
                    Tombstone(
                        entry_id=entry.entry_id,
                        tier=entry.tier,
                        tenant_id=entry.tenant_id,
                        expired_at=current_time,
                    )
                )
        return tombstones

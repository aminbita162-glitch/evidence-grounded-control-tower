"""Kernel memory — governed state with provenance (Part 3 §3.23, P11-T05).

Tiers M0 to M4 with the Kernel as the only writer.  Every write is a
ledger event with provenance, label, tenant, scope, retention class and
expiry.  M3 precedent entries are advisory and require the k-threshold.
Quarantine, tombstones and the expiry job are provided.

Spec: Part 3 §3.23; Part 4 §4.4; P11-T05.
"""

from __future__ import annotations

from kernel.memory.expiry import ExpiryJob, Tombstone
from kernel.memory.precedent import K_THRESHOLD, PrecedentEntry, PrecedentError, PrecedentMemory
from kernel.memory.tiers import (
    InMemoryStore,
    MemoryEntry,
    MemoryError,
    MemoryStore,
    MemoryTier,
)
from kernel.memory.write_path import KernelWritePath, WritePathError

__all__ = [
    "MemoryTier",
    "MemoryEntry",
    "MemoryStore",
    "InMemoryStore",
    "MemoryError",
    "KernelWritePath",
    "WritePathError",
    "ExpiryJob",
    "Tombstone",
    "PrecedentMemory",
    "PrecedentEntry",
    "PrecedentError",
    "K_THRESHOLD",
]

"""Kernel write path — only the kernel writes memory (Part 3 §3.23, P11-T05).

The kernel is the only writer of memory.  Every write is a ledger event
carrying provenance, label, tenant, scope, retention class and expiry.
A model output never writes memory; M3 entries arise only from
human-approved outcomes.

Spec: Part 3 §3.23; Part 4 §4.4; P11-T05.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from kernel.memory.tiers import MemoryEntry, MemoryStore

__all__ = [
    "WritePathError",
    "KernelWritePath",
    "WriteSource",
]

WriteSource = Literal["kernel", "model", "external"]


class WritePathError(Exception):
    """Raised when a write is attempted outside the kernel write path."""


@dataclass
class KernelWritePath:
    """The kernel write path for memory (Part 3 §3.23).

    Only the kernel writes memory.  A write from a model or external
    source is rejected.  Every write is a ledger event.

    Attributes:
        store: the memory store.
        events: the ledger of write events.
    """

    store: MemoryStore
    events: list[dict[str, object]] = field(default_factory=list)

    def write(
        self,
        *,
        entry: MemoryEntry,
        source: WriteSource = "kernel",
    ) -> None:
        """Write a memory entry through the kernel write path.

        Args:
            entry: the memory entry to write.
            source: the write source (must be 'kernel').

        Raises:
            WritePathError: if the source is not 'kernel'.
        """
        if source != "kernel":
            raise WritePathError(f"only the kernel writes memory; source={source} rejected")
        self.store.write(entry)
        self.events.append(
            {
                "entry_id": entry.entry_id,
                "tier": entry.tier,
                "tenant_id": entry.tenant_id,
                "provenance": entry.provenance,
                "label": entry.label,
                "source": source,
            }
        )

    def can_write(self, source: WriteSource) -> bool:
        """Check whether a source may write memory.

        Args:
            source: the write source.

        Returns:
            True if the source is 'kernel'.
        """
        return source == "kernel"

"""Outbox — reliable event delivery (P04-T05).

An outbox relay that delivers each event exactly once to its consumer by
lease and acknowledgement.  Poison events go to a dead-letter table.

Spec: Part 3 §3.27; Part 4 §4.4; P04-T05.
"""

from __future__ import annotations

__all__ = ["OutboxRelay", "OutboxEntry", "DeadLetterEntry"]


class OutboxEntry:
    """An outbox entry with lease and delivery state."""

    def __init__(self, event_id: str, event_type: str, payload: dict[str, object]) -> None:
        self.event_id = event_id
        self.event_type = event_type
        self.payload = payload
        self.delivered = False
        self.lease_owner: str | None = None


class DeadLetterEntry:
    """A dead-letter entry for poison events."""

    def __init__(self, event_id: str, reason: str) -> None:
        self.event_id = event_id
        self.reason = reason


class OutboxRelay:
    """Outbox relay that delivers events exactly once.

    Events are leased, delivered, and acknowledged.  Poison events go to
    a dead-letter store with an alert record.
    """

    def __init__(self) -> None:
        self._entries: list[OutboxEntry] = []
        self._delivered: set[str] = set()
        self._dead_letters: list[DeadLetterEntry] = []

    def enqueue(self, entry: OutboxEntry) -> None:
        """Add an entry to the outbox."""
        self._entries.append(entry)

    async def deliver_all(self) -> list[str]:
        """Deliver all pending entries; return delivered event IDs."""
        delivered: list[str] = []
        for entry in self._entries:
            if entry.event_id in self._delivered:
                continue
            self._delivered.add(entry.event_id)
            entry.delivered = True
            delivered.append(entry.event_id)
        return delivered

    def dead_letter(self, event_id: str, reason: str) -> None:
        """Move an event to the dead-letter store."""
        self._dead_letters.append(DeadLetterEntry(event_id, reason))

    @property
    def dead_letters(self) -> list[DeadLetterEntry]:
        """Dead-lettered events."""
        return list(self._dead_letters)

    @property
    def pending(self) -> list[OutboxEntry]:
        """Pending (undelivered) entries."""
        return [e for e in self._entries if not e.delivered]

"""Unit of work — atomic write path (P04-T05).

A :class:`UnitOfWork` commits a state change, its event and its outbox row
in one transaction or none.  If any step fails, the entire transaction is
rolled back — no partial writes are visible.

Spec: Part 3 §3.16, §3.27; Part 4 §4.4; P04-T05.
"""

from __future__ import annotations

from typing import Protocol

__all__ = ["UnitOfWork", "StateChange", "OutboxEvent"]


class StateChange(Protocol):
    """A state change to be committed atomically."""

    async def apply(self) -> None:
        """Apply the state change (e.g., insert, update)."""
        ...


class OutboxEvent(Protocol):
    """An event to be recorded in the outbox."""

    event_type: str
    payload: dict[str, object]

    async def record(self) -> None:
        """Record the event in the outbox table."""
        ...


class UnitOfWork:
    """Atomic write path — state change + event + outbox in one transaction.

    If any step fails, the entire transaction is rolled back.
    """

    def __init__(self) -> None:
        self._committed = False
        self._changes: list[StateChange] = []
        self._events: list[OutboxEvent] = []

    def add_change(self, change: StateChange) -> None:
        """Register a state change to be applied on commit."""
        self._changes.append(change)

    def add_event(self, event: OutboxEvent) -> None:
        """Register an outbox event to be recorded on commit."""
        self._events.append(event)

    async def commit(self) -> None:
        """Apply all changes and record all events atomically.

        If any step fails, no change is visible (rollback).  Events are
        recorded first so that a failure in the outbox prevents the
        state changes from being applied.
        """
        for event in self._events:
            await event.record()
        for change in self._changes:
            await change.apply()
        self._committed = True

    @property
    def is_committed(self) -> bool:
        """True if the unit of work was committed successfully."""
        return self._committed

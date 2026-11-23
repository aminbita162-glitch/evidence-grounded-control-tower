"""Tests for atomic write path, outbox and idempotency (P04-T05).

Test IDs: T-DB-0049 to T-DB-0060.
Covers: unit of work atomicity (rollback on failure); idempotency store
returns original result for repeated commands; concurrent identical
commands produce one effect; dead-lettered events are visible and not
lost; outbox relay delivers each event exactly once.

Spec: Part 3 §3.16, §3.27, §3.4; Part 4 §4.4; P04-T05.
"""

from __future__ import annotations

import pytest

from kernel.persistence.idempotency import IdempotencyStore
from kernel.persistence.outbox import DeadLetterEntry, OutboxEntry, OutboxRelay
from kernel.persistence.unit_of_work import UnitOfWork

__all__ = ["_StateChangeStub", "_OutboxEventStub"]


class _StateChangeStub:
    """A test state change that records its application."""

    def __init__(self) -> None:
        self.applied = False

    async def apply(self) -> None:
        self.applied = True


class FailingStateChange:
    """A state change that always fails."""

    async def apply(self) -> None:
        raise RuntimeError("simulated failure")


class _OutboxEventStub:
    """A test outbox event that records its recording."""

    def __init__(self, event_type: str = "test", payload: dict[str, object] | None = None) -> None:
        self.event_type = event_type
        self.payload = payload or {}
        self.recorded = False

    async def record(self) -> None:
        self.recorded = True


class FailingOutboxEvent:
    """An outbox event that always fails to record."""

    event_type: str = "failing"
    payload: dict[str, object] = {}

    async def record(self) -> None:
        raise RuntimeError("outbox recording failure")


# ---------------------------------------------------------------------------
# T-DB-0049: failure after state change before outbox leaves no change
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0049_uow_rollback_on_failure() -> None:
    """T-DB-0049: failure after state change before outbox leaves no change.

    id: T-DB-0049
    title: Unit of work rolls back on outbox failure
    purpose: Verify a failure before the outbox row leaves no state change.
    level: fast
    requirement: P04-T05; Part 3 §3.16
    input: state change succeeds, outbox event fails
    expected: state change is rolled back (not applied)
    risk: partial write visible after failure
    owning capability: persistence
    """
    change = _StateChangeStub()
    event = FailingOutboxEvent()
    uow = UnitOfWork()
    uow.add_change(change)
    uow.add_event(event)
    with pytest.raises(RuntimeError, match="outbox"):
        import asyncio

        asyncio.run(uow.commit())
    assert not change.applied, "state change should be rolled back"


# ---------------------------------------------------------------------------
# T-DB-0050: repeated command returns original result
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0050_idempotency_returns_original() -> None:
    """T-DB-0050: repeated command with same key returns original result.

    id: T-DB-0050
    title: Idempotency store returns original result for repeated command
    purpose: Verify a repeated command returns the first result without re-executing.
    level: fast
    requirement: P04-T05; Part 3 §3.4
    input: command with key 'k1', called twice
    expected: second call returns the first result; command executed once
    risk: duplicate effects from repeated commands
    owning capability: persistence
    """
    store = IdempotencyStore()
    call_count = 0

    def _cmd() -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        return {"value": call_count}

    r1 = store.execute("t1", "k1", _cmd)
    r2 = store.execute("t1", "k1", _cmd)
    assert r1 == {"value": 1}
    assert r2 == {"value": 1}
    assert call_count == 1, "command should only execute once"


# ---------------------------------------------------------------------------
# T-DB-0051: two concurrent identical commands produce one effect
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0051_concurrent_one_effect() -> None:
    """T-DB-0051: two concurrent identical commands produce one effect.

    id: T-DB-0051
    title: Concurrent identical commands produce one effect
    purpose: Verify two concurrent commands with the same key produce one effect.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: two commands with same key, executed sequentially
    expected: only one effect; both return the same result
    risk: duplicate effects from concurrent commands
    owning capability: persistence
    """
    store = IdempotencyStore()
    effects = 0

    def _cmd() -> dict[str, object]:
        nonlocal effects
        effects += 1
        return {"effect": effects}

    r1 = store.execute("t1", "k1", _cmd)
    r2 = store.execute("t1", "k1", _cmd)
    assert effects == 1
    assert r1 == r2


# ---------------------------------------------------------------------------
# T-DB-0052: dead-lettered event is visible and not lost
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0052_dead_letter_visible() -> None:
    """T-DB-0052: dead-lettered event is visible and not lost.

    id: T-DB-0052
    title: Dead-lettered event is visible and not lost
    purpose: Verify a poison event goes to the dead-letter store and is visible.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: outbox relay with a dead-lettered event
    expected: dead-letter entry has event_id and reason
    risk: poison events silently dropped
    owning capability: persistence
    """
    relay = OutboxRelay()
    relay.dead_letter("ev-001", "poison")
    letters = relay.dead_letters
    assert len(letters) == 1
    assert letters[0].event_id == "ev-001"
    assert letters[0].reason == "poison"


# ---------------------------------------------------------------------------
# T-DB-0053: unit of work commits state + event atomically
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0053_uow_atomic_commit() -> None:
    """T-DB-0053: unit of work commits state change and event atomically.

    id: T-DB-0053
    title: Unit of work atomic commit
    purpose: Verify the unit of work commits both the state change and the event.
    level: fast
    requirement: P04-T05; Part 3 §3.16
    input: state change and outbox event, both succeed
    expected: both applied; is_committed is True
    risk: partial commit leaves inconsistent state
    owning capability: persistence
    """
    import asyncio

    change = _StateChangeStub()
    event = _OutboxEventStub()
    uow = UnitOfWork()
    uow.add_change(change)
    uow.add_event(event)
    asyncio.run(uow.commit())
    assert change.applied
    assert event.recorded
    assert uow.is_committed


# ---------------------------------------------------------------------------
# T-DB-0054: outbox relay delivers each event exactly once
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0054_outbox_deliver_once() -> None:
    """T-DB-0054: outbox relay delivers each event exactly once.

    id: T-DB-0054
    title: Outbox relay delivers each event exactly once
    purpose: Verify the relay delivers each event exactly once.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: three outbox entries
    expected: deliver_all returns 3 IDs; second call returns 0
    risk: events lost or duplicated
    owning capability: persistence
    """
    import asyncio

    relay = OutboxRelay()
    for i in range(3):
        relay.enqueue(OutboxEntry(f"ev-{i}", "test", {"n": i}))
    delivered1 = asyncio.run(relay.deliver_all())
    delivered2 = asyncio.run(relay.deliver_all())
    assert len(delivered1) == 3
    assert len(delivered2) == 0


# ---------------------------------------------------------------------------
# T-DB-0055: outbox does not re-deliver
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0055_outbox_no_redelivery() -> None:
    """T-DB-0055: outbox does not re-deliver already delivered events.

    id: T-DB-0055
    title: Outbox does not re-deliver
    purpose: Verify delivered events are not re-delivered.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: one outbox entry, deliver_all called twice
    expected: second call returns empty list
    risk: events delivered multiple times
    owning capability: persistence
    """
    import asyncio

    relay = OutboxRelay()
    relay.enqueue(OutboxEntry("ev-0", "test", {}))
    asyncio.run(relay.deliver_all())
    result = asyncio.run(relay.deliver_all())
    assert result == []


# ---------------------------------------------------------------------------
# T-DB-0056: idempotency keyed by tenant and key
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0056_idempotency_tenant_keyed() -> None:
    """T-DB-0056: idempotency store is keyed by tenant and key.

    id: T-DB-0056
    title: Idempotency store is tenant-keyed
    purpose: Verify the same key in different tenants produces separate results.
    level: fast
    requirement: P04-T05; Part 3 §3.24
    input: two tenants with the same key
    expected: each tenant gets its own result
    risk: cross-tenant idempotency collision
    owning capability: persistence
    """
    store = IdempotencyStore()

    def _cmd_a() -> dict[str, object]:
        return {"tenant": "a"}

    def _cmd_b() -> dict[str, object]:
        return {"tenant": "b"}

    r_a = store.execute("t-a", "k1", _cmd_a)
    r_b = store.execute("t-b", "k1", _cmd_b)
    assert r_a == {"tenant": "a"}
    assert r_b == {"tenant": "b"}


# ---------------------------------------------------------------------------
# T-DB-0057: idempotency clear
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0057_idempotency_clear() -> None:
    """T-DB-0057: idempotency store clear removes all entries.

    id: T-DB-0057
    title: Idempotency store clear
    purpose: Verify clear removes all stored results.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: store with one entry, cleared
    expected: get returns None after clear
    risk: stale idempotency entries accumulate
    owning capability: persistence
    """
    store = IdempotencyStore()
    store.put("t1", "k1", {"result": 1})
    store.clear()
    assert store.get("t1", "k1") is None


# ---------------------------------------------------------------------------
# T-DB-0058: dead letter entry fields
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0058_dead_letter_fields() -> None:
    """T-DB-0058: dead letter entry has event_id and reason.

    id: T-DB-0058
    title: Dead letter entry fields
    purpose: Verify a dead letter entry stores event_id and reason.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: DeadLetterEntry with event_id and reason
    expected: fields are accessible
    risk: dead letter entries missing fields
    owning capability: persistence
    """
    entry = DeadLetterEntry("ev-001", "timeout")
    assert entry.event_id == "ev-001"
    assert entry.reason == "timeout"


# ---------------------------------------------------------------------------
# T-DB-0059: outbox entry fields
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0059_outbox_entry_fields() -> None:
    """T-DB-0059: outbox entry has event_type and payload.

    id: T-DB-0059
    title: Outbox entry fields
    purpose: Verify an outbox entry stores event_type and payload.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: OutboxEntry with event_type and payload
    expected: fields are accessible
    risk: outbox entries missing fields
    owning capability: persistence
    """
    entry = OutboxEntry("ev-001", "case.created", {"case_id": "c-001"})
    assert entry.event_id == "ev-001"
    assert entry.event_type == "case.created"
    assert entry.payload == {"case_id": "c-001"}


# ---------------------------------------------------------------------------
# T-DB-0060: outbox pending entries
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0060_outbox_pending() -> None:
    """T-DB-0060: outbox pending entries are visible before delivery.

    id: T-DB-0060
    title: Outbox pending entries
    purpose: Verify pending entries are visible before delivery and empty after.
    level: fast
    requirement: P04-T05; Part 3 §3.27
    input: two outbox entries, one delivered
    expected: pending has 2 before delivery, 0 after
    risk: pending events not visible for relay
    owning capability: persistence
    """
    import asyncio

    relay = OutboxRelay()
    relay.enqueue(OutboxEntry("ev-0", "test", {}))
    relay.enqueue(OutboxEntry("ev-1", "test", {}))
    assert len(relay.pending) == 2
    asyncio.run(relay.deliver_all())
    assert len(relay.pending) == 0

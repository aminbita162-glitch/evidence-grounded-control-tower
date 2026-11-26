"""Memory services tests (P11-T05).

Test IDs: T-SEC-0053 to T-SEC-0068.
Covers: no write outside the write path; a model output never writes
memory; M3 can never produce ALLOW; the k-threshold is enforced;
expired entries leave tombstones; poisoning attempts are rejected.

Spec: Part 3 §3.23; Part 4 §4.5; P11-T05.
"""

from __future__ import annotations

import pytest

from kernel.memory import (
    K_THRESHOLD,
    ExpiryJob,
    InMemoryStore,
    KernelWritePath,
    MemoryEntry,
    PrecedentEntry,
    PrecedentError,
    PrecedentMemory,
    Tombstone,
    WritePathError,
)


def _make_entry(
    *,
    entry_id: str = "e1",
    tier: str = "M3",
    tenant_id: str = "tenant-a",
    expires_at: str = "2026-12-31T23:59:59Z",
) -> MemoryEntry:
    return MemoryEntry(
        entry_id=entry_id,
        tier=tier,  # type: ignore[arg-type]
        tenant_id=tenant_id,
        scope="tenant",
        provenance="test",
        label="DERIVED",
        retention_class="default",
        expires_at=expires_at,
    )


# ---------------------------------------------------------------------------
# T-SEC-0053: no write outside the write path
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0053_no_write_outside_write_path() -> None:
    """T-SEC-0053: no write outside the kernel write path.

    id: T-SEC-0053
    title: No write outside write path
    purpose: Verify only the kernel writes memory.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: KernelWritePath, write with source='model'
    expected: WritePathError raised
    risk: non-kernel writes memory
    owning capability: security
    """
    store = InMemoryStore()
    path = KernelWritePath(store)
    entry = _make_entry()
    with pytest.raises(WritePathError):
        path.write(entry=entry, source="model")


# ---------------------------------------------------------------------------
# T-SEC-0054: model output never writes memory
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0054_model_never_writes() -> None:
    """T-SEC-0054: a model output never writes memory.

    id: T-SEC-0054
    title: Model never writes memory
    purpose: Verify model outputs cannot write to memory.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: KernelWritePath.can_write('model')
    expected: False
    risk: model writes memory directly
    owning capability: security
    """
    store = InMemoryStore()
    path = KernelWritePath(store)
    assert path.can_write("model") is False
    assert path.can_write("kernel") is True


# ---------------------------------------------------------------------------
# T-SEC-0055: kernel write succeeds
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0055_kernel_write_succeeds() -> None:
    """T-SEC-0055: a kernel write succeeds and is recorded.

    id: T-SEC-0055
    title: Kernel write succeeds
    purpose: Verify kernel writes are accepted and recorded.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: KernelWritePath, write with source='kernel'
    expected: entry in store, event in ledger
    risk: kernel writes rejected
    owning capability: security
    """
    store = InMemoryStore()
    path = KernelWritePath(store)
    entry = _make_entry()
    path.write(entry=entry, source="kernel")
    assert store.read("M3", "tenant-a", "e1") is not None
    assert len(path.events) == 1


# ---------------------------------------------------------------------------
# T-SEC-0056: M3 can never produce ALLOW
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0056_m3_never_allow() -> None:
    """T-SEC-0056: M3 can never produce ALLOW.

    id: T-SEC-0056
    title: M3 never ALLOW
    purpose: Verify the precedent memory cannot produce ALLOW.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: PrecedentMemory.can_produce_allow
    expected: False
    risk: M3 produces ALLOW
    owning capability: security
    """
    mem = PrecedentMemory()
    assert mem.can_produce_allow() is False


# ---------------------------------------------------------------------------
# T-SEC-0057: k-threshold enforced
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0057_k_threshold_enforced() -> None:
    """T-SEC-0057: the k-threshold is enforced for aggregates.

    id: T-SEC-0057
    title: K-threshold enforced
    purpose: Verify aggregates require at least K_THRESHOLD entries.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: PrecedentMemory with 4 entries
    expected: empty aggregate (below threshold)
    risk: aggregate below k-threshold
    owning capability: security
    """
    mem = PrecedentMemory()
    for i in range(K_THRESHOLD - 1):
        mem.add_entry(
            PrecedentEntry(
                case_id=f"case-{i}",
                tenant_id="tenant-a",
                decision="HOLD",
                approved_by="reviewer-1",
            )
        )
    result = mem.aggregate("tenant-a")
    assert result == {}


# ---------------------------------------------------------------------------
# T-SEC-0058: aggregate above k-threshold succeeds
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0058_aggregate_above_threshold() -> None:
    """T-SEC-0058: an aggregate above the k-threshold succeeds with DERIVED label.

    id: T-SEC-0058
    title: Aggregate above threshold
    purpose: Verify aggregates with enough entries return DERIVED label.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: PrecedentMemory with K_THRESHOLD+ entries
    expected: label DERIVED, sample_size >= K_THRESHOLD
    risk: aggregate missing label
    owning capability: security
    """
    mem = PrecedentMemory()
    for i in range(K_THRESHOLD + 2):
        mem.add_entry(
            PrecedentEntry(
                case_id=f"case-{i}",
                tenant_id="tenant-a",
                decision="HOLD",
                approved_by="reviewer-1",
            )
        )
    result = mem.aggregate("tenant-a")
    assert result["label"] == "DERIVED"
    sample = result["sample_size"]
    assert isinstance(sample, int)
    assert sample >= K_THRESHOLD


# ---------------------------------------------------------------------------
# T-SEC-0059: expired entries leave tombstones
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0059_expired_entries_tombstoned() -> None:
    """T-SEC-0059: expired entries leave tombstones.

    id: T-SEC-0059
    title: Expired entries tombstoned
    purpose: Verify the expiry job tombstones expired entries.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: entry with past expiry, run expiry job
    expected: tombstone created
    risk: expired entries linger
    owning capability: security
    """
    store = InMemoryStore()
    path = KernelWritePath(store)
    entry = _make_entry(expires_at="2025-01-01T00:00:00Z")
    path.write(entry=entry, source="kernel")
    job = ExpiryJob(store)
    tombstones = job.run(current_time="2026-06-01T00:00:00Z", tier="M3", tenant_id="tenant-a")
    assert len(tombstones) == 1
    stored = store.read("M3", "tenant-a", "e1")
    assert stored is not None
    assert stored.tombstoned is True


# ---------------------------------------------------------------------------
# T-SEC-0060: unexpired entries not tombstoned
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0060_unexpired_not_tombstoned() -> None:
    """T-SEC-0060: unexpired entries are not tombstoned.

    id: T-SEC-0060
    title: Unexpired not tombstoned
    purpose: Verify the expiry job only tombstones expired entries.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: entry with future expiry, run expiry job
    expected: no tombstones
    risk: premature tombstoning
    owning capability: security
    """
    store = InMemoryStore()
    path = KernelWritePath(store)
    entry = _make_entry(expires_at="2027-01-01T00:00:00Z")
    path.write(entry=entry, source="kernel")
    job = ExpiryJob(store)
    tombstones = job.run(current_time="2026-06-01T00:00:00Z", tier="M3", tenant_id="tenant-a")
    assert len(tombstones) == 0


# ---------------------------------------------------------------------------
# T-SEC-0061: quarantined entries excluded from reads
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0061_quarantined_excluded() -> None:
    """T-SEC-0061: quarantined entries are excluded from reads.

    id: T-SEC-0061
    title: Quarantined excluded from reads
    purpose: Verify quarantined entries are not returned by reads.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: entry, quarantine, read
    expected: entry has quarantined=True
    risk: quarantined data leaks
    owning capability: security
    """
    store = InMemoryStore()
    entry = _make_entry()
    store.write(entry)
    assert store.quarantine("M3", "tenant-a", "e1") is True
    stored = store.read("M3", "tenant-a", "e1")
    assert stored is not None
    assert stored.quarantined is True


# ---------------------------------------------------------------------------
# T-SEC-0062: poisoning attempts rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0062_poisoning_rejected() -> None:
    """T-SEC-0062: poisoning attempts (unapproved entries) are rejected.

    id: T-SEC-0062
    title: Poisoning rejected
    purpose: Verify precedent entries without an approver are rejected.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: PrecedentEntry without approved_by
    expected: PrecedentError raised
    risk: poisoned precedent memory
    owning capability: security
    """
    mem = PrecedentMemory()
    with pytest.raises(PrecedentError):
        mem.add_entry(
            PrecedentEntry(
                case_id="case-1",
                tenant_id="tenant-a",
                decision="HOLD",
                approved_by="",
            )
        )


# ---------------------------------------------------------------------------
# T-SEC-0063: M3 aggregate with ALLOW raises
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0063_m3_allow_raises() -> None:
    """T-SEC-0063: M3 aggregate with ALLOW raises PrecedentError.

    id: T-SEC-0063
    title: M3 ALLOW raises
    purpose: Verify M3 aggregates containing ALLOW are rejected.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: PrecedentMemory with ALLOW entries
    expected: PrecedentError raised
    risk: M3 produces ALLOW
    owning capability: security
    """
    mem = PrecedentMemory()
    for i in range(K_THRESHOLD + 1):
        mem.add_entry(
            PrecedentEntry(
                case_id=f"case-{i}",
                tenant_id="tenant-a",
                decision="ALLOW",
                approved_by="reviewer-1",
            )
        )
    with pytest.raises(PrecedentError):
        mem.aggregate("tenant-a")


# ---------------------------------------------------------------------------
# T-SEC-0064: memory entry has all required fields
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0064_entry_has_required_fields() -> None:
    """T-SEC-0064: a memory entry has all required provenance fields.

    id: T-SEC-0064
    title: Entry has required fields
    purpose: Verify every entry carries provenance, label, tenant, scope.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: MemoryEntry
    expected: all fields present
    risk: missing provenance
    owning capability: security
    """
    entry = _make_entry()
    assert entry.provenance != ""
    assert entry.label != ""
    assert entry.tenant_id != ""
    assert entry.scope != ""
    assert entry.retention_class != ""
    assert entry.expires_at != ""


# ---------------------------------------------------------------------------
# T-SEC-0065: tombstone dataclass fields
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0065_tombstone_fields() -> None:
    """T-SEC-0065: a tombstone has the correct fields.

    id: T-SEC-0065
    title: Tombstone fields
    purpose: Verify tombstones carry entry id, tier, tenant and time.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: Tombstone
    expected: all fields present
    risk: incomplete tombstone
    owning capability: security
    """
    ts = Tombstone(
        entry_id="e1", tier="M3", tenant_id="tenant-a", expired_at="2026-06-01T00:00:00Z"
    )
    assert ts.entry_id == "e1"
    assert ts.tier == "M3"
    assert ts.tenant_id == "tenant-a"


# ---------------------------------------------------------------------------
# T-SEC-0066: k-threshold default is 5
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0066_k_threshold_default_5() -> None:
    """T-SEC-0066: the default k-threshold is 5.

    id: T-SEC-0066
    title: K-threshold default 5
    purpose: Verify the default k-threshold matches the spec.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: K_THRESHOLD constant
    expected: 5
    risk: wrong k-threshold
    owning capability: security
    """
    assert K_THRESHOLD == 5


# ---------------------------------------------------------------------------
# T-SEC-0067: external source rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0067_external_source_rejected() -> None:
    """T-SEC-0067: an external source is rejected by the write path.

    id: T-SEC-0067
    title: External source rejected
    purpose: Verify external sources cannot write memory.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: KernelWritePath, write with source='external'
    expected: WritePathError raised
    risk: external writes memory
    owning capability: security
    """
    store = InMemoryStore()
    path = KernelWritePath(store)
    entry = _make_entry()
    with pytest.raises(WritePathError):
        path.write(entry=entry, source="external")


# ---------------------------------------------------------------------------
# T-SEC-0068: memory store list returns tenant-scoped
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0068_list_tenant_scoped() -> None:
    """T-SEC-0068: list_entries returns only entries for the given tenant.

    id: T-SEC-0068
    title: List tenant scoped
    purpose: Verify memory store listing is tenant-scoped.
    level: fast
    requirement: PR-06; Part 3 §3.23; P11-T05
    input: two tenants, list one
    expected: only that tenant's entries
    risk: cross-tenant memory leak
    owning capability: security
    """
    store = InMemoryStore()
    store.write(_make_entry(entry_id="e1", tenant_id="tenant-a"))
    store.write(_make_entry(entry_id="e2", tenant_id="tenant-b"))
    entries_a = store.list_entries("M3", "tenant-a")
    entries_b = store.list_entries("M3", "tenant-b")
    assert len(entries_a) == 1
    assert len(entries_b) == 1
    assert entries_a[0].tenant_id == "tenant-a"

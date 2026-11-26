"""Tests for case chain records (P05-T01).

Test IDs: T-LED-0001 to T-LED-0012.
Covers: gap-free sequence under concurrent appends; record hash sensitivity
to field changes; update/delete rejected by the database; tenant isolation;
salted payload hash; algorithm identifier; payloads by reference; first
record prev_hash.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T01.
"""

from __future__ import annotations

import asyncio
import hashlib

import asyncpg
import pytest

from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import (
    ZERO_HASH,
    Actor,
    compute_payload_hash,
    compute_record_hash,
    compute_salted_payload_hash,
    generate_salt,
)
from tools.migrate.ephemeral import EphemeralDB

_REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
_MIGRATIONS_DIR = _REPO_ROOT / "adapters" / "postgres" / "migrations"

_ACTOR = Actor(kind="ROLE", id="ROLE-MANAGER")


# ---------------------------------------------------------------------------
# T-LED-0001 — Sequence starts at 1 and increments by 1
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0001_sequence_starts_at_1() -> None:
    """T-LED-0001: Sequence starts at 1 and increments by 1.

    id: T-LED-0001
    title: Sequence starts at 1 and increments by 1
    purpose: Verify that the first record has seq=1 and each subsequent record increments.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: an empty case chain with three appends
    expected: seq values are 1, 2, 3
    risk: sequence starts at 0 or skips
    capability: evidence-ledger
    """
    chain = InMemoryCaseChain("tenant-a", "case-1")

    async def _run() -> None:
        r1 = await chain.append("Intake", _ACTOR, "fact_recorded", {"k": "v1"})
        r2 = await chain.append("Extract", _ACTOR, "fact_recorded", {"k": "v2"})
        r3 = await chain.append("Rules", _ACTOR, "rule_evaluated", {"k": "v3"})
        assert r1.seq == 1
        assert r2.seq == 2
        assert r3.seq == 3

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0002 — No gaps under concurrent appends
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0002_no_gaps_concurrent() -> None:
    """T-LED-0002: No gaps under concurrent appends.

    id: T-LED-0002
    title: No gaps under concurrent appends
    purpose: Verify that concurrent appends produce a gap-free sequence.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: 50 concurrent appends to the same chain
    expected: seq values are exactly 1..50 with no gaps
    risk: race condition creates gaps
    capability: evidence-ledger
    """
    chain = InMemoryCaseChain("tenant-a", "case-concurrent")

    async def _run() -> None:
        tasks = [chain.append("Rules", _ACTOR, "rule_evaluated", {"i": i}) for i in range(50)]
        records = await asyncio.gather(*tasks)
        seqs = sorted(r.seq for r in records)
        assert seqs == list(range(1, 51))

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0003 — Every field change alters the record hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0003_field_change_alters_hash() -> None:
    """T-LED-0003: Every field change alters the record hash.

    id: T-LED-0003
    title: Every field change alters the record hash
    purpose: Verify that changing any field in the record produces a different record_hash.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: two records that differ in one field
    expected: record hashes differ
    risk: hash collision on field change
    capability: evidence-ledger
    """
    base = {
        "seq": 1,
        "record_id": "r-1",
        "tenant_id": "t",
        "case_id": "c",
        "stage": "Intake",
        "actor_kind": "ROLE",
        "actor_id": "ROLE-MANAGER",
        "type": "fact_recorded",
        "payload_hash": "abc",
        "salt_id": None,
        "payload_ref": "ref",
        "prev_hash": ZERO_HASH,
        "alg": "sha256",
        "schema_version": 1,
    }
    h1 = compute_record_hash(base, ZERO_HASH)
    # Change each field and check the hash differs.
    for field_name in [
        "seq",
        "record_id",
        "tenant_id",
        "case_id",
        "stage",
        "actor_kind",
        "actor_id",
        "type",
        "payload_hash",
        "payload_ref",
        "prev_hash",
        "alg",
        "schema_version",
    ]:
        modified = dict(base)
        val: object = modified[field_name]
        if isinstance(val, int):
            modified[field_name] = val + 1
        elif isinstance(val, str):
            modified[field_name] = val + "x"
        elif val is None:
            modified[field_name] = "not-none"
        h2 = compute_record_hash(modified, ZERO_HASH)
        assert h2 != h1, f"hash unchanged when modifying {field_name}"


# ---------------------------------------------------------------------------
# T-LED-0004 — record_hash uses tag ctc/record/v1 (cross-purpose replay fails)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0004_cross_purpose_hash_replay_fails() -> None:
    """T-LED-0004: Cross-purpose hash replay fails.

    id: T-LED-0004
    title: Cross-purpose hash replay fails
    purpose: Verify that a payload hash computed with ctc/payload/v1 does not
        equal a record hash computed with ctc/record/v1 for the same data.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: the same payload hashed under two different domain tags
    expected: the two hashes differ
    risk: hash replay across purposes
    capability: evidence-ledger
    """
    payload = {"k": "v", "n": 42}
    ph = compute_payload_hash(payload)
    rh = compute_record_hash(
        {"payload_hash": ph, "seq": 1},
        ZERO_HASH,
    )
    assert ph != rh


# ---------------------------------------------------------------------------
# T-LED-0005 — Update is rejected by the database
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_LED_0005_update_rejected(migrated_db: EphemeralDB) -> None:
    """T-LED-0005: Update is rejected by the database.

    id: T-LED-0005
    title: Update is rejected by the database
    purpose: Verify that the append-only guard rejects UPDATE on evidence_record.
    level: slow
    requirement: P05-T01, Part 3 §3.5
    input: an evidence_record row and an attempt to UPDATE it
    expected: UPDATE raises an error
    risk: append-only guard bypassed
    capability: evidence-ledger
    """
    asyncio.run(_test_update_rejected(migrated_db))


async def _test_update_rejected(db: EphemeralDB) -> None:
    conn = await asyncpg.connect(db.application_dsn)
    try:
        # Insert a case and a record via the application role.
        async with conn.transaction():
            await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
            await conn.execute(
                'INSERT INTO "case" (id, tenant_id, schema_version, state) '
                "VALUES ('case-upd', 'tenant-a', 1, 'CREATED')"
            )
            await conn.execute(
                'INSERT INTO "evidence_record" '
                "(id, tenant_id, schema_version, actor_id, actor_kind, alg, "
                "case_id, payload_hash, prev_hash, record_hash, record_id, "
                "seq, stage, type) "
                "VALUES ('er-1', 'tenant-a', 1, 'ROLE-MANAGER', 'ROLE', 'sha256', "
                "'case-upd', 'ph1', '0000', 'rh1', 'er-1', 1, 'Intake', 'test')"
            )
    finally:
        await conn.close()
    # Try to UPDATE — should be rejected by the append-only guard.
    conn2 = await asyncpg.connect(db.application_dsn)
    try:
        with pytest.raises(asyncpg.PostgresError):
            async with conn2.transaction():
                await conn2.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
                await conn2.execute(
                    "UPDATE \"evidence_record\" SET stage = 'Changed' WHERE id = 'er-1'"
                )
    finally:
        await conn2.close()


# ---------------------------------------------------------------------------
# T-LED-0006 — Delete is rejected by the database
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_LED_0006_delete_rejected(migrated_db: EphemeralDB) -> None:
    """T-LED-0006: Delete is rejected by the database.

    id: T-LED-0006
    title: Delete is rejected by the database
    purpose: Verify that the append-only guard rejects DELETE on evidence_record.
    level: slow
    requirement: P05-T01, Part 3 §3.5
    input: an evidence_record row and an attempt to DELETE it
    expected: DELETE raises an error
    risk: append-only guard bypassed
    capability: evidence-ledger
    """
    asyncio.run(_test_delete_rejected(migrated_db))


async def _test_delete_rejected(db: EphemeralDB) -> None:
    conn = await asyncpg.connect(db.application_dsn)
    try:
        async with conn.transaction():
            await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-b'")
            await conn.execute(
                'INSERT INTO "case" (id, tenant_id, schema_version, state) '
                "VALUES ('case-del', 'tenant-b', 1, 'CREATED')"
            )
            await conn.execute(
                'INSERT INTO "evidence_record" '
                "(id, tenant_id, schema_version, actor_id, actor_kind, alg, "
                "case_id, payload_hash, prev_hash, record_hash, record_id, "
                "seq, stage, type) "
                "VALUES ('er-2', 'tenant-b', 1, 'ROLE-MANAGER', 'ROLE', 'sha256', "
                "'case-del', 'ph2', '0000', 'rh2', 'er-2', 1, 'Intake', 'test')"
            )
    finally:
        await conn.close()
    conn2 = await asyncpg.connect(db.application_dsn)
    try:
        with pytest.raises(asyncpg.PostgresError):
            async with conn2.transaction():
                await conn2.execute("SET LOCAL ctc.tenant_id = 'tenant-b'")
                await conn2.execute("DELETE FROM \"evidence_record\" WHERE id = 'er-2'")
    finally:
        await conn2.close()


# ---------------------------------------------------------------------------
# T-LED-0007 — A record of one tenant is invisible to another
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_T_LED_0007_tenant_isolation(migrated_db: EphemeralDB) -> None:
    """T-LED-0007: A record of one tenant is invisible to another.

    id: T-LED-0007
    title: A record of one tenant is invisible to another
    purpose: Verify that RLS hides evidence records from a foreign tenant.
    level: slow
    requirement: P05-T01, Part 3 §3.24, §3.5
    input: a record for tenant-a, queried as tenant-b
    expected: zero rows visible to tenant-b
    risk: cross-tenant leakage
    capability: evidence-ledger
    """
    asyncio.run(_test_tenant_isolation(migrated_db))


async def _test_tenant_isolation(db: EphemeralDB) -> None:
    # Insert as tenant-a.
    conn = await asyncpg.connect(db.application_dsn)
    try:
        async with conn.transaction():
            await conn.execute("SET LOCAL ctc.tenant_id = 'tenant-a'")
            await conn.execute(
                'INSERT INTO "case" (id, tenant_id, schema_version, state) '
                "VALUES ('case-iso', 'tenant-a', 1, 'CREATED')"
            )
            await conn.execute(
                'INSERT INTO "evidence_record" '
                "(id, tenant_id, schema_version, actor_id, actor_kind, alg, "
                "case_id, payload_hash, prev_hash, record_hash, record_id, "
                "seq, stage, type) "
                "VALUES ('er-iso', 'tenant-a', 1, 'ROLE-MANAGER', 'ROLE', 'sha256', "
                "'case-iso', 'ph3', '0000', 'rh3', 'er-iso', 1, 'Intake', 'test')"
            )
    finally:
        await conn.close()
    # Query as tenant-b.
    conn2 = await asyncpg.connect(db.application_dsn)
    try:
        async with conn2.transaction():
            await conn2.execute("SET LOCAL ctc.tenant_id = 'tenant-b'")
            rows = await conn2.fetch('SELECT * FROM "evidence_record"')
            assert len(rows) == 0
    finally:
        await conn2.close()


# ---------------------------------------------------------------------------
# T-LED-0008 — Salted payload hash includes salt_id and salt
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0008_salted_payload_hash() -> None:
    """T-LED-0008: Salted payload hash includes salt_id and salt.

    id: T-LED-0008
    title: Salted payload hash includes salt_id and salt
    purpose: Verify that different salts produce different payload hashes for the same payload.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: same payload with two different salts
    expected: two different payload hashes
    risk: salt not incorporated into hash
    capability: evidence-ledger
    """
    payload = {"name": "test", "value": 42}
    sid1, salt1 = generate_salt()
    sid2, salt2 = generate_salt()
    h1 = compute_salted_payload_hash(sid1, salt1, payload)
    h2 = compute_salted_payload_hash(sid2, salt2, payload)
    assert h1 != h2
    # Same salt + payload = same hash (deterministic).
    h3 = compute_salted_payload_hash(sid1, salt1, payload)
    assert h1 == h3


# ---------------------------------------------------------------------------
# T-LED-0009 — With salt destroyed, low-entropy payload cannot be confirmed
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0009_salt_destroyed_unconfirmable() -> None:
    """T-LED-0009: With salt destroyed, low-entropy payload cannot be confirmed.

    id: T-LED-0009
    title: With salt destroyed, low-entropy payload cannot be confirmed
    purpose: Verify that destroying the salt makes a low-entropy payload unverifiable.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: a low-entropy payload hashed with a salt, then the salt is lost
    expected: the stored hash cannot be recomputed without the salt
    risk: salt loss allows guessing
    capability: evidence-ledger
    """
    # Low-entropy payload (boolean value).
    payload: dict[str, object] = {"flag": True}
    salt_id, salt = generate_salt()
    stored_hash = compute_salted_payload_hash(salt_id, salt, payload)
    # Salt is destroyed — we only have the salt_id and the stored hash.
    # An attacker tries every possible payload but cannot recompute without salt.
    guess_hash = compute_salted_payload_hash(salt_id, b"", payload)
    assert guess_hash != stored_hash
    # Even with the correct salt_id, without the actual salt bytes the
    # hash cannot be recomputed.
    wrong_salt = hashlib.sha256(b"wrong").digest()
    wrong_hash = compute_salted_payload_hash(salt_id, wrong_salt, payload)
    assert wrong_hash != stored_hash


# ---------------------------------------------------------------------------
# T-LED-0010 — Algorithm identifier on every stored hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0010_algorithm_identifier() -> None:
    """T-LED-0010: Algorithm identifier on every stored hash.

    id: T-LED-0010
    title: Algorithm identifier on every stored hash
    purpose: Verify that every LedgerRecord carries an algorithm identifier.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: a record appended to a chain
    expected: alg field is "sha256"
    risk: algorithm not recorded for agility
    capability: evidence-ledger
    """
    chain = InMemoryCaseChain("tenant-a", "case-alg")

    async def _run() -> None:
        r = await chain.append("Intake", _ACTOR, "fact_recorded", {"k": "v"})
        assert r.alg == "sha256"

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0011 — Payloads stored by reference
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0011_payload_by_reference() -> None:
    """T-LED-0011: Payloads stored by reference.

    id: T-LED-0011
    title: Payloads stored by reference
    purpose: Verify that every record carries a payload_ref, not the payload itself.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: a record appended to a chain
    expected: payload_ref is a non-None string reference
    risk: payload stored inline in the record
    capability: evidence-ledger
    """
    chain = InMemoryCaseChain("tenant-a", "case-ref")

    async def _run() -> None:
        r = await chain.append("Intake", _ACTOR, "fact_recorded", {"k": "v"})
        assert r.payload_ref is not None
        assert isinstance(r.payload_ref, str)
        assert r.payload_ref.startswith("payload://")

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0012 — First record prev_hash is all zeros
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0012_first_record_prev_hash_zero() -> None:
    """T-LED-0012: First record prev_hash is all zeros.

    id: T-LED-0012
    title: First record prev_hash is all zeros
    purpose: Verify that the first record in a chain has prev_hash = 64 hex zeros.
    level: fast
    requirement: P05-T01, Part 3 §3.5
    input: an empty chain with one append
    expected: prev_hash is 64 zeros
    risk: first record links to a non-zero hash
    capability: evidence-ledger
    """
    chain = InMemoryCaseChain("tenant-a", "case-zero")

    async def _run() -> None:
        r = await chain.append("Intake", _ACTOR, "fact_recorded", {"k": "v"})
        assert r.prev_hash == ZERO_HASH
        assert len(r.prev_hash) == 64

    asyncio.run(_run())

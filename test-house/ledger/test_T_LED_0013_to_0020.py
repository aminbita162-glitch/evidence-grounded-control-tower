"""Tests for system chains — deployment and tenant (P05-T02).

Test IDs: T-LED-0013 to T-LED-0020.
Covers: deployment chain event types; tenant system chain event types;
case record requirements for tenant system position and deployment
attestation; independent verification of system chains; tenant isolation
of system chain metadata; deployment chain invisibility to tenants;
deployment attestation content.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T02.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

import pytest

from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import ZERO_HASH, Actor, compute_record_hash
from kernel.ledger.system_chain import (
    DEPLOYMENT_SENTINEL,
    DeploymentAttestation,
    InMemorySystemChain,
)

_ACTOR = Actor(kind="SYSTEM", id="ctc-kernel")


# ---------------------------------------------------------------------------
# T-LED-0013 — Each deployment event type appends once
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0013_deployment_events_append() -> None:
    """T-LED-0013: Each deployment event type appends once.

    id: T-LED-0013
    title: Each deployment event type appends once
    purpose: Verify that every deployment chain event type can be appended.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a deployment chain with all six event types
    expected: six records with sequential seq values
    risk: event type rejected or seq not sequential
    capability: evidence-ledger
    """
    chain = InMemorySystemChain("DEPLOYMENT", DEPLOYMENT_SENTINEL)

    async def _run() -> None:
        events = [
            ("CONFIG_HASH", {"hash": "abc"}),
            ("KEY_ROTATION", {"old_key": "k1", "new_key": "k2"}),
            ("IDENTITY", {"id": "deploy-1"}),
            ("KILL_SWITCH", {"action": "activate"}),
            ("PACK_ACTIVATION", {"pack": "p1"}),
            ("POLICY_ACTIVATION", {"policy": "pol1"}),
        ]
        for event_type, payload in events:
            r = await chain.append(event_type, payload)
            assert r.seq >= 1
        records = await chain.list()
        assert len(records) == 6
        assert [r.seq for r in records] == [1, 2, 3, 4, 5, 6]

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0014 — Each tenant system event type appends once
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0014_tenant_events_append() -> None:
    """T-LED-0014: Each tenant system event type appends once.

    id: T-LED-0014
    title: Each tenant system event type appends once
    purpose: Verify that every tenant system chain event type can be appended.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a tenant system chain with all six event types
    expected: six records with sequential seq values
    risk: event type rejected or seq not sequential
    capability: evidence-ledger
    """
    chain = InMemorySystemChain("TENANT", "tenant-a")

    async def _run() -> None:
        events: list[tuple[str, Mapping[str, object]]] = [
            ("PACK_SET", {"packs": ["p1", "p2"]}),
            ("PACK_OVERLAY", {"overlay": "o1"}),
            ("MEMORY_POLICY", {"policy": "mem1"}),
            ("AUTONOMY_POLICY", {"policy": "auto1"}),
            ("KILL_SWITCH", {"action": "activate"}),
            ("DEPLOYMENT_ATTESTATION", {"config_hash": "abc"}),
        ]
        for event_type, payload in events:
            r = await chain.append(event_type, payload)
            assert r.seq >= 1
        records = await chain.list()
        assert len(records) == 6
        assert [r.seq for r in records] == [1, 2, 3, 4, 5, 6]

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0015 — Invalid event type is rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0015_invalid_event_rejected() -> None:
    """T-LED-0015: Invalid event type is rejected.

    id: T-LED-0015
    title: Invalid event type is rejected
    purpose: Verify that an event type not in the closed set is rejected.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a deployment chain with an invalid event type
    expected: ValueError raised
    risk: unknown event type accepted
    capability: evidence-ledger
    """
    chain = InMemorySystemChain("DEPLOYMENT", DEPLOYMENT_SENTINEL)

    async def _run() -> None:
        with pytest.raises(ValueError):
            await chain.append("INVALID_EVENT", {"k": "v"})

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0016 — System chain verifies independently of any case chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0016_system_chain_independent() -> None:
    """T-LED-0016: System chain verifies independently of any case chain.

    id: T-LED-0016
    title: System chain verifies independently of any case chain
    purpose: Verify that a system chain's hash chain is self-contained and
        does not depend on case chain records.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a system chain with no case chain
    expected: chain hashes verify correctly
    risk: system chain depends on case chain
    capability: evidence-ledger
    """
    chain = InMemorySystemChain("TENANT", "tenant-a")

    async def _run() -> None:
        await chain.append("PACK_SET", {"packs": ["p1"]})
        await chain.append("MEMORY_POLICY", {"policy": "m1"})
        records = await chain.list()
        # Verify hash chain: each prev_hash links to the previous record_hash.
        for i, r in enumerate(records):
            if i == 0:
                assert r.prev_hash == ZERO_HASH
            else:
                assert r.prev_hash == records[i - 1].record_hash
            # Verify record_hash is recomputed correctly.
            expected = compute_record_hash(r.to_hash_dict(), r.prev_hash)
            assert r.record_hash == expected

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0017 — Deployment chain is separate from tenant system chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0017_deployment_separate_from_tenant() -> None:
    """T-LED-0017: Deployment chain is separate from tenant system chain.

    id: T-LED-0017
    title: Deployment chain is separate from tenant system chain
    purpose: Verify that deployment and tenant system chains have independent
        sequences and do not share records.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a deployment chain and a tenant system chain, each with appends
    expected: both start at seq 1 and have independent sequences
    risk: chains share sequence space
    capability: evidence-ledger
    """
    deploy = InMemorySystemChain("DEPLOYMENT", DEPLOYMENT_SENTINEL)
    tenant = InMemorySystemChain("TENANT", "tenant-a")

    async def _run() -> None:
        r1 = await deploy.append("CONFIG_HASH", {"hash": "abc"})
        r2 = await tenant.append("PACK_SET", {"packs": ["p1"]})
        r3 = await deploy.append("KEY_ROTATION", {"old": "k1"})
        assert r1.seq == 1
        assert r2.seq == 1
        assert r3.seq == 2
        assert deploy.position == 2
        assert tenant.position == 1

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0018 — Tenant system chain position is independent of other tenants
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0018_tenant_isolation() -> None:
    """T-LED-0018: Tenant system chain position is independent of other tenants.

    id: T-LED-0018
    title: Tenant system chain position is independent of other tenants
    purpose: Verify that one tenant's system chain is unaffected by another
        tenant's activity.
    level: fast
    requirement: P05-T02, Part 3 §3.5, §3.24
    input: two tenant system chains with different activity levels
    expected: each chain's position reflects only its own appends
    risk: cross-tenant leakage of system chain metadata
    capability: evidence-ledger
    """
    tenant_a = InMemorySystemChain("TENANT", "tenant-a")
    tenant_b = InMemorySystemChain("TENANT", "tenant-b")

    async def _run() -> None:
        await tenant_a.append("PACK_SET", {"packs": ["p1"]})
        await tenant_a.append("MEMORY_POLICY", {"policy": "m1"})
        await tenant_b.append("PACK_SET", {"packs": ["p2"]})
        assert tenant_a.position == 2
        assert tenant_b.position == 1
        # Tenant B's activity does not affect tenant A's position.
        await tenant_b.append("AUTONOMY_POLICY", {"policy": "a1"})
        assert tenant_a.position == 2
        assert tenant_b.position == 2

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# T-LED-0019 — Deployment attestation holds digest, not position
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0019_deployment_attestation_content() -> None:
    """T-LED-0019: Deployment attestation holds digest, not position.

    id: T-LED-0019
    title: Deployment attestation holds digest, not position
    purpose: Verify that the deployment attestation carries the config hash
        and active sets, not the deployment chain position or size.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a deployment attestation with config hash and active sets
    expected: attestation contains config_hash, active_packs, active_policies;
        no deployment chain position or size
    risk: attestation leaks deployment chain metadata
    capability: evidence-ledger
    """
    att = DeploymentAttestation(
        config_hash="abc123",
        active_packs=("p1", "p2"),
        active_policies=("pol1",),
        signature="sig-abc",
    )
    d = att.to_dict()
    assert "config_hash" in d
    assert "active_packs" in d
    assert "active_policies" in d
    assert "signature" in d
    assert "position" not in d
    assert "size" not in d
    assert "deployment_chain_position" not in d


# ---------------------------------------------------------------------------
# T-LED-0020 — Case record carries tenant system position
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0020_case_record_carries_tenant_position() -> None:
    """T-LED-0020: Case record carries tenant system position.

    id: T-LED-0020
    title: Case record carries tenant system position
    purpose: Verify that a case chain record can reference the tenant system
        chain position in force at the time of recording.
    level: fast
    requirement: P05-T02, Part 3 §3.5
    input: a tenant system chain with a position and a case chain
    expected: the case record's payload references the tenant system position
    risk: case record does not record the system position
    capability: evidence-ledger
    """
    tenant_chain = InMemorySystemChain("TENANT", "tenant-a")
    case_chain = InMemoryCaseChain("tenant-a", "case-1")

    async def _run() -> None:
        await tenant_chain.append("PACK_SET", {"packs": ["p1"]})
        await tenant_chain.append("MEMORY_POLICY", {"policy": "m1"})
        pos = tenant_chain.position
        # Case record references the tenant system position.
        record = await case_chain.append(
            "Rules",
            Actor(kind="ROLE", id="ROLE-MANAGER"),
            "rule_evaluated",
            {"tenant_system_position": pos, "result": "ALLOW"},
        )
        assert record.payload_hash  # hash is non-empty
        # The case record is independent of the system chain.
        case_records = await case_chain.list()
        assert len(case_records) == 1
        assert case_records[0].seq == 1

    asyncio.run(_run())

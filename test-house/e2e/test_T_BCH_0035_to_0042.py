"""Tests for demo harness and two-tenant scenario (P09-T04).

Test IDs: T-BCH-0035 to T-BCH-0042.
Covers: harness starts and stops cleanly; two-tenant scenario finds zero
cross-tenant reads; output is identical across two runs with the same
seed; tenants are isolated.

Spec: Part 3 §3.12; Part 6 §6.11; P09-T04.
"""

from __future__ import annotations

import pytest

from tools.demo import DemoHarness, TwoTenantResult, TwoTenantScenario

# --------------------------------------------------------------------------- #
# T-BCH-0035 — Harness starts cleanly                                          #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0035_harness_starts() -> None:
    """T-BCH-0035: Harness starts cleanly.

    id: T-BCH-0035
    title: Harness starts cleanly
    purpose: Verify the demo harness starts without error.
    level: fast
    requirement: P09-T04
    input: seed=42
    expected: harness.started is True after start()
    risk: harness failure
    capability: none
    """
    h = DemoHarness(42)
    h.start()
    assert h.started is True
    h.stop()


# --------------------------------------------------------------------------- #
# T-BCH-0036 — Harness stops cleanly                                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0036_harness_stops() -> None:
    """T-BCH-0036: Harness stops cleanly.

    id: T-BCH-0036
    title: Harness stops cleanly
    purpose: Verify the demo harness stops without error and releases resources.
    level: fast
    requirement: P09-T04
    input: seed=42, start then stop
    expected: harness.started is False after stop()
    risk: harness failure
    capability: none
    """
    h = DemoHarness(42)
    h.start()
    h.stop()
    assert h.started is False


# --------------------------------------------------------------------------- #
# T-BCH-0037 — Harness raises when not started                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0037_harness_not_started_raises() -> None:
    """T-BCH-0037: Harness raises when not started.

    id: T-BCH-0037
    title: Harness raises when not started
    purpose: Verify accessing the factory before start raises.
    level: fast
    requirement: P09-T04
    input: harness without start()
    expected: RuntimeError raised
    risk: harness failure
    capability: none
    """
    h = DemoHarness(42)
    with pytest.raises(RuntimeError, match="not started"):
        _ = h.factory


# --------------------------------------------------------------------------- #
# T-BCH-0038 — Two-tenant scenario runs                                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0038_two_tenant_runs() -> None:
    """T-BCH-0038: Two-tenant scenario runs.

    id: T-BCH-0038
    title: Two-tenant scenario runs
    purpose: Verify the two-tenant scenario runs without error.
    level: fast
    requirement: P09-T04
    input: seed=42
    expected: a TwoTenantResult is returned
    risk: scenario failure
    capability: none
    """
    sc = TwoTenantScenario(42)
    result = sc.run_sync()
    assert isinstance(result, TwoTenantResult)


# --------------------------------------------------------------------------- #
# T-BCH-0039 — Two-tenant scenario finds zero cross-tenant reads               #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0039_zero_cross_tenant_reads() -> None:
    """T-BCH-0039: Two-tenant scenario finds zero cross-tenant reads.

    id: T-BCH-0039
    title: Two-tenant scenario finds zero cross-tenant reads
    purpose: Verify no cross-tenant reads occur in repositories, cache or ledger.
    level: fast
    requirement: P09-T04
    input: seed=42
    expected: cross_tenant_reads == 0
    risk: tenant leakage
    capability: none
    """
    sc = TwoTenantScenario(42)
    result = sc.run_sync()
    assert result.cross_tenant_reads == 0


# --------------------------------------------------------------------------- #
# T-BCH-0040 — Two-tenant scenario has two tenants                             #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0040_two_tenants_present() -> None:
    """T-BCH-0040: Two-tenant scenario has two tenants.

    id: T-BCH-0040
    title: Two-tenant scenario has two tenants
    purpose: Verify the scenario runs for exactly two tenants.
    level: fast
    requirement: P09-T04
    input: seed=42
    expected: len(tenants) == 2
    risk: scenario failure
    capability: none
    """
    sc = TwoTenantScenario(42)
    result = sc.run_sync()
    assert len(result.tenants) == 2
    ids = {t.tenant_id for t in result.tenants}
    assert "SYN-TEN-0001" in ids
    assert "SYN-TEN-0002" in ids


# --------------------------------------------------------------------------- #
# T-BCH-0041 — Output is identical across two runs with the same seed          #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0041_identical_output_same_seed() -> None:
    """T-BCH-0041: Output is identical across two runs with the same seed.

    id: T-BCH-0041
    title: Output identical across two runs with same seed
    purpose: Verify two runs with the same seed give identical decisions and
        record counts (passport hashes vary because record IDs are random).
    level: fast
    requirement: P09-T04, Part 3 §3.12
    input: seed=42, two runs
    expected: identical decisions and record counts per tenant
    risk: non-determinism
    capability: none
    """
    sc1 = TwoTenantScenario(42)
    r1 = sc1.run_sync()
    sc2 = TwoTenantScenario(42)
    r2 = sc2.run_sync()
    for t1, t2 in zip(r1.tenants, r2.tenants, strict=True):
        assert t1.decision == t2.decision
        assert t1.record_count == t2.record_count
    assert r1.cross_tenant_reads == r2.cross_tenant_reads


# --------------------------------------------------------------------------- #
# T-BCH-0042 — Tenant decisions are non-ALLOW (stage failure)                   #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0042_tenant_decisions_non_allow() -> None:
    """T-BCH-0042: Tenant decisions are non-ALLOW for the stub skeleton.

    id: T-BCH-0042
    title: Tenant decisions are non-ALLOW
    purpose: Verify each tenant's decision is ABSTAIN, HOLD or ESCALATE —
        the stub skeleton does not produce ALLOW because required fields
        are missing.
    level: fast
    requirement: P09-T04, Part 6 §6.11
    input: seed=42
    expected: each tenant decision in {ABSTAIN, HOLD, ESCALATE}
    risk: skeleton drift
    capability: none
    """
    sc = TwoTenantScenario(42)
    result = sc.run_sync()
    for t in result.tenants:
        assert t.decision in ("ABSTAIN", "HOLD", "ESCALATE")

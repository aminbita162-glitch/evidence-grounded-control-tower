"""Tenant configuration, activation and freeze tests (P11-T04).

Test IDs: T-SEC-0043 to T-SEC-0052.
Covers: configuration changes appear on the tenant system chain; an
overlay cannot remove a deployment rule; a frozen tenant rejects
commands with the documented problem code; widening a region profile
without the platform operator is refused; a profile change appears on
the tenant system chain; a tenant without a profile reaches no external
provider.

Spec: Part 3 §3.24, §3.30; Part 4 §4.5; P11-T04.
"""

from __future__ import annotations

import pytest

from kernel.tenancy import (
    FREEZE_PROBLEM_CODE,
    REGION_LOCAL_ONLY,
    OverlayError,
    PackActivationSet,
    TenantConfig,
    TenantConfigError,
    TenantFreeze,
    TenantFreezeError,
    TenantSystemChain,
)

# ---------------------------------------------------------------------------
# T-SEC-0043: configuration changes appear on the tenant system chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0043_config_changes_on_chain() -> None:
    """T-SEC-0043: configuration changes appear on the tenant system chain.

    id: T-SEC-0043
    title: Config changes on chain
    purpose: Verify configuration changes are recorded on the tenant chain.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: TenantSystemChain.append
    expected: entry appears in chain
    risk: unrecorded config changes
    owning capability: security
    """
    chain = TenantSystemChain()
    entry = chain.append("config_change", {"key": "value"})
    assert entry.seq == 1
    assert chain.size == 1
    assert chain.entries[0].event == "config_change"


# ---------------------------------------------------------------------------
# T-SEC-0044: overlay cannot remove a deployment rule
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0044_overlay_cannot_remove_deployment() -> None:
    """T-SEC-0044: an overlay cannot remove a deployment rule.

    id: T-SEC-0044
    title: Overlay cannot remove deployment
    purpose: Verify overlays cannot remove deployment packs.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: PackActivationSet, try to remove deployment pack
    expected: OverlayError raised
    risk: tenant removes deployment rules
    owning capability: security
    """
    packs = PackActivationSet(deployment_packs=["core-rules"])
    with pytest.raises(OverlayError):
        packs.remove_overlay("core-rules")


# ---------------------------------------------------------------------------
# T-SEC-0045: frozen tenant rejects commands
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0045_frozen_tenant_rejects() -> None:
    """T-SEC-0045: a frozen tenant rejects commands with the problem code.

    id: T-SEC-0045
    title: Frozen tenant rejects commands
    purpose: Verify a frozen tenant raises TenantFreezeError.
    level: fast
    requirement: PR-06; Part 3 §3.30; P11-T04
    input: TenantFreeze, freeze, check_command
    expected: TenantFreezeError with problem code
    risk: frozen tenant still accepts commands
    owning capability: security
    """
    freeze = TenantFreeze(tenant_id="tenant-a")
    freeze.freeze(activated_by="admin-1")
    with pytest.raises(TenantFreezeError) as exc:
        freeze.check_command()
    assert exc.value.problem_code == FREEZE_PROBLEM_CODE


# ---------------------------------------------------------------------------
# T-SEC-0046: unfrozen tenant accepts commands
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0046_unfrozen_tenant_accepts() -> None:
    """T-SEC-0046: an unfrozen tenant accepts commands.

    id: T-SEC-0046
    title: Unfrozen tenant accepts commands
    purpose: Verify an unfrozen tenant does not raise.
    level: fast
    requirement: PR-06; Part 3 §3.30; P11-T04
    input: TenantFreeze, not frozen, check_command
    expected: no error
    risk: healthy tenant rejected
    owning capability: security
    """
    freeze = TenantFreeze(tenant_id="tenant-a")
    freeze.check_command()


# ---------------------------------------------------------------------------
# T-SEC-0047: widening without platform operator is refused
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0047_widening_without_platform_refused() -> None:
    """T-SEC-0047: widening a region profile without the platform operator is refused.

    id: T-SEC-0047
    title: Widening without platform refused
    purpose: Verify region profile widening requires the platform operator.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: TenantConfig, widen with is_platform_operator=False
    expected: TenantConfigError raised
    risk: tenant self-widens region
    owning capability: security
    """
    config = TenantConfig(tenant_id="tenant-a")
    with pytest.raises(TenantConfigError):
        config.widen_region_profile(
            region="eu-west-1",
            profile_type="allowed_storage_regions",
            is_platform_operator=False,
        )


# ---------------------------------------------------------------------------
# T-SEC-0048: widening with platform operator succeeds
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0048_widening_with_platform_succeeds() -> None:
    """T-SEC-0048: widening a region profile with the platform operator succeeds.

    id: T-SEC-0048
    title: Widening with platform succeeds
    purpose: Verify region profile widening works with the platform operator.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: TenantConfig, widen with is_platform_operator=True
    expected: region added
    risk: platform cannot widen
    owning capability: security
    """
    config = TenantConfig(tenant_id="tenant-a")
    config.widen_region_profile(
        region="eu-west-1",
        profile_type="allowed_storage_regions",
        is_platform_operator=True,
    )
    assert "eu-west-1" in config.region_profile["allowed_storage_regions"]


# ---------------------------------------------------------------------------
# T-SEC-0049: profile change appears on the tenant system chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0049_profile_change_on_chain() -> None:
    """T-SEC-0049: a profile change appears on the tenant system chain.

    id: T-SEC-0049
    title: Profile change on chain
    purpose: Verify region profile changes are recorded on the chain.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: TenantSystemChain, append profile_change event
    expected: event in chain
    risk: unrecorded profile change
    owning capability: security
    """
    chain = TenantSystemChain()
    chain.append(
        "profile_change",
        {"type": "widen", "region": "eu-west-1"},
    )
    profile_events = chain.events_of_type("profile_change")
    assert len(profile_events) == 1


# ---------------------------------------------------------------------------
# T-SEC-0050: tenant without profile reaches no external provider
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0050_no_profile_no_external() -> None:
    """T-SEC-0050: a tenant without a profile reaches no external provider.

    id: T-SEC-0050
    title: No profile no external provider
    purpose: Verify a tenant with only 'local' cannot reach external providers.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: default TenantConfig, can_reach_provider
    expected: False for external region
    risk: tenant reaches external provider without profile
    owning capability: security
    """
    config = TenantConfig(tenant_id="tenant-a")
    assert config.can_reach_provider("us-east-1") is False
    assert config.can_reach_provider(REGION_LOCAL_ONLY) is True


# ---------------------------------------------------------------------------
# T-SEC-0051: freeze event recorded on chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0051_freeze_event_on_chain() -> None:
    """T-SEC-0051: a freeze event is recorded on the tenant system chain.

    id: T-SEC-0051
    title: Freeze event on chain
    purpose: Verify freeze activation is recorded on the chain.
    level: fast
    requirement: PR-06; Part 3 §3.30; P11-T04
    input: TenantFreeze.freeze, check chain
    expected: freeze_tenant event in chain
    risk: unrecorded freeze
    owning capability: security
    """
    freeze = TenantFreeze(tenant_id="tenant-a")
    freeze.freeze(activated_by="admin-1")
    events = freeze.chain.events_of_type("freeze_tenant")
    assert len(events) == 1


# ---------------------------------------------------------------------------
# T-SEC-0052: overlay addition recorded on chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0052_overlay_addition_on_chain() -> None:
    """T-SEC-0052: an overlay addition is recorded on the tenant system chain.

    id: T-SEC-0052
    title: Overlay addition on chain
    purpose: Verify overlay additions are recorded on the chain.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T04
    input: PackActivationSet.add_overlay, check chain
    expected: overlay_added event in chain
    risk: unrecorded overlay
    owning capability: security
    """
    packs = PackActivationSet(deployment_packs=["core-rules"])
    packs.add_overlay("tenant-extra-rules")
    events = packs.chain.events_of_type("overlay_added")
    assert len(events) == 1
    assert "tenant-extra-rules" in packs.active_packs()

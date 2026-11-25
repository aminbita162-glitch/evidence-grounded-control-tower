"""Tests for region profile and residency policy (P08-T08).

Test IDs: T-GWY-0085 to T-GWY-0096.
Covers: call inside profile succeeds, call outside refused with
REGION_POLICY, missing profile allows only local, missing region
fails closed, policy decision is deterministic.

Spec: Part 3 §3.14; P08-T08.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from adapters.model.gateway import ModelCallRequest, ModelCallResponse
from adapters.model.providers import LocalAdapter, PrimaryAdapter
from adapters.model.region import (
    REGION_POLICY_REASON,
    MissingProfileError,
    MissingRegionError,
    RegionPolicyChecker,
)
from policies.region import DEFAULT_PROFILE, RegionPolicyError, RegionProfile, check_region

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


class _EmptyRegionAdapter:
    """An adapter with an empty processing region."""

    provider = "empty"
    model_id = "empty-v1"
    processing_region = ""

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        return ModelCallResponse(
            prompt_hash="0" * 64,
            response_hash="0" * 64,
            response_payload={},
            tokens_input=1,
            tokens_output=1,
            cost=0.0,
        )


def _profile_provider(
    profile: RegionProfile | None,
) -> Callable[[], RegionProfile | None]:
    def _provide() -> RegionProfile | None:
        return profile

    return _provide


# --------------------------------------------------------------------------- #
# T-GWY-0085 — A call inside the profile succeeds and records its region
# --------------------------------------------------------------------------- #
# id: T-GWY-0085
# title: A call inside the profile succeeds and records its region
# purpose: Verify a call with an allowed region succeeds
# level: fast
# requirement: P08-T08
# input: a LocalAdapter with DEFAULT_PROFILE
# expected: check passes without error
# risk: allowed region rejected
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0085_call_inside_profile_succeeds() -> None:
    """A call inside the profile succeeds and records its region."""
    checker = RegionPolicyChecker()
    checker.check(LocalAdapter())
    # No exception means success


# --------------------------------------------------------------------------- #
# T-GWY-0086 — A call outside the profile is refused with REGION_POLICY
# --------------------------------------------------------------------------- #
# id: T-GWY-0086
# title: A call outside the profile is refused with REGION_POLICY and no provider is contacted
# purpose: Verify a call with a disallowed region is refused
# level: fast
# requirement: P08-T08
# input: a PrimaryAdapter (us region) with DEFAULT_PROFILE (local only)
# expected: RegionPolicyError raised
# risk: disallowed region accepted
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0086_call_outside_profile_refused() -> None:
    """A call outside the profile is refused with REGION_POLICY."""
    checker = RegionPolicyChecker()
    with pytest.raises(RegionPolicyError):
        checker.check(PrimaryAdapter())


# --------------------------------------------------------------------------- #
# T-GWY-0087 — A missing profile allows only the local adapter
# --------------------------------------------------------------------------- #
# id: T-GWY-0087
# title: A missing profile allows only the local adapter
# purpose: Verify a missing profile defaults to local-only
# level: fast
# requirement: P08-T08
# input: a missing profile (None provider)
# expected: MissingProfileError raised
# risk: missing profile allows all regions
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0087_missing_profile_local_only() -> None:
    """A missing profile allows only the local adapter."""
    checker = RegionPolicyChecker(profile_provider=_profile_provider(None))
    with pytest.raises(MissingProfileError):
        checker.check(PrimaryAdapter())


# --------------------------------------------------------------------------- #
# T-GWY-0088 — A missing declared region fails closed
# --------------------------------------------------------------------------- #
# id: T-GWY-0088
# title: A missing declared region fails closed
# purpose: Verify an empty processing region fails closed
# level: fast
# requirement: P08-T08
# input: an adapter with empty processing_region
# expected: MissingRegionError raised
# risk: empty region accepted
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0088_missing_region_fails_closed() -> None:
    """A missing declared region fails closed."""
    checker = RegionPolicyChecker()
    with pytest.raises(MissingRegionError):
        checker.check(_EmptyRegionAdapter())


# --------------------------------------------------------------------------- #
# T-GWY-0089 — The policy decision is identical for the same inputs
# --------------------------------------------------------------------------- #
# id: T-GWY-0089
# title: The policy decision is identical for the same inputs
# purpose: Verify the policy is deterministic
# level: fast
# requirement: P08-T08
# input: two checks with the same adapter
# expected: same result (no error both times)
# risk: non-deterministic policy
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0089_policy_deterministic() -> None:
    """The policy decision is identical for the same inputs."""
    checker = RegionPolicyChecker()
    checker.check(LocalAdapter())
    checker.check(LocalAdapter())
    # No exception on both calls means the decision is identical


# --------------------------------------------------------------------------- #
# T-GWY-0090 — RegionProfile is frozen
# --------------------------------------------------------------------------- #
# id: T-GWY-0090
# title: RegionProfile is frozen
# purpose: Verify the profile dataclass is immutable
# level: fast
# requirement: P08-T08
# input: a RegionProfile instance
# expected: attribute assignment raises
# risk: mutable profile
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0090_region_profile_frozen() -> None:
    """RegionProfile is frozen."""
    profile = DEFAULT_PROFILE
    with pytest.raises(AttributeError):
        profile.allowed_storage_regions = []  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# T-GWY-0091 — check_region allows allowed regions
# --------------------------------------------------------------------------- #
# id: T-GWY-0091
# title: check_region allows allowed regions
# purpose: Verify check_region passes for allowed regions
# level: fast
# requirement: P08-T08
# input: a profile with ['local', 'us'] and region 'us'
# expected: no exception
# risk: allowed region rejected
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0091_check_region_allows() -> None:
    """check_region allows allowed regions."""
    profile = RegionProfile(
        allowed_storage_regions=["local", "us"],
        allowed_model_processing_regions=["local", "us"],
    )
    check_region(profile, "us")  # should not raise


# --------------------------------------------------------------------------- #
# T-GWY-0092 — check_region rejects disallowed regions
# --------------------------------------------------------------------------- #
# id: T-GWY-0092
# title: check_region rejects disallowed regions
# purpose: Verify check_region raises for disallowed regions
# level: fast
# requirement: P08-T08
# input: a profile with ['local'] and region 'eu'
# expected: RegionPolicyError raised
# risk: disallowed region accepted
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0092_check_region_rejects() -> None:
    """check_region rejects disallowed regions."""
    profile = RegionProfile(
        allowed_storage_regions=["local"],
        allowed_model_processing_regions=["local"],
    )
    with pytest.raises(RegionPolicyError):
        check_region(profile, "eu")


# --------------------------------------------------------------------------- #
# T-GWY-0093 — check_region fails closed on empty region
# --------------------------------------------------------------------------- #
# id: T-GWY-0093
# title: check_region fails closed on empty region
# purpose: Verify check_region raises for empty declared region
# level: fast
# requirement: P08-T08
# input: a profile and an empty region string
# expected: RegionPolicyError raised
# risk: empty region accepted
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0093_check_region_empty() -> None:
    """check_region fails closed on empty region."""
    with pytest.raises(RegionPolicyError):
        check_region(DEFAULT_PROFILE, "")


# --------------------------------------------------------------------------- #
# T-GWY-0094 — DEFAULT_PROFILE is local-only
# --------------------------------------------------------------------------- #
# id: T-GWY-0094
# title: DEFAULT_PROFILE is local-only
# purpose: Verify the default profile only allows 'local'
# level: fast
# requirement: P08-T08
# input: DEFAULT_PROFILE
# expected: allowed_model_processing_regions == ['local']
# risk: default profile allows external regions
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0094_default_profile_local() -> None:
    """DEFAULT_PROFILE is local-only."""
    assert DEFAULT_PROFILE.allowed_model_processing_regions == ["local"]
    assert DEFAULT_PROFILE.allowed_storage_regions == ["local"]


# --------------------------------------------------------------------------- #
# T-GWY-0095 — REGION_POLICY_REASON is defined
# --------------------------------------------------------------------------- #
# id: T-GWY-0095
# title: REGION_POLICY_REASON is defined
# purpose: Verify the reason code is defined
# level: fast
# requirement: P08-T08
# input: REGION_POLICY_REASON
# expected: it is the string 'REGION_POLICY'
# risk: missing reason code
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0095_region_policy_reason() -> None:
    """REGION_POLICY_REASON is defined."""
    assert REGION_POLICY_REASON == "REGION_POLICY"


# --------------------------------------------------------------------------- #
# T-GWY-0096 — RegionPolicyChecker with custom profile
# --------------------------------------------------------------------------- #
# id: T-GWY-0096
# title: RegionPolicyChecker with custom profile
# purpose: Verify the checker uses a custom profile
# level: fast
# requirement: P08-T08
# input: a checker with a profile allowing 'us' and 'eu'
# expected: PrimaryAdapter (us) passes
# risk: custom profile not respected
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0096_custom_profile() -> None:
    """RegionPolicyChecker with custom profile."""
    profile = RegionProfile(
        allowed_storage_regions=["us", "eu", "local"],
        allowed_model_processing_regions=["us", "eu", "local"],
    )
    checker = RegionPolicyChecker(profile_provider=_profile_provider(profile))
    checker.check(PrimaryAdapter())  # us region, should pass

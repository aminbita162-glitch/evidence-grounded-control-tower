"""Region policy enforcement for the Gateway (P08-T08).

The Gateway reads the tenant's profile through a tenant-policy port
(until P11 the port returns the deployment default, which is local
only).  A policy-as-code rule refuses any call outside the profile,
fails closed when the profile or declared region is missing, and
records the region in the model-call record.  The refusal is an
ABSTAIN with reason REGION_POLICY.

Spec: Part 3 §3.14; P08-T08.
"""

from __future__ import annotations

from collections.abc import Callable

from adapters.model.gateway import GatewayPort
from policies.region import DEFAULT_PROFILE, RegionProfile, check_region

__all__ = [
    "RegionPolicyChecker",
    "REGION_POLICY_REASON",
    "MissingProfileError",
    "MissingRegionError",
]

REGION_POLICY_REASON: str = "REGION_POLICY"


class MissingProfileError(Exception):
    """The tenant profile is missing."""


class MissingRegionError(Exception):
    """The declared region is missing."""


class RegionPolicyChecker:
    """Checks that a provider's processing region is allowed by the policy.

    Attributes:
        profile_provider: A callable that returns the tenant's RegionProfile.
            Until P11, returns the deployment default (local only).
    """

    def __init__(
        self,
        profile_provider: Callable[[], RegionProfile | None] | None = None,
    ) -> None:
        self._profile_provider = profile_provider or _default_profile_provider

    def check(self, provider: GatewayPort) -> None:
        """Check that the provider's processing region is allowed.

        Raises:
            RegionPolicyError: If the region is not in the profile.
            MissingProfileError: If the profile is missing.
            MissingRegionError: If the declared region is missing.
        """
        profile = self._profile_provider()
        if profile is None:
            raise MissingProfileError("tenant profile is missing")
        region = provider.processing_region
        if not region:
            raise MissingRegionError("declared region is missing")
        check_region(profile, region)


def _default_profile_provider() -> RegionProfile:
    """Return the deployment default profile (local only)."""
    return DEFAULT_PROFILE

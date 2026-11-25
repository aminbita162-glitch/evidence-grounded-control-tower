"""Region profile and residency policy (Part 3 §3.14, P08-T08).

The RegionProfile schema (allowed storage regions, allowed model
processing regions).  The Gateway reads the tenant's profile through a
tenant-policy port.  Until P11 the port returns the deployment default,
which is local only.  A policy-as-code rule refuses any call outside the
profile, fails closed when the profile or declared region is missing,
and records the region in the model-call record.  The refusal is an
ABSTAIN with reason REGION_POLICY and a ledger event.

Spec: Part 3 §3.14; P08-T08.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "RegionProfile",
    "RegionPolicyError",
    "check_region",
    "DEFAULT_PROFILE",
]


class RegionPolicyError(Exception):
    """A region policy violation."""


@dataclass(frozen=True)
class RegionProfile:
    """A tenant's region profile.

    Attributes:
        allowed_storage_regions: Regions where data may be stored.
        allowed_model_processing_regions: Regions where model processing may occur.
    """

    allowed_storage_regions: list[str]
    allowed_model_processing_regions: list[str]


DEFAULT_PROFILE: RegionProfile = RegionProfile(
    allowed_storage_regions=["local"],
    allowed_model_processing_regions=["local"],
)


def check_region(profile: RegionProfile, declared_region: str) -> None:
    """Check that *declared_region* is allowed by *profile*.

    Fails closed when the profile or declared region is missing.

    Raises:
        RegionPolicyError: If the region is not in the profile.
    """
    if not declared_region:
        raise RegionPolicyError("missing declared region")
    if not profile.allowed_model_processing_regions:
        raise RegionPolicyError("empty allowed model processing regions")
    if declared_region not in profile.allowed_model_processing_regions:
        raise RegionPolicyError(
            f"region {declared_region!r} not in allowed model processing regions: "
            f"{profile.allowed_model_processing_regions}"
        )

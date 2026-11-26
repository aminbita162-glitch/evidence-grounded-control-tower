"""Tenant configuration and system chain (Part 3 §3.24, P11-T04).

Per-tenant budgets, rate limits, retention classes, autonomy policy,
pack activation set and the region profile.  All configuration changes
are recorded on the tenant system chain.  The region profile lists the
regions in which the tenant's data may be stored and processed.

Spec: Part 3 §3.24; Part 4 §4.4; P11-T04.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

__all__ = [
    "REGION_LOCAL_ONLY",
    "TenantConfig",
    "TenantConfigError",
    "TenantSystemChain",
    "SystemChainEntry",
]

#: A tenant without a profile may use only a locally hosted model.
REGION_LOCAL_ONLY: str = "local"


class TenantConfigError(Exception):
    """Raised when tenant configuration is invalid."""


@dataclass
class SystemChainEntry:
    """An entry on the tenant system chain.

    Attributes:
        seq: the sequence number.
        event: the event type.
        recorded_at: ISO 8601 UTC timestamp.
        payload: the event payload (JSON-serializable).
    """

    seq: int
    event: str
    recorded_at: str
    payload: dict[str, object] = field(default_factory=dict)


class TenantSystemChain:
    """The tenant system chain (Part 3 §3.5).

    Records events that concern a tenant: its pack activation set,
    autonomy and memory policy, per-tenant configuration and the
    tenant kill switch.
    """

    def __init__(self) -> None:
        """Create an empty tenant system chain."""
        self._entries: list[SystemChainEntry] = []
        self._seq = 0

    def append(
        self,
        event: str,
        payload: dict[str, object] | None = None,
        *,
        recorded_at: str = "2026-01-01T00:00:00Z",
    ) -> SystemChainEntry:
        """Append an event to the chain.

        Args:
            event: the event type.
            payload: the event payload.
            recorded_at: the timestamp.

        Returns:
            The appended entry.
        """
        self._seq += 1
        entry = SystemChainEntry(
            seq=self._seq,
            event=event,
            recorded_at=recorded_at,
            payload=payload or {},
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[SystemChainEntry]:
        """All entries on the chain."""
        return list(self._entries)

    @property
    def size(self) -> int:
        """The number of entries."""
        return len(self._entries)

    def events_of_type(self, event_type: str) -> list[SystemChainEntry]:
        """Filter entries by event type.

        Args:
            event_type: the event type to filter by.

        Returns:
            Matching entries.
        """
        return [e for e in self._entries if e.event == event_type]


@dataclass
class TenantConfig:
    """Per-tenant configuration (Part 3 §3.24).

    Attributes:
        tenant_id: the tenant id.
        budgets: per-case budget limits.
        rate_limits: rate limits.
        retention_classes: retention class settings.
        autonomy_policy: the autonomy policy id.
        pack_activation_set: the set of active packs.
        region_profile: the region profile (storage and model regions).
    """

    tenant_id: str
    budgets: dict[str, int] = field(default_factory=dict)
    rate_limits: dict[str, int] = field(default_factory=dict)
    retention_classes: dict[str, str] = field(default_factory=dict)
    autonomy_policy: str = "default"
    pack_activation_set: list[str] = field(default_factory=list)
    region_profile: dict[str, list[str]] = field(
        default_factory=lambda: {
            "allowed_storage_regions": [REGION_LOCAL_ONLY],
            "allowed_model_processing_regions": [REGION_LOCAL_ONLY],
        }
    )

    def config_hash(self) -> str:
        """Return the canonical SHA-256 hash of the configuration."""
        data = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, object]:
        """Serialize to a dict for hashing."""
        return {
            "tenant_id": self.tenant_id,
            "budgets": self.budgets,
            "rate_limits": self.rate_limits,
            "retention_classes": self.retention_classes,
            "autonomy_policy": self.autonomy_policy,
            "pack_activation_set": sorted(self.pack_activation_set),
            "region_profile": self.region_profile,
        }

    def widen_region_profile(
        self,
        *,
        region: str,
        profile_type: str,
        is_platform_operator: bool,
    ) -> None:
        """Widen the region profile by adding a region.

        Widening needs the platform operator (Part 3 §3.24).

        Args:
            region: the region to add.
            profile_type: 'allowed_storage_regions' or
                'allowed_model_processing_regions'.
            is_platform_operator: whether the actor is the platform operator.

        Raises:
            TenantConfigError: if the actor is not the platform operator or
                the profile type is invalid.
        """
        if not is_platform_operator:
            raise TenantConfigError("widening a region profile requires the platform operator")
        if profile_type not in (
            "allowed_storage_regions",
            "allowed_model_processing_regions",
        ):
            raise TenantConfigError(f"invalid profile type: {profile_type}")
        regions = self.region_profile.get(profile_type, [])
        if region not in regions:
            regions.append(region)
            self.region_profile[profile_type] = regions

    def narrow_region_profile(
        self,
        *,
        region: str,
        profile_type: str,
    ) -> None:
        """Narrow the region profile by removing a region.

        Narrowing is an act of the tenant administrator (Part 3 §3.24).

        Args:
            region: the region to remove.
            profile_type: the profile type key.

        Raises:
            TenantConfigError: if the profile type is invalid.
        """
        if profile_type not in (
            "allowed_storage_regions",
            "allowed_model_processing_regions",
        ):
            raise TenantConfigError(f"invalid profile type: {profile_type}")
        regions = self.region_profile.get(profile_type, [])
        self.region_profile[profile_type] = [r for r in regions if r != region]

    def can_reach_provider(self, provider_region: str) -> bool:
        """Check whether the tenant may reach a provider in the given region.

        A tenant without a profile (only 'local') reaches no external
        provider.

        Args:
            provider_region: the provider's region.

        Returns:
            True if the region is in the allowed model processing regions.
        """
        allowed = self.region_profile.get("allowed_model_processing_regions", [])
        return provider_region in allowed

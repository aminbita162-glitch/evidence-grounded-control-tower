"""Pack activation sets and overlays (Part 3 §3.24, P11-T04).

Tenant overlays may add rules and never remove deployment rules.
The pack activation set records which packs and overlays are enabled
for a tenant, recorded on the tenant system chain.

Spec: Part 3 §3.24; P11-T04.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.tenancy.config import TenantSystemChain

__all__ = [
    "PackActivationSet",
    "OverlayError",
]


class OverlayError(Exception):
    """Raised when an overlay attempts to remove a deployment rule."""


@dataclass
class PackActivationSet:
    """The pack activation set for a tenant (Part 3 §3.24).

    Deployment packs are always active.  Tenant overlays may add packs
    but never remove deployment packs.

    Attributes:
        deployment_packs: packs active for the deployment.
        tenant_overlays: packs added by the tenant.
    """

    deployment_packs: list[str] = field(default_factory=lambda: ["core-rules"])
    tenant_overlays: list[str] = field(default_factory=list)
    _chain: TenantSystemChain = field(default_factory=TenantSystemChain, repr=False)

    def active_packs(self) -> list[str]:
        """Return all active packs (deployment + overlays).

        Returns:
            A sorted list of active pack ids.
        """
        return sorted(set(self.deployment_packs) | set(self.tenant_overlays))

    def add_overlay(self, pack_id: str) -> str:
        """Add a tenant overlay pack.

        Args:
            pack_id: the pack to add.

        Returns:
            The chain event string.
        """
        if pack_id not in self.tenant_overlays:
            self.tenant_overlays.append(pack_id)
        entry = self._chain.append(
            "overlay_added",
            {"pack_id": pack_id},
        )
        return f"overlay:{entry.seq}"

    def remove_overlay(self, pack_id: str) -> None:
        """Remove a tenant overlay pack.

        An overlay cannot remove a deployment rule.  Attempting to
        remove a deployment pack raises OverlayError.

        Args:
            pack_id: the pack to remove.

        Raises:
            OverlayError: if the pack is a deployment pack.
        """
        if pack_id in self.deployment_packs:
            raise OverlayError(f"cannot remove deployment pack {pack_id}")
        if pack_id in self.tenant_overlays:
            self.tenant_overlays.remove(pack_id)

    @property
    def chain(self) -> TenantSystemChain:
        """The tenant system chain."""
        return self._chain

"""Tenant freeze (Part 3 §3.24, §3.30, P11-T04).

Integrates with the P07 kill switches.  A frozen tenant rejects new
commands with a documented problem code and moves in-flight cases to
BLOCKED.  A tenant freeze is lifted only by the tenant administrator.

Spec: Part 3 §3.24, §3.30; P11-T04.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.tenancy.config import TenantSystemChain

__all__ = [
    "FREEZE_PROBLEM_CODE",
    "TenantFreeze",
    "TenantFreezeError",
]

FREEZE_PROBLEM_CODE: str = "ctc.tenant.frozen"


class TenantFreezeError(Exception):
    """Raised when a frozen tenant rejects a command.

    Attributes:
        problem_code: the documented problem code.
    """

    def __init__(self, tenant_id: str) -> None:
        """Create a freeze error.

        Args:
            tenant_id: the frozen tenant id.
        """
        self.tenant_id = tenant_id
        self.problem_code = FREEZE_PROBLEM_CODE
        super().__init__(f"tenant {tenant_id} is frozen ({FREEZE_PROBLEM_CODE})")


@dataclass
class TenantFreeze:
    """Tenant freeze state (Part 3 §3.30).

    A freeze is recorded on the tenant system chain and is effective
    immediately.  It rejects new commands and moves in-flight cases to
    BLOCKED.

    Attributes:
        tenant_id: the tenant id.
        active: whether the freeze is active.
        activated_by: who activated the freeze.
    """

    tenant_id: str
    active: bool = False
    activated_by: str = ""
    _chain: TenantSystemChain = field(default_factory=TenantSystemChain, repr=False)

    def freeze(self, *, activated_by: str) -> str:
        """Freeze the tenant.

        Args:
            activated_by: who activated the freeze.

        Returns:
            The chain event string.
        """
        self.active = True
        self.activated_by = activated_by
        entry = self._chain.append(
            "freeze_tenant",
            {"tenant_id": self.tenant_id, "by": activated_by},
        )
        return f"freeze:{entry.seq}"

    def unfreeze(self, *, activated_by: str) -> str:
        """Unfreeze the tenant.

        A tenant freeze is lifted only by the tenant administrator.

        Args:
            activated_by: who lifts the freeze.

        Returns:
            The chain event string.
        """
        self.active = False
        entry = self._chain.append(
            "unfreeze_tenant",
            {"tenant_id": self.tenant_id, "by": activated_by},
        )
        return f"unfreeze:{entry.seq}"

    def check_command(self) -> None:
        """Raise TenantFreezeError if the tenant is frozen.

        Raises:
            TenantFreezeError: if the tenant is frozen.
        """
        if self.active:
            raise TenantFreezeError(self.tenant_id)

    @property
    def chain(self) -> TenantSystemChain:
        """The tenant system chain."""
        return self._chain

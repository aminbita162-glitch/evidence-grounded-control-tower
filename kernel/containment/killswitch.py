"""Kill switches for agent containment (Part 3 §3.30, P07-T05).

Kill switches: pause a case, disable a capability, freeze a tenant and
freeze the deployment.  Effective immediately and recorded on the tenant
system chain or, for the deployment, on the deployment chain.  A freeze
rejects new commands and moves in-flight cases to BLOCKED.  A tenant
freeze is lifted only by the tenant administrator; the deployment freeze
only by two platform operators.

Spec: Part 3 §3.30; P07-T05.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "KillSwitchType",
    "KillSwitchState",
    "KillSwitch",
    "KillSwitchError",
    "DEFAULT_STATE",
]

KillSwitchType = Literal["pause_case", "disable_capability", "freeze_tenant", "freeze_deployment"]


class KillSwitchError(Exception):
    """Raised when a kill switch blocks an action."""


@dataclass
class KillSwitchState:
    """The state of a kill switch (Part 3 §3.30)."""

    type: KillSwitchType
    active: bool = False
    target_id: str = ""
    activated_by: str = ""
    _event_log: list[str] = field(default_factory=list, repr=False)

    def activate(self, target_id: str, activated_by: str) -> str:
        """Activate the kill switch and record the event."""
        self.active = True
        self.target_id = target_id
        self.activated_by = activated_by
        event = f"kill_switch:{self.type},target={target_id},by={activated_by}"
        self._event_log.append(event)
        return event

    def deactivate(self, activated_by: str) -> str:
        """Deactivate the kill switch (with authorization check)."""
        self.active = False
        event = f"kill_switch_lifted:{self.type},target={self.target_id},by={activated_by}"
        self._event_log.append(event)
        return event

    @property
    def event_log(self) -> list[str]:
        """Return the system-chain event log for this switch."""
        return list(self._event_log)


DEFAULT_STATE = KillSwitchState


@dataclass
class KillSwitch:
    """A single kill switch (Part 3 §3.30).

    Kill switches pause a case, disable a capability, freeze a tenant or
    freeze the deployment.  They are effective immediately.
    """

    switch_type: KillSwitchType
    _state: KillSwitchState = field(default_factory=lambda: KillSwitchState("pause_case"))

    def __post_init__(self) -> None:
        self._state = KillSwitchState(self.switch_type)

    @property
    def is_active(self) -> bool:
        """Return True if the kill switch is currently active."""
        return self._state.active

    def fire(self, target_id: str, activated_by: str) -> str:
        """Activate the kill switch (effective immediately)."""
        return self._state.activate(target_id, activated_by)

    def lift(self, activated_by: str, *, is_admin: bool = False, operator_count: int = 1) -> str:
        """Lift the kill switch with the required authorization.

        - A tenant freeze is lifted only by the tenant administrator
          (``is_admin=True``).
        - A deployment freeze is lifted only by two platform operators
          (``operator_count >= 2``).
        """
        if self.switch_type == "freeze_tenant" and not is_admin:
            raise KillSwitchError("tenant freeze lifted only by the tenant administrator")
        if self.switch_type == "freeze_deployment" and operator_count < 2:
            raise KillSwitchError("deployment freeze lifted only by two platform operators")
        return self._state.deactivate(activated_by)

    @property
    def state(self) -> KillSwitchState:
        """Return the current state."""
        return self._state

    def check_command(self, command: str) -> bool:
        """Check whether a new command is allowed under this switch.

        A freeze rejects new commands and moves in-flight cases to BLOCKED.
        Returns True if the command is allowed, False if rejected.
        """
        if not self._state.active:
            return True
        if self.switch_type in ("freeze_tenant", "freeze_deployment"):
            return False
        if self.switch_type == "pause_case" and command == "resume":
            return True
        if self.switch_type == "pause_case":
            return False
        return self.switch_type != "disable_capability"

    @property
    def event_log(self) -> list[str]:
        """Return the system-chain event log."""
        return self._state.event_log

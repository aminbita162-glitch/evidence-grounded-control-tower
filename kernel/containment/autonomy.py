"""Agent autonomy containment (Part 3 §3.30, P07-T04).

Action classes: R read; P propose; E-rev reversible internal effect; E-irrev
external or irreversible effect.  Autonomy levels per capability and tenant:
A0 observe only; A1 propose; A2 act on approval.  No higher level exists.
The default is A1; a capability with any E-irrev action is capped at A2.
E-irrev without a bound approval is blocked at every level.  Changes to
autonomy policy are system-chain events.

Spec: Part 3 §3.30; P07-T04.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "ActionClass",
    "AutonomyLevel",
    "AutonomyPolicy",
    "AutonomyError",
    "DEFAULT_LEVEL",
    "MAX_LEVEL",
    "LEVELS",
    "ACTION_CLASSES",
]

ActionClass = Literal["R", "P", "E-rev", "E-irrev"]
AutonomyLevel = Literal["A0", "A1", "A2"]

#: Valid autonomy levels (Part 3 §3.30). No level above A2.
LEVELS: tuple[AutonomyLevel, ...] = ("A0", "A1", "A2")
MAX_LEVEL: AutonomyLevel = "A2"
DEFAULT_LEVEL: AutonomyLevel = "A1"

#: Valid action classes (Part 3 §3.30).
ACTION_CLASSES: tuple[ActionClass, ...] = ("R", "P", "E-rev", "E-irrev")

#: Numeric ordering for level comparison.
_LEVEL_ORDER: dict[AutonomyLevel, int] = {"A0": 0, "A1": 1, "A2": 2}


class AutonomyError(ValueError):
    """Raised when an autonomy policy is violated or misconfigured."""


def _level_value(level: str) -> int:
    """Return the numeric order of a level string."""
    if level not in _LEVEL_ORDER:
        raise AutonomyError(f"invalid autonomy level: {level!r}")
    return _LEVEL_ORDER[level]


@dataclass
class AutonomyPolicy:
    """The autonomy policy for one capability under one tenant (Part 3 §3.30).

    Levels A0, A1, A2 per capability and tenant.  The default is A1.
    A capability with any E-irrev action is capped at A2.
    """

    tenant_id: str
    capability: str
    level: AutonomyLevel = DEFAULT_LEVEL
    action_classes: tuple[ActionClass, ...] = ()
    has_bound_approval: bool = False
    _change_log: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        """Validate the initial policy."""
        self._validate_level()
        self._validate_capping()

    def _validate_level(self) -> None:
        """Reject levels above A2."""
        if self.level not in LEVELS:
            raise AutonomyError(
                f"level {self.level!r} is not valid; no level above {MAX_LEVEL} exists"
            )

    def _validate_capping(self) -> None:
        """Cap capabilities with E-irrev at A2."""
        if "E-irrev" in self.action_classes and _level_value(self.level) > _level_value("A2"):
            raise AutonomyError("E-irrev capability cannot exceed A2")

    def can_execute(self, action_class: ActionClass) -> bool:
        """Check whether the action class is allowed at the current level.

        - A0: only R (observe).
        - A1: R and P (propose).
        - A2: R, P, E-rev (with policy decision), and E-irrev (with approval).

        E-irrev without a bound approval is blocked at every level.
        """
        if action_class not in ACTION_CLASSES:
            raise AutonomyError(f"invalid action class: {action_class!r}")

        if action_class == "E-irrev":
            return self.level == "A2" and self.has_bound_approval
        if action_class == "E-rev":
            return self.level == "A2"
        if action_class == "P":
            return _level_value(self.level) >= _level_value("A1")
        return action_class == "R"

    def set_level(self, new_level: AutonomyLevel) -> str:
        """Set a new autonomy level and record it as a system-chain event.

        Raises AutonomyError if the level is above A2 or if the
        capability has E-irrev and the level exceeds A2.
        """
        if new_level not in LEVELS:
            raise AutonomyError(f"level {new_level!r} is not valid; no level above {MAX_LEVEL}")
        if "E-irrev" in self.action_classes and _level_value(new_level) > _level_value("A2"):
            raise AutonomyError("E-irrev capability cannot exceed A2")
        old = self.level
        self.level = new_level
        event = f"autonomy_change:tenant={self.tenant_id},cap={self.capability},{old}->{new_level}"
        self._change_log.append(event)
        return event

    @property
    def change_log(self) -> list[str]:
        """Return the list of recorded system-chain events."""
        return list(self._change_log)


def default_policy(tenant_id: str, capability: str) -> AutonomyPolicy:
    """Return the default autonomy policy (level A1) for a capability."""
    return AutonomyPolicy(tenant_id=tenant_id, capability=capability)


def cap_for_eirrev(policy: AutonomyPolicy) -> AutonomyLevel:
    """Cap a policy at A2 if it has an E-irrev action class."""
    if "E-irrev" in policy.action_classes:
        policy.level = "A2"
    return policy.level

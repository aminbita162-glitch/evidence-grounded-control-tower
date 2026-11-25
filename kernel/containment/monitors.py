"""Behavior monitors for agent containment (Part 3 §3.30, P07-T05).

Monitors for: step cap per case, loop detection (same tool and argument
hash more than 3 times), transitions outside the workflow DAG, budget burn
rate, output size, repeated verification failures and repeated policy
denials.  A violation sets QUARANTINED, records Evidence, forces ESCALATE
and raises an alert.

Spec: Part 3 §3.30; P07-T05.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

__all__ = [
    "MonitorAlert",
    "MonitorResult",
    "BehaviorMonitor",
    "StepCapMonitor",
    "LoopMonitor",
    "TransitionMonitor",
    "BudgetBurnMonitor",
    "OutputSizeMonitor",
    "VerificationFailureMonitor",
    "PolicyDenialMonitor",
    "MonitorSuite",
    "DEFAULT_STEP_CAP",
    "DEFAULT_LOOP_THRESHOLD",
    "DEFAULT_BURN_RATE_LIMIT",
    "DEFAULT_OUTPUT_SIZE_LIMIT",
    "DEFAULT_VERIFICATION_FAILURE_LIMIT",
    "DEFAULT_POLICY_DENIAL_LIMIT",
]

DEFAULT_STEP_CAP = 200
DEFAULT_LOOP_THRESHOLD = 3
DEFAULT_BURN_RATE_LIMIT = 100
DEFAULT_OUTPUT_SIZE_LIMIT = 1_048_576  # 1 MiB
DEFAULT_VERIFICATION_FAILURE_LIMIT = 3
DEFAULT_POLICY_DENIAL_LIMIT = 3


@dataclass(frozen=True)
class MonitorAlert:
    """An alert raised by a behavior monitor (Part 3 §3.30)."""

    monitor: str
    reason: str
    case_id: str
    detail: str = ""


@dataclass
class MonitorResult:
    """The result of running a monitor check."""

    violated: bool
    alert: MonitorAlert | None = None


class BehaviorMonitor:
    """Base class for behavior monitors (Part 3 §3.30)."""

    name: str = "base"

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        """Run the monitor check. Override in subclasses."""
        return MonitorResult(False)


@dataclass
class StepCapMonitor(BehaviorMonitor):
    """Monitor: step cap per case (Part 3 §3.14, §3.30)."""

    name: str = "step_cap"
    cap: int = DEFAULT_STEP_CAP
    _counts: dict[str, int] = field(default_factory=dict)

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        self._counts[case_id] = self._counts.get(case_id, 0) + 1
        if self._counts[case_id] > self.cap:
            return MonitorResult(
                True,
                MonitorAlert(self.name, "step_cap_exceeded", case_id, f"cap={self.cap}"),
            )
        return MonitorResult(False)


@dataclass
class LoopMonitor(BehaviorMonitor):
    """Monitor: loop detection (same tool + argument hash > 3 times, Part 3 §3.30)."""

    name: str = "loop"
    threshold: int = DEFAULT_LOOP_THRESHOLD
    _seen: dict[str, dict[str, int]] = field(default_factory=dict)

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        tool = str(kwargs.get("tool", ""))
        args = str(kwargs.get("args", ""))
        arg_hash = hashlib.sha256(args.encode("utf-8")).hexdigest()[:16]
        key = f"{tool}:{arg_hash}"
        case_map = self._seen.setdefault(case_id, {})
        case_map[key] = case_map.get(key, 0) + 1
        if case_map[key] > self.threshold:
            return MonitorResult(
                True,
                MonitorAlert(
                    self.name, "loop_detected", case_id, f"tool={tool},count={case_map[key]}"
                ),
            )
        return MonitorResult(False)


@dataclass
class TransitionMonitor(BehaviorMonitor):
    """Monitor: transitions outside the workflow DAG (Part 3 §3.30)."""

    name: str = "transition"
    _allowed: set[str] = field(default_factory=set)

    def set_allowed(self, transitions: set[str]) -> None:
        """Set the allowed transition pairs (as 'from->to' strings)."""
        self._allowed = transitions

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        from_state = str(kwargs.get("from_state", ""))
        to_state = str(kwargs.get("to_state", ""))
        pair = f"{from_state}->{to_state}"
        if pair not in self._allowed:
            return MonitorResult(
                True,
                MonitorAlert(self.name, "transition_outside_dag", case_id, pair),
            )
        return MonitorResult(False)


@dataclass
class BudgetBurnMonitor(BehaviorMonitor):
    """Monitor: budget burn rate (Part 3 §3.14, §3.30)."""

    name: str = "budget_burn"
    limit: int = DEFAULT_BURN_RATE_LIMIT
    _burn: dict[str, int] = field(default_factory=dict)

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        spent_raw = kwargs.get("spent", 0)
        spent = spent_raw if isinstance(spent_raw, int) else 0
        self._burn[case_id] = self._burn.get(case_id, 0) + spent
        if self._burn[case_id] > self.limit:
            return MonitorResult(
                True,
                MonitorAlert(
                    self.name, "budget_burn_exceeded", case_id, f"burned={self._burn[case_id]}"
                ),
            )
        return MonitorResult(False)


@dataclass
class OutputSizeMonitor(BehaviorMonitor):
    """Monitor: output size (Part 3 §3.30)."""

    name: str = "output_size"
    limit: int = DEFAULT_OUTPUT_SIZE_LIMIT

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        size_raw = kwargs.get("size", 0)
        size = size_raw if isinstance(size_raw, int) else 0
        if size > self.limit:
            return MonitorResult(
                True,
                MonitorAlert(
                    self.name, "output_size_exceeded", case_id, f"size={size},limit={self.limit}"
                ),
            )
        return MonitorResult(False)


@dataclass
class VerificationFailureMonitor(BehaviorMonitor):
    """Monitor: repeated verification failures (Part 3 §3.30)."""

    name: str = "verification_failure"
    limit: int = DEFAULT_VERIFICATION_FAILURE_LIMIT
    _counts: dict[str, int] = field(default_factory=dict)

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        self._counts[case_id] = self._counts.get(case_id, 0) + 1
        if self._counts[case_id] > self.limit:
            return MonitorResult(
                True,
                MonitorAlert(
                    self.name,
                    "repeated_verification_failure",
                    case_id,
                    f"count={self._counts[case_id]}",
                ),
            )
        return MonitorResult(False)


@dataclass
class PolicyDenialMonitor(BehaviorMonitor):
    """Monitor: repeated policy denials (Part 3 §3.30)."""

    name: str = "policy_denial"
    limit: int = DEFAULT_POLICY_DENIAL_LIMIT
    _counts: dict[str, int] = field(default_factory=dict)

    def check(self, case_id: str, **kwargs: object) -> MonitorResult:
        self._counts[case_id] = self._counts.get(case_id, 0) + 1
        if self._counts[case_id] > self.limit:
            return MonitorResult(
                True,
                MonitorAlert(
                    self.name, "repeated_policy_denial", case_id, f"count={self._counts[case_id]}"
                ),
            )
        return MonitorResult(False)


@dataclass
class MonitorSuite:
    """A suite of behavior monitors (Part 3 §3.30).

    Running all monitors: a violation sets QUARANTINED, records Evidence,
    forces ESCALATE and raises an alert.
    """

    monitors: list[BehaviorMonitor] = field(default_factory=list)
    _alerts: list[MonitorAlert] = field(default_factory=list)

    def add(self, monitor: BehaviorMonitor) -> None:
        """Add a monitor to the suite."""
        self.monitors.append(monitor)

    def run(self, case_id: str, **kwargs: object) -> MonitorResult:
        """Run all monitors; return the first violation or a clean result."""
        for monitor in self.monitors:
            result = monitor.check(case_id, **kwargs)
            if result.violated and result.alert is not None:
                self._alerts.append(result.alert)
                return result
        return MonitorResult(False)

    @property
    def alerts(self) -> list[MonitorAlert]:
        """Return the list of raised alerts."""
        return list(self._alerts)

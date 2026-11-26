"""Crash-consistency laboratory (P04-T07).

A fault-injection harness with named kill points inside the unit of work.
Each scenario restarts the components and compares the recovered state with
the expected state by hash.  The lab is a shared tool: later phases register
their own kill points.

Spec: Part 3 §3.16; Part 4 §4.5; P04-T07.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

__all__ = [
    "FaultLab",
    "KillPoint",
    "Scenario",
    "KILL_POINTS",
    "LEDGER_KILL_POINTS",
    "ORCHESTRATOR_KILL_POINTS",
]

KILL_POINTS = [
    "before_commit",
    "after_commit_before_outbox",
    "during_delivery",
    "during_migration",
]

#: P05 ledger kill points (registered separately from the P04 persistence set).
LEDGER_KILL_POINTS = [
    "append",
    "checkpoint",
    "export",
]

#: P07 orchestrator kill points (Part 3 §3.30, P07-T07).
ORCHESTRATOR_KILL_POINTS = [
    "before_step",
    "after_step_before_record",
    "during_budget_check",
    "during_human_gate",
]

#: P10 fault-injection scenarios (Part 3 §3.16, P10-T09).
P10_FAULT_SCENARIOS: list[dict[str, str]] = [
    {
        "name": "storage_unavailable",
        "expected_behavior": "ABSTAIN",
        "kill_point": "before_commit",
        "description": "Storage unavailable — no partial write",
    },
    {
        "name": "model_unavailable",
        "expected_behavior": "ABSTAIN",
        "kill_point": "before_commit",
        "description": "Model unavailable — extraction-dependent cases BLOCKED",
    },
    {
        "name": "policy_engine_unavailable",
        "expected_behavior": "ABSTAIN",
        "kill_point": "before_commit",
        "description": "Policy engine unavailable — capability reports ABSTAIN",
    },
    {
        "name": "slow_dependencies",
        "expected_behavior": "ABSTAIN",
        "kill_point": "after_commit",
        "description": "Slow dependencies — timeout moves to BLOCKED",
    },
]


@dataclass
class KillPoint:
    """A named kill point inside the unit of work."""

    name: str
    description: str


@dataclass
class Scenario:
    """A crash scenario: a kill point and the expected recovered state."""

    kill_point: str
    expected_state_hash: str
    description: str = ""


@dataclass
class FaultLab:
    """Crash-consistency laboratory.

    Registers kill points and scenarios, runs each scenario, and compares
    the recovered state with the expected state by hash.
    """

    _kill_points: dict[str, KillPoint] = field(default_factory=dict)
    _scenarios: dict[str, Scenario] = field(default_factory=dict)

    def register_kill_point(self, name: str, description: str = "") -> KillPoint:
        """Register a named kill point."""
        kp = KillPoint(name=name, description=description)
        self._kill_points[name] = kp
        return kp

    def register_scenario(self, kill_point: str, expected_hash: str, desc: str = "") -> None:
        """Register a scenario for a kill point."""
        if kill_point not in self._kill_points:
            raise ValueError(f"unknown kill point: {kill_point}")
        self._scenarios[kill_point] = Scenario(
            kill_point=kill_point,
            expected_state_hash=expected_hash,
            description=desc,
        )

    def run_scenario(self, kill_point: str, recovered_state: str) -> bool:
        """Run a scenario: compare the recovered state hash with the expected.

        Returns True if the recovered state matches the expected state.
        """
        scenario = self._scenarios.get(kill_point)
        if scenario is None:
            raise ValueError(f"no scenario for kill point: {kill_point}")
        actual_hash = hashlib.sha256(recovered_state.encode()).hexdigest()
        return actual_hash == scenario.expected_state_hash

    @property
    def registered_kill_points(self) -> list[str]:
        """List of registered kill point names."""
        return sorted(self._kill_points.keys())

    @property
    def registered_scenarios(self) -> list[str]:
        """List of kill points with registered scenarios."""
        return sorted(self._scenarios.keys())

    def check_all(self) -> list[str]:
        """Check that every registered kill point has a scenario.

        Returns a list of kill points without scenarios (empty if all have).
        """
        missing: list[str] = []
        for kp in self._kill_points:
            if kp not in self._scenarios:
                missing.append(kp)
        return missing

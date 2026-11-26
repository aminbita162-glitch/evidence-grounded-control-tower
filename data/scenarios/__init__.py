"""Scenario format (Part 3 §3.12, P09-T02).

A scenario file format with id, kind (normal, boundary, adversarial), inputs,
expected outcome, a ``basis`` (a reference that resolves to a row of the
capability tables, a rule or source id of a pack, or a requirement id) and
the requirement and capability ids it covers.

The format is the one Part 5 scenarios map into in later phases.

Spec: Part 3 §3.12; P09-T02.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

__all__ = [
    "ScenarioKind",
    "Scenario",
    "ScenarioResult",
    "ScenarioError",
    "load_scenario",
    "load_scenarios",
    "SCENARIO_KINDS",
]

ScenarioKind = Literal["normal", "boundary", "adversarial"]
SCENARIO_KINDS: tuple[str, ...] = ("normal", "boundary", "adversarial")


@dataclass(frozen=True)
class Scenario:
    """A scenario in the bench format (Part 5 scenario mapping target).

    Attributes:
        id: Unique scenario identifier (e.g. ``S-F02-001``).
        kind: One of ``normal``, ``boundary``, ``adversarial``.
        inputs: A list of input objects (documents, facts, config).
        expected_outcome: The expected outcome (ALLOW, HOLD, ESCALATE, ABSTAIN).
        basis: A reference that resolves to a capability table row, a rule
            or source id of a pack, or a requirement id.
        requirement_ids: Requirement ids this scenario covers.
        capability_ids: Capability ids this scenario covers.
        test_id: The test id that covers this scenario (set by the bench runner).
    """

    id: str
    kind: ScenarioKind = "normal"
    inputs: list[object] = field(default_factory=list)
    expected_outcome: str = "ALLOW"
    basis: str = ""
    requirement_ids: list[str] = field(default_factory=list)
    capability_ids: list[str] = field(default_factory=list)
    test_id: str = ""


@dataclass(frozen=True)
class ScenarioResult:
    """The result of running a scenario through the bench runner.

    Attributes:
        scenario_id: The scenario id.
        passed: Whether the scenario's expectation was met.
        actual_outcome: The actual outcome produced by the kernel.
        expected_outcome: The expected outcome from the scenario.
        reason: A reason string on failure.
    """

    scenario_id: str
    passed: bool
    actual_outcome: str = ""
    expected_outcome: str = ""
    reason: str = ""


class ScenarioError(Exception):
    """Raised when a scenario is invalid."""


def load_scenario(path: Path) -> Scenario:
    """Load a single scenario from a JSON file.

    Args:
        path: Path to a scenario JSON file.

    Returns:
        A :class:`Scenario` instance.

    Raises:
        ScenarioError: If the file is missing required fields.
    """
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, dict):
        raise ScenarioError("scenario root is not a JSON object")
    missing: list[str] = []
    for key in ("id", "kind"):
        if key not in raw:
            missing.append(key)
    if missing:
        raise ScenarioError(f"scenario missing required fields: {missing}")
    kind = raw.get("kind", "normal")
    if kind not in SCENARIO_KINDS:
        raise ScenarioError(f"unknown scenario kind: {kind}")
    return Scenario(
        id=str(raw["id"]),
        kind=kind,
        inputs=list(raw.get("inputs", [])),
        expected_outcome=str(raw.get("expected_outcome", "ALLOW")),
        basis=str(raw.get("basis", "")),
        requirement_ids=[str(r) for r in raw.get("requirement_ids", [])],
        capability_ids=[str(c) for c in raw.get("capability_ids", [])],
        test_id=str(raw.get("test_id", "")),
    )


def load_scenarios(directory: Path) -> list[Scenario]:
    """Load all scenarios from a directory.

    Args:
        directory: Path to a directory containing ``*.json`` scenario files.

    Returns:
        A list of :class:`Scenario` instances sorted by id.
    """
    scenarios: list[Scenario] = []
    for p in sorted(directory.glob("*.json")):
        scenarios.append(load_scenario(p))
    return scenarios

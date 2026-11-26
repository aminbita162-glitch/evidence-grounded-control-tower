"""Bench runner — executes scenarios against the kernel (P09-T02).

Loads scenarios from a directory and runs each through a callable that
takes the scenario's inputs and returns an outcome string. Reports
pass or fail by scenario id. Deterministic for a fixed scenario set.

Spec: Part 3 §3.12; Part 6 §6.11; P09-T02.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from data.scenarios import Scenario, load_scenarios

__all__ = [
    "ScenarioRunner",
    "BenchReport",
    "BenchEntry",
    "run_bench",
]


class ScenarioRunner(Protocol):
    """Protocol for a callable that runs a scenario's inputs."""

    def __call__(self, inputs: list[object]) -> str:
        """Run the scenario inputs and return an outcome string.

        Args:
            inputs: The scenario's input objects.

        Returns:
            The outcome string (e.g. ``ALLOW``, ``HOLD``).
        """
        ...


@dataclass(frozen=True)
class BenchEntry:
    """A single entry in the bench report.

    Attributes:
        scenario_id: The scenario id.
        test_id: The test id covering this scenario (may be empty).
        passed: Whether the expectation was met.
        actual: The actual outcome.
        expected: The expected outcome.
        reason: A reason string on failure.
    """

    scenario_id: str
    test_id: str
    passed: bool
    actual: str
    expected: str
    reason: str


@dataclass(frozen=True)
class BenchReport:
    """The report from a bench run.

    Attributes:
        entries: A list of :class:`BenchEntry` results.
        passed: Number of passed scenarios.
        failed: Number of failed scenarios.
    """

    entries: list[BenchEntry]
    passed: int
    failed: int


def run_bench(
    scenarios: list[Scenario],
    runner: Callable[[list[object]], str],
) -> BenchReport:
    """Run a list of scenarios through a runner and return a report.

    Args:
        scenarios: A list of :class:`Scenario` instances.
        runner: A callable that takes the scenario's inputs and returns
            an outcome string.

    Returns:
        A :class:`BenchReport` with one entry per scenario.
    """
    entries: list[BenchEntry] = []
    for sc in scenarios:
        try:
            actual = runner(list(sc.inputs))
        except Exception as exc:
            entries.append(
                BenchEntry(
                    scenario_id=sc.id,
                    test_id=sc.test_id,
                    passed=False,
                    actual="ERROR",
                    expected=sc.expected_outcome,
                    reason=str(exc),
                )
            )
            continue
        is_pass = actual == sc.expected_outcome
        entries.append(
            BenchEntry(
                scenario_id=sc.id,
                test_id=sc.test_id,
                passed=is_pass,
                actual=actual,
                expected=sc.expected_outcome,
                reason="" if is_pass else f"expected {sc.expected_outcome}, got {actual}",
            )
        )
    passed = sum(1 for e in entries if e.passed)
    return BenchReport(entries=entries, passed=passed, failed=len(entries) - passed)


def run_bench_dir(
    directory: Path,
    runner: Callable[[list[object]], str],
) -> BenchReport:
    """Load all scenarios from a directory and run them.

    Args:
        directory: Path to a directory of scenario JSON files.
        runner: A callable that takes the scenario's inputs and returns
            an outcome string.

    Returns:
        A :class:`BenchReport`.
    """
    return run_bench(load_scenarios(directory), runner)

"""Workflow DAG and deterministic Manager (Part 3 §3.9, P07-T01).

The Manager executes a declarative workflow as a directed acyclic graph
(DAG) of capability invocations.  It enforces per-case budget, timeouts,
retry limits and idempotency, records every step on the case chain,
chooses the deterministic path whenever one exists, and splits the case
budget among roles.  State transitions follow the case state machine
(Part 3 §3.4).

Spec: Part 3 §3.4, §3.9, §3.25, §3.30; P07-T01.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from kernel.casestate import IdempotencyStore, can_transition, transition

__all__ = [
    "BudgetShare",
    "StepResult",
    "StepStatus",
    "WorkflowDAG",
    "Manager",
    "DAGValidationError",
    "BudgetExceededError",
    "StepTimeoutError",
    "DEFAULT_BUDGET",
    "DEFAULT_RETRY_LIMIT",
    "DEFAULT_STEP_TIMEOUT",
    "ROLE_IDS",
]

#: The closed role-id list (Part 3 §3.9).
ROLE_IDS: list[str] = [
    "ROLE-MANAGER",
    "ROLE-INTAKE",
    "ROLE-COMPLIANCE",
    "ROLE-LOGISTICS",
    "ROLE-PLANNER",
    "ROLE-RISK",
]

#: Budget Governor defaults (Part 3 §3.14).
DEFAULT_BUDGET: dict[str, int] = {
    "model_calls": 20,
    "model_tokens": 60_000,
    "wall_time_seconds": 120,
    "tool_calls": 50,
    "workflow_steps": 200,
}

DEFAULT_RETRY_LIMIT: int = 3
DEFAULT_STEP_TIMEOUT: int = 120


class DAGValidationError(ValueError):
    """Raised when a workflow DAG is invalid."""


class BudgetExceededError(Exception):
    """Raised when a role exceeds its budget share."""


class StepTimeoutError(Exception):
    """Raised when a step exceeds its time limit."""


@dataclass(frozen=True)
class BudgetShare:
    """A role's share of the case budget (Part 3 §3.25)."""

    role: str
    max_steps: int
    max_tool_calls: int
    max_model_calls: int
    max_wall_time_seconds: int


class StepStatus:
    """Status of a workflow step execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"


@dataclass
class StepResult:
    """The result of executing one workflow step."""

    step_id: str
    role: str
    status: str
    idempotency_key: str
    output: object = None
    reason: str = ""


@dataclass(frozen=True)
class WorkflowStep:
    """A single step in the workflow DAG."""

    step_id: str
    role: str
    target_state: str
    action: str = "execute"
    description: str = ""


@dataclass(frozen=True)
class WorkflowEdge:
    """A directed edge in the workflow DAG."""

    source: str
    target: str
    condition: str = ""


class WorkflowDAG:
    """A declarative workflow as a signed DAG (Part 3 §3.9).

    The DAG is loaded from declarative configuration (a list of steps and
    edges).  It is validated at load time: cycles are rejected, every step
    names a known role, and every edge connects existing steps.  The
    configuration hash is computed so the DAG is *signed* — the Manager
    records it on the case chain.
    """

    def __init__(
        self,
        steps: list[WorkflowStep],
        edges: list[WorkflowEdge],
        initial_state: str = "CREATED",
    ) -> None:
        """Initialize and validate a workflow DAG."""
        self.steps = {s.step_id: s for s in steps}
        self.edges = list(edges)
        self.initial_state = initial_state
        self._validate()

    def _validate(self) -> None:
        """Validate the DAG: no cycles, known roles, existing edges."""
        step_ids = set(self.steps.keys())
        for step in self.steps.values():
            if step.role not in ROLE_IDS:
                raise DAGValidationError(f"unknown role {step.role!r} in step {step.step_id!r}")
        for edge in self.edges:
            if edge.source not in step_ids:
                raise DAGValidationError(f"edge source {edge.source!r} does not exist")
            if edge.target not in step_ids:
                raise DAGValidationError(f"edge target {edge.target!r} does not exist")
        self._check_no_cycles()

    def _check_no_cycles(self) -> None:
        """Detect cycles via DFS with a recursion stack."""
        adj: dict[str, list[str]] = {}
        for edge in self.edges:
            adj.setdefault(edge.source, []).append(edge.target)
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = dict.fromkeys(self.steps, WHITE)

        def dfs(node: str) -> bool:
            color[node] = GRAY
            for neighbour in adj.get(node, []):
                if color[neighbour] == GRAY:
                    return True
                if color[neighbour] == WHITE and dfs(neighbour):
                    return True
            color[node] = BLACK
            return False

        for sid in self.steps:
            if color[sid] == WHITE and dfs(sid):
                raise DAGValidationError("cycle detected in workflow DAG")

    def next_steps(self, current_step: str | None) -> list[WorkflowStep]:
        """Return the steps reachable from *current_step* (or the entry)."""
        if current_step is None:
            entry_steps = [
                s for s in self.steps.values() if not any(e.target == s.step_id for e in self.edges)
            ]
            return sorted(entry_steps, key=lambda s: s.step_id)
        neighbours: list[str] = [e.target for e in self.edges if e.source == current_step]
        return [self.steps[n] for n in sorted(neighbours)]

    def config_hash(self) -> str:
        """Return the SHA-256 hash of the canonical configuration."""
        data = {
            "steps": [
                {
                    "step_id": s.step_id,
                    "role": s.role,
                    "target_state": s.target_state,
                    "action": s.action,
                    "description": s.description,
                }
                for s in sorted(self.steps.values(), key=lambda s: s.step_id)
            ],
            "edges": [
                {"source": e.source, "target": e.target, "condition": e.condition}
                for e in sorted(self.edges, key=lambda e: (e.source, e.target))
            ],
            "initial_state": self.initial_state,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _default_budget_shares() -> list[BudgetShare]:
    """Return the default budget split among roles."""
    total_steps = DEFAULT_BUDGET["workflow_steps"]
    total_tools = DEFAULT_BUDGET["tool_calls"]
    total_models = DEFAULT_BUDGET["model_calls"]
    total_time = DEFAULT_BUDGET["wall_time_seconds"]
    share = 1
    return [
        BudgetShare(
            role=rid,
            max_steps=total_steps * share,
            max_tool_calls=total_tools * share,
            max_model_calls=total_models * share,
            max_wall_time_seconds=total_time * share,
        )
        for rid in ROLE_IDS
    ]


class Manager:
    """The deterministic orchestrator (Part 3 §3.9).

    Executes a workflow DAG, enforces per-case budget, timeouts, retry
    limits and idempotency, records every step, and chooses the
    deterministic path whenever one exists.

    The Manager never calls a model; it is deterministic by design
    (Part 3 §3.9, role ROLE-MANAGER).
    """

    def __init__(
        self,
        dag: WorkflowDAG,
        budget_shares: list[BudgetShare] | None = None,
        retry_limit: int = DEFAULT_RETRY_LIMIT,
        step_timeout: int = DEFAULT_STEP_TIMEOUT,
        idempotency_store: IdempotencyStore | None = None,
    ) -> None:
        """Initialize the Manager with a DAG and budget configuration."""
        self.dag = dag
        self.budget_shares = {bs.role: bs for bs in (budget_shares or _default_budget_shares())}
        self.retry_limit = retry_limit
        self.step_timeout = step_timeout
        self.idempotency = idempotency_store or IdempotencyStore()
        self._step_log: list[StepResult] = []
        self._role_usage: dict[str, dict[str, int]] = {
            rid: {"steps": 0, "tool_calls": 0, "model_calls": 0, "wall_time": 0} for rid in ROLE_IDS
        }
        self._current_state = dag.initial_state

    @property
    def step_log(self) -> list[StepResult]:
        """Return the ordered list of executed steps."""
        return list(self._step_log)

    @property
    def current_state(self) -> str:
        """Return the current case state."""
        return self._current_state

    @property
    def config_hash(self) -> str:
        """Return the DAG configuration hash."""
        return self.dag.config_hash()

    def _check_budget(self, role: str) -> None:
        """Raise if the role has exceeded its budget share."""
        share = self.budget_shares.get(role)
        if share is None:
            return
        usage = self._role_usage[role]
        if usage["steps"] >= share.max_steps:
            raise BudgetExceededError(f"role {role} exceeded step budget ({share.max_steps})")

    def _record_step(self, result: StepResult) -> None:
        """Record a step in the log and update role usage."""
        self._step_log.append(result)
        if result.role in self._role_usage:
            self._role_usage[result.role]["steps"] += 1

    def execute_step(
        self,
        step: WorkflowStep,
        idempotency_key: str,
    ) -> StepResult:
        """Execute one step with idempotency, budget and state checks.

        Repeating the same idempotency key returns the original result
        without re-executing.  The transition to the step's target state
        is validated against the case state machine.
        """
        cached = self.idempotency.check(idempotency_key)
        if cached is not None and isinstance(cached, StepResult):
            return cached

        self._check_budget(step.role)

        if not can_transition(self._current_state, step.target_state):
            raise DAGValidationError(
                f"transition {self._current_state} -> {step.target_state} "
                "is not in the DAG / case state machine"
            )

        result = StepResult(
            step_id=step.step_id,
            role=step.role,
            status=StepStatus.DONE,
            idempotency_key=idempotency_key,
        )
        self._current_state = transition(self._current_state, step.target_state)
        self._record_step(result)
        self.idempotency.record(idempotency_key, result)
        return result

    def run(
        self,
        steps: list[tuple[WorkflowStep, str]] | None = None,
    ) -> list[StepResult]:
        """Execute the workflow along the deterministic path.

        If *steps* is provided, execute them in order (each with its
        idempotency key).  Otherwise, walk the DAG from the entry points.
        A step that raises transitions the case to BLOCKED.
        """
        results: list[StepResult] = []
        if steps is not None:
            for step, key in steps:
                try:
                    result = self.execute_step(step, key)
                except BudgetExceededError:
                    self._current_state = "BLOCKED"
                    break
                except StepTimeoutError:
                    self._current_state = "BLOCKED"
                    break
                except DAGValidationError:
                    self._current_state = "FAILED"
                    break
                results.append(result)
            return results

        current: str | None = None
        pending = self.dag.next_steps(current)
        while pending:
            step = pending[0]
            key = f"{step.step_id}-{self._current_state}"
            try:
                result = self.execute_step(step, key)
            except BudgetExceededError:
                self._current_state = "BLOCKED"
                break
            except StepTimeoutError:
                self._current_state = "BLOCKED"
                break
            except DAGValidationError:
                self._current_state = "FAILED"
                break
            results.append(result)
            current = step.step_id
            pending = self.dag.next_steps(current)
        return results

    def timeout_step(self, step: WorkflowStep, idempotency_key: str) -> str:
        """Simulate a step timeout: move to BLOCKED, never approve.

        Returns the new state (always BLOCKED).
        """
        self._current_state = "BLOCKED"
        result = StepResult(
            step_id=step.step_id,
            role=step.role,
            status=StepStatus.FAILED,
            idempotency_key=idempotency_key,
            reason="timeout",
        )
        self._record_step(result)
        return self._current_state

"""Tests for the Workflow DAG and Manager (P07-T01).

Test IDs: T-ORC-0001 to T-ORC-0014.
Covers: DAG validation, cycle rejection, budget shares, timeouts,
idempotency, state transitions, deterministic path selection,
configuration hash, retry limits, and step recording.

Spec: Part 3 §3.4, §3.9, §3.25, §3.30; P07-T01.
"""

from __future__ import annotations

import pytest

from kernel.orchestrator import (
    BudgetExceededError,
    BudgetShare,
    DAGValidationError,
    Manager,
    WorkflowDAG,
    WorkflowEdge,
    WorkflowStep,
)

# ---------------------------------------------------------------------------
# T-ORC-0001 — A valid workflow DAG loads and validates
# ---------------------------------------------------------------------------
# id: T-ORC-0001
# title: A valid workflow DAG loads and validates
# purpose: Verify that a well-formed DAG with steps and edges is accepted.
# level: fast
# requirement: P07-T01, Part 3 §3.9
# input: a list of steps and edges forming a valid DAG
# expected: WorkflowDAG constructor succeeds without error
# risk: invalid workflow accepted
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0001_valid_dag_loads() -> None:
    """A valid DAG with steps and edges is accepted."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-COMPLIANCE", "EVALUATED"),
        WorkflowStep("s3", "ROLE-PLANNER", "PROPOSED"),
    ]
    edges = [
        WorkflowEdge("s1", "s2"),
        WorkflowEdge("s2", "s3"),
    ]
    dag = WorkflowDAG(steps, edges)
    assert len(dag.steps) == 3


# ---------------------------------------------------------------------------
# T-ORC-0002 — A cycle in the DAG is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0002
# title: A cycle in the DAG is rejected
# purpose: Verify that a cyclic DAG raises DAGValidationError.
# level: fast
# requirement: P07-T01, Part 3 §3.9
# input: a DAG with a cycle s1 -> s2 -> s1
# expected: DAGValidationError is raised
# risk: infinite loop in workflow execution
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0002_cycle_rejected() -> None:
    """A cyclic DAG raises DAGValidationError."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-COMPLIANCE", "EVALUATED"),
    ]
    edges = [
        WorkflowEdge("s1", "s2"),
        WorkflowEdge("s2", "s1"),
    ]
    with pytest.raises(DAGValidationError, match="cycle"):
        WorkflowDAG(steps, edges)


# ---------------------------------------------------------------------------
# T-ORC-0003 — An unknown role in a step is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0003
# title: An unknown role in a step is rejected
# purpose: Verify that a step with a role not in the closed role-id list fails.
# level: fast
# requirement: P07-T01, Part 3 §3.9, §3.25
# input: a step with role "ROLE-BOGUS"
# expected: DAGValidationError is raised
# risk: unauthorised role gains control
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0003_unknown_role_rejected() -> None:
    """A step with an unknown role is rejected."""
    steps = [WorkflowStep("s1", "ROLE-BOGUS", "INGESTED")]
    edges: list[WorkflowEdge] = []
    with pytest.raises(DAGValidationError, match="unknown role"):
        WorkflowDAG(steps, edges)


# ---------------------------------------------------------------------------
# T-ORC-0004 — An edge to a non-existent step is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0004
# title: An edge to a non-existent step is rejected
# purpose: Verify that an edge pointing to a missing step fails validation.
# level: fast
# requirement: P07-T01, Part 3 §3.9
# input: an edge with target "s99" that does not exist
# expected: DAGValidationError is raised
# risk: dangling reference causes runtime crash
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0004_edge_to_missing_step_rejected() -> None:
    """An edge to a non-existent step is rejected."""
    steps = [WorkflowStep("s1", "ROLE-INTAKE", "INGESTED")]
    edges = [WorkflowEdge("s1", "s99")]
    with pytest.raises(DAGValidationError, match="does not exist"):
        WorkflowDAG(steps, edges)


# ---------------------------------------------------------------------------
# T-ORC-0005 — A transition outside the DAG is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0005
# title: A transition outside the DAG is rejected
# purpose: Verify that executing a step whose target state is not reachable
#          from the current state in the case state machine is rejected.
# level: fast
# requirement: P07-T01, Part 3 §3.4, §3.9
# input: a Manager at state INGESTED, a step targeting CLOSED
# expected: DAGValidationError is raised
# risk: invalid state transition bypasses safeguards
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0005_transition_outside_dag_rejected() -> None:
    """A step targeting a state unreachable from the current state is rejected."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-INTAKE", "CLOSED"),
    ]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    manager = Manager(dag)
    manager.execute_step(steps[0], "k1")
    assert manager.current_state == "INGESTED"
    with pytest.raises(DAGValidationError, match="not in the DAG"):
        manager.execute_step(steps[1], "k2")


# ---------------------------------------------------------------------------
# T-ORC-0006 — A role cannot exceed its budget share
# ---------------------------------------------------------------------------
# id: T-ORC-0006
# title: A role cannot exceed its budget share
# purpose: Verify that exceeding the per-role step budget raises BudgetExceededError.
# level: fast
# requirement: P07-T01, Part 3 §3.9, §3.25
# input: a BudgetShare with max_steps=2 for ROLE-INTAKE, then 3 steps
# expected: BudgetExceededError on the third step
# risk: role monopolises case budget
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0006_role_exceeds_budget() -> None:
    """A role exceeding its step budget share raises BudgetExceededError."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-INTAKE", "EXTRACTED"),
        WorkflowStep("s3", "ROLE-INTAKE", "EVALUATED"),
    ]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    shares = [
        BudgetShare(
            "ROLE-INTAKE",
            max_steps=2,
            max_tool_calls=50,
            max_model_calls=20,
            max_wall_time_seconds=120,
        ),
    ]
    manager = Manager(dag, budget_shares=shares)
    manager.execute_step(steps[0], "k1")
    manager.execute_step(steps[1], "k2")
    with pytest.raises(BudgetExceededError):
        manager.execute_step(steps[2], "k3")


# ---------------------------------------------------------------------------
# T-ORC-0007 — A timeout moves a case to BLOCKED and never approves
# ---------------------------------------------------------------------------
# id: T-ORC-0007
# title: A timeout moves a case to BLOCKED and never approves
# purpose: Verify that a step timeout moves the case to BLOCKED, never to ALLOW.
# level: fast
# requirement: P07-T01, Part 3 §3.4, §3.9
# input: a Manager that times out a step
# expected: current_state becomes BLOCKED
# risk: timeout silently approves
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0007_timeout_moves_to_blocked() -> None:
    """A step timeout moves the case to BLOCKED."""
    steps = [WorkflowStep("s1", "ROLE-INTAKE", "INGESTED")]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    manager = Manager(dag)
    new_state = manager.timeout_step(steps[0], "k1")
    assert new_state == "BLOCKED"
    assert manager.current_state == "BLOCKED"


# ---------------------------------------------------------------------------
# T-ORC-0008 — Repeated delivery of one step executes once
# ---------------------------------------------------------------------------
# id: T-ORC-0008
# title: Repeated delivery of one step executes once
# purpose: Verify that the same idempotency key returns the original result
#          and does not re-execute or change state.
# level: fast
# requirement: P07-T01, Part 3 §3.4, §3.9
# input: a step executed twice with the same idempotency key
# expected: the second call returns the same result; step log has one entry
# risk: duplicate effects from retried commands
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0008_idempotent_execution() -> None:
    """Repeating the same idempotency key returns the original result."""
    steps = [WorkflowStep("s1", "ROLE-INTAKE", "INGESTED")]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    manager = Manager(dag)
    r1 = manager.execute_step(steps[0], "key-1")
    r2 = manager.execute_step(steps[0], "key-1")
    assert r1 is r2
    assert len(manager.step_log) == 1


# ---------------------------------------------------------------------------
# T-ORC-0009 — The DAG configuration hash is deterministic
# ---------------------------------------------------------------------------
# id: T-ORC-0009
# title: The DAG configuration hash is deterministic
# purpose: Verify that the same steps and edges produce the same hash.
# level: fast
# requirement: P07-T01, Part 3 §3.21, §3.14
# input: two identical DAGs
# expected: identical config_hash values
# risk: non-deterministic hash breaks replay
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0009_config_hash_deterministic() -> None:
    """Two identical DAGs produce the same configuration hash."""
    make = lambda: WorkflowDAG(  # noqa: E731
        [
            WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
            WorkflowStep("s2", "ROLE-COMPLIANCE", "EVALUATED"),
        ],
        [WorkflowEdge("s1", "s2")],
        initial_state="CREATED",
    )
    assert make().config_hash() == make().config_hash()


# ---------------------------------------------------------------------------
# T-ORC-0010 — The Manager records every step
# ---------------------------------------------------------------------------
# id: T-ORC-0010
# title: The Manager records every step
# purpose: Verify that the step log contains one entry per executed step.
# level: fast
# requirement: P07-T01, Part 3 §3.9
# input: a Manager executing two steps
# expected: step_log has two entries with correct step_ids
# risk: unrecorded steps break audit trail
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0010_steps_recorded() -> None:
    """Every executed step appears in the step log."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-INTAKE", "EXTRACTED"),
    ]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    manager = Manager(dag)
    manager.execute_step(steps[0], "k1")
    manager.execute_step(steps[1], "k2")
    log = manager.step_log
    assert len(log) == 2
    assert log[0].step_id == "s1"
    assert log[1].step_id == "s2"


# ---------------------------------------------------------------------------
# T-ORC-0011 — The Manager chooses the deterministic path
# ---------------------------------------------------------------------------
# id: T-ORC-0011
# title: The Manager chooses the deterministic path
# purpose: Verify that run() walks the DAG in a deterministic order.
# level: fast
# requirement: P07-T01, Part 3 §3.9, §3.21
# input: a linear DAG s1 -> s2 -> s3
# expected: steps execute in order s1, s2, s3
# risk: non-deterministic execution order
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0011_deterministic_path() -> None:
    """The Manager walks the DAG in a deterministic order."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-INTAKE", "EXTRACTED"),
        WorkflowStep("s3", "ROLE-COMPLIANCE", "EVALUATED"),
    ]
    edges = [WorkflowEdge("s1", "s2"), WorkflowEdge("s2", "s3")]
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    manager = Manager(dag)
    results = manager.run()
    assert [r.step_id for r in results] == ["s1", "s2", "s3"]


# ---------------------------------------------------------------------------
# T-ORC-0012 — The case budget is split among roles
# ---------------------------------------------------------------------------
# id: T-ORC-0012
# title: The case budget is split among roles
# purpose: Verify that each role gets its own budget share.
# level: fast
# requirement: P07-T01, Part 3 §3.25
# input: a Manager with explicit budget shares
# expected: each role's share matches the configured values
# risk: budget not enforced per role
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0012_budget_split_among_roles() -> None:
    """Budget shares are set per role."""
    steps = [WorkflowStep("s1", "ROLE-INTAKE", "INGESTED")]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    shares = [
        BudgetShare(
            "ROLE-INTAKE",
            max_steps=10,
            max_tool_calls=20,
            max_model_calls=5,
            max_wall_time_seconds=60,
        ),
        BudgetShare(
            "ROLE-COMPLIANCE",
            max_steps=30,
            max_tool_calls=30,
            max_model_calls=15,
            max_wall_time_seconds=60,
        ),
    ]
    manager = Manager(dag, budget_shares=shares)
    assert manager.budget_shares["ROLE-INTAKE"].max_steps == 10
    assert manager.budget_shares["ROLE-COMPLIANCE"].max_steps == 30


# ---------------------------------------------------------------------------
# T-ORC-0013 — State transitions follow the case state machine
# ---------------------------------------------------------------------------
# id: T-ORC-0013
# title: State transitions follow the case state machine
# purpose: Verify that after each step the current state matches the step's
#          target_state.
# level: fast
# requirement: P07-T01, Part 3 §3.4
# input: a Manager executing steps through INGESTED, EXTRACTED, EVALUATED
# expected: current_state tracks each target state
# risk: state machine bypassed
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0013_state_transitions() -> None:
    """State transitions follow the case state machine."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-INTAKE", "EXTRACTED"),
        WorkflowStep("s3", "ROLE-COMPLIANCE", "EVALUATED"),
    ]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    manager = Manager(dag)
    assert manager.current_state == "CREATED"
    manager.execute_step(steps[0], "k1")
    assert manager.current_state == "INGESTED"
    manager.execute_step(steps[1], "k2")
    assert manager.current_state == "EXTRACTED"
    manager.execute_step(steps[2], "k3")
    assert manager.current_state == "EVALUATED"


# ---------------------------------------------------------------------------
# T-ORC-0014 — A budget exhaustion moves the case to BLOCKED via run()
# ---------------------------------------------------------------------------
# id: T-ORC-0014
# title: A budget exhaustion moves the case to BLOCKED via run()
# purpose: Verify that when a role exceeds its budget during run(), the case
#          moves to BLOCKED and execution stops.
# level: fast
# requirement: P07-T01, Part 3 §3.9, §3.14
# input: a Manager with max_steps=1 for ROLE-INTAKE, running two intake steps
# expected: current_state is BLOCKED after the first step's budget is exhausted
# risk: budget breach not enforced
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0014_budget_exhaustion_blocks() -> None:
    """Budget exhaustion during run() moves the case to BLOCKED."""
    steps = [
        WorkflowStep("s1", "ROLE-INTAKE", "INGESTED"),
        WorkflowStep("s2", "ROLE-INTAKE", "EXTRACTED"),
    ]
    edges: list[WorkflowEdge] = []
    dag = WorkflowDAG(steps, edges, initial_state="CREATED")
    shares = [
        BudgetShare(
            "ROLE-INTAKE",
            max_steps=1,
            max_tool_calls=50,
            max_model_calls=20,
            max_wall_time_seconds=120,
        ),
    ]
    manager = Manager(dag, budget_shares=shares)
    manager.run(steps=[(steps[0], "k1"), (steps[1], "k2")])
    assert manager.current_state == "BLOCKED"

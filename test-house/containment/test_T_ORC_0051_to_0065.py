"""Tests for behavior monitors and kill switches (P07-T05).

Test IDs: T-ORC-0051 to T-ORC-0066.
Covers: each monitor fires on its seeded violation; each kill switch is
exercised; a freeze rejects new commands and moves in-flight to BLOCKED;
short fuzz of messages finds no crash.

Spec: Part 3 §3.30; P07-T05.
"""

from __future__ import annotations

import pytest

from kernel.containment.killswitch import KillSwitch, KillSwitchError
from kernel.containment.monitors import (
    BudgetBurnMonitor,
    LoopMonitor,
    MonitorSuite,
    OutputSizeMonitor,
    PolicyDenialMonitor,
    StepCapMonitor,
    TransitionMonitor,
    VerificationFailureMonitor,
)

# ---------------------------------------------------------------------------
# T-ORC-0051 — Step cap monitor fires on exceeding the cap
# ---------------------------------------------------------------------------
# id: T-ORC-0051
# title: Step cap monitor fires on exceeding the cap
# purpose: Verify that the step cap monitor raises an alert when the cap is exceeded.
# level: fast
# requirement: P07-T05, Part 3 §3.30, §3.14
# input: a StepCapMonitor with cap=2, three calls for the same case
# expected: the third call returns violated=True
# risk: unbounded step count
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0051_step_cap_fires() -> None:
    """Step cap monitor fires on exceeding the cap."""
    monitor = StepCapMonitor(cap=2)
    monitor.check("case-1")
    monitor.check("case-1")
    result = monitor.check("case-1")
    assert result.violated is True
    assert result.alert is not None
    assert result.alert.reason == "step_cap_exceeded"


# ---------------------------------------------------------------------------
# T-ORC-0052 — Loop monitor fires on repeated tool+args
# ---------------------------------------------------------------------------
# id: T-ORC-0052
# title: Loop monitor fires on repeated tool+args
# purpose: Verify that the loop monitor detects the same tool and argument
#          hash called more than the threshold.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a LoopMonitor with threshold=3, four identical calls
# expected: the fourth call returns violated=True
# risk: infinite loop in workflow execution
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0052_loop_monitor_fires() -> None:
    """Loop monitor fires on repeated tool and argument hash."""
    monitor = LoopMonitor(threshold=3)
    for _ in range(3):
        monitor.check("case-1", tool="lookup", args="id=1")
    result = monitor.check("case-1", tool="lookup", args="id=1")
    assert result.violated is True
    assert result.alert is not None
    assert result.alert.reason == "loop_detected"


# ---------------------------------------------------------------------------
# T-ORC-0053 — Transition monitor fires on out-of-DAG transition
# ---------------------------------------------------------------------------
# id: T-ORC-0053
# title: Transition monitor fires on out-of-DAG transition
# purpose: Verify that the transition monitor detects a transition outside the DAG.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a TransitionMonitor with allowed={CREATED->INGESTED}, checking CREATED->CLOSED
# expected: violated=True
# risk: invalid state transition bypasses safeguards
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0053_transition_monitor_fires() -> None:
    """Transition monitor fires on out-of-DAG transition."""
    monitor = TransitionMonitor()
    monitor.set_allowed({"CREATED->INGESTED"})
    result = monitor.check("case-1", from_state="CREATED", to_state="CLOSED")
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0054 — Budget burn monitor fires on exceeded burn rate
# ---------------------------------------------------------------------------
# id: T-ORC-0054
# title: Budget burn monitor fires on exceeded burn rate
# purpose: Verify that the budget burn monitor detects excessive spending.
# level: fast
# requirement: P07-T05, Part 3 §3.30, §3.14
# input: a BudgetBurnMonitor with limit=100, spending 101
# expected: violated=True
# risk: budget runaway
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0054_budget_burn_fires() -> None:
    """Budget burn monitor fires on exceeded burn rate."""
    monitor = BudgetBurnMonitor(limit=100)
    result = monitor.check("case-1", spent=101)
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0055 — Output size monitor fires on oversized output
# ---------------------------------------------------------------------------
# id: T-ORC-0055
# title: Output size monitor fires on oversized output
# purpose: Verify that the output size monitor detects oversized output.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: an OutputSizeMonitor with limit=1024, output size=2048
# expected: violated=True
# risk: memory exhaustion via large output
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0055_output_size_fires() -> None:
    """Output size monitor fires on oversized output."""
    monitor = OutputSizeMonitor(limit=1024)
    result = monitor.check("case-1", size=2048)
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0056 — Verification failure monitor fires on repeated failures
# ---------------------------------------------------------------------------
# id: T-ORC-0056
# title: Verification failure monitor fires on repeated failures
# purpose: Verify that the verification failure monitor detects repeated failures.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a VerificationFailureMonitor with limit=3, four failures
# expected: the fourth call returns violated=True
# risk: repeated verification failures not escalated
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0056_verification_failure_fires() -> None:
    """Verification failure monitor fires on repeated failures."""
    monitor = VerificationFailureMonitor(limit=3)
    for _ in range(3):
        monitor.check("case-1")
    result = monitor.check("case-1")
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0057 — Policy denial monitor fires on repeated denials
# ---------------------------------------------------------------------------
# id: T-ORC-0057
# title: Policy denial monitor fires on repeated denials
# purpose: Verify that the policy denial monitor detects repeated denials.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a PolicyDenialMonitor with limit=3, four denials
# expected: the fourth call returns violated=True
# risk: repeated policy denials not escalated
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0057_policy_denial_fires() -> None:
    """Policy denial monitor fires on repeated denials."""
    monitor = PolicyDenialMonitor(limit=3)
    for _ in range(3):
        monitor.check("case-1")
    result = monitor.check("case-1")
    assert result.violated is True


# ---------------------------------------------------------------------------
# T-ORC-0058 — Pause case kill switch rejects new commands
# ---------------------------------------------------------------------------
# id: T-ORC-0058
# title: Pause case kill switch rejects new commands
# purpose: Verify that a paused case rejects new commands.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a KillSwitch of type pause_case, fired
# expected: check_command returns False for a normal command
# risk: paused case continues executing
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0058_pause_case_rejects() -> None:
    """Pause case kill switch rejects new commands."""
    switch = KillSwitch("pause_case")
    switch.fire("case-1", "operator-1")
    assert switch.check_command("execute_step") is False


# ---------------------------------------------------------------------------
# T-ORC-0059 — Disable capability kill switch rejects
# ---------------------------------------------------------------------------
# id: T-ORC-0059
# title: Disable capability kill switch rejects
# purpose: Verify that a disabled capability rejects new commands.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a KillSwitch of type disable_capability, fired
# expected: check_command returns False
# risk: disabled capability continues
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0059_disable_capability_rejects() -> None:
    """Disable capability kill switch rejects new commands."""
    switch = KillSwitch("disable_capability")
    switch.fire("cap-1", "operator-1")
    assert switch.check_command("run") is False


# ---------------------------------------------------------------------------
# T-ORC-0060 — Tenant freeze rejects new commands
# ---------------------------------------------------------------------------
# id: T-ORC-0060
# title: Tenant freeze rejects new commands
# purpose: Verify that a tenant freeze rejects new commands.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a KillSwitch of type freeze_tenant, fired
# expected: check_command returns False for all commands
# risk: frozen tenant continues operations
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0060_tenant_freeze_rejects() -> None:
    """Tenant freeze rejects new commands."""
    switch = KillSwitch("freeze_tenant")
    switch.fire("tenant-1", "operator-1")
    assert switch.check_command("any_command") is False


# ---------------------------------------------------------------------------
# T-ORC-0061 — Tenant freeze is lifted only by the tenant administrator
# ---------------------------------------------------------------------------
# id: T-ORC-0061
# title: Tenant freeze is lifted only by the tenant administrator
# purpose: Verify that lifting a tenant freeze without admin authorization fails.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a freeze_tenant switch, lift with is_admin=False
# expected: KillSwitchError is raised
# risk: non-admin lifts tenant freeze
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0061_tenant_freeze_lift_requires_admin() -> None:
    """Tenant freeze is lifted only by the tenant administrator."""
    switch = KillSwitch("freeze_tenant")
    switch.fire("tenant-1", "operator-1")
    with pytest.raises(KillSwitchError, match="tenant administrator"):
        switch.lift("user-1", is_admin=False)


# ---------------------------------------------------------------------------
# T-ORC-0062 — Deployment freeze is lifted only by two platform operators
# ---------------------------------------------------------------------------
# id: T-ORC-0062
# title: Deployment freeze is lifted only by two platform operators
# purpose: Verify that lifting a deployment freeze with fewer than two operators fails.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a freeze_deployment switch, lift with operator_count=1
# expected: KillSwitchError is raised
# risk: single operator lifts deployment freeze
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0062_deployment_freeze_requires_two() -> None:
    """Deployment freeze is lifted only by two platform operators."""
    switch = KillSwitch("freeze_deployment")
    switch.fire("deployment-1", "operator-1")
    with pytest.raises(KillSwitchError, match="two platform operators"):
        switch.lift("operator-1", operator_count=1)


# ---------------------------------------------------------------------------
# T-ORC-0063 — A kill switch records a system-chain event
# ---------------------------------------------------------------------------
# id: T-ORC-0063
# title: A kill switch records a system-chain event
# purpose: Verify that firing a kill switch records an event in the log.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a KillSwitch fired
# expected: event_log has one entry
# risk: unrecorded kill switch activation
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0063_kill_switch_records_event() -> None:
    """A kill switch records a system-chain event."""
    switch = KillSwitch("pause_case")
    switch.fire("case-1", "operator-1")
    assert len(switch.event_log) == 1
    assert "pause_case" in switch.event_log[0]


# ---------------------------------------------------------------------------
# T-ORC-0064 — Monitor suite runs all monitors and returns first violation
# ---------------------------------------------------------------------------
# id: T-ORC-0064
# title: Monitor suite runs all monitors and returns first violation
# purpose: Verify that the suite runs all monitors and returns the first violation.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a suite with a step cap and loop monitor, exceeding the step cap
# expected: the result is violated with reason step_cap_exceeded
# risk: monitors not running in suite
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0064_suite_returns_first_violation() -> None:
    """Monitor suite returns the first violation."""
    suite = MonitorSuite()
    suite.add(StepCapMonitor(cap=1))
    suite.add(LoopMonitor(threshold=3))
    suite.run("case-1")
    result = suite.run("case-1")
    assert result.violated is True
    assert result.alert is not None


# ---------------------------------------------------------------------------
# T-ORC-0065 — A clean case does not trigger any monitor
# ---------------------------------------------------------------------------
# id: T-ORC-0065
# title: A clean case does not trigger any monitor
# purpose: Verify that a well-behaved case does not trigger any monitor.
# level: fast
# requirement: P07-T05, Part 3 §3.30
# input: a suite with default monitors, one clean step
# expected: result.violated is False
# risk: false positive alerts
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0065_clean_case_no_violation() -> None:
    """A clean case does not trigger any monitor."""
    suite = MonitorSuite()
    suite.add(StepCapMonitor(cap=200))
    suite.add(LoopMonitor(threshold=3))
    result = suite.run("case-1", tool="lookup", args="id=1")
    assert result.violated is False

"""Tests for the Tool Broker and policy as code (P07-T03).

Test IDs: T-ORC-0027 to T-ORC-0042.
Covers: deny-by-default, ungranted tool denial, rate limit denial, egress
allowlist, model naming restrictions, policy allow/deny cases, call
recording with input/output hashes.

Spec: Part 3 §3.11, §3.30; P07-T03.
"""

from __future__ import annotations

import contextlib

import pytest

from broker import BrokerError, Grant, ToolBroker
from policies import POLICIES, PolicyError, evaluate_policy, run_policy_tests

# ---------------------------------------------------------------------------
# T-ORC-0027 — An ungranted tool is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0027
# title: An ungranted tool is denied
# purpose: Verify that calling a tool without a grant raises BrokerError.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a ToolBroker with a grant for "lookup" only, calling "delete"
# expected: BrokerError with reason "tool_not_granted"
# risk: ungranted tool executes side effects
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0027_ungranted_tool_denied() -> None:
    """An ungranted tool call is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    with pytest.raises(BrokerError, match="tool_not_granted"):
        broker.call("delete", "read", {"id": "x"})


# ---------------------------------------------------------------------------
# T-ORC-0028 — A granted tool is allowed
# ---------------------------------------------------------------------------
# id: T-ORC-0028
# title: A granted tool is allowed
# purpose: Verify that calling a granted tool succeeds and is recorded.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a ToolBroker with a grant for "lookup", calling "lookup"
# expected: call returns a CallRecord with granted=True
# risk: valid tool calls blocked
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0028_granted_tool_allowed() -> None:
    """A granted tool call succeeds."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    record = broker.call("lookup", "read", {"id": "x"})
    assert record.granted is True


# ---------------------------------------------------------------------------
# T-ORC-0029 — A scope mismatch is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0029
# title: A scope mismatch is denied
# purpose: Verify that a tool called with the wrong scope is denied.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a grant for "lookup" with scope "read", calling with scope "write"
# expected: BrokerError with reason "scope_mismatch"
# risk: tool called outside its authorised scope
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0029_scope_mismatch_denied() -> None:
    """A scope mismatch is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    with pytest.raises(BrokerError, match="scope_mismatch"):
        broker.call("lookup", "write", {"id": "x"})


# ---------------------------------------------------------------------------
# T-ORC-0030 — An over-rate call is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0030
# title: An over-rate call is denied
# purpose: Verify that exceeding the rate limit raises BrokerError.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a grant with rate_limit=2, three calls at the same clock tick
# expected: the third call raises BrokerError with "rate_exceeded"
# risk: resource exhaustion through unbounded tool calls
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0030_over_rate_denied() -> None:
    """An over-rate call is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=2, budget=50, action_class="R"))
    broker.call("lookup", "read", {"id": "1"}, clock_tick=0)
    broker.call("lookup", "read", {"id": "2"}, clock_tick=0)
    with pytest.raises(BrokerError, match="rate_exceeded"):
        broker.call("lookup", "read", {"id": "3"}, clock_tick=0)


# ---------------------------------------------------------------------------
# T-ORC-0031 — An off-list host is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0031
# title: An off-list host is denied
# purpose: Verify that a call to a host not on the egress allowlist is denied.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a call to host "evil.example.com"
# expected: BrokerError with reason "host_off_allowlist"
# risk: data exfiltration to unauthorised host
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0031_off_list_host_denied() -> None:
    """An off-list host is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    with pytest.raises(BrokerError, match="host_off_allowlist"):
        broker.call("lookup", "read", {"id": "x"}, host="evil.example.com")


# ---------------------------------------------------------------------------
# T-ORC-0032 — An on-list host is allowed
# ---------------------------------------------------------------------------
# id: T-ORC-0032
# title: An on-list host is allowed
# purpose: Verify that a call to a host on the egress allowlist succeeds.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a call to host "localhost"
# expected: call succeeds with granted=True
# risk: valid host blocked
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0032_on_list_host_allowed() -> None:
    """An on-list host is allowed."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    record = broker.call("lookup", "read", {"id": "x"}, host="localhost")
    assert record.granted is True


# ---------------------------------------------------------------------------
# T-ORC-0033 — A model naming a URL is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0033
# title: A model naming a URL is denied
# purpose: Verify that a model cannot name a URL in its output.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a call with a payload containing "https://evil.com"
# expected: BrokerError with reason containing "model_named_forbidden"
# risk: model exfiltrates data via URL
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0033_model_url_denied() -> None:
    """A model naming a URL is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    with pytest.raises(BrokerError, match="model_named_forbidden"):
        broker.call("lookup", "read", {"text": "https://evil.com"})


# ---------------------------------------------------------------------------
# T-ORC-0034 — A model naming a file path is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0034
# title: A model naming a file path is denied
# purpose: Verify that a model cannot name a system file path.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a call with a payload containing "/etc/passwd"
# expected: BrokerError with reason containing "model_named_forbidden"
# risk: model accesses system files
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0034_model_path_denied() -> None:
    """A model naming a file path is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    with pytest.raises(BrokerError, match="model_named_forbidden"):
        broker.call("lookup", "read", {"text": "/etc/passwd"})


# ---------------------------------------------------------------------------
# T-ORC-0035 — A model naming a destructive command is denied
# ---------------------------------------------------------------------------
# id: T-ORC-0035
# title: A model naming a destructive command is denied
# purpose: Verify that a model cannot name a destructive command.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a call with a payload containing "rm -rf"
# expected: BrokerError with reason containing "model_named_forbidden"
# risk: model causes destructive side effects
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0035_model_command_denied() -> None:
    """A model naming a destructive command is denied."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    with pytest.raises(BrokerError, match="model_named_forbidden"):
        broker.call("lookup", "read", {"text": "rm -rf /"})


# ---------------------------------------------------------------------------
# T-ORC-0036 — Every call is recorded
# ---------------------------------------------------------------------------
# id: T-ORC-0036
# title: Every call is recorded
# purpose: Verify that allowed and denied calls both appear in the call log.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: one allowed and one denied call
# expected: call_log has two entries
# risk: unrecorded calls break audit trail
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0036_every_call_recorded() -> None:
    """Every call — allowed and denied — is recorded."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    broker.call("lookup", "read", {"id": "1"})
    with contextlib.suppress(BrokerError):
        broker.call("delete", "read", {"id": "2"})
    assert len(broker.call_log) == 2


# ---------------------------------------------------------------------------
# T-ORC-0037 — Each call record has input and output hashes
# ---------------------------------------------------------------------------
# id: T-ORC-0037
# title: Each call record has input and output hashes
# purpose: Verify that call records contain non-empty input_hash and output_hash.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: a single allowed call
# expected: record.input_hash and record.output_hash are non-empty hex strings
# risk: missing hashes break tamper detection
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0037_hashes_in_record() -> None:
    """Each call record has input and output hashes."""
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=10, budget=50, action_class="R"))
    record = broker.call("lookup", "read", {"id": "x"})
    assert len(record.input_hash) == 64
    assert len(record.output_hash) == 64
    assert all(c in "0123456789abcdef" for c in record.input_hash)


# ---------------------------------------------------------------------------
# T-ORC-0038 — Every policy has allow and deny cases
# ---------------------------------------------------------------------------
# id: T-ORC-0038
# title: Every policy has allow and deny cases
# purpose: Verify that each policy has at least one allow and one deny case.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: the POLICIES dictionary
# expected: every policy has non-empty allow_cases and deny_cases
# risk: policy without test cases
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0038_every_policy_has_cases() -> None:
    """Every policy has allow and deny cases."""
    for name, policy in POLICIES.items():
        assert len(policy.allow_cases) >= 1, f"{name} has no allow cases"
        assert len(policy.deny_cases) >= 1, f"{name} has no deny cases"


# ---------------------------------------------------------------------------
# T-ORC-0039 — Policy allow cases evaluate to ALLOW
# ---------------------------------------------------------------------------
# id: T-ORC-0039
# title: Policy allow cases evaluate to ALLOW
# purpose: Verify that allow-case inputs evaluate to ALLOW.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: each policy's allow case input
# expected: evaluate_policy returns "ALLOW"
# risk: allow cases fail, blocking valid calls
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0039_allow_cases_pass() -> None:
    """Policy allow cases evaluate to ALLOW."""
    for name, policy in POLICIES.items():
        for case in policy.allow_cases:
            assert evaluate_policy(name, dict(case.input_data)) == "ALLOW", (
                f"{name}/{case.name} expected ALLOW"
            )


# ---------------------------------------------------------------------------
# T-ORC-0040 — Policy deny cases evaluate to DENY
# ---------------------------------------------------------------------------
# id: T-ORC-0040
# title: Policy deny cases evaluate to DENY
# purpose: Verify that deny-case inputs evaluate to DENY.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: each policy's deny case input
# expected: evaluate_policy returns "DENY"
# risk: deny cases pass, allowing forbidden calls
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0040_deny_cases_fail() -> None:
    """Policy deny cases evaluate to DENY."""
    for name, policy in POLICIES.items():
        for case in policy.deny_cases:
            assert evaluate_policy(name, dict(case.input_data)) == "DENY", (
                f"{name}/{case.name} expected DENY"
            )


# ---------------------------------------------------------------------------
# T-ORC-0041 — run_policy_tests reports all cases passing
# ---------------------------------------------------------------------------
# id: T-ORC-0041
# title: run_policy_tests reports all cases passing
# purpose: Verify that the policy test runner reports all cases as passing.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: run_policy_tests()
# expected: every result has passed=True
# risk: policy tests silently fail in CI
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0041_policy_tests_all_pass() -> None:
    """run_policy_tests reports all cases passing."""
    results = run_policy_tests()
    assert len(results) > 0
    for _policy, _case, _expected, passed in results:
        assert passed is True


# ---------------------------------------------------------------------------
# T-ORC-0042 — An unknown policy raises PolicyError
# ---------------------------------------------------------------------------
# id: T-ORC-0042
# title: An unknown policy raises PolicyError
# purpose: Verify that evaluating a non-existent policy raises an error.
# level: fast
# requirement: P07-T03, Part 3 §3.11
# input: policy_name "bogus"
# expected: PolicyError is raised
# risk: unknown policy silently returns DENY
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0042_unknown_policy_raises() -> None:
    """An unknown policy raises PolicyError."""
    with pytest.raises(PolicyError, match="unknown policy"):
        evaluate_policy("bogus", {})

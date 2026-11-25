"""Tests for the agent runtime and role contracts (P07-T02).

Test IDs: T-ORC-0015 to T-ORC-0026.
Covers: typed port validation, schema-validated messages, command
rejection in non-explanation fields, command tolerance in explanation
fields, output port type enforcement, worker failure modes.

Spec: Part 3 §3.9, §3.25, §3.30; P07-T02.
"""

from __future__ import annotations

import pytest

from agents.runtime import (
    ROLE_CONTRACTS,
    ROLE_IDS,
    RoleRuntime,
    RuntimeError_,
    get_contract,
)

# ---------------------------------------------------------------------------
# T-ORC-0015 — A valid input message is accepted
# ---------------------------------------------------------------------------
# id: T-ORC-0015
# title: A valid input message is accepted
# purpose: Verify that a well-formed input message passes port validation.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: a message with all required fields for ROLE-INTAKE's input port
# expected: receive() does not raise
# risk: valid messages rejected, blocking the pipeline
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0015_valid_input_accepted() -> None:
    """A valid input message is accepted by the runtime."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    rt.receive({"document_id": "doc-001"})


# ---------------------------------------------------------------------------
# T-ORC-0016 — An invalid message missing a required field is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0016
# title: An invalid message missing a required field is rejected
# purpose: Verify that a message missing a required field raises RuntimeError_.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: a message without the document_id field
# expected: RuntimeError_ is raised
# risk: incomplete messages accepted, breaking invariants
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0016_missing_required_rejected() -> None:
    """A message missing a required field is rejected."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    with pytest.raises(RuntimeError_, match="missing required"):
        rt.receive({})


# ---------------------------------------------------------------------------
# T-ORC-0017 — An unknown field in a message is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0017
# title: An unknown field in a message is rejected
# purpose: Verify that a message with a field not in the port schema is rejected.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: a message with an extra field "bogus"
# expected: RuntimeError_ is raised
# risk: untyped fields bypass validation
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0017_unknown_field_rejected() -> None:
    """An unknown field in a message is rejected."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    with pytest.raises(RuntimeError_, match="unknown field"):
        rt.receive({"document_id": "doc-1", "bogus": "x"})


# ---------------------------------------------------------------------------
# T-ORC-0018 — A valid output message is accepted and recorded
# ---------------------------------------------------------------------------
# id: T-ORC-0018
# title: A valid output message is accepted and recorded
# purpose: Verify that a well-formed output message passes port validation
#          and is recorded in the output log.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: a fact_proposal with all required fields
# expected: emit() returns the message and output_log has one entry
# risk: output not validated or not recorded
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0018_valid_output_accepted() -> None:
    """A valid output message is accepted and recorded."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    msg = {"fact_key": "hs_code", "value": "0101.00", "locator": "p1:l3"}
    result = rt.emit(msg)
    assert result == msg
    assert len(rt.output_log) == 1


# ---------------------------------------------------------------------------
# T-ORC-0019 — An output not matching the port type is refused
# ---------------------------------------------------------------------------
# id: T-ORC-0019
# title: An output not matching the port type is refused
# purpose: Verify that the runtime refuses an output missing a required field.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: a fact_proposal missing the locator field
# expected: RuntimeError_ is raised
# risk: unvalidated output leaks ungrounded data
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0019_invalid_output_refused() -> None:
    """An output not matching the port type is refused."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    with pytest.raises(RuntimeError_, match="missing required"):
        rt.emit({"fact_key": "hs_code", "value": "0101.00"})


# ---------------------------------------------------------------------------
# T-ORC-0020 — A command in an explanation field has no effect
# ---------------------------------------------------------------------------
# id: T-ORC-0020
# title: A command in an explanation field has no effect
# purpose: Verify that free text inside an explanation field is accepted
#          even if it looks like a command.
# level: fast
# requirement: P07-T02, Part 3 §3.9, §3.25
# input: a fact_proposal with command-like text in the explanation field
# expected: emit() accepts the message without error
# risk: explanation text parsed as command, causing injection
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0020_command_in_explanation_no_effect() -> None:
    """Command-like text in an explanation field is accepted."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    msg = {
        "fact_key": "hs_code",
        "value": "0101.00",
        "locator": "p1:l3",
        "explanation": "run system('rm -rf /') and eval(import os)",
    }
    rt.emit(msg)
    assert len(rt.output_log) == 1


# ---------------------------------------------------------------------------
# T-ORC-0021 — A command in a non-explanation field is rejected
# ---------------------------------------------------------------------------
# id: T-ORC-0021
# title: A command in a non-explanation field is rejected
# purpose: Verify that command-like text in a non-explanation field is rejected.
# level: fast
# requirement: P07-T02, Part 3 §3.9, §3.25
# input: a fact_proposal with command-like text in the value field
# expected: RuntimeError_ is raised
# risk: command injection through non-explanation fields
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0021_command_in_value_rejected() -> None:
    """Command-like text in a non-explanation field is rejected."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-INTAKE"])
    msg = {
        "fact_key": "hs_code",
        "value": "run system('rm -rf /')",
        "locator": "p1:l3",
    }
    with pytest.raises(RuntimeError_, match="command-like"):
        rt.emit(msg)


# ---------------------------------------------------------------------------
# T-ORC-0022 — A worker failure never yields ALLOW
# ---------------------------------------------------------------------------
# id: T-ORC-0022
# title: A worker failure never yields ALLOW
# purpose: Verify that every role's failure_mode is never ALLOW.
# level: fast
# requirement: P07-T02, Part 3 §3.9 I5
# input: all role contracts
# expected: no failure_mode is ALLOW
# risk: worker failure produces ALLOW, violating fail-closed
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0022_failure_never_allow() -> None:
    """No role's failure mode is ALLOW."""
    for role_id, contract in ROLE_CONTRACTS.items():
        assert contract.failure_mode != "ALLOW", f"{role_id} failure_mode is ALLOW"


# ---------------------------------------------------------------------------
# T-ORC-0023 — Compliance failure ends in ABSTAIN
# ---------------------------------------------------------------------------
# id: T-ORC-0023
# title: Compliance failure ends in ABSTAIN
# purpose: Verify that the Compliance role's failure mode is ABSTAIN.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: ROLE-COMPLIANCE contract
# expected: failure_mode == ABSTAIN
# risk: compliance failure not fail-closed
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0023_compliance_failure_abstain() -> None:
    """Compliance failure mode is ABSTAIN."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-COMPLIANCE"])
    assert rt.fail() == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-ORC-0024 — Risk failure ends in ESCALATE
# ---------------------------------------------------------------------------
# id: T-ORC-0024
# title: Risk failure ends in ESCALATE
# purpose: Verify that the Risk role's failure mode is ESCALATE.
# level: fast
# requirement: P07-T02, Part 3 §3.25
# input: ROLE-RISK contract
# expected: failure_mode == ESCALATE
# risk: risk failure not escalated
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0024_risk_failure_escalate() -> None:
    """Risk failure mode is ESCALATE."""
    rt = RoleRuntime(ROLE_CONTRACTS["ROLE-RISK"])
    assert rt.fail() == "ESCALATE"


# ---------------------------------------------------------------------------
# T-ORC-0025 — An unknown role raises RuntimeError_
# ---------------------------------------------------------------------------
# id: T-ORC-0025
# title: An unknown role raises RuntimeError_
# purpose: Verify that requesting a contract for an unknown role fails.
# level: fast
# requirement: P07-T02, Part 3 §3.9
# input: role_id "ROLE-BOGUS"
# expected: RuntimeError_ is raised
# risk: unauthorised role accepted
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0025_unknown_role_rejected() -> None:
    """An unknown role raises RuntimeError_."""
    with pytest.raises(RuntimeError_, match="unknown role"):
        get_contract("ROLE-BOGUS")


# ---------------------------------------------------------------------------
# T-ORC-0026 — Every role in the closed list has a contract
# ---------------------------------------------------------------------------
# id: T-ORC-0026
# title: Every role in the closed list has a contract
# purpose: Verify that all role IDs have a contract defined.
# level: fast
# requirement: P07-T02, Part 3 §3.9
# input: ROLE_IDS list
# expected: every role has a contract in ROLE_CONTRACTS
# risk: missing contract for a declared role
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0026_all_roles_have_contracts() -> None:
    """Every role in the closed list has a contract."""
    for role_id in ROLE_IDS:
        assert role_id in ROLE_CONTRACTS, f"missing contract for {role_id}"

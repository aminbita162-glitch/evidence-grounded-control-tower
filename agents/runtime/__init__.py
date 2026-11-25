"""Agent runtime and typed role contracts (Part 3 §3.25, P07-T02).

Each role is a component with typed input and output ports, a tool grant,
readable memory classes, a model-use rule, action classes, a budget share
and a failure behavior.  Messages are schema-validated; free text appears
only inside designated explanation fields and is never parsed for
commands.  The runtime refuses any output that does not match the port
type.  A worker failure never yields ALLOW (Part 3 §3.9 I5).

Spec: Part 3 §3.9, §3.25, §3.30; P07-T02.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "ActionClass",
    "FailureMode",
    "MemoryClass",
    "MessagePort",
    "RoleContract",
    "RoleRuntime",
    "RuntimeError_",
    "ROLE_CONTRACTS",
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

ActionClass = Literal["R", "P", "E-rev", "E-irrev"]
FailureMode = Literal["BLOCKED", "FAILED", "ABSTAIN", "ESCALATE"]
MemoryClass = Literal["M0", "M1", "M2", "M3"]


class RuntimeError_(ValueError):
    """Raised when the runtime rejects a message or output."""


@dataclass(frozen=True)
class MessagePort:
    """A typed input or output port for a role message (Part 3 §3.25).

    Each port has a name, a list of required fields, and a list of
    optional fields.  Free-text fields must be listed in
    ``explanation_fields``; they are never parsed for commands.
    """

    name: str
    required_fields: tuple[str, ...] = ()
    optional_fields: tuple[str, ...] = ()
    explanation_fields: tuple[str, ...] = ()

    def validate(self, message: Mapping[str, object]) -> None:
        """Validate *message* against this port's schema.

        Raises RuntimeError_ if a required field is missing, an
        unknown field is present, or a non-explanation field contains
        free text that looks like a command.
        """
        for req in self.required_fields:
            if req not in message:
                raise RuntimeError_(f"missing required field: {req!r}")
        allowed = (
            set(self.required_fields) | set(self.optional_fields) | set(self.explanation_fields)
        )
        for key in message:
            if key not in allowed:
                raise RuntimeError_(f"unknown field: {key!r}")
        for key, value in message.items():
            if (
                key not in self.explanation_fields
                and isinstance(value, str)
                and _looks_like_command(value)
            ):
                raise RuntimeError_(f"command-like text in non-explanation field {key!r}")


@dataclass(frozen=True)
class RoleContract:
    """The contract for one role (Part 3 §3.25).

    Defines typed input/output ports, tool grant, readable memory
    classes, model-use rule, action classes, and failure behavior.
    """

    role_id: str
    display_name: str
    input_port: MessagePort
    output_port: MessagePort
    memory_classes: tuple[MemoryClass, ...]
    uses_model: bool
    action_classes: tuple[ActionClass, ...]
    failure_mode: FailureMode
    failure_never: str = "ALLOW"


def _looks_like_command(text: str) -> bool:
    """Heuristic: detect command-like text in a non-explanation field.

    Free text inside explanation fields is never parsed; but if command
    markers appear outside explanation fields, the runtime rejects them.
    """
    markers = ("run ", "exec ", "call ", "import ", "eval(", "system(")
    lowered = text.lower()
    return any(lowered.startswith(m) for m in markers)


# ---- Role contracts (Part 3 §3.25) -----------------------------------------

ROLE_CONTRACTS: dict[str, RoleContract] = {
    "ROLE-MANAGER": RoleContract(
        role_id="ROLE-MANAGER",
        display_name="Conductor",
        input_port=MessagePort(
            "case_command",
            required_fields=("case_id", "command"),
        ),
        output_port=MessagePort(
            "workflow_step",
            required_fields=("step_id", "role", "target_state"),
        ),
        memory_classes=("M1", "M2"),
        uses_model=False,
        action_classes=("R",),
        failure_mode="BLOCKED",
    ),
    "ROLE-INTAKE": RoleContract(
        role_id="ROLE-INTAKE",
        display_name="Reader",
        input_port=MessagePort(
            "document_record",
            required_fields=("document_id",),
        ),
        output_port=MessagePort(
            "fact_proposal",
            required_fields=("fact_key", "value", "locator"),
            optional_fields=("confidence",),
            explanation_fields=("explanation",),
        ),
        memory_classes=("M0",),
        uses_model=True,
        action_classes=("P",),
        failure_mode="BLOCKED",
    ),
    "ROLE-COMPLIANCE": RoleContract(
        role_id="ROLE-COMPLIANCE",
        display_name="Verifier",
        input_port=MessagePort(
            "verified_facts",
            required_fields=("facts", "evaluation_time"),
        ),
        output_port=MessagePort(
            "rule_result",
            required_fields=("rule_id", "state", "reason_codes"),
            optional_fields=("explanation",),
            explanation_fields=("explanation",),
        ),
        memory_classes=("M1", "M2"),
        uses_model=False,
        action_classes=("R", "P"),
        failure_mode="ABSTAIN",
    ),
    "ROLE-LOGISTICS": RoleContract(
        role_id="ROLE-LOGISTICS",
        display_name="Estimator",
        input_port=MessagePort(
            "cost_input",
            required_fields=("facts",),
        ),
        output_port=MessagePort(
            "cost_output",
            required_fields=("cost", "currency"),
            optional_fields=("explanation",),
            explanation_fields=("explanation",),
        ),
        memory_classes=("M1", "M2"),
        uses_model=False,
        action_classes=("R", "P"),
        failure_mode="ABSTAIN",
    ),
    "ROLE-PLANNER": RoleContract(
        role_id="ROLE-PLANNER",
        display_name="Planner",
        input_port=MessagePort(
            "plan_input",
            required_fields=("decision", "constraints"),
        ),
        output_port=MessagePort(
            "plan_candidate",
            required_fields=("plan",),
            optional_fields=("explanation",),
            explanation_fields=("explanation",),
        ),
        memory_classes=("M1", "M2"),
        uses_model=False,
        action_classes=("P",),
        failure_mode="BLOCKED",
    ),
    "ROLE-RISK": RoleContract(
        role_id="ROLE-RISK",
        display_name="Sentinel",
        input_port=MessagePort(
            "risk_input",
            required_fields=("decision", "evidence"),
        ),
        output_port=MessagePort(
            "adversarial_finding",
            required_fields=("finding",),
            optional_fields=("explanation",),
            explanation_fields=("explanation",),
        ),
        memory_classes=("M1", "M2", "M3"),
        uses_model=True,
        action_classes=("P",),
        failure_mode="ESCALATE",
    ),
}


@dataclass
class RoleRuntime:
    """The typed runtime for one role (Part 3 §3.25).

    Validates input messages against the role's input port and output
    messages against the role's output port.  Free text in explanation
    fields is accepted but never parsed for commands.  A worker failure
    never yields ALLOW.
    """

    contract: RoleContract
    _output_log: list[dict[str, object]] = field(default_factory=list)

    def receive(self, message: Mapping[str, object]) -> None:
        """Validate an input message against the role's input port."""
        self.contract.input_port.validate(message)

    def emit(self, message: Mapping[str, object]) -> dict[str, object]:
        """Validate and record an output message.

        Raises RuntimeError_ if the message does not match the
        output port schema.
        """
        self.contract.output_port.validate(message)
        recorded: dict[str, object] = dict(message)
        self._output_log.append(recorded)
        return recorded

    @property
    def output_log(self) -> list[dict[str, object]]:
        """Return the list of emitted messages."""
        return list(self._output_log)

    def fail(self) -> FailureMode:
        """Return the role's failure mode (never ALLOW, Part 3 §3.9 I5)."""
        return self.contract.failure_mode


def get_contract(role_id: str) -> RoleContract:
    """Return the contract for *role_id*.

    Raises RuntimeError_ if the role is unknown.
    """
    contract = ROLE_CONTRACTS.get(role_id)
    if contract is None:
        raise RuntimeError_(f"unknown role: {role_id!r}")
    return contract

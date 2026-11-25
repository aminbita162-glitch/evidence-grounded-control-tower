"""Human Gate: approval, rejection, override (Part 3 §3.9, P07-T06).

APPROVE is bound to the exact proposal hash.  REJECT and OVERRIDE are
separate records with written justification that never rewrite a Decision
(I11).  A reviewer role is required.  An Override of ESCALATE needs a
second, different reviewer by default.  Approvals expire with the case
state.  Concurrent approvals: the first wins, the second receives a
conflict.

Spec: Part 3 §3.5, §3.7, §3.9; P07-T06.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "GateOutcome",
    "Approval",
    "HumanGate",
    "HumanGateError",
    "ConflictError",
]

GateOutcome = Literal["APPROVE", "REJECT", "OVERRIDE"]


class HumanGateError(Exception):
    """Raised when a Human Gate action is invalid."""


class ConflictError(HumanGateError):
    """Raised when a concurrent approval conflicts (Part 3 §3.4)."""


@dataclass(frozen=True)
class Approval:
    """A Human Gate record (Part 3 §3.9).

    APPROVE is bound to the exact proposal hash.  REJECT and OVERRIDE
    carry a written justification.  An Override never rewrites the
    Decision (I11); it is a separate record referencing it.
    """

    outcome: GateOutcome
    proposal_hash: str
    reviewer_id: str
    reviewer_role: str
    case_state: str
    justification: str = ""
    second_reviewer_id: str = ""
    second_reviewer_role: str = ""


def _hash_proposal(proposal: object) -> str:
    """Compute the SHA-256 hash of a proposal."""
    import json

    canonical = json.dumps(proposal, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class HumanGate:
    """The Human Gate (Part 3 §3.9).

    Manages approvals, rejections and overrides for a case.  Approvals
    are bound to the exact proposal hash; a changed proposal invalidates
    a prior approval.  Overrides of ESCALATE require a second, different
    reviewer by default.  Concurrent approvals: the first wins.
    """

    case_id: str
    require_second_reviewer: bool = True
    _approvals: list[Approval] = field(default_factory=list)
    _decided: bool = False

    @property
    def approvals(self) -> list[Approval]:
        """Return the list of approval records."""
        return list(self._approvals)

    @property
    def is_decided(self) -> bool:
        """Return True if the case has been decided."""
        return self._decided

    def approve(
        self,
        proposal: object,
        proposal_hash: str,
        reviewer_id: str,
        reviewer_role: str,
        case_state: str,
    ) -> Approval:
        """Approve a proposal bound to its hash (Part 3 §3.5, §3.9).

        Raises HumanGateError if the reviewer role is missing or the
        proposal hash does not match.  Raises ConflictError if an
        approval for the same proposal already exists (concurrent:
        the first wins).
        """
        if not reviewer_role:
            raise HumanGateError("reviewer role required")
        actual_hash = _hash_proposal(proposal)
        if actual_hash != proposal_hash:
            raise HumanGateError(
                "proposal hash mismatch: approval of a changed proposal is invalid"
            )
        for existing in self._approvals:
            if existing.outcome == "APPROVE" and existing.proposal_hash == proposal_hash:
                raise ConflictError("concurrent approval: the first wins")
        record = Approval(
            outcome="APPROVE",
            proposal_hash=proposal_hash,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            case_state=case_state,
        )
        self._approvals.append(record)
        self._decided = True
        return record

    def reject(
        self,
        proposal_hash: str,
        reviewer_id: str,
        reviewer_role: str,
        case_state: str,
        justification: str,
    ) -> Approval:
        """Reject a proposal with written justification (Part 3 §3.9)."""
        if not reviewer_role:
            raise HumanGateError("reviewer role required")
        if not justification:
            raise HumanGateError("written justification required for rejection")
        record = Approval(
            outcome="REJECT",
            proposal_hash=proposal_hash,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            case_state=case_state,
            justification=justification,
        )
        self._approvals.append(record)
        return record

    def override(
        self,
        proposal_hash: str,
        reviewer_id: str,
        reviewer_role: str,
        case_state: str,
        justification: str,
        second_reviewer_id: str = "",
        second_reviewer_role: str = "",
    ) -> Approval:
        """Override a HOLD or ESCALATE with written justification (Part 3 §3.9).

        An Override is a separate record that never rewrites the
        Decision (I11).  An Override of ESCALATE needs a second,
        different reviewer by default.
        """
        if not reviewer_role:
            raise HumanGateError("reviewer role required")
        if not justification:
            raise HumanGateError("written justification required for override")
        if self.require_second_reviewer:
            if not second_reviewer_id:
                raise HumanGateError("override of ESCALATE needs a second reviewer")
            if second_reviewer_id == reviewer_id:
                raise HumanGateError("second reviewer must be different from the first")
        record = Approval(
            outcome="OVERRIDE",
            proposal_hash=proposal_hash,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            case_state=case_state,
            justification=justification,
            second_reviewer_id=second_reviewer_id,
            second_reviewer_role=second_reviewer_role,
        )
        self._approvals.append(record)
        return record

    def is_expired(self, current_state: str, approval: Approval) -> bool:
        """Check whether an approval has expired with the case state.

        Approvals expire when the case state changes beyond the
        approval's recorded state (Part 3 §3.9).
        """
        _state_order = [
            "CREATED",
            "INGESTED",
            "EXTRACTED",
            "EVALUATED",
            "PROPOSED",
            "AWAITING_HUMAN",
            "DECIDED",
            "CLOSED",
        ]
        try:
            approval_idx = _state_order.index(approval.case_state)
            current_idx = _state_order.index(current_state)
        except ValueError:
            return True
        return current_idx > approval_idx

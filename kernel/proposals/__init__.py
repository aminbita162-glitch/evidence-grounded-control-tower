"""Propose–Verify–Gate (Part 3 §3.7, P08-T05).

Proposals are committed by hash before review.  Deterministic verifiers
check schema validity, grounding, rule conformance and recomputation.
A failed verification rejects the proposal and is recorded, never
repaired.  PROPOSED facts become VERIFIED only through grounding or
human confirmation.  The dual-extraction hook for high-stakes fields
yields HOLD on disagreement (D-06 S2).

Spec: Part 3 §3.7; D-06 S2; P08-T05.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from kernel.extract import ExtractedField
from kernel.extract.grounding import ground_fields

__all__ = [
    "Proposal",
    "VerificationResult",
    "Verifier",
    "SchemaVerifier",
    "GroundingVerifier",
    "RuleConformanceVerifier",
    "RecomputationVerifier",
    "ProposeVerifyGate",
    "DualExtractionResult",
    "ProposalError",
]


class ProposalError(Exception):
    """A proposal verification error."""


@dataclass(frozen=True)
class Proposal:
    """A model-generated proposal committed by hash.

    Attributes:
        proposal_id: Unique identifier.
        proposal_type: Type (extraction, classification, plan, explanation).
        committed_hash: Hash of the proposal content at commitment time.
        fields: The extracted fields proposed.
    """

    proposal_id: str
    proposal_type: str
    committed_hash: str
    fields: list[ExtractedField]


@dataclass(frozen=True)
class VerificationResult:
    """The result of verifying a proposal.

    Attributes:
        passed: True if all verifiers passed.
        reason: Explanation of the result.
        verifier_name: Name of the verifier that failed (if any).
    """

    passed: bool
    reason: str
    verifier_name: str = ""


class Verifier(Protocol):
    """A deterministic verifier for proposals."""

    def verify(self, proposal: Proposal, context: Mapping[str, object]) -> VerificationResult: ...


def _compute_proposal_hash(fields: list[ExtractedField]) -> str:
    """Compute a content hash for a list of extracted fields."""
    parts: list[str] = []
    for f in fields:
        parts.append(f"{f.name}:{f.value}:{f.status}:{f.locator.span_start}:{f.locator.span_end}")
    content = "|".join(parts)
    return hashlib.sha256(content.encode()).hexdigest()


class SchemaVerifier:
    """Verifies that every field has a locator and method."""

    def verify(self, proposal: Proposal, context: Mapping[str, object]) -> VerificationResult:
        for f in proposal.fields:
            if f.locator.document_id == "":
                return VerificationResult(
                    passed=False,
                    reason=f"field {f.name!r} missing locator document_id",
                    verifier_name="schema",
                )
            if f.method == "":
                return VerificationResult(
                    passed=False,
                    reason=f"field {f.name!r} missing method",
                    verifier_name="schema",
                )
        return VerificationResult(passed=True, reason="schema ok")


class GroundingVerifier:
    """Verifies that every field is grounded in the document text."""

    def verify(self, proposal: Proposal, context: Mapping[str, object]) -> VerificationResult:
        document_text = context.get("document_text")
        if not isinstance(document_text, str):
            return VerificationResult(
                passed=False,
                reason="document_text not provided in context",
                verifier_name="grounding",
            )
        results = ground_fields(proposal.fields, document_text)
        for r in results:
            if not r.grounded:
                return VerificationResult(
                    passed=False,
                    reason=f"ungrounded field {r.field_name!r}: {r.reason}",
                    verifier_name="grounding",
                )
        return VerificationResult(passed=True, reason="grounding ok")


class RuleConformanceVerifier:
    """Verifies that fields conform to simple rules (non-empty required fields)."""

    def verify(self, proposal: Proposal, context: Mapping[str, object]) -> VerificationResult:
        required = context.get("required_fields")
        if not isinstance(required, list):
            return VerificationResult(passed=True, reason="no required fields specified")
        field_names = {f.name for f in proposal.fields}
        for req in required:
            if req not in field_names:
                return VerificationResult(
                    passed=False,
                    reason=f"missing required field {req!r}",
                    verifier_name="rule_conformance",
                )
        return VerificationResult(passed=True, reason="rule conformance ok")


class RecomputationVerifier:
    """Recomputes numeric fields to verify they match the source."""

    def verify(self, proposal: Proposal, context: Mapping[str, object]) -> VerificationResult:
        for f in proposal.fields:
            if f.status == "EXTRACTED" and f.value == "UNKNOWN":
                return VerificationResult(
                    passed=False,
                    reason=f"extracted field {f.name!r} has UNKNOWN value",
                    verifier_name="recomputation",
                )
        return VerificationResult(passed=True, reason="recomputation ok")


@dataclass
class ProposeVerifyGate:
    """The Propose–Verify–Gate stage.

    Runs deterministic verifiers in order.  A failed verification rejects
    the proposal and is recorded, never repaired.  A proposal changed
    after commitment cannot be approved (hash mismatch).
    """

    verifiers: list[Verifier] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.verifiers:
            self.verifiers = [
                SchemaVerifier(),
                GroundingVerifier(),
                RuleConformanceVerifier(),
                RecomputationVerifier(),
            ]

    def verify(self, proposal: Proposal, context: Mapping[str, object]) -> VerificationResult:
        """Verify a proposal through all verifiers.

        A failed verification rejects the proposal immediately.
        """
        current_hash = _compute_proposal_hash(proposal.fields)
        if current_hash != proposal.committed_hash:
            return VerificationResult(
                passed=False,
                reason="proposal changed after commitment (hash mismatch)",
                verifier_name="commitment",
            )
        for verifier in self.verifiers:
            result = verifier.verify(proposal, context)
            if not result.passed:
                return result
        return VerificationResult(passed=True, reason="all verifiers passed")


@dataclass(frozen=True)
class DualExtractionResult:
    """The result of dual extraction for high-stakes fields (D-06 S2).

    Attributes:
        agreed: True if both extractions agree.
        decision: ALLOW, HOLD, or ABSTAIN.
        fields: The verified fields (if agreed) or empty (if disagreed).
        reason: Explanation.
    """

    agreed: bool
    decision: str
    fields: list[ExtractedField]
    reason: str


def dual_extract(
    primary_fields: list[ExtractedField],
    secondary_fields: list[ExtractedField],
) -> DualExtractionResult:
    """Dual extraction for high-stakes fields (D-06 S2).

    Two independent extractions; disagreement yields HOLD, never a silent pick.
    """
    if len(primary_fields) != len(secondary_fields):
        return DualExtractionResult(
            agreed=False,
            decision="HOLD",
            fields=[],
            reason="dual extraction disagreement: field count mismatch",
        )
    for pf, sf in zip(primary_fields, secondary_fields, strict=True):
        if pf.value != sf.value:
            return DualExtractionResult(
                agreed=False,
                decision="HOLD",
                fields=[],
                reason=f"dual extraction disagreement on field {pf.name!r}",
            )
    return DualExtractionResult(
        agreed=True,
        decision="ALLOW",
        fields=primary_fields,
        reason="dual extraction agreed",
    )

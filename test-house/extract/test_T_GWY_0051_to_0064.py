"""Tests for Propose-Verify-Gate and grounding (P08-T05).

Test IDs: T-GWY-0051 to T-GWY-0064.
Covers: proposal commitment hash, ungrounded claim rejection, dual
extraction HOLD, verified fact locators, schema/grounding/rule verifiers.

Spec: Part 3 §3.7; D-06 S2; P08-T05.
"""

from __future__ import annotations

import hashlib

import pytest

from kernel.extract import ExtractedField, FieldLocator
from kernel.extract.grounding import ground_field, ground_fields
from kernel.proposals import (
    Proposal,
    ProposeVerifyGate,
    RecomputationVerifier,
    RuleConformanceVerifier,
    SchemaVerifier,
    VerificationResult,
    dual_extract,
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_DOC = "Invoice number: INV-2024-001\nTotal: 1500 USD"

_LOC = FieldLocator(document_id="doc1", page=0, span_start=0, span_end=12)
_BAD_LOC = FieldLocator(document_id="doc1", page=0, span_start=0, span_end=0)


def _make_field(
    name: str = "invoice_number",
    value: str = "INV-2024-001",
    loc: FieldLocator | None = None,
    status: str = "EXTRACTED",
    method: str = "model",
) -> ExtractedField:
    return ExtractedField(
        name=name,
        value=value,
        locator=loc or _LOC,
        method=method,
        status=status,
    )


def _proposal_hash(fields: list[ExtractedField]) -> str:
    parts: list[str] = []
    for f in fields:
        parts.append(f"{f.name}:{f.value}:{f.status}:{f.locator.span_start}:{f.locator.span_end}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


# --------------------------------------------------------------------------- #
# T-GWY-0051 — A proposal changed after commitment cannot be approved
# --------------------------------------------------------------------------- #
# id: T-GWY-0051
# title: A proposal changed after commitment cannot be approved
# purpose: Verify hash mismatch rejects the proposal
# level: fast
# requirement: P08-T05
# input: a proposal with a stale committed_hash
# expected: verification fails with hash mismatch
# risk: proposal tampered after commitment
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0051_changed_proposal_rejected() -> None:
    """A proposal changed after commitment cannot be approved."""
    fields = [_make_field()]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash="0" * 64,  # wrong hash
        fields=fields,
    )
    gate = ProposeVerifyGate()
    result = gate.verify(proposal, {"document_text": _DOC})
    assert not result.passed
    assert "hash mismatch" in result.reason


# --------------------------------------------------------------------------- #
# T-GWY-0052 — Ungrounded claims are rejected
# --------------------------------------------------------------------------- #
# id: T-GWY-0052
# title: Ungrounded claims are rejected
# purpose: Verify the grounding verifier rejects ungrounded fields
# level: fast
# requirement: P08-T05
# input: a field whose value doesn't match the document span
# expected: grounding verification fails
# risk: ungrounded values accepted
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0052_ungrounded_claims_rejected() -> None:
    """Ungrounded claims are rejected."""
    bad_loc = FieldLocator(document_id="doc1", page=0, span_start=0, span_end=5)
    field = _make_field(value="WRONG_VALUE", loc=bad_loc)
    fields = [field]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash=_proposal_hash(fields),
        fields=fields,
    )
    gate = ProposeVerifyGate()
    result = gate.verify(proposal, {"document_text": _DOC})
    assert not result.passed
    assert "ground" in result.reason or "match" in result.reason


# --------------------------------------------------------------------------- #
# T-GWY-0053 — Dual extraction disagreement gives HOLD
# --------------------------------------------------------------------------- #
# id: T-GWY-0053
# title: Dual extraction disagreement gives HOLD
# purpose: Verify dual extraction yields HOLD on disagreement
# level: fast
# requirement: P08-T05
# input: two extractions with different values
# expected: decision is HOLD
# risk: silent pick on disagreement
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0053_dual_extraction_disagreement_hold() -> None:
    """Dual extraction disagreement gives HOLD."""
    primary = [_make_field(value="VALUE_A")]
    secondary = [_make_field(value="VALUE_B")]
    result = dual_extract(primary, secondary)
    assert not result.agreed
    assert result.decision == "HOLD"


# --------------------------------------------------------------------------- #
# T-GWY-0054 — Verified facts carry their locator
# --------------------------------------------------------------------------- #
# id: T-GWY-0054
# title: Verified facts carry their locator
# purpose: Verify that verified fields preserve their source locator
# level: fast
# requirement: P08-T05
# input: a successfully verified proposal
# expected: fields retain their locator
# risk: locator lost during verification
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0054_verified_facts_carry_locator() -> None:
    """Verified facts carry their locator."""
    loc = FieldLocator(document_id="doc1", page=0, span_start=0, span_end=14)
    field = _make_field(value="Invoice number", loc=loc)
    fields = [field]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash=_proposal_hash(fields),
        fields=fields,
    )
    gate = ProposeVerifyGate()
    result = gate.verify(proposal, {"document_text": _DOC})
    assert result.passed
    assert proposal.fields[0].locator.document_id == "doc1"
    assert proposal.fields[0].locator.page == 0


# --------------------------------------------------------------------------- #
# T-GWY-0055 — Grounding exact match passes
# --------------------------------------------------------------------------- #
# id: T-GWY-0055
# title: Grounding exact match passes
# purpose: Verify exact span match grounds successfully
# level: fast
# requirement: P08-T05
# input: a field whose value exactly matches the span text
# expected: grounded is True
# risk: exact match rejected
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0055_grounding_exact_match() -> None:
    """Grounding exact match passes."""
    doc = "Hello World"
    field = _make_field(
        value="Hello",
        loc=FieldLocator("d", 0, 0, 5),
    )
    result = ground_field(field, doc)
    assert result.grounded
    assert result.reason == "exact match"


# --------------------------------------------------------------------------- #
# T-GWY-0056 — Grounding normalized match passes
# --------------------------------------------------------------------------- #
# id: T-GWY-0056
# title: Grounding normalized match passes
# purpose: Verify normalized (case/whitespace) match grounds successfully
# level: fast
# requirement: P08-T05
# input: a field whose value differs only in case/whitespace
# expected: grounded is True via normalized match
# risk: normalized match rejected
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0056_grounding_normalized_match() -> None:
    """Grounding normalized match passes."""
    doc = "  Hello  World  "
    field = _make_field(
        value="hello  world",
        loc=FieldLocator("d", 0, 2, 14),
    )
    result = ground_field(field, doc)
    assert result.grounded
    assert "normalized" in result.reason


# --------------------------------------------------------------------------- #
# T-GWY-0057 — SchemaVerifier rejects missing method
# --------------------------------------------------------------------------- #
# id: T-GWY-0057
# title: SchemaVerifier rejects missing method
# purpose: Verify the schema verifier checks method presence
# level: fast
# requirement: P08-T05
# input: a field with empty method
# expected: schema verification fails
# risk: methodless field accepted
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0057_schema_verifier_missing_method() -> None:
    """SchemaVerifier rejects missing method."""
    field = _make_field(method="")
    fields = [field]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash=_proposal_hash(fields),
        fields=fields,
    )
    verifier = SchemaVerifier()
    result = verifier.verify(proposal, {})
    assert not result.passed
    assert "method" in result.reason


# --------------------------------------------------------------------------- #
# T-GWY-0058 — RuleConformanceVerifier checks required fields
# --------------------------------------------------------------------------- #
# id: T-GWY-0058
# title: RuleConformanceVerifier checks required fields
# purpose: Verify the rule verifier rejects missing required fields
# level: fast
# requirement: P08-T05
# input: a proposal missing a required field
# expected: rule conformance fails
# risk: required field missing
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0058_rule_conformance_missing() -> None:
    """RuleConformanceVerifier checks required fields."""
    field = _make_field(name="field_a")
    fields = [field]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash=_proposal_hash(fields),
        fields=fields,
    )
    verifier = RuleConformanceVerifier()
    result = verifier.verify(proposal, {"required_fields": ["field_a", "field_b"]})
    assert not result.passed
    assert "field_b" in result.reason


# --------------------------------------------------------------------------- #
# T-GWY-0059 — RecomputationVerifier rejects UNKNOWN extracted fields
# --------------------------------------------------------------------------- #
# id: T-GWY-0059
# title: RecomputationVerifier rejects UNKNOWN extracted fields
# purpose: Verify recomputation rejects fields with UNKNOWN value
# level: fast
# requirement: P08-T05
# input: a field with status EXTRACTED but value UNKNOWN
# expected: recomputation fails
# risk: unknown value treated as extracted
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0059_recomputation_unknown() -> None:
    """RecomputationVerifier rejects UNKNOWN extracted fields."""
    field = _make_field(value="UNKNOWN", status="EXTRACTED")
    fields = [field]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash=_proposal_hash(fields),
        fields=fields,
    )
    verifier = RecomputationVerifier()
    result = verifier.verify(proposal, {})
    assert not result.passed


# --------------------------------------------------------------------------- #
# T-GWY-0060 — Dual extraction agreement yields ALLOW
# --------------------------------------------------------------------------- #
# id: T-GWY-0060
# title: Dual extraction agreement yields ALLOW
# purpose: Verify dual extraction agreement yields ALLOW
# level: fast
# requirement: P08-T05
# input: two identical extractions
# expected: decision is ALLOW
# risk: agreement not recognized
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0060_dual_extraction_agreement() -> None:
    """Dual extraction agreement yields ALLOW."""
    fields = [_make_field(value="SAME")]
    result = dual_extract(fields, fields)
    assert result.agreed
    assert result.decision == "ALLOW"


# --------------------------------------------------------------------------- #
# T-GWY-0061 — ground_fields grounds multiple fields
# --------------------------------------------------------------------------- #
# id: T-GWY-0061
# title: ground_fields grounds multiple fields
# purpose: Verify ground_fields processes all fields
# level: fast
# requirement: P08-T05
# input: multiple fields
# expected: a result for each field
# risk: batch grounding fails
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0061_ground_fields() -> None:
    """ground_fields grounds multiple fields."""
    doc = "Alpha Beta"
    f1 = _make_field(name="f1", value="Alpha", loc=FieldLocator("d", 0, 0, 5))
    f2 = _make_field(name="f2", value="Beta", loc=FieldLocator("d", 0, 6, 10))
    results = ground_fields([f1, f2], doc)
    assert len(results) == 2
    assert all(r.grounded for r in results)


# --------------------------------------------------------------------------- #
# T-GWY-0062 — ProposeVerifyGate passes valid proposal
# --------------------------------------------------------------------------- #
# id: T-GWY-0062
# title: ProposeVerifyGate passes a valid proposal
# purpose: Verify the full gate passes a well-formed proposal
# level: fast
# requirement: P08-T05
# input: a valid proposal with correct hash and grounding
# expected: all verifiers pass
# risk: valid proposal rejected
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0062_gate_passes_valid() -> None:
    """ProposeVerifyGate passes a valid proposal."""
    doc = "Hello World"
    field = _make_field(value="Hello", loc=FieldLocator("d", 0, 0, 5))
    fields = [field]
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash=_proposal_hash(fields),
        fields=fields,
    )
    gate = ProposeVerifyGate()
    result = gate.verify(proposal, {"document_text": doc})
    assert result.passed
    assert "passed" in result.reason


# --------------------------------------------------------------------------- #
# T-GWY-0063 — Proposal is frozen
# --------------------------------------------------------------------------- #
# id: T-GWY-0063
# title: Proposal is frozen
# purpose: Verify the proposal dataclass is immutable
# level: fast
# requirement: P08-T05
# input: a Proposal instance
# expected: attribute assignment raises
# risk: mutable proposal
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0063_proposal_frozen() -> None:
    """Proposal is frozen."""
    proposal = Proposal(
        proposal_id="p1",
        proposal_type="extraction",
        committed_hash="0" * 64,
        fields=[],
    )
    with pytest.raises(AttributeError):
        proposal.proposal_id = "changed"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# T-GWY-0064 — VerificationResult is frozen
# --------------------------------------------------------------------------- #
# id: T-GWY-0064
# title: VerificationResult is frozen
# purpose: Verify the result dataclass is immutable
# level: fast
# requirement: P08-T05
# input: a VerificationResult instance
# expected: attribute assignment raises
# risk: mutable result
# capability: proposals


@pytest.mark.fast
def test_T_GWY_0064_verification_result_frozen() -> None:
    """VerificationResult is frozen."""
    result = VerificationResult(passed=True, reason="ok")
    with pytest.raises(AttributeError):
        result.passed = False  # type: ignore[misc]

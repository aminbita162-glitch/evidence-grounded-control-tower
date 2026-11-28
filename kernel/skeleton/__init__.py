"""Walking skeleton — one thin end-to-end slice on SYNTHETIC data (P09-T03).

One synthetic case runs Intake, Extract (recorded responses), Facts, Rules
(a fixture pack), Decision, Evidence, Human Gate (a scripted approval) and
Passport through the kernel entry points with stub capabilities.  The
Passport is replayed from the case bundle and verified by both the kernel
verifier and the independent verifier.  The skeleton uses kernel contracts
only — it never imports capability internals (Part 6 §6.11).

Spec: Part 3 §3.2, §3.5, §3.8, §3.9, §3.10; Part 6 §6.11; P09-T03.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from data.synthetic import SyntheticDocument, SyntheticFactory
from kernel.auth.roles import Principal
from kernel.config import DEFAULTS
from kernel.decision import EligibilityResult, FactEntry, evaluate_allow
from kernel.extract import ExtractRequest, ExtractResult, ExtractStage
from kernel.humangate import HumanGate
from kernel.ledger.bundle import export_bundle, verify_bundle
from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import Actor, LedgerRecord
from kernel.ledger.replay import CaseExport, compute_passport_hash, replay
from kernel.ledger.verify import verify_structural
from kernel.rules.interpreter import FactSet, RuleResult, interpret
from kernel.skeleton.intake import IntakePipelinePort, SourceDocument
from kernel.types.decision import DecisionValue, combine_decisions

__all__ = [
    "SkeletonResult",
    "WalkingSkeleton",
    "StubExtractModel",
    "fixture_pack",
    "STUB_SCHEMA",
]

#: The stub extraction target schema.
STUB_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "consignee_name": {"type": "string"},
        "commodity": {"type": "string"},
        "origin_port": {"type": "string"},
        "amount": {"type": "string"},
    },
}

#: Evaluation time for the skeleton (fixed, deterministic).
_EVAL_TIME: str = "2026-01-15T00:00:00Z"

#: The fixture rule pack — a simple pack with one rule that checks a fact.
_FIXTURE_PACK: list[dict[str, object]] = [
    {
        "id": "R-STUB-001",
        "version": "1",
        "valid_from": "2020-01-01T00:00:00Z",
        "valid_to": "2099-12-31T00:00:00Z",
        "applies_when": {},
        "condition": {
            "type": "string_eq",
            "left": {"type": "field", "name": "consignee_name"},
            "right": {"type": "string", "value": ""},
        },
        "outcome": "HOLD",
        "reason_code": "R-STUB-001.EMPTY_CONSIGNEE",
        "severity": 2,
        "citation": {"source_id": "SYN-SRC-001", "locator": "§1"},
    },
]

_ACTOR = Actor(kind="ROLE", id="ROLE-MANAGER")


def fixture_pack() -> list[dict[str, object]]:
    """Return a copy of the fixture rule pack for the skeleton."""
    return [dict(r) for r in _FIXTURE_PACK]


class StubExtractModel:
    """A stub Extract model port that returns recorded responses (P09-T03).

    The model is tool-less and secret-less (Part 3 §3.2).  It extracts
    fields from the synthetic document text deterministically — no live
    model call, no network, no secrets.
    """

    def __init__(self, doc: SyntheticDocument) -> None:
        self._doc = doc

    async def __call__(self, text: str, schema: Mapping[str, object]) -> dict[str, object]:
        """Return a deterministic structured response from the document text."""
        lines = text.split("\n")
        values: dict[str, object] = {}
        for line in lines:
            if line.startswith("SYNTHETIC invoice:"):
                parts = line.split(" - ", 1)
                if len(parts) == 2:
                    values["consignee_name"] = parts[0].split(": ", 1)[1].strip()
                    values["commodity"] = parts[1].strip()
            elif line.startswith("From:"):
                values["origin_port"] = line.split(":", 1)[1].strip()
            elif line.startswith("Amount:"):
                values["amount"] = line.split(":", 1)[1].strip()
        return values


@dataclass
class SkeletonResult:
    """The result of a walking-skeleton run.

    Attributes:
        case_id: The case identifier.
        tenant_id: The tenant identifier.
        decision: The decision value string (ALLOW, HOLD, ABSTAIN, ESCALATE).
        reason_codes: The reason codes from the decision.
        passport_hash: The SHA-256 hash of the serialized Passport.
        bundle_hash: The bundle hash from the case bundle.
        records: The case chain records.
        structural_ok: Whether the kernel verifier passed.
        bundle_ok: Whether the independent verifier passed.
        replay_ok: Whether the replay reproduces the same passport hash.
        configuration_hash: The public configuration digest recorded on the Passport.
    """

    case_id: str = ""
    tenant_id: str = ""
    decision: str = ""
    reason_codes: list[str] = field(default_factory=list)
    passport_hash: str = ""
    bundle_hash: str = ""
    records: list[LedgerRecord] = field(default_factory=list)
    structural_ok: bool = False
    bundle_ok: bool = False
    replay_ok: bool = False
    configuration_hash: str = ""


class WalkingSkeleton:
    """The walking skeleton — one thin end-to-end case on SYNTHETIC data.

    Runs the full kernel pipeline (Intake → Extract → Facts → Rules →
    Decision → Evidence → Human Gate → Passport) with stub capabilities.
    The Passport is replayed from the case bundle and verified by both
    the kernel verifier and the independent verifier (Part 6 §6.11).

    Args:
        seed: The synthetic data factory seed.
        configuration_hash: The validated deployment configuration digest, when supplied.
    """

    def __init__(self, seed: int = 42, *, configuration_hash: str | None = None) -> None:
        self.seed: int = seed
        self.configuration_hash = (
            DEFAULTS.config_hash() if configuration_hash is None else configuration_hash
        )
        self.tenant_id: str = "SYN-TEN-0001"
        self.case_id: str = "SYN-CASE-0001"
        self._factory: SyntheticFactory = SyntheticFactory(seed)

    async def run(
        self,
        *,
        intake: IntakePipelinePort | None = None,
        uploads: Sequence[SourceDocument] = (),
    ) -> SkeletonResult:
        """Run the full skeleton pipeline and return a :class:`SkeletonResult`."""
        chain = InMemoryCaseChain(self.tenant_id, self.case_id)
        if intake is not None:
            principal = Principal(
                principal_id="SYN-OPERATOR", role="operator", tenant_id=self.tenant_id
            )
            intake_inputs = await intake.ingest(
                principal, self.case_id, uploads, _EVAL_TIME, chain=chain
            )

        else:
            intake_inputs = None

        if intake_inputs is None:
            fact_entries = await self._fixture_facts(chain)
            required_keys = ["consignee_name", "commodity"]
            origin = "SYNTHETIC"
        else:
            fact_entries = list(intake_inputs.facts)
            required_keys = list(intake_inputs.required_keys)
            origin = intake_inputs.data_origin

        # 4. Rules — fixture pack.
        fact_set: FactSet = {f.key: (f.value, f.status, ()) for f in fact_entries}
        rule_results: list[RuleResult] = interpret(fixture_pack(), fact_set, _EVAL_TIME)
        rule_failures: list[str] = [r.reason_code for r in rule_results if r.outcome == "HOLD"]
        await chain.append(
            stage="Rules",
            actor=_ACTOR,
            record_type="rule_results",
            payload={
                "results": [
                    {"id": r.rule_id, "state": r.state, "outcome": r.outcome} for r in rule_results
                ],
            },
        )

        # 5. Decision — evaluate ALLOW eligibility.
        eligibility: EligibilityResult = evaluate_allow(
            fact_entries,
            required_keys=required_keys,
            rule_failures=rule_failures,
            data_origin=origin,
            calibration_basis=None,
        )
        if intake_inputs is not None:
            outcome, reasons = combine_decisions(
                [
                    eligibility.value,
                    *(value for value, _ in intake_inputs.decisions),
                    *(judgment.outcome for judgment in intake_inputs.judgments),
                ],
                [
                    eligibility.reason_codes,
                    *(list(codes) for _, codes in intake_inputs.decisions),
                    *(list(judgment.reasons) for judgment in intake_inputs.judgments),
                ],
            )
            eligibility = EligibilityResult(outcome, reasons, eligibility.stamped_label)
        decision_str: str = DecisionValue(eligibility.value).name
        decision_payload = {
            "decision": decision_str,
            "reason_codes": eligibility.reason_codes,
        }
        decision_record = await chain.append(
            stage="Decision",
            actor=_ACTOR,
            record_type="decision",
            payload=decision_payload,
        )

        # 6. Evidence — already appending to the chain above.

        # 7. Human Gate — scripted approval (no second reviewer for stub).
        gate = HumanGate(self.case_id, require_second_reviewer=False)
        proposal = {"decision": decision_str, "case_id": self.case_id}
        proposal_hash = hashlib.sha256(
            json.dumps(proposal, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()
        approval = gate.approve(
            proposal=proposal,
            proposal_hash=proposal_hash,
            reviewer_id="SYN-REVIEWER-001",
            reviewer_role="reviewer",
            case_state="DECIDED",
        )
        await chain.append(
            stage="HumanGate",
            actor=Actor(kind="HUMAN", id="SYN-REVIEWER-001"),
            record_type="approval",
            payload={
                "outcome": approval.outcome,
                "reviewer_id": approval.reviewer_id,
            },
        )

        # 8. Passport — build from the case chain.
        records: list[LedgerRecord] = await chain.list()
        bundle = export_bundle(records, self.tenant_id, self.case_id)
        passport_hash = compute_passport_hash(
            case_id=self.case_id,
            tenant_id=self.tenant_id,
            decision=decision_str,
            reason_codes=eligibility.reason_codes,
            record_count=len(records),
            bundle_hash=bundle.manifest.bundle_hash,
            evaluation_time=_EVAL_TIME,
            configuration_hash=self.configuration_hash,
        )
        passport_payload = {
            "passport_hash": passport_hash,
            "bundle_hash": bundle.manifest.bundle_hash,
            "configuration_hash": self.configuration_hash,
        }
        passport_record = await chain.append(
            stage="Passport",
            actor=_ACTOR,
            record_type="passport",
            payload=passport_payload,
        )

        # 9. Replay — reconstruct the Passport from the recorded case export.
        replay_result = replay(
            CaseExport(
                records=[*records, passport_record],
                payloads={
                    decision_record.record_id: decision_payload,
                    passport_record.record_id: passport_payload,
                },
                evaluation_time=_EVAL_TIME,
                pack_versions={str(rule["id"]): str(rule["version"]) for rule in _FIXTURE_PACK},
                model_outputs={},
            )
        )

        # 10. Verify — both verifiers.
        structural = verify_structural(records)
        bundle_ok = verify_bundle(bundle)

        return SkeletonResult(
            case_id=self.case_id,
            tenant_id=self.tenant_id,
            decision=decision_str,
            reason_codes=list(eligibility.reason_codes),
            passport_hash=passport_hash,
            bundle_hash=bundle.manifest.bundle_hash,
            records=records,
            structural_ok=structural.ok,
            bundle_ok=bundle_ok,
            replay_ok=replay_result.ok,
            configuration_hash=self.configuration_hash,
        )

    async def _fixture_facts(self, chain: InMemoryCaseChain) -> list[FactEntry]:
        # 1. Intake — generate a synthetic document and store it.
        doc = self._factory.generate_document("invoice", "en")
        await chain.append(
            stage="Intake",
            actor=_ACTOR,
            record_type="document",
            payload={
                "document_id": doc.document_id,
                "doc_type": doc.doc_type,
                "sha256": doc.sha256,
                "label": doc.label,
            },
        )

        # 2. Extract — stub model with recorded responses.
        stub = StubExtractModel(doc)
        stage = ExtractStage(stub)
        request = ExtractRequest(
            document_text=doc.text,
            target_schema=STUB_SCHEMA,
            document_id=doc.document_id,
        )
        extract_result: ExtractResult = await stage.extract(request)
        await chain.append(
            stage="Extract",
            actor=_ACTOR,
            record_type="extract_result",
            payload={
                "document_id": doc.document_id,
                "fields": [f.name for f in extract_result.fields],
                "schema_valid": extract_result.schema_valid,
            },
        )

        # 3. Facts — convert extracted fields to verified facts.
        fact_entries: list[FactEntry] = []
        for f in extract_result.fields:
            if f.status == "EXTRACTED":
                fact_entries.append(
                    FactEntry(
                        key=f.name,
                        value=f.value,
                        status="VERIFIED",
                        label="SYNTHETIC",
                    )
                )
        await chain.append(
            stage="Facts",
            actor=_ACTOR,
            record_type="facts",
            payload={
                "facts": [f.key for f in fact_entries],
                "count": len(fact_entries),
            },
        )
        return fact_entries


def run_skeleton(seed: int = 42, *, configuration_hash: str | None = None) -> SkeletonResult:
    """Run the walking skeleton synchronously and return the result.

    Args:
        seed: The synthetic data factory seed.
        configuration_hash: The validated deployment configuration digest, when supplied.

    Returns:
        A :class:`SkeletonResult`.
    """
    return asyncio.run(WalkingSkeleton(seed, configuration_hash=configuration_hash).run())

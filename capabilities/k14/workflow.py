"""Compose Intake, K14, F01 and K09 for one tenant-owned case."""

from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, Protocol

from adapters.postgres.tenant_context import TenantContext
from capabilities import f01, k09
from capabilities.k14 import (
    BilingualIntake,
    BilingualIntakeReport,
    Field,
    NameLink,
    name_links,
    parallel_differences,
)
from kernel.auth.roles import Principal
from kernel.decision import FactEntry
from kernel.hashing import domain_hash
from kernel.humangate import HumanGate
from kernel.intake import IntakeDocument, IntakeStage
from kernel.ledger.chain import CaseChain, InMemoryCaseChain
from kernel.ledger.records import Actor
from kernel.skeleton.intake import IntakeInputs, Judgment, SourceDocument
from kernel.types.decision import DecisionValue

_COMMON = (
    Field("seller_name", "text"),
    Field("buyer_name", "text"),
    Field("consignee_name", "text"),
    Field("goods_description", "text"),
    Field("gross_weight", "quantity"),
    Field("net_weight", "quantity"),
    Field("total_quantity", "quantity"),
    Field("package_count", "number"),
    Field("currency", "identifier"),
    Field("invoice_total", "number"),
    Field("invoice_number", "identifier"),
    Field("transport_document_number", "identifier"),
    Field("container_numbers", "text"),
    Field("incoterm", "identifier"),
    Field("port_of_loading", "text"),
    Field("port_of_discharge", "text"),
    Field("declared_classification_code", "identifier", r"[0-9]{2,12}"),
    Field("shipped_on_board_date", "date"),
    Field("issue_date", "date"),
    Field("issuer", "text"),
    Field("packing_list_number", "identifier"),
    Field("certificate_number", "identifier"),
    Field("delivery_order_number", "identifier"),
    Field("declaration_number", "identifier"),
    Field("declared_customs_value", "number"),
    Field("declared_date", "date"),
    Field("freight", "number"),
    Field("insurance", "number"),
)
_REGISTRY = Path(__file__).resolve().parents[2] / "data" / "registry" / "sources.yaml"


class JudgeReport(Protocol):
    @property
    def outcome(self) -> DecisionValue: ...

    @property
    def reasons(self) -> Sequence[str]: ...


class CaseJudge(Protocol):
    def run(
        self, facts: Sequence[f01.CanonicalFact], at: datetime, origin: str
    ) -> tuple[JudgeReport, dict[str, object]]: ...


@dataclass(frozen=True)
class IntakeEvaluation:
    case_id: str
    label: str
    documents: tuple[IntakeDocument, ...]
    extraction: tuple[BilingualIntakeReport, ...]
    consistency: f01.ConsistencyReport
    shield: k09.DocumentShieldReport
    evidence: dict[str, list[dict[str, object]]]
    judgments: tuple[Judgment, ...] = ()

    def outcome(self, capability: str) -> tuple[str, tuple[str, ...]]:
        if capability == "F01":
            return self.consistency.outcome, self.consistency.reason_codes
        if capability == "K09":
            return self.shield.outcome, self.shield.reason_codes
        severity = ("PROVIDED", "NEEDS_REVIEW", "ABSTAINED")
        state = max((r.status for r in self.extraction), key=severity.index, default="ABSTAINED")
        return state, tuple(sorted({code for r in self.extraction for code in r.reason_codes}))


class IntakeWorkflow:
    """Orchestrate ports using an authenticated principal and server-owned policy."""

    def __init__(
        self,
        intake: IntakeStage,
        extraction: BilingualIntake,
        fingerprints: k09.FingerprintIndex,
        workflow: f01.Workflow,
        *,
        fields: Sequence[Field] = _COMMON,
        name_variants: Mapping[str, Sequence[str]] | None = None,
        label: Literal["DERIVED", "SYNTHETIC"] = "DERIVED",
        canonical_writer: f01.CanonicalWriter | None = None,
        case_access: Callable[[Principal, str], bool] | None = None,
        case_chain: Callable[[str, str], CaseChain] = InMemoryCaseChain,
        judges: Mapping[str, CaseJudge] | None = None,
    ) -> None:
        self._intake = intake
        self._extract = extraction
        self._index = fingerprints
        self._workflow = workflow
        self._fields = tuple(fields)
        self._name_variants = dict(name_variants or {})
        self._label = label
        self._writer = canonical_writer
        self._case_access = case_access
        self._case_chain = case_chain
        self._judges = dict(judges or {})
        self._chains: dict[tuple[str, str], CaseChain] = {}
        self._owners: dict[tuple[str, str], str] = {}
        self._results: dict[tuple[str, str], IntakeEvaluation] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._review: dict[tuple[str, str], HumanGate] = {}
        self._recorded_extraction: dict[tuple[str, str], BilingualIntakeReport] = {}
        self._parallel: dict[tuple[str, str], dict[str, str]] = {}

    def _accessible(self, principal: Principal, case_id: str) -> bool:
        if not principal.tenant_id:
            return False
        if self._case_access:
            return self._case_access(principal, case_id)
        return self._owners.get((principal.tenant_id, case_id)) == principal.principal_id

    def result(self, principal: Principal, case_id: str) -> IntakeEvaluation | None:
        if principal.tenant_id is None or not self._accessible(principal, case_id):
            return None
        state = self._results.get((principal.tenant_id, case_id))
        if state is None:
            return None
        shield = self._index.result(principal.tenant_id, case_id)
        if shield is None:
            return None
        permitted = frozenset(
            f.other_case_id
            for f in shield.findings
            if f.other_case_id and self._accessible(principal, f.other_case_id)
        )
        return replace(state, shield=shield.view(permitted, reviewer=principal.is_reviewer))

    async def ingest(
        self,
        principal: Principal,
        case_id: str,
        uploads: Sequence[SourceDocument],
        evaluation_time: str,
        *,
        chain: CaseChain | None = None,
    ) -> IntakeInputs:
        if not principal.tenant_id or not principal.can_operate():
            raise PermissionError("CASE_NOT_FOUND")
        tenant = principal.tenant_id
        key = (tenant, case_id)
        context = TenantContext(tenant, principal.principal_id)
        actor = Actor("ROLE", principal.role)
        async with self._locks.setdefault(tenant, asyncio.Lock()):
            if (key in self._owners or self._case_access) and not self._accessible(
                principal, case_id
            ):
                raise PermissionError("CASE_NOT_FOUND")
            if chain is None:
                if key not in self._chains:
                    self._chains[key] = self._case_chain(tenant, case_id)
                chain = self._chains[key]
            if (chain.tenant_id, chain.case_id) != key:
                raise PermissionError("CASE_NOT_FOUND")
            self._owners.setdefault(key, principal.principal_id)
            self._chains[key] = chain
            groups = self._parallel.setdefault(key, {})
            observed = set()
            for upload in uploads:
                document = await self._intake.ingest(
                    context,
                    chain,
                    actor,
                    payload=upload.payload,
                    filename=upload.filename,
                    document_type=upload.document_type,
                    created_at=evaluation_time,
                )
                if upload.parallel_group:
                    groups[document.record.document_id] = upload.parallel_group
                if document.duplicate:
                    observed.add(document.record.document_id)
            documents = tuple(
                sorted(
                    await self._intake.documents(context, case_id),
                    key=lambda doc: doc.record.document_id,
                )
            )
            await self._evaluate(
                context, chain, actor, documents, groups, observed, evaluation_time
            )
            result = self._results[key]
            facts = tuple(
                FactEntry(
                    fact.key,
                    json.dumps(fact.value, ensure_ascii=False),
                    fact.status,
                    fact.label,
                )
                for fact in result.consistency.canonical
            )
            required = tuple(
                f"shipment.{field}" for field in sorted(self._workflow.required_fields)
            )
            return IntakeInputs(
                facts,
                required,
                (
                    (DecisionValue[result.consistency.outcome], result.consistency.reason_codes),
                    (DecisionValue[result.shield.outcome], result.shield.reason_codes),
                ),
                self._label,
                result.judgments,
            )

    async def erase_document(
        self,
        principal: Principal,
        case_id: str,
        document_id: str,
    ) -> bool:
        tenant = principal.tenant_id
        if tenant is None or principal.role != "administrator":
            raise PermissionError("CASE_NOT_FOUND")
        async with self._locks.setdefault(tenant, asyncio.Lock()):
            if not self._accessible(principal, case_id):
                raise PermissionError("CASE_NOT_FOUND")
            key = (tenant, case_id)
            state = self._results.get(key)
            if state is None:
                return False
            context = TenantContext(tenant, principal.principal_id)
            digest = await self._intake.erase(context, case_id, document_id)
            if digest is None:
                return False
            self._index.erase(tenant, document_id)
            self._recorded_extraction.pop((tenant, document_id), None)
            groups = self._parallel[key]
            groups.pop(document_id, None)
            chain = self._chains[key]
            actor = Actor("ROLE", principal.role)
            await chain.append(
                "Intake",
                actor,
                "document_erased",
                {
                    "document_id": document_id,
                    "sha256": digest,
                },
            )
            retained = tuple(
                doc for doc in state.documents if doc.record.document_id != document_id
            )
            await self._evaluate(
                context, chain, actor, retained, groups, set(), state.consistency.evaluation_time
            )
            return True

    async def declare_relation(
        self,
        principal: Principal,
        case_id: str,
        other_case: str,
        document_id: str,
        other_document: str,
        relation: k09.RelationKind,
    ) -> None:
        tenant = principal.tenant_id
        if tenant is None or not principal.can_approve():
            raise PermissionError("CASE_NOT_FOUND")
        async with self._locks.setdefault(tenant, asyncio.Lock()):
            if not self._accessible(principal, case_id) or not self._accessible(
                principal, other_case
            ):
                raise PermissionError("CASE_NOT_FOUND")
            first = self._results.get((tenant, case_id))
            second = self._results.get((tenant, other_case))
            if first is None or second is None or document_id == other_document:
                raise PermissionError("CASE_NOT_FOUND")
            if not any(d.record.document_id == document_id for d in first.documents) or not any(
                d.record.document_id == other_document for d in second.documents
            ):
                raise PermissionError("CASE_NOT_FOUND")
            proposal = {"documents": sorted((document_id, other_document)), "relation": relation}
            encoded = json.dumps(proposal, sort_keys=True, separators=(",", ":")).encode()
            commitment = hashlib.sha256(encoded).hexdigest()
            review = self._review.setdefault((tenant, case_id), HumanGate(case_id))
            approved = review.approve(
                proposal,
                commitment,
                principal.principal_id,
                principal.role,
                "REVIEW",
            )
            chain = self._chains[(tenant, case_id)]
            actor = Actor("ROLE", principal.role)
            event = await chain.append(
                "HumanGate",
                actor,
                "document_relation",
                {
                    **proposal,
                    "approval_hash": approved.proposal_hash,
                    "status": "VERIFIED",
                },
            )
            self._index.declare(
                tenant, k09.Relation(document_id, other_document, relation, event.record_id)
            )
            self._index.evaluate(tenant, case_id)
            self._index.evaluate(tenant, other_case)
            await self._record_symmetry(tenant)

    async def _record_symmetry(self, tenant: str) -> None:
        for key, old in tuple(self._results.items()):
            if key[0] != tenant:
                continue
            current = self._index.result(*key)
            if current is None or current == old.shield:
                continue
            chain = self._chains[key]
            actor = Actor("SYSTEM", "intake")
            previous = old.shield.output_hash
            await chain.append("Facts", actor, "document_shield_stale", {"output_hash": previous})
            updated = {
                **old.evidence["K09"][-1],
                "output_hash": current.output_hash,
                "supersedes": previous,
            }
            await chain.append("Facts", actor, "document_shield", updated)
            evidence = {**old.evidence, "K09": [*old.evidence["K09"], updated]}
            self._results[key] = replace(old, shield=current, evidence=evidence)

    async def _evaluate(
        self,
        context: TenantContext,
        chain: CaseChain,
        actor: Actor,
        documents: tuple[IntakeDocument, ...],
        groups: dict[str, str],
        observed: set[str],
        evaluation_time: str,
    ) -> None:
        reports = []
        for doc in documents:
            key = (context.tenant_id, doc.record.document_id)
            report = self._recorded_extraction.get(key)
            if report is None or report.status == "ABSTAINED":
                report = await self._extract.evaluate(doc, self._fields)
                self._recorded_extraction[key] = report
            reports.append(report)
        extraction = _parallel(tuple(reports), groups, self._name_variants)
        facts: list[f01.Fact] = []
        prints: list[k09.Fingerprint] = []
        evidence: dict[str, list[dict[str, object]]] = {"K14": [], "F01": [], "K09": []}
        for doc, report in zip(documents, extraction, strict=True):
            commitment: dict[str, object] = {
                "document_hash": report.document_hash,
                "output_hash": report.output_hash,
                "pack_version": report.pack_version,
                "calls": [asdict(call) for call in report.calls],
                "normalization_counts": report.normalization_counts,
            }
            evidence["K14"].append(commitment)
            await chain.append("Extract", actor, "bilingual_intake", commitment)
            currency = next(
                (
                    f.normalized.upper()
                    for f in report.facts
                    if f.name == "currency" and f.normalized and f.status == "VERIFIED"
                ),
                None,
            )
            doc_facts = []
            for fact in report.facts:
                status = fact.status
                if "PARALLEL_DIFFERENCE" in fact.flags:
                    status = "UNKNOWN"
                fid = domain_hash("ctc/payload/v1", [report.document_id, fact.name])
                scale = (
                    max(0, -int(Decimal(fact.normalized).as_tuple().exponent))
                    if fact.normalized and fact.kind in {"number", "quantity"}
                    else None
                )
                doc_facts.append(
                    f01.Fact(
                        fid,
                        report.document_id,
                        doc.document_type,
                        fact.name,
                        fact.normalized or "",
                        fact.original,
                        str((fact.page, fact.span)),
                        status,
                        self._label,
                        fact.unit,
                        scale,
                        currency,
                    )
                )
            facts.extend(doc_facts)
            printed = k09.fingerprint(
                replace(doc, duplicate=report.document_id in observed),
                [k09.IdentityFact(f.field, f.value, f.status) for f in doc_facts],
            )
            prints.append(printed)
        workflow = replace(
            self._workflow, container_rule_verified=f01.container_rule_verified(_REGISTRY)
        )
        configuration = domain_hash(
            "ctc/payload/v1",
            {
                "required_fields": sorted(workflow.required_fields),
                "required_documents": sorted(workflow.required_document_types),
                "agreements": [asdict(agreement) for agreement in workflow.agreements],
                "allowed_labels": sorted(workflow.allowed_labels),
                "quantity_tolerance": str(workflow.quantity_tolerance),
                "description_bands": [
                    str(workflow.description_lower),
                    str(workflow.description_upper),
                ],
                "confirmed_name_links": sorted(
                    sorted(link) for link in workflow.confirmed_name_links
                ),
                "currency_precision": workflow.currency_precision,
                "container_rule_verified": workflow.container_rule_verified,
            },
        )
        consistency = f01.evaluate(
            chain.case_id,
            facts,
            [doc.document_type for doc in documents],
            workflow,
            evaluation_time=evaluation_time,
            configuration_hash=configuration,
        )
        consistent = dict(f01.evaluation_record(consistency, facts))
        evidence["F01"].append(consistent)
        await chain.append("Facts", actor, "consistency_evaluation", consistent)
        for finding in consistency.findings:
            await chain.append(
                "Facts",
                actor,
                "consistency_finding",
                {
                    "finding_id": finding.finding_id,
                    "reason_code": finding.reason_code,
                    "fact_ids": [f.fact_id for f in finding.facts],
                    "core": finding.core,
                },
            )
        if self._writer is not None:
            await consistency.publish(self._writer)
        for request in consistency.canonical:
            await chain.append(
                "Facts",
                actor,
                "canonical_fact",
                {
                    "key": request.key,
                    "source_fact_ids": request.source_fact_ids,
                    "label": request.label,
                    "status": request.status,
                },
            )
        for printed in prints:
            self._index.upsert(printed)
        shield = self._index.evaluate(context.tenant_id, chain.case_id)
        shield_record = dict(k09.evidence(shield, prints, configuration))
        evidence["K09"].append(shield_record)
        await chain.append("Facts", actor, "document_shield", shield_record)
        for shield_finding in shield.findings:
            await chain.append(
                "Facts",
                actor,
                "document_shield_finding",
                {
                    "reason_code": shield_finding.reason_code,
                    "document_id": shield_finding.document_id,
                },
            )
        key = (context.tenant_id, chain.case_id)
        previous = self._results.get(key)
        judgments = await self._judge_case(chain, actor, consistency, previous)
        for judgment in judgments:
            evidence[judgment.capability_id] = [dict(judgment.evidence)]
        self._results[key] = IntakeEvaluation(
            chain.case_id,
            self._label,
            documents,
            extraction,
            consistency,
            shield,
            evidence,
            judgments,
        )
        self._index.recompute_stale(context.tenant_id)
        await self._record_symmetry(context.tenant_id)

    async def _judge_case(
        self,
        chain: CaseChain,
        actor: Actor,
        consistency: f01.ConsistencyReport,
        previous: IntakeEvaluation | None,
    ) -> tuple[Judgment, ...]:
        """Recompute configured judgments and record when earlier evidence becomes stale."""
        if not self._judges:
            return ()
        at = datetime.fromisoformat(consistency.evaluation_time)
        previous_judgments = {
            item.capability_id: item.evidence for item in (previous.judgments if previous else ())
        }
        judgments = []
        for capability_id, judge in sorted(self._judges.items()):
            report, record = judge.run(consistency.canonical, at, self._label)
            prior = previous_judgments.get(capability_id)
            if prior and any(
                record.get(key) != prior.get(key)
                for key in (
                    "input_hash",
                    "configuration_hash",
                    "reference_pack_hash",
                    "fx_pack_hash",
                    "tariff_pack_hash",
                    "calibration_hash",
                    "calibration_hashes",
                )
            ):
                old = prior["output_hash"]
                await chain.append(
                    "Facts",
                    actor,
                    "case_judgment_stale",
                    {
                        "capability_id": capability_id,
                        "output_hash": old,
                    },
                )
                record["supersedes"] = old
            await chain.append("Facts", actor, "case_judgment", record)
            judgments.append(Judgment(capability_id, report.outcome, tuple(report.reasons), record))
        return tuple(judgments)


def _parallel(
    reports: tuple[BilingualIntakeReport, ...],
    groups: dict[str, str],
    variants: Mapping[str, Sequence[str]],
) -> tuple[BilingualIntakeReport, ...]:
    proposed: dict[str, list[NameLink]] = {}
    flagged: dict[str, set[str]] = {}
    for index, first in enumerate(reports):
        group = groups.get(first.document_id)
        if not group:
            continue
        for second in reports[index + 1 :]:
            if group != groups.get(second.document_id):
                continue
            links = name_links(first, second, variants)
            if links:
                proposed.setdefault(first.document_id, []).extend(links)
                proposed.setdefault(second.document_id, []).extend(links)
            fields = parallel_differences(first, second)
            if fields:
                flagged.setdefault(first.document_id, set()).update(fields)
                flagged.setdefault(second.document_id, set()).update(fields)
    updated = []
    for report in reports:
        flagged_fields = flagged.get(report.document_id, set())
        links = tuple(dict.fromkeys(proposed.get(report.document_id, [])))
        altered = replace(report, name_link_proposals=links)
        if flagged_fields:
            altered = replace(
                altered,
                status="NEEDS_REVIEW",
                parallel_fields=tuple(sorted(flagged_fields)),
                reason_codes=tuple(
                    sorted({*report.reason_codes, "K14.NEEDS_REVIEW.PARALLEL_DIFFERENCE"})
                ),
                facts=tuple(
                    replace(f, status="UNKNOWN", flags=(*f.flags, "PARALLEL_DIFFERENCE"))
                    if f.name in flagged_fields
                    else f
                    for f in report.facts
                ),
            )
        updated.append(altered)
    return tuple(updated)

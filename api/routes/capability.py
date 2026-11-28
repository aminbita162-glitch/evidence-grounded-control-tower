"""Uniform capability route family (P10-T02).

A single uniform route family through which any capability is invoked by its
registration entry.  Four operations per capability:

  - ``POST /api/v1/capabilities/{capability_id}/invoke`` — invoke
  - ``GET  /api/v1/capabilities/{capability_id}/status``  — status
  - ``GET  /api/v1/capabilities/{capability_id}/result``   — result
  - ``GET  /api/v1/capabilities/{capability_id}/evidence``  — evidence

Every operation appears in the OpenAPI contract (architecture test, T02
acceptance).  Interactive documentation is served at ``/api/v1/docs``.

Spec: Part 3 §3.17; P10-T02.
"""

from __future__ import annotations

import base64
import binascii
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import asdict, replace
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Annotated, Any, Literal, Protocol

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi import Path as PathParam
from pydantic import BaseModel, Field, ValidationError
from pydantic_core import to_jsonable_python

from api.authentication import operator_principal, reviewer_principal, tenant_principal
from api.problems import not_found_response, problem_response
from capabilities.f02.registration import register as evaluate_classification
from capabilities.k05.registration import register as evaluate_valuation
from kernel.auth.roles import Principal
from kernel.errors import ProblemDetails
from kernel.hashing import domain_hash
from kernel.humangate import HumanGateError
from kernel.skeleton.finance import FINANCE_IDS, CaseFinance, FinanceResult, FinanceSource
from kernel.skeleton.intake import SourceDocument
from kernel.types.decision import DecisionValue

if TYPE_CHECKING:
    from capabilities.f02.registration import ClassificationJudge
    from capabilities.k05.registration import ValuationJudge
    from capabilities.k14.workflow import IntakeEvaluation, IntakeWorkflow

__all__ = [
    "InvokeRequest",
    "CapabilityResponse",
    "CapabilityInvocation",
    "StatusResponse",
    "ResultResponse",
    "EvidenceResponse",
    "create_capability_router",
    "register_capability_routes",
]

_API_PREFIX = "/api/v1"
_INTAKE_IDS = {"K14", "F01", "K09"}
_MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
_MAX_DOCUMENTS = 6


class InvokeRequest(BaseModel):
    """Request body for the invoke operation."""

    facts: dict[str, Any] = Field(
        default_factory=dict, description="Input facts for the capability."
    )
    evaluation_time: str = Field(default="", description="The evaluation time in ISO 8601 UTC.")


class CapabilityResponse(BaseModel):
    """Generic response for a capability operation."""

    capability_id: str = Field(description="The capability identifier.")
    case_id: str = Field(default="", description="The case identifier, if assigned.")
    status: str = Field(default="PENDING", description="The invocation status.")
    label: str = Field(default="SYNTHETIC", description="The data label.")


type CapabilityInvocation = Callable[[Principal, InvokeRequest], Awaitable[CapabilityResponse]]


class StatusResponse(BaseModel):
    """Response for the status operation."""

    capability_id: str = Field(description="The capability identifier.")
    case_id: str = Field(default="", description="The case identifier, if assigned.")
    state: str = Field(default="CREATED", description="The case state.")
    updated: str = Field(default="", description="The last update time.")


class ResultResponse(BaseModel):
    """Response for the result operation."""

    capability_id: str = Field(description="The capability identifier.")
    case_id: str = Field(default="", description="The case identifier, if assigned.")
    decision: str = Field(default="", description="The decision value.")
    reason_codes: list[str] = Field(
        default_factory=list, description="Reason codes for the decision."
    )
    label: str = Field(default="SYNTHETIC", description="The data label.")
    report: dict[str, Any] | None = Field(default=None, description="Registered capability report.")


class EvidenceResponse(BaseModel):
    """Response for the evidence operation."""

    capability_id: str = Field(description="The capability identifier.")
    case_id: str = Field(default="", description="The case identifier, if assigned.")
    records: list[dict[str, Any]] = Field(default_factory=list, description="Evidence records.")
    bundle_hash: str = Field(default="", description="The evidence bundle hash.")


class RelationRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=128)
    other_case_id: str = Field(min_length=1, max_length=128)
    document_id: str = Field(min_length=1, max_length=128)
    other_document_id: str = Field(min_length=1, max_length=128)
    relation: Literal["SUPERSEDES", "AMENDS", "SPLIT_OF", "SAME_CONSIGNMENT"]


def _source_documents(raw: object) -> tuple[SourceDocument, ...]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= _MAX_DOCUMENTS:
        raise HTTPException(status_code=422, detail="INTAKE_DOCUMENT_COUNT")
    uploads = []
    total = 0
    for item in raw:
        if not isinstance(item, dict):
            raise HTTPException(status_code=422, detail="INTAKE_DOCUMENT_INVALID")
        name, kind, encoded, group = (
            item.get("filename"),
            item.get("document_type"),
            item.get("content_base64"),
            item.get("parallel_group", ""),
        )
        if not isinstance(name, str) or not 1 <= len(name) <= 255 or not isinstance(kind, str):
            raise HTTPException(status_code=422, detail="INTAKE_DOCUMENT_INVALID")
        if kind not in {
            "COMMERCIAL_INVOICE",
            "PACKING_LIST",
            "TRANSPORT_DOCUMENT",
            "ORIGIN_CERTIFICATE",
            "DELIVERY_ORDER",
            "INSURANCE_CERTIFICATE",
            "DECLARATION_DRAFT",
        }:
            raise HTTPException(status_code=422, detail="INTAKE_DOCUMENT_TYPE")
        if not isinstance(encoded, str) or not isinstance(group, str) or len(group) > 64:
            raise HTTPException(status_code=422, detail="INTAKE_DOCUMENT_INVALID")
        if len(encoded) > 4 * ((_MAX_DOCUMENT_BYTES + 2) // 3):
            raise HTTPException(status_code=413, detail="INTAKE_DOCUMENT_SIZE")
        try:
            payload = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise HTTPException(status_code=422, detail="INTAKE_DOCUMENT_ENCODING") from exc
        total += len(payload)
        if total > _MAX_DOCUMENT_BYTES:
            raise HTTPException(status_code=413, detail="INTAKE_DOCUMENT_SIZE")
        uploads.append(SourceDocument(name, kind, payload, group))
    return tuple(uploads)


def intake_invocation(capability_id: str, workflow: IntakeWorkflow) -> CapabilityInvocation:
    """Bind a document-backed capability to the uniform invoke route."""

    async def invoke(principal: Principal, request: InvokeRequest) -> CapabilityResponse:
        case = request.facts.get("case_id")
        if not isinstance(case, str) or not 1 <= len(case) <= 128:
            raise HTTPException(status_code=422, detail="INTAKE_CASE_ID")
        documents = request.facts.get("documents")
        if documents is not None:
            uploads = _source_documents(documents)
            try:
                await workflow.ingest(principal, case, uploads, request.evaluation_time)
            except PermissionError as exc:
                raise HTTPException(status_code=404, detail="Resource not found") from exc
        result = workflow.result(principal, case)
        if result is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        status, _ = result.outcome(capability_id)
        return CapabilityResponse(
            capability_id=capability_id, case_id=case, status=status, label=result.label
        )

    return invoke


def _intake_report(result: IntakeEvaluation, capability: str) -> dict[str, Any]:
    if capability == "F01":
        return asdict(result.consistency)
    if capability == "K09":
        return asdict(result.shield)
    return {"documents": [asdict(report) for report in result.extraction]}


def create_capability_router(
    registrations: Mapping[str, CapabilityInvocation] | None = None,
    *,
    intake: IntakeWorkflow | None = None,
    valuation: ValuationJudge | None = None,
    classification: ClassificationJudge | None = None,
    finance: FinanceSource | None = None,
) -> APIRouter:
    """Create the uniform capability router.

    Returns:
        An :class:`APIRouter` with the four capability operations.
    """
    router = APIRouter(
        prefix=_API_PREFIX, tags=["capabilities"], dependencies=[Depends(tenant_principal)]
    )

    handlers = dict(registrations or {})
    _cap_desc = "The capability identifier."
    _cap_path = PathParam(..., description=_cap_desc, examples=["F01", "K01"])

    @router.post(
        "/capabilities/{capability_id}/invoke",
        response_model=CapabilityResponse,
        summary="Invoke a capability",
        operation_id="invoke_capability",
    )
    async def invoke_capability(
        principal: Annotated[Principal, Depends(operator_principal)],
        capability_id: str = _cap_path,
        request: InvokeRequest | None = None,
    ) -> CapabilityResponse:
        """Invoke a capability by its registration entry."""
        if capability_id in handlers:
            return await handlers[capability_id](principal, request or InvokeRequest())
        return CapabilityResponse(
            capability_id=capability_id,
            case_id="",
            status="PENDING",
            label="SYNTHETIC",
        )

    @router.get(
        "/capabilities/{capability_id}/status",
        response_model=StatusResponse,
        summary="Get capability invocation status",
        operation_id="get_status",
    )
    async def get_status(
        principal: Annotated[Principal, Depends(tenant_principal)],
        capability_id: str = _cap_path,
        case_id: Annotated[str | None, Query(max_length=128)] = None,
    ) -> StatusResponse | Response:
        """Get the status of a capability invocation."""
        if intake is not None and capability_id in _INTAKE_IDS and case_id is not None:
            result = intake.result(principal, case_id)
            if result is None:
                return not_found_response()
            return StatusResponse(
                capability_id=capability_id,
                case_id=case_id,
                state=result.outcome(capability_id)[0],
                updated=result.consistency.evaluation_time,
            )
        return StatusResponse(
            capability_id=capability_id,
            case_id="",
            state="CREATED",
            updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    @router.get(
        "/capabilities/{capability_id}/result",
        response_model=ResultResponse,
        summary="Get capability result",
        operation_id="get_result",
    )
    async def get_result(
        principal: Annotated[Principal, Depends(tenant_principal)],
        capability_id: str = _cap_path,
        case_id: Annotated[str | None, Query(max_length=128)] = None,
    ) -> ResultResponse | Response:
        """Get the result of a capability invocation."""
        if intake is not None and capability_id in _INTAKE_IDS and case_id is not None:
            result = intake.result(principal, case_id)
            if result is None:
                return not_found_response()
            decision, codes = result.outcome(capability_id)
            return ResultResponse(
                capability_id=capability_id,
                case_id=case_id,
                decision=decision,
                reason_codes=list(codes),
                label=result.label,
                report=_intake_report(result, capability_id),
            )
        return ResultResponse(
            capability_id=capability_id,
            case_id="",
            decision="",
            reason_codes=[],
            label="SYNTHETIC",
        )

    @router.get(
        "/capabilities/{capability_id}/evidence",
        response_model=EvidenceResponse,
        summary="Get capability evidence",
        operation_id="get_evidence",
    )
    async def get_evidence(
        principal: Annotated[Principal, Depends(tenant_principal)],
        capability_id: str = _cap_path,
        case_id: Annotated[str | None, Query(max_length=128)] = None,
    ) -> EvidenceResponse | Response:
        """Get the evidence records for a capability invocation."""
        if intake is not None and capability_id in _INTAKE_IDS and case_id is not None:
            result = intake.result(principal, case_id)
            if result is None:
                return not_found_response()
            return EvidenceResponse(
                capability_id=capability_id, case_id=case_id, records=result.evidence[capability_id]
            )
        return EvidenceResponse(
            capability_id=capability_id,
            case_id="",
            records=[],
            bundle_hash="",
        )

    _add_case_evaluations(router, intake, valuation, classification, finance)
    if intake is not None:
        bound = intake

        @router.post(
            "/capabilities/K09/relations", status_code=204, operation_id="declare_document_relation"
        )
        async def declare_relation(
            principal: Annotated[Principal, Depends(reviewer_principal)],
            request: RelationRequest,
        ) -> Response:
            try:
                await bound.declare_relation(
                    principal,
                    request.case_id,
                    request.other_case_id,
                    request.document_id,
                    request.other_document_id,
                    request.relation,
                )
            except PermissionError:
                return not_found_response()
            except HumanGateError as exc:
                raise HTTPException(status_code=409, detail="RELATION_ALREADY_RECORDED") from exc
            return Response(status_code=204)

    return router


class _JudgeReport(Protocol):
    @property
    def outcome(self) -> DecisionValue: ...

    def view(self, role: str) -> dict[str, object]: ...


class FinanceProblem(HTTPException):
    """A stable problem response for the case finance route."""


async def _finance_problem(_request: Request, error: Exception) -> Response:
    if not isinstance(error, FinanceProblem):
        raise error
    if error.status_code == 404:
        return not_found_response()
    detail = str(error.detail)
    return problem_response(
        ProblemDetails(
            type=f"urn:ctc:problem:{detail.lower().replace('_', '-')}",
            title=HTTPStatus(error.status_code).phrase,
            status=error.status_code,
            detail=detail,
        )
    )


def _validate_finance_decimals(value: object) -> None:
    if isinstance(value, float):
        raise ValueError("recorded decimal inputs require exact decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _validate_finance_decimals(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _validate_finance_decimals(item)


def evaluate_finance_step(
    capability_id: str,
    payload: Mapping[str, object],
    at: datetime,
) -> FinanceResult:
    """Validate and evaluate a recorded case input for the requested financial step."""
    _validate_finance_decimals(payload)

    from capabilities.f03 import registration as f03
    from capabilities.f07 import registration as f07
    from capabilities.l01 import registration as l01
    from capabilities.l02 import registration as l02

    if capability_id == "F03":
        clocks, evidence = f03.register(f03.INPUT.validate_python(payload), at)
        public = f03.OUTPUT.dump_python(clocks, mode="json")
        return FinanceResult(
            clocks.decision.name,
            public,
            evidence,
            f03.render_timeline(clocks),
            tuple(sorted({row.reason.value for row in clocks.clocks})),
        )
    if capability_id == "L01":
        invoice, evidence = l01.register(l01.INPUT.validate_python(payload), at)
        public = l01.OUTPUT.dump_python(invoice, mode="json")
        return FinanceResult(
            invoice.outcome.name,
            public,
            evidence,
            l01.render_audit(invoice),
            tuple(invoice.reason_codes),
        )
    if capability_id == "L02":
        estimate, evidence = l02.register(l02.INPUT.validate_python(payload), at)
        public = l02.OUTPUT.dump_python(estimate, mode="json")
        return FinanceResult(
            estimate.status.value,
            public,
            evidence,
            l02.render_estimate(estimate),
            tuple(estimate.reason_codes),
        )
    if capability_id == "F07":
        charges, evidence = f07.register(f07.INPUT.validate_python(payload), at)
        public = f07.OUTPUT.dump_python(charges, mode="json")
        return FinanceResult(
            charges.outcome.name,
            public,
            evidence,
            f07.render_audit(charges),
            tuple(charges.reason_codes),
        )
    raise ValueError("unknown case finance capability")


def _add_case_evaluations(
    router: APIRouter,
    intake: IntakeWorkflow | None,
    valuation: ValuationJudge | None,
    classification: ClassificationJudge | None,
    finance: FinanceSource | None,
) -> None:
    """Bind case evaluation and retrieval to the authenticated tenant and case."""
    evaluations: dict[
        tuple[str, str, str, str], tuple[str, str, _JudgeReport, dict[str, object]]
    ] = {}
    idempotency: dict[tuple[str, str, str, str], str] = {}

    finance_evaluations: dict[tuple[str, str, str, str], tuple[str, str, FinanceResult]] = {}
    finance_simulations: dict[tuple[str, str, str, str], tuple[str, str, FinanceResult]] = {}

    def saved_finance(key: tuple[str, str, str, str]) -> tuple[str, str, FinanceResult] | None:
        return finance_evaluations.get(key) or finance_simulations.get(key)

    def finance_case(principal: Principal, case_id: str) -> CaseFinance:
        tenant = principal.tenant_id
        snapshot = finance(tenant, case_id) if finance is not None and tenant else None
        if snapshot is None or (snapshot.tenant_id, snapshot.case_id) != (tenant, case_id):
            raise FinanceProblem(status_code=404, detail="Resource not found")
        if intake is not None and ("F03" in snapshot.inputs or "F07" in snapshot.inputs):
            intake_result = intake.result(principal, case_id)
            if intake_result is None:
                raise FinanceProblem(status_code=404, detail="Resource not found")
            containers: set[str] = set()
            for fact in intake_result.consistency.canonical:
                if fact.key == "shipment.container_numbers" and fact.status == "VERIFIED":
                    if isinstance(fact.value, (list, tuple)):
                        containers.update(item for item in fact.value if isinstance(item, str))
                    elif isinstance(fact.value, str):
                        containers.add(fact.value)
            inputs = {
                name: {**values, "canonical_containers": sorted(containers)}
                if name in {"F03", "F07"}
                else values
                for name, values in snapshot.inputs.items()
            }
            snapshot = replace(snapshot, inputs=inputs)
        return snapshot

    def case_result(principal: Principal, case_id: str, capability_id: str) -> IntakeEvaluation:
        result = (
            intake.result(principal, case_id)
            if intake is not None and capability_id in {"K05", "F02"}
            else None
        )
        if result is None or principal.tenant_id is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        return result

    @router.post(
        "/cases/{case_id}/capabilities/{capability_id}/evaluations",
        operation_id="create_case_capability_evaluation",
        status_code=201,
    )
    async def create_evaluation(
        principal: Annotated[Principal, Depends(operator_principal)],
        case_id: Annotated[str, PathParam(min_length=1, max_length=128)],
        capability_id: str,
        request: InvokeRequest,
        idempotency_key: Annotated[str, Header(min_length=1, max_length=128)],
    ) -> dict[str, object]:
        tenant = principal.tenant_id or ""
        snapshot = finance_case(principal, case_id) if capability_id in FINANCE_IDS else None
        case = None if snapshot is not None else case_result(principal, case_id, capability_id)
        error_type = FinanceProblem if snapshot is not None else HTTPException
        if request.facts:
            raise error_type(status_code=422, detail="CASE_FACTS_ARE_SERVER_OWNED")
        try:
            at = datetime.fromisoformat(request.evaluation_time)
        except ValueError as error:
            raise error_type(status_code=422, detail="EVALUATION_TIME_REQUIRED") from error
        if at.tzinfo is None:
            raise error_type(status_code=422, detail="EVALUATION_TIME_REQUIRED")
        request_hash = domain_hash("ctc/payload/v1", at.isoformat())
        if snapshot is not None:
            payload = snapshot.input_for(capability_id)
            if payload is None:
                raise FinanceProblem(status_code=404, detail="Resource not found")
            version = snapshot.version(capability_id)
            key = (tenant, case_id, capability_id, idempotency_key)
            identifier = idempotency.get(key)
            if identifier is not None:
                saved = saved_finance((tenant, case_id, capability_id, identifier))
                if saved is None:
                    raise FinanceProblem(status_code=404, detail="Resource not found")
                saved_request, saved_version, earlier = saved
                if saved_request != request_hash:
                    raise FinanceProblem(status_code=409, detail="IDEMPOTENCY_CONFLICT")
                return {
                    "evaluation_id": identifier,
                    "status": earlier.status if saved_version == version else "STALE",
                }
            try:
                finance_result = evaluate_finance_step(capability_id, payload, at)
            except (ValidationError, ValueError, ArithmeticError) as error:
                raise FinanceProblem(
                    status_code=422, detail="INVALID_RECORDED_FINANCE_INPUT"
                ) from error
            identifier = domain_hash("ctc/payload/v1", (*key, version, request_hash))
            records = (
                finance_simulations
                if finance_result.evidence.get("record_kind") == "SIMULATION"
                else finance_evaluations
            )
            records[(tenant, case_id, capability_id, identifier)] = (
                request_hash,
                version,
                finance_result,
            )
            idempotency[key] = identifier
            return {"evaluation_id": identifier, "status": finance_result.status}
        if case is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        case_version = case.consistency.output_hash
        key = (tenant, case_id, capability_id, idempotency_key)
        evaluation_id = idempotency.get(key)
        if evaluation_id is not None:
            saved_hash, version, earlier_report, _ = evaluations[
                (tenant, case_id, capability_id, evaluation_id)
            ]
            if request_hash != saved_hash:
                raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT")
            status = earlier_report.outcome.name if version == case_version else "STALE"
            return {"evaluation_id": evaluation_id, "status": status}
        report: _JudgeReport
        if capability_id == "K05":
            report, record = evaluate_valuation(
                valuation, case.consistency.canonical, at, case.label
            )
        else:
            report, record = evaluate_classification(
                classification, case.consistency.canonical, at, case.label
            )
        evaluation_id = domain_hash("ctc/payload/v1", (*key, case_version, request_hash))
        evaluations[(tenant, case_id, capability_id, evaluation_id)] = (
            request_hash,
            case_version,
            report,
            record,
        )
        idempotency[key] = evaluation_id
        return {"evaluation_id": evaluation_id, "status": report.outcome.name}

    @router.get(
        "/cases/{case_id}/capabilities/{capability_id}/evaluations/{evaluation_id}",
        operation_id="get_case_capability_evaluation",
    )
    async def get_evaluation(
        principal: Annotated[Principal, Depends(tenant_principal)],
        case_id: Annotated[str, PathParam(min_length=1, max_length=128)],
        capability_id: str,
        evaluation_id: str,
    ) -> dict[str, object]:
        if capability_id in FINANCE_IDS:
            snapshot = finance_case(principal, case_id)
            saved = saved_finance(
                (principal.tenant_id or "", case_id, capability_id, evaluation_id)
            )
            if saved is None:
                raise FinanceProblem(status_code=404, detail="Resource not found")
            _, version, result = saved
            response = {"evaluation_id": evaluation_id, "evidence": result.evidence}
            if version != snapshot.version(capability_id):
                return {**response, "status": "STALE"}
            return {
                **response,
                "status": result.status,
                "report": result.report,
                "view": result.view,
            }
        case = case_result(principal, case_id, capability_id)
        entry = evaluations.get((principal.tenant_id or "", case_id, capability_id, evaluation_id))
        if entry is None:
            raise HTTPException(status_code=404, detail="Resource not found")
        _, version, report, record = entry
        if version != case.consistency.output_hash:
            return {"evaluation_id": evaluation_id, "status": "STALE", "evidence": record}
        return {
            "evaluation_id": evaluation_id,
            "status": report.outcome.name,
            "report": to_jsonable_python(report.view(principal.role)),
            "evidence": record,
        }


def register_capability_routes(
    app: Any,
    registrations: Mapping[str, CapabilityInvocation] | None = None,
    *,
    intake: IntakeWorkflow | None = None,
    valuation: ValuationJudge | None = None,
    classification: ClassificationJudge | None = None,
    finance: FinanceSource | None = None,
) -> None:
    """Register the uniform capability routes on a FastAPI app."""

    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app.add_exception_handler(FinanceProblem, _finance_problem)
    app.include_router(
        create_capability_router(
            registrations,
            intake=intake,
            valuation=valuation,
            classification=classification,
            finance=finance,
        )
    )

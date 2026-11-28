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
from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response
from fastapi import Path as PathParam
from pydantic import BaseModel, Field

from api.authentication import operator_principal, reviewer_principal, tenant_principal
from api.problems import not_found_response
from capabilities.k05.registration import register as evaluate_valuation
from kernel.auth.roles import Principal
from kernel.hashing import domain_hash
from kernel.humangate import HumanGateError
from kernel.skeleton.intake import SourceDocument

if TYPE_CHECKING:
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

    if intake is not None:
        bound = intake
        _add_case_evaluations(router, bound, valuation)

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


def _add_case_evaluations(
    router: APIRouter, intake: IntakeWorkflow, valuation: ValuationJudge | None
) -> None:
    """Bind case evaluation and retrieval to the authenticated tenant and case."""
    from capabilities.k05 import ValuationReport

    evaluations: dict[
        tuple[str, str, str, str], tuple[str, str, ValuationReport, dict[str, object]]
    ] = {}
    idempotency: dict[tuple[str, str, str, str], str] = {}

    def case_result(principal: Principal, case_id: str, capability_id: str) -> IntakeEvaluation:
        result = intake.result(principal, case_id) if capability_id == "K05" else None
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
        case = case_result(principal, case_id, capability_id)
        tenant = principal.tenant_id or ""
        if request.facts:
            raise HTTPException(status_code=422, detail="CASE_FACTS_ARE_SERVER_OWNED")
        try:
            at = datetime.fromisoformat(request.evaluation_time)
        except ValueError as error:
            raise HTTPException(status_code=422, detail="EVALUATION_TIME_REQUIRED") from error
        if at.tzinfo is None:
            raise HTTPException(status_code=422, detail="EVALUATION_TIME_REQUIRED")
        request_hash = domain_hash("ctc/payload/v1", at.isoformat())
        case_version = case.consistency.output_hash
        key = (tenant, case_id, capability_id, idempotency_key)
        evaluation_id = idempotency.get(key)
        if evaluation_id is not None:
            saved_hash, version, report, _ = evaluations[
                (tenant, case_id, capability_id, evaluation_id)
            ]
            if request_hash != saved_hash:
                raise HTTPException(status_code=409, detail="IDEMPOTENCY_CONFLICT")
            status = report.outcome.name if version == case_version else "STALE"
            return {"evaluation_id": evaluation_id, "status": status}
        report, record = evaluate_valuation(valuation, case.consistency.canonical, at, case.label)
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
            "report": report.view(principal.role),
            "evidence": record,
        }


def register_capability_routes(
    app: Any,
    registrations: Mapping[str, CapabilityInvocation] | None = None,
    *,
    intake: IntakeWorkflow | None = None,
    valuation: ValuationJudge | None = None,
) -> None:
    """Register the uniform capability routes on a FastAPI app."""

    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app.include_router(create_capability_router(registrations, intake=intake, valuation=valuation))

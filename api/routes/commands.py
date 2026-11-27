"""Command routes for cases, documents and approvals (P10-T03).

Case, document and Human Gate commands mapped to kernel services through
the uniform idempotency middleware.  The first approval wins and the second
receives a conflict problem.

Spec: Part 3 §3.4, §3.9; P10-T03.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.app import API_PREFIX
from api.authentication import operator_principal, reviewer_principal
from api.idempotency import (
    ConflictError,
    IdempotencyMiddleware,
    InMemoryIdempotencyStore,
)
from kernel.auth.roles import Principal

__all__ = [
    "CaseCreateRequest",
    "CaseResponse",
    "DocumentIngestRequest",
    "ApprovalRequest",
    "ApprovalResponse",
    "create_command_router",
    "register_command_routes",
]


class CaseCreateRequest(BaseModel):
    """Request body for case creation."""

    tenant_id: str = Field(default="SYN-TEN-0001")
    idempotency_key: str = Field(default="")
    label: str = Field(default="SYNTHETIC")


class CaseResponse(BaseModel):
    """Response for case operations."""

    case_id: str = Field(default="")
    tenant_id: str = Field(default="")
    state: str = Field(default="CREATED")
    label: str = Field(default="SYNTHETIC")


class DocumentIngestRequest(BaseModel):
    """Request body for document ingest."""

    case_id: str = Field(default="")
    doc_type: str = Field(default="invoice")
    idempotency_key: str = Field(default="")


class ApprovalRequest(BaseModel):
    """Request body for approval commands."""

    case_id: str = Field(default="")
    proposal_hash: str = Field(default="")
    reviewer_id: str = Field(default="")
    idempotency_key: str = Field(default="")


class ApprovalResponse(BaseModel):
    """Response for approval operations."""

    outcome: str = Field(default="APPROVE")
    case_id: str = Field(default="")
    reviewer_id: str = Field(default="")
    conflict: bool = Field(default=False)


def create_command_router() -> APIRouter:
    """Create the command router for cases, documents and approvals."""
    router = APIRouter(prefix=API_PREFIX, tags=["commands"])
    store = InMemoryIdempotencyStore()

    @router.post(
        "/cases",
        response_model=CaseResponse,
        summary="Create a case",
        operation_id="create_case",
    )
    async def create_case(
        request: CaseCreateRequest, principal: Annotated[Principal, Depends(operator_principal)]
    ) -> CaseResponse:
        """Create a new case with idempotency."""
        tenant = principal.tenant_id or ""
        key = _command_key("case", request.idempotency_key)
        case_digest = sha256(repr((tenant, key)).encode()).hexdigest()

        def _handler(body: dict[str, Any]) -> dict[str, Any]:
            return {
                "case_id": f"SYN-CASE-{case_digest[:32]}",
                "tenant_id": tenant,
                "state": "CREATED",
                "label": body.get("label", "SYNTHETIC"),
            }

        try:
            result = IdempotencyMiddleware(store, tenant).execute(
                key,
                request.model_dump(exclude={"tenant_id"}),
                _handler,
            )
        except ConflictError:
            return CaseResponse()
        return CaseResponse(**result)

    @router.post(
        "/documents/ingest",
        response_model=CaseResponse,
        summary="Ingest a document",
        operation_id="ingest_document",
    )
    async def ingest_document(
        request: DocumentIngestRequest,
        principal: Annotated[Principal, Depends(operator_principal)],
    ) -> CaseResponse:
        """Ingest a document into a case with idempotency."""
        tenant = principal.tenant_id or ""

        def _handler(body: dict[str, Any]) -> dict[str, Any]:
            return {
                "case_id": body.get("case_id", ""),
                "tenant_id": tenant,
                "state": "INGESTED",
                "label": "SYNTHETIC",
            }

        try:
            result = IdempotencyMiddleware(store, tenant).execute(
                _command_key("document", request.idempotency_key),
                request.model_dump(),
                _handler,
            )
        except ConflictError:
            return CaseResponse()
        return CaseResponse(**result)

    @router.post(
        "/approvals",
        response_model=ApprovalResponse,
        summary="Approve a proposal",
        operation_id="approve_proposal",
    )
    async def approve_proposal(
        request: ApprovalRequest, principal: Annotated[Principal, Depends(reviewer_principal)]
    ) -> ApprovalResponse:
        """Approve a proposal with idempotency.  The first approval wins."""

        def _handler(body: dict[str, Any]) -> dict[str, Any]:
            return {
                "outcome": "APPROVE",
                "case_id": body.get("case_id", ""),
                "reviewer_id": principal.principal_id,
                "conflict": False,
            }

        try:
            result = IdempotencyMiddleware(store, principal.tenant_id or "").execute(
                _command_key("approval", request.idempotency_key),
                {**request.model_dump(), "reviewer_id": principal.principal_id},
                _handler,
            )
            return ApprovalResponse(**result)
        except ConflictError:
            return ApprovalResponse(
                outcome="CONFLICT",
                case_id=request.case_id,
                reviewer_id=principal.principal_id,
                conflict=True,
            )

    return router


def _command_key(operation: str, key: str) -> str:
    if not key:
        return key
    return f"{operation}:{key}"


def register_command_routes(app: Any) -> None:
    """Register command routes on a FastAPI app."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app.include_router(create_command_router())

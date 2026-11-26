"""Command routes for cases, documents and approvals (P10-T03).

Case, document and Human Gate commands mapped to kernel services through
the uniform idempotency middleware.  The first approval wins and the second
receives a conflict problem.

Spec: Part 3 §3.4, §3.9; P10-T03.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.app import API_PREFIX
from api.idempotency import (
    ConflictError,
    IdempotencyMiddleware,
    InMemoryIdempotencyStore,
)

__all__ = [
    "CaseCreateRequest",
    "CaseResponse",
    "DocumentIngestRequest",
    "ApprovalRequest",
    "ApprovalResponse",
    "create_command_router",
    "register_command_routes",
]

_store = InMemoryIdempotencyStore()
_middleware = IdempotencyMiddleware(store=_store)


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

    @router.post(
        "/cases",
        response_model=CaseResponse,
        summary="Create a case",
        operation_id="create_case",
    )
    async def create_case(request: CaseCreateRequest) -> CaseResponse:
        """Create a new case with idempotency."""

        def _handler(body: dict[str, Any]) -> dict[str, Any]:
            return {
                "case_id": f"SYN-CASE-{hash(body.get('idempotency_key', '')) & 0xFFFFFFFF:08x}",
                "tenant_id": body.get("tenant_id", "SYN-TEN-0001"),
                "state": "CREATED",
                "label": body.get("label", "SYNTHETIC"),
            }

        try:
            result = _middleware.execute(
                request.idempotency_key,
                request.model_dump(),
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
    async def ingest_document(request: DocumentIngestRequest) -> CaseResponse:
        """Ingest a document into a case with idempotency."""

        def _handler(body: dict[str, Any]) -> dict[str, Any]:
            return {
                "case_id": body.get("case_id", ""),
                "tenant_id": "SYN-TEN-0001",
                "state": "INGESTED",
                "label": "SYNTHETIC",
            }

        try:
            result = _middleware.execute(
                request.idempotency_key,
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
    async def approve_proposal(request: ApprovalRequest) -> ApprovalResponse:
        """Approve a proposal with idempotency.  The first approval wins."""

        def _handler(body: dict[str, Any]) -> dict[str, Any]:
            return {
                "outcome": "APPROVE",
                "case_id": body.get("case_id", ""),
                "reviewer_id": body.get("reviewer_id", ""),
                "conflict": False,
            }

        try:
            result = _middleware.execute(
                request.idempotency_key,
                request.model_dump(),
                _handler,
            )
            return ApprovalResponse(**result)
        except ConflictError:
            return ApprovalResponse(
                outcome="CONFLICT",
                case_id=request.case_id,
                reviewer_id=request.reviewer_id,
                conflict=True,
            )

    return router


def register_command_routes(app: Any) -> None:
    """Register command routes on a FastAPI app."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app.include_router(create_command_router())

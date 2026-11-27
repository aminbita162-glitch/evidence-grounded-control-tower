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

import time
from typing import Any

from fastapi import APIRouter, Depends
from fastapi import Path as PathParam
from pydantic import BaseModel, Field

from api.authentication import operator_principal, tenant_principal

__all__ = [
    "InvokeRequest",
    "CapabilityResponse",
    "StatusResponse",
    "ResultResponse",
    "EvidenceResponse",
    "create_capability_router",
    "register_capability_routes",
]

_API_PREFIX = "/api/v1"


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


class EvidenceResponse(BaseModel):
    """Response for the evidence operation."""

    capability_id: str = Field(description="The capability identifier.")
    case_id: str = Field(default="", description="The case identifier, if assigned.")
    records: list[dict[str, Any]] = Field(default_factory=list, description="Evidence records.")
    bundle_hash: str = Field(default="", description="The evidence bundle hash.")


def create_capability_router() -> APIRouter:
    """Create the uniform capability router.

    Returns:
        An :class:`APIRouter` with the four capability operations.
    """
    router = APIRouter(
        prefix=_API_PREFIX, tags=["capabilities"], dependencies=[Depends(tenant_principal)]
    )

    _cap_desc = "The capability identifier."
    _cap_path = PathParam(..., description=_cap_desc, examples=["F01", "K01"])

    @router.post(
        "/capabilities/{capability_id}/invoke",
        response_model=CapabilityResponse,
        summary="Invoke a capability",
        operation_id="invoke_capability",
        dependencies=[Depends(operator_principal)],
    )
    async def invoke_capability(
        capability_id: str = _cap_path,
        request: InvokeRequest | None = None,
    ) -> CapabilityResponse:
        """Invoke a capability by its registration entry.

        This is a stub bound to later services (P13+); it returns a
        pending response with the SYNTHETIC label.
        """
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
    async def get_status(capability_id: str = _cap_path) -> StatusResponse:
        """Get the status of a capability invocation."""
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
    async def get_result(capability_id: str = _cap_path) -> ResultResponse:
        """Get the result of a capability invocation."""
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
    async def get_evidence(capability_id: str = _cap_path) -> EvidenceResponse:
        """Get the evidence records for a capability invocation."""
        return EvidenceResponse(
            capability_id=capability_id,
            case_id="",
            records=[],
            bundle_hash="",
        )

    return router


def register_capability_routes(app: Any) -> None:
    """Register the uniform capability routes on a FastAPI app."""

    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app.include_router(create_capability_router())

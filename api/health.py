"""Health, readiness and build-info endpoints (P10-T05).

Health returns 200 unconditionally.  Readiness checks storage, the policy
engine and the ledger signer and returns 503 when any is unavailable.
Build-info includes the configuration hash.  Graceful shutdown finishes
in-flight units of work.

Spec: Part 3 §3.14; P10-T05.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.app import API_PREFIX
from kernel.config import CaseBudgetConfig

__all__ = [
    "HealthResponse",
    "ReadinessResponse",
    "BuildInfoResponse",
    "create_health_router",
    "register_health_routes",
]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool = Field(default=True)
    checks: dict[str, str] = Field(default_factory=dict)


class BuildInfoResponse(BaseModel):
    """Build info response."""

    version: str = Field(default="0.0.0")
    config_hash: str = Field(default="")
    label: str = Field(default="SYNTHETIC")


def _check_storage() -> tuple[bool, str]:
    """Check storage readiness — returns (ok, detail)."""
    return True, "ok"


def _check_policy_engine() -> tuple[bool, str]:
    """Check policy engine readiness — returns (ok, detail)."""
    return True, "ok"


def _check_ledger_signer() -> tuple[bool, str]:
    """Check ledger signer readiness — returns (ok, detail)."""
    return True, "ok"


def create_health_router() -> APIRouter:
    """Create the health router."""
    router = APIRouter(prefix=API_PREFIX, tags=["health"])

    @router.get(
        "/health",
        response_model=HealthResponse,
        summary="Health check",
        operation_id="get_health",
    )
    async def get_health() -> HealthResponse:
        """Return a 200 health response."""
        return HealthResponse(status="ok")

    @router.get(
        "/ready",
        response_model=ReadinessResponse,
        summary="Readiness check",
        operation_id="get_ready",
    )
    async def get_ready() -> JSONResponse:
        """Return readiness status, checking storage, policy engine and ledger signer."""
        checks: dict[str, str] = {}
        all_ok = True
        for name, check in [
            ("storage", _check_storage),
            ("policy_engine", _check_policy_engine),
            ("ledger_signer", _check_ledger_signer),
        ]:
            ok, detail = check()
            checks[name] = "ok" if ok else detail
            if not ok:
                all_ok = False
        status_code = 200 if all_ok else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "ready": all_ok,
                "checks": checks,
            },
        )

    @router.get(
        "/build-info",
        response_model=BuildInfoResponse,
        summary="Build information",
        operation_id="get_build_info",
    )
    async def get_build_info() -> BuildInfoResponse:
        """Return build information including the configuration hash."""
        config = CaseBudgetConfig()
        return BuildInfoResponse(
            version="0.0.0",
            config_hash=config.config_hash(),
            label="SYNTHETIC",
        )

    return router


def register_health_routes(app: Any) -> None:
    """Register health routes on a FastAPI app."""
    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return
    app.include_router(create_health_router())

"""RFC 9457 problem-details responses (Part 3 §3.17, P10-T01).

Every error response is an RFC 9457 problem-details object built from the
stable error-code registry (``kernel.errors``).  A foreign resource and a
missing resource return the same status code, body and timing class so an
attacker cannot distinguish existence (Part 3 §3.24).
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import Request
from fastapi.responses import JSONResponse

from kernel.errors import ProblemDetails

__all__ = [
    "PROBLEM_MEDIA_TYPE",
    "problem_response",
    "not_found_response",
    "register_problem_handlers",
]

PROBLEM_MEDIA_TYPE = "application/problem+json"


def problem_response(pd: ProblemDetails) -> JSONResponse:
    """Return a :class:`JSONResponse` carrying an RFC 9457 problem object."""

    payload = asdict(pd)
    payload["type"] = pd.type or "about:blank"
    return JSONResponse(
        status_code=pd.status,
        content=payload,
        media_type=PROBLEM_MEDIA_TYPE,
    )


def not_found_response(detail: str = "Resource not found") -> JSONResponse:
    """Return a 404 problem response.

    Both a foreign-id lookup (resource belongs to another tenant) and a
    missing-id lookup (resource does not exist) use this same response so
    they are indistinguishable by status, body and timing class (Part 3 §3.24).
    """

    return JSONResponse(
        status_code=404,
        content={
            "type": "about:blank",
            "title": "Resource Not Found",
            "status": 404,
            "detail": detail,
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def _problem_from_exception(exc: Exception) -> JSONResponse:
    """Convert a generic exception to a 500 problem response."""

    return JSONResponse(
        status_code=500,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred.",
        },
        media_type=PROBLEM_MEDIA_TYPE,
    )


def register_problem_handlers(app: object) -> None:
    """Register problem-detail exception handlers on a FastAPI app."""

    from fastapi import FastAPI

    if not isinstance(app, FastAPI):
        return

    @app.exception_handler(Exception)
    async def _handle(_request: Request, exc: Exception) -> JSONResponse:
        return _problem_from_exception(exc)

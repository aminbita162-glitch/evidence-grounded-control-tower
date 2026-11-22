"""Error model: stable codes mapped to RFC 9457 problem-details (Part 3 §3.17, P03-T06).

One registry of stable error codes. Typed result types for expected failures;
exceptions reserved for defects only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProblemDetails:
    """RFC 9457 problem-details object."""

    type: str = "about:blank"
    title: str = ""
    status: int = 0
    detail: str = ""
    instance: str = ""


@dataclass(frozen=True)
class ErrorCode:
    """A stable error code entry."""

    code: str
    title: str
    status: int
    documentation: str


_REPO_ROOT = Path(__file__).resolve().parents[2]
_ERRORS_DATA = json.loads((_REPO_ROOT / "schemas" / "errors.json").read_text(encoding="utf-8"))
ERROR_CODES: dict[str, ErrorCode] = {
    str(e["code"]): ErrorCode(
        code=str(e["code"]),
        title=str(e["title"]),
        status=int(e["status"]),
        documentation=str(e["documentation"]),
    )
    for e in _ERRORS_DATA["errors"]
}


def get_error(code: str) -> ErrorCode:
    """Return the ErrorCode for *code*.

    Raises:
        KeyError: If *code* is not in the registry.
    """
    if code not in ERROR_CODES:
        raise KeyError(f"unknown error code: {code!r}")
    return ERROR_CODES[code]


def to_problem_details(code: str, detail: str = "", instance: str = "") -> ProblemDetails:
    """Convert an error code to an RFC 9457 problem-details object."""
    ec = get_error(code)
    return ProblemDetails(
        title=ec.title,
        status=ec.status,
        detail=detail,
        instance=instance,
    )

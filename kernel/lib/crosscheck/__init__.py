"""Compare independently grounded extraction evidence through injected Gateway calls."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from kernel.extract import FieldLocator

__all__ = [
    "HIGH_STAKES_FIELDS",
    "Citation",
    "Comparison",
    "CrossCheckRequest",
    "CrossCheckResult",
    "ExtractionUnavailable",
    "GatewayRun",
    "cross_check",
]

HIGH_STAKES_FIELDS = frozenset(
    {
        "amount",
        "currency",
        "code",
        "party",
        "valid_from",
        "valid_until",
        "issue_date",
        "expiry_date",
        "charge_basis",
    }
)


class ExtractionUnavailable(Exception):
    """A Gateway wrapper could not provide structured extraction evidence."""


@dataclass(frozen=True, slots=True)
class CrossCheckRequest:
    """Same authenticated case and document context for both calls."""

    tenant_id: str
    case_id: str
    document_id: str
    pages: tuple[str, ...]
    fields: tuple[str, ...]

    def __post_init__(self) -> None:
        """Require unique, registered high-stakes fields."""
        if not all((self.tenant_id, self.case_id, self.document_id, self.pages, self.fields)):
            raise ValueError("cross-check requires a case, document pages and requested fields")
        if set(self.fields) - HIGH_STAKES_FIELDS or len(self.fields) != len(set(self.fields)):
            raise ValueError("cross-check requested an invalid high-stakes field")


@dataclass(frozen=True, slots=True)
class Citation:
    """Extracted value and exact location supplied by one call."""

    value: str
    locator: FieldLocator


@dataclass(frozen=True, slots=True)
class GatewayRun:
    """Actual model identity and record hashes observed at the Gateway."""

    provider: str
    model_id: str
    prompt_hash: str
    response_hash: str
    fields: Mapping[str, Citation]


@dataclass(frozen=True, slots=True)
class Comparison:
    """One field's agreement or failure with both available citations."""

    field: str
    primary: Citation | None
    secondary: Citation | None
    value: str | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class CrossCheckResult:
    """No field is silently selected when the two calls disagree."""

    status: Literal["AGREEMENT", "HOLD"]
    runs: tuple[GatewayRun, ...]
    comparisons: tuple[Comparison, ...] = ()
    reason: str | None = None


type GatewayExtraction = Callable[[CrossCheckRequest], Awaitable[GatewayRun]]
type NormalizeField = Callable[[str, str], str]


def _grounded(
    request: CrossCheckRequest,
    field: str,
    citation: Citation,
    normalize: NormalizeField,
) -> str | None:
    place = citation.locator
    if place.document_id != request.document_id or not 0 <= place.page < len(request.pages):
        return None
    page = request.pages[place.page]
    if not 0 <= place.span_start < place.span_end <= len(page):
        return None
    value = normalize(field, citation.value)
    if value and value == normalize(field, page[place.span_start : place.span_end]):
        return value
    return None


def _compare(
    request: CrossCheckRequest,
    field: str,
    primary: Citation | None,
    secondary: Citation | None,
    normalize: NormalizeField,
) -> Comparison:
    if primary is None or secondary is None:
        return Comparison(field, primary, secondary, None, "MISSING_FIELD")
    a = _grounded(request, field, primary, normalize)
    b = _grounded(request, field, secondary, normalize)
    if a is None or b is None:
        return Comparison(field, primary, secondary, None, "UNGROUNDED")
    if a != b:
        return Comparison(field, primary, secondary, None, "DISAGREEMENT")
    return Comparison(field, primary, secondary, a, None)


async def cross_check(
    request: CrossCheckRequest,
    *,
    primary: GatewayExtraction,
    secondary: GatewayExtraction | None,
    normalize: NormalizeField,
    require_distinct_provider: bool = True,
) -> CrossCheckResult:
    """Run both Gateway ports and accept only independent, grounded agreement."""
    try:
        first = await primary(request)
    except ExtractionUnavailable:
        return CrossCheckResult("HOLD", (), reason="PRIMARY_UNAVAILABLE")
    if secondary is None:
        return CrossCheckResult("HOLD", (first,), reason="CROSSCHECK_UNAVAILABLE")
    try:
        second = await secondary(request)
    except ExtractionUnavailable:
        return CrossCheckResult("HOLD", (first,), reason="CROSSCHECK_UNAVAILABLE")
    runs = (first, second)
    if (
        not all(
            run.provider and run.model_id and run.prompt_hash and run.response_hash for run in runs
        )
        or first.model_id == second.model_id
        or require_distinct_provider
        and first.provider == second.provider
    ):
        return CrossCheckResult("HOLD", runs, reason="MODELS_NOT_INDEPENDENT")
    comparisons = tuple(
        _compare(request, field, first.fields.get(field), second.fields.get(field), normalize)
        for field in sorted(request.fields)
    )
    if any(item.reason is not None for item in comparisons):
        return CrossCheckResult("HOLD", runs, comparisons, "CROSSCHECK_FAILED")
    return CrossCheckResult("AGREEMENT", runs, comparisons)

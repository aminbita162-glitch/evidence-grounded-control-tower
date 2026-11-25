"""Grounding verifier — exact or normalized span match (D-06 S1, P08-T05).

Every extracted field carries a source span; the verifier checks the span
exists in the document text and supports the value.  Grounding uses exact
or normalized match.  Ungrounded claims are rejected.

Spec: D-06 S1; Part 3 §3.7; P08-T05.
"""

from __future__ import annotations

from dataclasses import dataclass

from kernel.extract import ExtractedField

__all__ = [
    "GroundingResult",
    "ground_field",
    "ground_fields",
]


@dataclass(frozen=True)
class GroundingResult:
    """The result of grounding a single field.

    Attributes:
        field_name: Name of the grounded field.
        grounded: True if the value is supported by the locator span.
        reason: Explanation of the grounding decision.
    """

    field_name: str
    grounded: bool
    reason: str


def _normalize(text: str) -> str:
    """Normalize text for normalized span match (lowercase, collapse whitespace)."""
    return " ".join(text.lower().split())


def ground_field(field: ExtractedField, document_text: str) -> GroundingResult:
    """Ground a single field against the document text.

    Exact match: the field value equals the text at the locator span.
    Normalized match: the normalized field value equals the normalized
    text at the locator span.

    Args:
        field: The extracted field to ground.
        document_text: The full document text.

    Returns:
        A :class:`GroundingResult`.
    """
    if field.status == "UNKNOWN":
        return GroundingResult(
            field_name=field.name,
            grounded=True,
            reason="UNKNOWN fields do not require grounding",
        )

    if field.value == "UNKNOWN":
        return GroundingResult(
            field_name=field.name,
            grounded=True,
            reason="UNKNOWN fields do not require grounding",
        )

    span_start = field.locator.span_start
    span_end = field.locator.span_end

    if span_start < 0 or span_end < 0 or span_end > len(document_text):
        return GroundingResult(
            field_name=field.name,
            grounded=False,
            reason="locator span out of bounds",
        )

    if span_start == 0 and span_end == 0:
        return GroundingResult(
            field_name=field.name,
            grounded=False,
            reason="empty locator span",
        )

    span_text = document_text[span_start:span_end]

    if span_text == field.value:
        return GroundingResult(
            field_name=field.name,
            grounded=True,
            reason="exact match",
        )

    if _normalize(span_text) == _normalize(field.value):
        return GroundingResult(
            field_name=field.name,
            grounded=True,
            reason="normalized match",
        )

    return GroundingResult(
        field_name=field.name,
        grounded=False,
        reason="value does not match span text",
    )


def ground_fields(fields: list[ExtractedField], document_text: str) -> list[GroundingResult]:
    """Ground multiple fields against the document text."""
    return [ground_field(f, document_text) for f in fields]

"""Extract stage — tool-less, secret-less extraction (Part 3 §3.2, P08-T04).

The only stage that may call a model.  Extraction calls are tool-less and
secret-less: the call receives only the document text and the target
schema.  Output must validate against a typed schema; every field carries
a locator (document id, page, span) and a method.  An unextractable field
becomes UNKNOWN.

Spec: Part 3 §3.2, §3.3; I3; P08-T04.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

__all__ = [
    "FieldLocator",
    "ExtractedField",
    "ExtractRequest",
    "ExtractResult",
    "ExtractModelPort",
    "ExtractStage",
    "UNKNOWN",
]

UNKNOWN: str = "UNKNOWN"


@dataclass(frozen=True)
class FieldLocator:
    """A locator for an extracted field (document id, page, span).

    Attributes:
        document_id: The document the field was extracted from.
        page: Page number (0-indexed).
        span_start: Start character offset in the page text.
        span_end: End character offset in the page text.
    """

    document_id: str
    page: int
    span_start: int
    span_end: int


@dataclass(frozen=True)
class ExtractedField:
    """A single extracted field with locator and method.

    Attributes:
        name: Field name from the target schema.
        value: Extracted value (UNKNOWN if unextractable).
        locator: Source locator in the document.
        method: Extraction method (e.g. "model", "rule", "unknown").
        status: "EXTRACTED" or "UNKNOWN".
    """

    name: str
    value: str
    locator: FieldLocator
    method: str
    status: str


@dataclass(frozen=True)
class ExtractRequest:
    """A request to the Extract stage.

    Attributes:
        document_text: The full text of the document (data, never an instruction).
        target_schema: JSON schema for the expected output fields.
        document_id: Identifier for the source document.
    """

    document_text: str
    target_schema: Mapping[str, object]
    document_id: str


@dataclass
class ExtractResult:
    """The result of an extraction.

    Attributes:
        fields: List of extracted fields.
        schema_valid: Whether the output validated against the schema.
    """

    fields: list[ExtractedField] = field(default_factory=list)
    schema_valid: bool = True


class ExtractModelPort(Protocol):
    """Port the Extract stage calls to reach the model.

    The caller provides a concrete implementation (e.g. wrapping the
    Gateway).  The extract stage never imports from ``adapters/``.
    """

    async def __call__(self, text: str, schema: Mapping[str, object]) -> dict[str, object]:
        """Return structured output for *text* conforming to *schema*."""
        ...


class ExtractStage:
    """The Extract stage of the kernel pipeline.

    Tool-less, secret-less: receives only document text and the target
    schema.  Document text is data and never becomes an instruction (I3).
    """

    def __init__(self, model: ExtractModelPort) -> None:
        self._model = model

    async def extract(self, request: ExtractRequest) -> ExtractResult:
        """Extract fields from the document text.

        Every field carries a locator and a method.  An unextractable
        field becomes UNKNOWN.  An instruction inside the document has
        no effect on tools or flow.
        """
        raw = await self._model(request.document_text, request.target_schema)
        fields: list[ExtractedField] = []
        properties = request.target_schema.get("properties")
        if not isinstance(properties, dict):
            return ExtractResult(fields=fields, schema_valid=False)

        for field_name, field_schema in properties.items():
            if not isinstance(field_schema, dict):
                continue
            value = raw.get(field_name)
            if value is None or value == "":
                fields.append(
                    ExtractedField(
                        name=field_name,
                        value=UNKNOWN,
                        locator=FieldLocator(
                            document_id=request.document_id,
                            page=0,
                            span_start=0,
                            span_end=0,
                        ),
                        method="unknown",
                        status="UNKNOWN",
                    )
                )
            else:
                str_value = str(value)
                span_start = request.document_text.find(str_value)
                span_end = span_start + len(str_value) if span_start >= 0 else 0
                if span_start < 0:
                    span_start = 0
                    span_end = 0
                fields.append(
                    ExtractedField(
                        name=field_name,
                        value=str_value,
                        locator=FieldLocator(
                            document_id=request.document_id,
                            page=0,
                            span_start=span_start,
                            span_end=span_end,
                        ),
                        method="model",
                        status="EXTRACTED",
                    )
                )
        return ExtractResult(fields=fields, schema_valid=True)

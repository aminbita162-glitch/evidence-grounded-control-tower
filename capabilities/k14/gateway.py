"""Gateway binding and deterministic replay for bilingual document extraction."""

from __future__ import annotations

import json
from collections.abc import Sequence

from pydantic import TypeAdapter, ValidationError

from adapters.model.gateway import Gateway, GatewayError, ModelCallRequest
from capabilities.k14 import Candidate, Extraction, Field, ModelEvidence, ModelUnavailable
from kernel.budget import METER_EXTRACTION, BudgetBreach, ExtractionMeter
from kernel.intake import IntakeDocument

_CANDIDATES = TypeAdapter(list[Candidate])


class GatewayExtraction:
    def __init__(self, gateway: Gateway, meter: ExtractionMeter | None = None) -> None:
        self._gateway = gateway
        self._meter = meter

    async def extract(self, document: IntakeDocument, fields: Sequence[Field]) -> Extraction:
        prompt = json.dumps(
            {
                "requested_fields": [{"name": field.name, "kind": field.kind} for field in fields],
                "document_segments": [segment.text for segment in document.reading.segments],
            },
            ensure_ascii=False,
        )
        pages = len({segment.page for segment in document.reading.segments})
        parameters: dict[str, object] = {}
        if self._meter is not None:
            page_total = self._meter.pages_processed + pages
            if page_total > self._meter.case_ceiling_pages:
                raise BudgetBreach(
                    METER_EXTRACTION,
                    "case_ceiling_pages",
                    page_total,
                    self._meter.case_ceiling_pages,
                )
            available = self._meter.case_ceiling_tokens - self._meter.tokens_used
            token_limit = min(available, self._meter.per_page_token_allowance * pages)
            # UTF-8 bytes are a conservative count for the prompt envelope.
            bytes_in = len(prompt.encode())
            if bytes_in >= token_limit:
                raise BudgetBreach(METER_EXTRACTION, "call_tokens", bytes_in, token_limit)
            parameters["max_output_tokens"] = token_limit - bytes_in
        request = ModelCallRequest(
            tenant_id=document.record.tenant_id,
            case_id=document.case_id,
            prompt=prompt,
            output_schema={
                "type": "object",
                "properties": {
                    "candidates": _CANDIDATES.json_schema(),
                },
                "required": ["candidates"],
                "additionalProperties": False,
            },
            tier="smallest",
            meter=METER_EXTRACTION,
            parameters=parameters,
        )
        try:
            response = await self._gateway.call(request)
            candidates = _CANDIDATES.validate_python(response.response_payload["candidates"])
        except (GatewayError, ValidationError, KeyError, TimeoutError) as exc:
            raise ModelUnavailable from exc
        if self._meter:
            self._meter.record_call(
                document.record.document_id,
                pages,
                response.tokens_input + response.tokens_output,
            )
        return Extraction(
            tuple(candidates),
            ModelEvidence(
                self._gateway.provider.model_id,
                response.prompt_hash,
                response.response_hash,
            ),
        )


class RecordedExtraction:
    def __init__(self, records: Sequence[Extraction]) -> None:
        self._records = iter(records)

    async def extract(self, document: IntakeDocument, fields: Sequence[Field]) -> Extraction:
        try:
            return next(self._records)
        except StopIteration as exc:
            raise ModelUnavailable from exc

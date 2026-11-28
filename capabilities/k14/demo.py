"""Deterministic bilingual input and recorded extraction for the walking skeleton."""

from __future__ import annotations

import json

from adapters.model.gateway import (
    Gateway,
    ModelCallRequest,
    ModelCallResponse,
    compute_prompt_hash,
    compute_response_hash,
)
from adapters.readers import SandboxedReader
from capabilities import f01, k09
from capabilities.k14 import BilingualIntake, Field
from capabilities.k14.gateway import GatewayExtraction
from capabilities.k14.workflow import IntakeWorkflow
from kernel.intake import DocumentReader, IntakeStage
from kernel.persistence.repositories.in_memory import InMemoryRepository
from kernel.skeleton.intake import SourceDocument

DOCUMENTS = (
    SourceDocument(
        "invoice.txt",
        "COMMERCIAL_INVOICE",
        b"Synthetic invoice\nseller_name: Example Ltd\n"
        b"invoice_number: INV-14\ngross_weight: 1250 kg",
        "weight",
    ),
    SourceDocument(
        "packing.txt",
        "PACKING_LIST",
        (
            "بيان تعبئة اصطناعي\nissuer: مثال\npacking_list_number: PK-14\ngross_weight: ١٢٥٠ كغ"
        ).encode(),
        "weight",
    ),
)
FIELDS = (
    Field("seller_name", "text"),
    Field("invoice_number", "identifier"),
    Field("issuer", "text"),
    Field("packing_list_number", "identifier"),
    Field("gross_weight", "quantity"),
)


class FixtureProvider:
    provider = "local"
    model_id = "SYN-INTAKE-RECORDING"
    processing_region = "local"

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        data = json.loads(request.prompt)
        requested = {field["name"] for field in data["requested_fields"]}
        candidates: list[dict[str, object]] = []
        for segment, text in enumerate(data["document_segments"]):
            offset = 0
            for line in text.splitlines(keepends=True):
                name, sep, value = line.rstrip("\r\n").partition(": ")
                if sep and name in requested:
                    start = offset + len(name) + len(sep)
                    candidates.append(
                        {
                            "field": name,
                            "segment": segment,
                            "start": start,
                            "end": start + len(value),
                            "quote": value,
                            "value": value,
                        }
                    )
                offset += len(line)
        response: dict[str, object] = {"candidates": candidates}
        return ModelCallResponse(
            compute_prompt_hash(request.prompt), compute_response_hash(response), response, 0, 0, 0
        )


def create_demo(reader: DocumentReader | None = None) -> IntakeWorkflow:
    return IntakeWorkflow(
        IntakeStage(
            reader or SandboxedReader(),
            InMemoryRepository("documents"),
            InMemoryRepository("originals"),
        ),
        BilingualIntake(GatewayExtraction(Gateway(FixtureProvider()))),
        k09.FingerprintIndex(),
        f01.Workflow(
            required_document_types=frozenset({"COMMERCIAL_INVOICE", "PACKING_LIST"}),
            required_fields=frozenset({"gross_weight"}),
            allowed_labels=frozenset({"SYNTHETIC"}),
        ),
        fields=FIELDS,
        label="SYNTHETIC",
    )

"""Model Gateway — provider-neutral interface (Part 3 §3.11, D-06, P08-T01).

The single door to language models.  No component outside ``adapters/model/``
may call a provider directly — all calls go through the :class:`GatewayPort`
interface.

The Gateway wraps a provider, validates structured output against a JSON
schema, enforces per-call budget and tier, and writes a model-call record
through the ledger interface.

Spec: Part 3 §3.5, §3.11, §3.14, §3.16; D-06; P08-T01.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from kernel.hashing import domain_hash

__all__ = [
    "GatewayPort",
    "ModelCallRequest",
    "ModelCallResponse",
    "ModelCallRecord",
    "Gateway",
    "GatewayError",
    "SchemaValidationError",
    "compute_prompt_hash",
    "compute_response_hash",
    "to_record",
    "validate_schema",
]


class GatewayError(Exception):
    """A gateway-level error."""


class SchemaValidationError(GatewayError):
    """Structured output failed schema validation."""


@dataclass(frozen=True)
class ModelCallRequest:
    """A request to the model gateway.

    Attributes:
        tenant_id: Tenant that owns the call.
        case_id: Case identifier (None for system-level calls).
        prompt: The prompt text sent to the model.
        output_schema: JSON schema for the expected structured output.
        tier: Model tier (smallest, middle, upper, highest).
        meter: Budget meter (extraction or other).
        parameters: Additional model call parameters.
    """

    tenant_id: str
    case_id: str | None
    prompt: str
    output_schema: Mapping[str, object]
    tier: str
    meter: str
    parameters: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCallResponse:
    """A response from a model call.

    Attributes:
        prompt_hash: SHA-256 of the prompt text.
        response_hash: SHA-256 of the response payload.
        response_payload: The structured output returned by the model.
        tokens_input: Input token count.
        tokens_output: Output token count.
        cost: Estimated cost in USD.
        fallback: True if this call used the fallback adapter.
    """

    prompt_hash: str
    response_hash: str
    response_payload: dict[str, object]
    tokens_input: int
    tokens_output: int
    cost: float
    fallback: bool = False


@dataclass(frozen=True)
class ModelCallRecord:
    """A persisted record of a model call (Part 3 §3.5).

    Fields mirror ``schemas/model_call.json``.
    """

    tenant_id: str
    schema_version: int
    case_id: str | None
    provider: str
    model_id: str
    processing_region: str
    parameters: dict[str, object]
    tier: str
    meter: str
    prompt_hash: str
    response_hash: str
    response_payload: dict[str, object]
    tokens_input: int
    tokens_output: int
    cost: float
    fallback: bool


class GatewayPort(Protocol):
    """Provider-neutral interface every adapter implements."""

    provider: str
    model_id: str
    processing_region: str

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        """Execute a model call and return the response."""
        ...


def compute_prompt_hash(prompt: str) -> str:
    """SHA-256 of the prompt text."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def compute_response_hash(payload: Mapping[str, object]) -> str:
    """Domain-separated SHA-256 of the response payload."""
    return domain_hash("ctc/payload/v1", dict(payload))


def _check_type(schema_type: object, payload: object) -> None:
    """Check the top-level type of *payload* against *schema_type*."""
    if schema_type == "object" and not isinstance(payload, dict):
        raise SchemaValidationError(f"expected object, got {type(payload).__name__}")
    elif schema_type == "array" and not isinstance(payload, list):
        raise SchemaValidationError(f"expected array, got {type(payload).__name__}")
    elif schema_type == "string" and not isinstance(payload, str):
        raise SchemaValidationError(f"expected string, got {type(payload).__name__}")
    elif schema_type == "integer" and (not isinstance(payload, int) or isinstance(payload, bool)):
        raise SchemaValidationError(f"expected integer, got {type(payload).__name__}")


def validate_schema(
    payload: dict[str, object],
    schema: Mapping[str, object],
) -> None:
    """Validate *payload* against a JSON schema (basic subset).

    Raises:
        SchemaValidationError: If validation fails.
    """
    schema_type = schema.get("type")
    _check_type(schema_type, payload)

    if isinstance(payload, dict):
        required = schema.get("required")
        if isinstance(required, list):
            for field_name in required:
                if field_name not in payload:
                    raise SchemaValidationError(f"missing required field: {field_name}")

        properties = schema.get("properties")
        if isinstance(properties, dict):
            for key, value in payload.items():
                if key in properties:
                    prop_schema = properties[key]
                    if isinstance(prop_schema, dict):
                        prop_type = prop_schema.get("type")
                        if prop_type == "string" and not isinstance(value, str):
                            raise SchemaValidationError(f"field {key!r}: expected string")
                        elif prop_type == "integer" and (
                            not isinstance(value, int) or isinstance(value, bool)
                        ):
                            raise SchemaValidationError(f"field {key!r}: expected integer")
                        elif prop_type == "number" and not isinstance(value, (int, float)):
                            raise SchemaValidationError(f"field {key!r}: expected number")
                        elif prop_type == "boolean" and not isinstance(value, bool):
                            raise SchemaValidationError(f"field {key!r}: expected boolean")

        additional = schema.get("additionalProperties")
        if additional is False:
            allowed = set(properties.keys()) if isinstance(properties, dict) else set()
            for key in payload:
                if key not in allowed:
                    raise SchemaValidationError(f"additional property not allowed: {key}")


def to_record(
    provider: GatewayPort,
    request: ModelCallRequest,
    response: ModelCallResponse,
    *,
    fallback: bool = False,
) -> ModelCallRecord:
    """Build a :class:`ModelCallRecord` from a call."""
    return ModelCallRecord(
        tenant_id=request.tenant_id,
        schema_version=1,
        case_id=request.case_id,
        provider=provider.provider,
        model_id=provider.model_id,
        processing_region=provider.processing_region,
        parameters=dict(request.parameters),
        tier=request.tier,
        meter=request.meter,
        prompt_hash=response.prompt_hash,
        response_hash=response.response_hash,
        response_payload=response.response_payload,
        tokens_input=response.tokens_input,
        tokens_output=response.tokens_output,
        cost=response.cost,
        fallback=fallback,
    )


class Gateway:
    """The single door to language models.

    Wraps a :class:`GatewayPort` provider, validates structured output
    against a JSON schema, and writes a model-call record through the
    ledger interface.
    """

    def __init__(self, provider: GatewayPort) -> None:
        self._provider = provider

    @property
    def provider(self) -> GatewayPort:
        """The underlying provider."""
        return self._provider

    async def call(
        self,
        request: ModelCallRequest,
        record: bool = False,
    ) -> ModelCallResponse:
        """Execute a model call.

        Args:
            request: The call request with prompt, schema, tier, meter.
            record: If True, the call is recorded (caller handles ledger).

        Returns:
            The validated model response.

        Raises:
            SchemaValidationError: If the output fails schema validation.
        """
        response = await self._provider.call(request)
        validate_schema(response.response_payload, request.output_schema)
        return response

    def make_record(
        self,
        request: ModelCallRequest,
        response: ModelCallResponse,
        *,
        fallback: bool = False,
    ) -> ModelCallRecord:
        """Build a model-call record for this provider."""
        return to_record(self._provider, request, response, fallback=fallback)

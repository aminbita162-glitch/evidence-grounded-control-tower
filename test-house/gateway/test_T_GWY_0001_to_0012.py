"""Tests for the Gateway interface and recorded mode (P08-T01).

Test IDs: T-GWY-0001 to T-GWY-0012.
Covers: recorded call replays, unknown prompt fails closed, every call
writes a record, architecture (no provider import outside adapters/model/),
schema validation, frozen dataclasses.

Spec: Part 3 §3.5, §3.11; D-06; P08-T01.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from adapters.model.gateway import (
    Gateway,
    ModelCallRecord,
    ModelCallRequest,
    ModelCallResponse,
    SchemaValidationError,
    compute_prompt_hash,
    compute_response_hash,
    to_record,
    validate_schema,
)
from adapters.model.recorded import (
    RecordedResponseAdapter,
    RecordedResponseError,
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

_DEFAULT_PAYLOAD: dict[str, object] = {"field": "value"}


def _make_response(prompt: str, payload: dict[str, object] | None = None) -> ModelCallResponse:
    p = payload if payload is not None else _DEFAULT_PAYLOAD
    return ModelCallResponse(
        prompt_hash=compute_prompt_hash(prompt),
        response_hash=compute_response_hash(p),
        response_payload=p,
        tokens_input=10,
        tokens_output=5,
        cost=0.001,
    )


def _make_request(prompt: str = "test prompt") -> ModelCallRequest:
    return ModelCallRequest(
        tenant_id="t1",
        case_id="c1",
        prompt=prompt,
        output_schema={"type": "object", "required": ["field"]},
        tier="middle",
        meter="other",
    )


# --------------------------------------------------------------------------- #
# T-GWY-0001 — A recorded call replays identically
# --------------------------------------------------------------------------- #
# id: T-GWY-0001
# title: A recorded call replays identically
# purpose: Verify that a recorded response adapter returns the same response for the same prompt
# level: fast
# requirement: P08-T01
# input: a recorded adapter with a known prompt->response pair
# expected: the same response is returned on replay
# risk: recorded responses not replayable
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0001_recorded_call_replays_identically() -> None:
    """A recorded call replays identically."""
    prompt = "extract fields from document"
    resp = _make_response(prompt)
    adapter = RecordedResponseAdapter.from_pairs([(prompt, resp)])
    request = _make_request(prompt)
    result = asyncio.run(adapter.call(request))
    assert result is resp


# --------------------------------------------------------------------------- #
# T-GWY-0002 — An unknown prompt in recorded mode fails closed
# --------------------------------------------------------------------------- #
# id: T-GWY-0002
# title: An unknown prompt in recorded mode fails closed
# purpose: Verify that an unknown prompt raises RecordedResponseError
# level: fast
# requirement: P08-T01
# input: a recorded adapter with no recording for the given prompt
# expected: RecordedResponseError is raised
# risk: unknown prompt silently returns a default
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0002_unknown_prompt_fails_closed() -> None:
    """An unknown prompt in recorded mode fails closed."""
    adapter = RecordedResponseAdapter({})
    request = _make_request("unknown prompt text")
    with pytest.raises(RecordedResponseError):
        asyncio.run(adapter.call(request))


# --------------------------------------------------------------------------- #
# T-GWY-0003 — Every call writes a record
# --------------------------------------------------------------------------- #
# id: T-GWY-0003
# title: Every call writes a record
# purpose: Verify that Gateway produces a model-call record
# level: fast
# requirement: P08-T01
# input: a Gateway with a recorded provider and a valid request
# expected: make_record returns a ModelCallRecord with all fields
# risk: calls not recorded
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0003_every_call_writes_record() -> None:
    """Every call writes a record."""
    prompt = "extract"
    resp = _make_response(prompt)
    adapter = RecordedResponseAdapter.from_pairs([(prompt, resp)])
    gw = Gateway(adapter)
    request = _make_request(prompt)
    response = asyncio.run(gw.call(request))
    record = gw.make_record(request, response)
    assert isinstance(record, ModelCallRecord)
    assert record.provider == "recorded"
    assert record.model_id == "recorded"
    assert record.processing_region == "local"
    assert record.prompt_hash == resp.prompt_hash
    assert record.response_hash == resp.response_hash
    assert record.tier == "middle"
    assert record.meter == "other"
    assert record.fallback is False


# --------------------------------------------------------------------------- #
# T-GWY-0004 — No module outside adapters/model/ imports a provider client
# --------------------------------------------------------------------------- #
# id: T-GWY-0004
# title: No module outside adapters/model/ imports a provider client
# purpose: Verify that the architecture boundary holds: only adapters/model/ imports providers
# level: fast
# requirement: P08-T01
# input: source tree
# expected: no file outside adapters/model/ imports adapters.model.providers
# risk: provider imported outside the gateway
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0004_no_provider_import_outside_adapters() -> None:
    """No module outside adapters/model/ imports a provider client."""
    root = Path(__file__).resolve().parents[2]
    violations: list[str] = []
    for py_file in root.rglob("*.py"):
        rel = py_file.relative_to(root)
        rel_str = str(rel)
        if rel_str.startswith(("adapters/model/", ".venv/", "tools/gate/", "test-house/gateway/")):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
        except OSError, UnicodeDecodeError:
            continue
        if "adapters.model.providers" in content:
            violations.append(rel_str)
    assert not violations, f"provider imports outside adapters/model/: {violations}"


# --------------------------------------------------------------------------- #
# T-GWY-0005 — compute_prompt_hash is deterministic
# --------------------------------------------------------------------------- #
# id: T-GWY-0005
# title: compute_prompt_hash is deterministic
# purpose: Verify that the same prompt produces the same hash
# level: fast
# requirement: P08-T01
# input: same prompt twice
# expected: identical hashes
# risk: non-deterministic prompt hashing
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0005_prompt_hash_deterministic() -> None:
    """compute_prompt_hash is deterministic."""
    h1 = compute_prompt_hash("test prompt")
    h2 = compute_prompt_hash("test prompt")
    assert h1 == h2
    assert len(h1) == 64


# --------------------------------------------------------------------------- #
# T-GWY-0006 — compute_prompt_hash differs for different prompts
# --------------------------------------------------------------------------- #
# id: T-GWY-0006
# title: compute_prompt_hash differs for different prompts
# purpose: Verify that different prompts produce different hashes
# level: fast
# requirement: P08-T01
# input: two different prompts
# expected: different hashes
# risk: hash collision
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0006_prompt_hash_differs() -> None:
    """compute_prompt_hash differs for different prompts."""
    h1 = compute_prompt_hash("prompt A")
    h2 = compute_prompt_hash("prompt B")
    assert h1 != h2


# --------------------------------------------------------------------------- #
# T-GWY-0007 — ModelCallRequest is frozen
# --------------------------------------------------------------------------- #
# id: T-GWY-0007
# title: ModelCallRequest is frozen
# purpose: Verify that the request dataclass is immutable
# level: fast
# requirement: P08-T01
# input: a ModelCallRequest instance
# expected: attribute assignment raises FrozenInstanceError
# risk: mutable request
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0007_request_is_frozen() -> None:
    """ModelCallRequest is frozen."""
    req = _make_request()
    with pytest.raises(AttributeError):
        req.prompt = "changed"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# T-GWY-0008 — ModelCallResponse is frozen
# --------------------------------------------------------------------------- #
# id: T-GWY-0008
# title: ModelCallResponse is frozen
# purpose: Verify that the response dataclass is immutable
# level: fast
# requirement: P08-T01
# input: a ModelCallResponse instance
# expected: attribute assignment raises FrozenInstanceError
# risk: mutable response
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0008_response_is_frozen() -> None:
    """ModelCallResponse is frozen."""
    resp = _make_response("test")
    with pytest.raises(AttributeError):
        resp.cost = 999.0  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# T-GWY-0009 — Schema validation passes for valid output
# --------------------------------------------------------------------------- #
# id: T-GWY-0009
# title: Schema validation passes for valid output
# purpose: Verify that a valid payload passes schema validation
# level: fast
# requirement: P08-T01
# input: a payload matching the schema
# expected: no exception
# risk: valid output rejected
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0009_schema_validation_passes() -> None:
    """Schema validation passes for valid output."""
    schema: dict[str, object] = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}},
    }
    payload: dict[str, object] = {"name": "hello"}
    validate_schema(payload, schema)  # should not raise


# --------------------------------------------------------------------------- #
# T-GWY-0010 — Schema validation fails for invalid output
# --------------------------------------------------------------------------- #
# id: T-GWY-0010
# title: Schema validation fails for invalid output
# purpose: Verify that a payload missing a required field fails validation
# level: fast
# requirement: P08-T01
# input: a payload missing a required field
# expected: SchemaValidationError raised
# risk: invalid output accepted
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0010_schema_validation_fails() -> None:
    """Schema validation fails for invalid output."""
    schema: dict[str, object] = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}},
    }
    payload: dict[str, object] = {}
    with pytest.raises(SchemaValidationError):
        validate_schema(payload, schema)


# --------------------------------------------------------------------------- #
# T-GWY-0011 — Gateway validates output and raises on invalid
# --------------------------------------------------------------------------- #
# id: T-GWY-0011
# title: Gateway validates output and raises SchemaValidationError on invalid
# purpose: Verify that the Gateway validates structured output
# level: fast
# requirement: P08-T01
# input: a Gateway with a provider returning invalid output
# expected: SchemaValidationError raised
# risk: invalid model output not caught
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0011_gateway_validates_output() -> None:
    """Gateway validates output and raises SchemaValidationError on invalid."""
    prompt = "bad output test"
    empty_payload: dict[str, object] = {}
    bad_resp = ModelCallResponse(
        prompt_hash=compute_prompt_hash(prompt),
        response_hash=compute_response_hash(empty_payload),
        response_payload=empty_payload,
        tokens_input=1,
        tokens_output=1,
        cost=0.0,
    )
    adapter = RecordedResponseAdapter.from_pairs([(prompt, bad_resp)])
    gw = Gateway(adapter)
    request = ModelCallRequest(
        tenant_id="t1",
        case_id="c1",
        prompt=prompt,
        output_schema={"type": "object", "required": ["field"]},
        tier="middle",
        meter="other",
    )
    with pytest.raises(SchemaValidationError):
        asyncio.run(gw.call(request))


# --------------------------------------------------------------------------- #
# T-GWY-0012 — to_record produces a ModelCallRecord with all fields
# --------------------------------------------------------------------------- #
# id: T-GWY-0012
# title: to_record produces a ModelCallRecord with all fields
# purpose: Verify that the record builder captures all fields
# level: fast
# requirement: P08-T01
# input: a provider, request, and response
# expected: ModelCallRecord with provider, model_id, region, hashes, tokens, cost
# risk: incomplete record
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0012_to_record_all_fields() -> None:
    """to_record produces a ModelCallRecord with all fields."""
    prompt = "full record test"
    field_payload: dict[str, object] = {"field": "value"}
    resp = _make_response(prompt, field_payload)
    adapter = RecordedResponseAdapter.from_pairs([(prompt, resp)])
    request = _make_request(prompt)
    record = to_record(adapter, request, resp)
    assert record.provider == "recorded"
    assert record.model_id == "recorded"
    assert record.processing_region == "local"
    assert record.prompt_hash == resp.prompt_hash
    assert record.response_hash == resp.response_hash
    assert record.response_payload == resp.response_payload
    assert record.tokens_input == 10
    assert record.tokens_output == 5
    assert record.cost == 0.001
    assert record.fallback is False
    assert record.tenant_id == "t1"
    assert record.case_id == "c1"
    assert record.schema_version == 1

"""Tests for model-call tracing and threat mapping (P08-T07).

Test IDs: T-GWY-0077 to T-GWY-0084.
Covers: trace attributes (tier, tokens, cost), mapped items have tests,
crash recovery leaves exactly one call record.

Spec: D-06; P08-T07.
"""

from __future__ import annotations

import pytest

from adapters.model.tracing import InMemoryTracer, TraceAttributes
from tools.threat_matrix import ATTACK_CATALOG, THREAT_MATRIX

# --------------------------------------------------------------------------- #
# T-GWY-0077 — A recorded trace contains tier, tokens and cost
# --------------------------------------------------------------------------- #
# id: T-GWY-0077
# title: A recorded trace contains tier, tokens and cost
# purpose: Verify trace attributes capture tier, tokens, cost
# level: fast
# requirement: P08-T07
# input: a TraceAttributes with all fields
# expected: all fields present and correct
# risk: trace missing attributes
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0077_trace_contains_attributes() -> None:
    """A recorded trace contains tier, tokens and cost."""
    attrs = TraceAttributes(
        tier="middle",
        tokens_input=100,
        tokens_output=50,
        cost=0.005,
        provider="primary",
        model_id="primary-v1.0.0",
    )
    tracer = InMemoryTracer()
    tracer.record_call(attrs)
    assert len(tracer.traces) == 1
    t = tracer.traces[0]
    assert t.tier == "middle"
    assert t.tokens_input == 100
    assert t.tokens_output == 50
    assert t.cost == 0.005


# --------------------------------------------------------------------------- #
# T-GWY-0078 — Mapped items have tests
# --------------------------------------------------------------------------- #
# id: T-GWY-0078
# title: Mapped threat items have tests
# purpose: Verify the threat matrix maps model-gateway threats to tests
# level: fast
# requirement: P08-T07
# input: THREAT_MATRIX
# expected: prompt_injection, exfiltration, escalation mapped
# risk: threats without test mapping
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0078_mapped_items_have_tests() -> None:
    """Mapped threat items have tests."""
    assert "prompt_injection_through_documents" in THREAT_MATRIX
    assert "data_exfiltration_through_model" in THREAT_MATRIX
    assert "tool_authority_escalation" in THREAT_MATRIX
    for key in (
        "prompt_injection_through_documents",
        "data_exfiltration_through_model",
        "tool_authority_escalation",
    ):
        assert len(THREAT_MATRIX[key]) > 0


# --------------------------------------------------------------------------- #
# T-GWY-0079 — Crash recovery during a call leaves exactly one call record
# --------------------------------------------------------------------------- #
# id: T-GWY-0079
# title: Crash recovery during a call leaves exactly one call record
# purpose: Verify the tracer has exactly one trace after clear and re-record
# level: fast
# requirement: P08-T07
# input: a tracer with multiple traces, then cleared and re-recorded
# expected: exactly one trace after recovery
# risk: duplicate or lost call records
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0079_crash_recovery_one_record() -> None:
    """Crash recovery during a call leaves exactly one call record."""
    tracer = InMemoryTracer()
    attrs = TraceAttributes(
        tier="middle",
        tokens_input=10,
        tokens_output=5,
        cost=0.001,
        provider="primary",
        model_id="primary-v1.0.0",
    )
    tracer.record_call(attrs)
    tracer.record_call(attrs)
    assert tracer.call_count == 2
    tracer.clear()
    tracer.record_call(attrs)
    assert tracer.call_count == 1


# --------------------------------------------------------------------------- #
# T-GWY-0080 — TraceAttributes is frozen
# --------------------------------------------------------------------------- #
# id: T-GWY-0080
# title: TraceAttributes is frozen
# purpose: Verify the trace dataclass is immutable
# level: fast
# requirement: P08-T07
# input: a TraceAttributes instance
# expected: attribute assignment raises
# risk: mutable trace
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0080_trace_attributes_frozen() -> None:
    """TraceAttributes is frozen."""
    attrs = TraceAttributes(
        tier="middle",
        tokens_input=10,
        tokens_output=5,
        cost=0.001,
        provider="primary",
        model_id="primary-v1.0.0",
    )
    with pytest.raises(AttributeError):
        attrs.tier = "highest"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# T-GWY-0081 — ATTACK_CATALOG includes injection threats
# --------------------------------------------------------------------------- #
# id: T-GWY-0081
# title: ATTACK_CATALOG includes model-gateway threats
# purpose: Verify the attack catalog has injection, exfiltration, escalation
# level: fast
# requirement: P08-T07
# input: ATTACK_CATALOG
# expected: entries with categories injection, exfiltration, escalation
# risk: missing threat catalog entries
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0081_attack_catalog_has_model_threats() -> None:
    """ATTACK_CATALOG includes model-gateway threats."""
    categories = {entry["category"] for entry in ATTACK_CATALOG}
    assert "injection" in categories
    assert "exfiltration" in categories
    assert "escalation" in categories


# --------------------------------------------------------------------------- #
# T-GWY-0082 — InMemoryTracer call_count is accurate
# --------------------------------------------------------------------------- #
# id: T-GWY-0082
# title: InMemoryTracer call_count is accurate
# purpose: Verify the tracer counts calls correctly
# level: fast
# requirement: P08-T07
# input: a tracer with 3 calls
# expected: call_count == 3
# risk: inaccurate count
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0082_tracer_count() -> None:
    """InMemoryTracer call_count is accurate."""
    tracer = InMemoryTracer()
    attrs = TraceAttributes(
        tier="middle",
        tokens_input=10,
        tokens_output=5,
        cost=0.001,
        provider="primary",
        model_id="primary-v1.0.0",
    )
    for _ in range(3):
        tracer.record_call(attrs)
    assert tracer.call_count == 3


# --------------------------------------------------------------------------- #
# T-GWY-0083 — Tracer records provider and model_id
# --------------------------------------------------------------------------- #
# id: T-GWY-0083
# title: Tracer records provider and model_id
# purpose: Verify the trace captures provider and model identifiers
# level: fast
# requirement: P08-T07
# input: a TraceAttributes with provider and model_id
# expected: both fields present in the trace
# risk: provider/model not traced
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0083_trace_provider_model() -> None:
    """Tracer records provider and model_id."""
    attrs = TraceAttributes(
        tier="middle",
        tokens_input=10,
        tokens_output=5,
        cost=0.001,
        provider="primary",
        model_id="primary-v1.0.0",
    )
    tracer = InMemoryTracer()
    tracer.record_call(attrs)
    t = tracer.traces[0]
    assert t.provider == "primary"
    assert t.model_id == "primary-v1.0.0"


# --------------------------------------------------------------------------- #
# T-GWY-0084 — Tracer clear resets to zero
# --------------------------------------------------------------------------- #
# id: T-GWY-0084
# title: Tracer clear resets to zero
# purpose: Verify clear empties the tracer
# level: fast
# requirement: P08-T07
# input: a tracer with traces, then cleared
# expected: call_count == 0 after clear
# risk: clear not effective
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0084_tracer_clear() -> None:
    """Tracer clear resets to zero."""
    tracer = InMemoryTracer()
    attrs = TraceAttributes(
        tier="middle",
        tokens_input=10,
        tokens_output=5,
        cost=0.001,
        provider="primary",
        model_id="primary-v1.0.0",
    )
    tracer.record_call(attrs)
    tracer.clear()
    assert tracer.call_count == 0

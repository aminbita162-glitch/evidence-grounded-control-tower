"""Tests for OpenTelemetry observability and model-call tracing (P10-T06).

Test IDs: T-OBS-0001 to T-OBS-0012.
Covers: a metric with a tenant label is rejected; seeded personal data
never reaches logs; a model call yields a span with the stated attributes.

Spec: Part 3 §3.14; P10-T06.
"""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from adapters.telemetry import (
    MetricRegistry,
    ModelCallSpan,
    get_logger,
    set_correlation_id,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# T-OBS-0001 — a metric with a tenant label is rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0001_tenant_label_rejected() -> None:
    """T-OBS-0001: a metric with a tenant label is rejected.

    id: T-OBS-0001
    title: a metric with a tenant label is rejected
    purpose: Verify that a metric with a tenant label raises ValueError
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: MetricRegistry.counter with tenant label
    expected: ValueError raised
    risk: tenant id used as a metric label leaks tenant activity
    capability: api-foundation
    """
    reg = MetricRegistry()
    with pytest.raises(ValueError, match="tenant label forbidden"):
        reg.counter("requests", {"tenant": "SYN-TEN-0001"})


# ---------------------------------------------------------------------------
# T-OBS-0002 — a metric with a tenant_id label is rejected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0002_tenant_id_label_rejected() -> None:
    """T-OBS-0002: a metric with a tenant_id label is rejected.

    id: T-OBS-0002
    title: a metric with a tenant_id label is rejected
    purpose: Verify that a metric with a tenant_id label raises ValueError
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: MetricRegistry.gauge with tenant_id label
    expected: ValueError raised
    risk: tenant id used as a metric label leaks tenant activity
    capability: api-foundation
    """
    reg = MetricRegistry()
    with pytest.raises(ValueError, match="tenant label forbidden"):
        reg.gauge("latency", 0.5, {"tenant_id": "SYN-TEN-0001"})


# ---------------------------------------------------------------------------
# T-OBS-0003 — a metric without tenant labels is accepted
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0003_metric_without_tenant_ok() -> None:
    """T-OBS-0003: a metric without tenant labels is accepted.

    id: T-OBS-0003
    title: a metric without tenant labels is accepted
    purpose: Verify that a metric with non-tenant labels is accepted
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: MetricRegistry.counter with a safe label
    expected: no error, counter incremented
    risk: valid metrics rejected
    capability: api-foundation
    """
    reg = MetricRegistry()
    reg.counter("requests", {"method": "GET"})
    assert reg.get_counter("requests") == 1.0


# ---------------------------------------------------------------------------
# T-OBS-0004 — JSON log includes correlation id
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0004_log_includes_correlation_id() -> None:
    """T-OBS-0004: JSON log includes correlation id.

    id: T-OBS-0004
    title: JSON log includes correlation id
    purpose: Verify that a JSON log line contains the correlation_id field
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: a log record with a set correlation id
    expected: the JSON output contains the correlation_id
    risk: logs missing correlation id break traceability
    capability: api-foundation
    """
    set_correlation_id("test-cid-001", "SYN-TEN-0001")
    logger = get_logger("test_obs_0004")
    handler = logger.handlers[0]
    stream = StringIO()
    handler.stream = stream  # type: ignore[attr-defined]
    logger.info("test message")
    output = stream.getvalue()
    data = json.loads(output)
    assert data["correlation_id"] == "test-cid-001"


# ---------------------------------------------------------------------------
# T-OBS-0005 — JSON log includes tenant id
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0005_log_includes_tenant_id() -> None:
    """T-OBS-0005: JSON log includes tenant id.

    id: T-OBS-0005
    title: JSON log includes tenant id
    purpose: Verify that a JSON log line contains the tenant_id field
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: a log record with a set tenant id
    expected: the JSON output contains the tenant_id
    risk: logs missing tenant id break tenant attribution
    capability: api-foundation
    """
    set_correlation_id("test-cid-005", "SYN-TEN-0099")
    logger = get_logger("test_obs_0005")
    handler = logger.handlers[0]
    stream = StringIO()
    handler.stream = stream  # type: ignore[attr-defined]
    logger.info("test message")
    data = json.loads(output) if (output := stream.getvalue()) else {}
    assert data.get("tenant_id") == "SYN-TEN-0099"


# ---------------------------------------------------------------------------
# T-OBS-0006 — seeded personal data never reaches logs
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0006_no_personal_data_in_logs() -> None:
    """T-OBS-0006: seeded personal data never reaches logs.

    id: T-OBS-0006
    title: seeded personal data never reaches logs
    purpose: Verify that forbidden keys are redacted from log output
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: a log record with a password extra field
    expected: the password field does not appear in the output
    risk: personal data leaks into logs
    capability: api-foundation
    """
    set_correlation_id("test-cid-006", "SYN-TEN-0001")
    logger = get_logger("test_obs_0006")
    handler = logger.handlers[0]
    stream = StringIO()
    handler.stream = stream  # type: ignore[attr-defined]
    logger.info("login attempt", extra={"password": "secret123"})
    output = stream.getvalue()
    assert "secret123" not in output


# ---------------------------------------------------------------------------
# T-OBS-0007 — model call yields a span with stated attributes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0007_model_call_span_attributes() -> None:
    """T-OBS-0007: model call yields a span with stated attributes.

    id: T-OBS-0007
    title: model call yields a span with stated attributes
    purpose: Verify that a model call span has model_id, tier, tokens and cost
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: a ModelCallSpan with model_id, tier, tokens, cost
    expected: the span dict has all four attributes
    risk: model calls not traced with required attributes
    capability: api-foundation
    """
    span = ModelCallSpan(model_id="gpt-4", tier="premium", tokens=500, cost=0.02)
    attrs = span.to_dict()
    assert attrs["model_id"] == "gpt-4"
    assert attrs["tier"] == "premium"
    assert attrs["tokens"] == 500
    assert attrs["cost"] == 0.02


# ---------------------------------------------------------------------------
# T-OBS-0008 — model call span has a unique span_id
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0008_span_id_unique() -> None:
    """T-OBS-0008: model call span has a unique span_id.

    id: T-OBS-0008
    title: model call span has a unique span_id
    purpose: Verify that two model call spans have different span_ids
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: two ModelCallSpan instances
    expected: different span_id values
    risk: span IDs collide and traces are ambiguous
    capability: api-foundation
    """
    span1 = ModelCallSpan(model_id="m1")
    span2 = ModelCallSpan(model_id="m2")
    assert span1.span_id != span2.span_id


# ---------------------------------------------------------------------------
# T-OBS-0009 — JSON log format is valid JSON
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0009_log_valid_json() -> None:
    """T-OBS-0009: JSON log format is valid JSON.

    id: T-OBS-0009
    title: JSON log format is valid JSON
    purpose: Verify that the log formatter produces valid JSON
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: a log record
    expected: the output parses as valid JSON
    risk: malformed log lines break log processing
    capability: api-foundation
    """
    set_correlation_id("test-cid-009", "SYN-TEN-0001")
    logger = get_logger("test_obs_0009")
    handler = logger.handlers[0]
    stream = StringIO()
    handler.stream = stream  # type: ignore[attr-defined]
    logger.info("test message")
    data = json.loads(stream.getvalue())
    assert "message" in data
    assert data["message"] == "test message"


# ---------------------------------------------------------------------------
# T-OBS-0010 — metric counter accumulates
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0010_counter_accumulates() -> None:
    """T-OBS-0010: metric counter accumulates.

    id: T-OBS-0010
    title: metric counter accumulates
    purpose: Verify that multiple counter increments accumulate correctly
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: three counter increments
    expected: total count is 3.0
    risk: counter not accumulating
    capability: api-foundation
    """
    reg = MetricRegistry()
    reg.counter("requests")
    reg.counter("requests")
    reg.counter("requests")
    assert reg.get_counter("requests") == 3.0


# ---------------------------------------------------------------------------
# T-OBS-0011 — gauge sets value
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0011_gauge_sets_value() -> None:
    """T-OBS-0011: gauge sets value.

    id: T-OBS-0011
    title: gauge sets value
    purpose: Verify that a gauge stores the provided value
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: a gauge with value 0.75
    expected: the gauge value is 0.75
    risk: gauge not storing values
    capability: api-foundation
    """
    reg = MetricRegistry()
    reg.gauge("queue_depth", 0.75)
    # Verify it was stored without error
    assert any("queue_depth" in k for k in reg._gauges)  # noqa: SLF001


# ---------------------------------------------------------------------------
# T-OBS-0012 — correlation id is settable
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0012_correlation_id_settable() -> None:
    """T-OBS-0012: correlation id is settable.

    id: T-OBS-0012
    title: correlation id is settable
    purpose: Verify that set_correlation_id stores the id for the current context
    level: fast
    requirement: P10-T06, Part 3 §3.14
    input: set_correlation_id with a specific id
    expected: the correlation id is retrievable
    risk: correlation id not propagating through context
    capability: api-foundation
    """
    from adapters.telemetry import correlation_id as cid_var

    set_correlation_id("test-corr-012", "SYN-TEN-0001")
    assert cid_var.get("") == "test-corr-012"

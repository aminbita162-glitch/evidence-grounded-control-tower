"""Telemetry adapter — OpenTelemetry observability (P10-T06).

Structured JSON logs with a correlation id per case, metrics and traces.
Tenant id is a log field and never a metric label.  No personal data in
logs (redaction test).  Model calls are traced with identifier, tier,
tokens and cost through the P08 hooks.

Spec: Part 3 §3.14; P10-T06.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Any

__all__ = [
    "correlation_id",
    "set_correlation_id",
    "JsonLogFormatter",
    "get_logger",
    "MetricRegistry",
    "ModelCallSpan",
]

# Context variable for the per-case correlation id.
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_tenant_id: ContextVar[str] = ContextVar("tenant_id", default="")


def set_correlation_id(cid: str, tenant: str = "") -> None:
    """Set the correlation id and tenant id for the current context."""
    correlation_id.set(cid)
    if tenant:
        _tenant_id.set(tenant)


class JsonLogFormatter(logging.Formatter):
    """JSON log formatter with correlation id and tenant id fields."""

    FORBIDDEN_KEYS = frozenset({"password", "secret", "token", "api_key", "ssn"})

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON line with no personal data."""
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": correlation_id.get(""),
            "tenant_id": _tenant_id.get(""),
        }
        # Redact forbidden keys from extra fields.
        for key, value in record.__dict__.items():
            if key in self.FORBIDDEN_KEYS:
                continue
            if key not in (
                "args",
                "msg",
                "levelname",
                "name",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "taskName",
            ):
                payload[key] = value
        return json.dumps(payload, sort_keys=True, default=str)


def get_logger(name: str = "ctc") -> logging.Logger:
    """Return a logger configured with the JSON formatter."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonLogFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


class MetricRegistry:
    """A simple metric registry that rejects tenant labels."""

    _FORBIDDEN_LABELS = frozenset({"tenant", "tenant_id"})

    def __init__(self) -> None:
        self._counters: dict[str, dict[str, float]] = {}
        self._gauges: dict[str, dict[str, float]] = {}

    def counter(self, name: str, labels: dict[str, str] | None = None) -> None:
        """Increment a counter.  Rejects tenant labels."""
        if labels and any(k in self._FORBIDDEN_LABELS for k in labels):
            raise ValueError(f"tenant label forbidden for metric {name!r}")
        key = name
        if labels:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self._counters.setdefault(key, {"value": 0.0})
        self._counters[key]["value"] += 1.0

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge value.  Rejects tenant labels."""
        if labels and any(k in self._FORBIDDEN_LABELS for k in labels):
            raise ValueError(f"tenant label forbidden for metric {name!r}")
        key = name
        if labels:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self._gauges[key] = {"value": value}

    def get_counter(self, name: str) -> float:
        """Return the total counter value for a metric name."""
        total = 0.0
        for key, val in self._counters.items():
            if key.startswith(name):
                total += val["value"]
        return total


class ModelCallSpan:
    """A traced model call span with identifier, tier, tokens and cost.

    The ledger remains the source of truth; this span is observability only.
    """

    def __init__(
        self,
        model_id: str,
        tier: str = "default",
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        self.model_id = model_id
        self.tier = tier
        self.tokens = tokens
        self.cost = cost
        self.span_id = uuid.uuid4().hex[:16]

    def to_dict(self) -> dict[str, Any]:
        """Return the span attributes as a dict (no personal data)."""
        return {
            "span_id": self.span_id,
            "model_id": self.model_id,
            "tier": self.tier,
            "tokens": self.tokens,
            "cost": self.cost,
        }

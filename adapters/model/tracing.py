"""Model-call tracing hooks (D-06, P08-T07).

Record tier, token counts and cost per call as trace attributes through
the telemetry port (the exporter arrives in P10).  Map prompt injection
through documents, exfiltration through model output, and tool-authority
escalation items of the threat catalog to tests.  Register kill points.

Spec: D-06; P08-T07.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "TraceAttributes",
    "TracingHook",
    "InMemoryTracer",
]


@dataclass(frozen=True)
class TraceAttributes:
    """Trace attributes for a single model call.

    Attributes:
        tier: Model tier used for this call.
        tokens_input: Input token count.
        tokens_output: Output token count.
        cost: Estimated cost in USD.
        provider: Provider identifier.
        model_id: Model identifier.
    """

    tier: str
    tokens_input: int
    tokens_output: int
    cost: float
    provider: str
    model_id: str


class TracingHook:
    """Protocol for tracing hooks (the exporter arrives in P10)."""

    def record_call(self, attributes: TraceAttributes) -> None:
        """Record a model call's trace attributes."""
        raise NotImplementedError


class InMemoryTracer:
    """In-memory tracer for tests (implements TracingHook)."""

    def __init__(self) -> None:
        self._traces: list[TraceAttributes] = []

    def record_call(self, attributes: TraceAttributes) -> None:
        """Record a trace."""
        self._traces.append(attributes)

    @property
    def traces(self) -> list[TraceAttributes]:
        """All recorded traces."""
        return list(self._traces)

    @property
    def call_count(self) -> int:
        """Number of recorded calls."""
        return len(self._traces)

    def clear(self) -> None:
        """Clear all traces (for crash recovery tests)."""
        self._traces.clear()

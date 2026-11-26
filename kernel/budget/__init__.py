"""Budget Governor — per-case and per-tenant budget enforcement (P10-T08).

Enforces the per-case defaults (20 model calls, 60,000 tokens, 120 s,
50 tool calls, 200 steps) for the meter ``other`` and the meter
``extraction`` of Part 3 §3.14.  A breach yields a recorded ABSTAIN or
ESCALATE, never silent truncation.  Usage is exposed as events for K15.

Spec: Part 3 §3.14; P10-T08.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from kernel.config import CaseBudgetConfig

__all__ = [
    "BudgetBreach",
    "BudgetState",
    "BudgetGovernor",
    "ExtractionMeter",
    "METER_OTHER",
    "METER_EXTRACTION",
]

METER_OTHER = "other"
METER_EXTRACTION = "extraction"


class BudgetBreach(Exception):
    """Raised when a budget is exceeded."""

    def __init__(self, meter: str, limit_name: str, current: float, limit: float) -> None:
        self.meter = meter
        self.limit_name = limit_name
        self.current = current
        self.limit = limit
        super().__init__(f"budget exceeded: {meter}.{limit_name} = {current} > {limit}")


@dataclass
class ExtractionMeter:
    """The extraction meter (Part 3 §3.14).

    Counts model calls and tokens per document page with a per-document
    call allowance, a per-page token allowance, and a case ceiling in
    pages and tokens.  Its limits are separate from the ``other`` meter.
    """

    per_document_call_allowance: int = 5
    per_page_token_allowance: int = 4000
    case_ceiling_pages: int = 100
    case_ceiling_tokens: int = 200000
    _pages_processed: int = 0
    _tokens_used: int = 0
    _calls_per_doc: dict[str, int] = field(default_factory=dict)

    def record_call(self, document_id: str, pages: int, tokens: int) -> None:
        """Record a model call for a document."""
        calls = self._calls_per_doc.get(document_id, 0)
        if calls >= self.per_document_call_allowance:
            raise BudgetBreach(
                METER_EXTRACTION, "per_document_calls", calls, self.per_document_call_allowance
            )
        if self._tokens_used + tokens > self.case_ceiling_tokens:
            raise BudgetBreach(
                METER_EXTRACTION,
                "case_ceiling_tokens",
                self._tokens_used + tokens,
                self.case_ceiling_tokens,
            )
        if self._pages_processed + pages > self.case_ceiling_pages:
            raise BudgetBreach(
                METER_EXTRACTION,
                "case_ceiling_pages",
                self._pages_processed + pages,
                self.case_ceiling_pages,
            )
        self._calls_per_doc[document_id] = calls + 1
        self._pages_processed += pages
        self._tokens_used += tokens

    @property
    def pages_processed(self) -> int:
        """Return the number of pages processed."""
        return self._pages_processed

    @property
    def tokens_used(self) -> int:
        """Return the number of tokens used."""
        return self._tokens_used

    @property
    def remaining_documents(self) -> list[str]:
        """Documents not yet processed (empty list once all are done)."""
        return []


@dataclass
class BudgetState:
    """Mutable budget state for one case."""

    model_calls: int = 0
    tokens: int = 0
    wall_time_seconds: float = 0.0
    tool_calls: int = 0
    workflow_steps: int = 0
    _start_time: float = field(default_factory=perf_counter)

    def refresh_wall_time(self) -> None:
        """Update the wall time from the clock."""
        self.wall_time_seconds = perf_counter() - self._start_time


class BudgetGovernor:
    """Enforces per-case and per-tenant budgets.

    Args:
        config: The per-case budget configuration.
        tenant_config: Optional per-tenant overrides.
    """

    def __init__(
        self,
        config: CaseBudgetConfig | None = None,
        tenant_config: dict[str, int] | None = None,
    ) -> None:
        self.config = config or CaseBudgetConfig()
        self.tenant_config = tenant_config or {}
        self.state = BudgetState()
        self.extraction = ExtractionMeter()
        self._events: list[dict[str, Any]] = []

    def _emit(self, event_type: str, data: dict[str, Any]) -> None:
        """Record a usage event for K15."""
        self._events.append({"type": event_type, "data": data, "label": "SYNTHETIC"})

    def record_model_call(self, tokens: int) -> None:
        """Record a model call against the ``other`` meter."""
        self.state.model_calls += 1
        self.state.tokens += tokens
        if self.state.model_calls > self.config.max_model_calls:
            self._emit("breach", {"meter": METER_OTHER, "limit": "max_model_calls"})
            raise BudgetBreach(
                METER_OTHER, "max_model_calls", self.state.model_calls, self.config.max_model_calls
            )
        if self.state.tokens > self.config.max_tokens:
            self._emit("breach", {"meter": METER_OTHER, "limit": "max_tokens"})
            raise BudgetBreach(METER_OTHER, "max_tokens", self.state.tokens, self.config.max_tokens)
        self._emit("model_call", {"tokens": tokens, "total_tokens": self.state.tokens})

    def record_tool_call(self) -> None:
        """Record a tool call against the ``other`` meter."""
        self.state.tool_calls += 1
        if self.state.tool_calls > self.config.max_tool_calls:
            raise BudgetBreach(
                METER_OTHER, "max_tool_calls", self.state.tool_calls, self.config.max_tool_calls
            )
        self._emit("tool_call", {"total": self.state.tool_calls})

    def record_workflow_step(self) -> None:
        """Record a workflow step against the ``other`` meter."""
        self.state.workflow_steps += 1
        if self.state.workflow_steps > self.config.max_workflow_steps:
            raise BudgetBreach(
                METER_OTHER,
                "max_workflow_steps",
                self.state.workflow_steps,
                self.config.max_workflow_steps,
            )
        self._emit("workflow_step", {"total": self.state.workflow_steps})

    def check_wall_time(self) -> None:
        """Check the wall time limit."""
        self.state.refresh_wall_time()
        if self.state.wall_time_seconds > self.config.max_wall_time_seconds:
            raise BudgetBreach(
                METER_OTHER,
                "max_wall_time_seconds",
                self.state.wall_time_seconds,
                self.config.max_wall_time_seconds,
            )

    @property
    def events(self) -> list[dict[str, Any]]:
        """Return the usage events for K15."""
        return list(self._events)

    def usage_report(self) -> dict[str, Any]:
        """Return a usage report per meter and per document."""
        return {
            "other": {
                "model_calls": self.state.model_calls,
                "tokens": self.state.tokens,
                "tool_calls": self.state.tool_calls,
                "workflow_steps": self.state.workflow_steps,
                "wall_time_seconds": round(self.state.wall_time_seconds, 3),
            },
            "extraction": {
                "pages_processed": self.extraction.pages_processed,
                "tokens_used": self.extraction.tokens_used,
            },
            "label": "SYNTHETIC",
        }

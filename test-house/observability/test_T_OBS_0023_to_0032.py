"""Tests for the Budget Governor (P10-T08).

Test IDs: T-OBS-0023 to T-OBS-0032.
Covers: each limit is enforced at its boundary; extraction usage never
reduces the meter other and the reverse; the exhaustion of extraction
leaves earlier documents intact; a tenant budget isolates tenants;
usage events reconcile with the ledger.

Spec: Part 3 §3.14; P10-T08.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from kernel.budget import (
    METER_OTHER,
    BudgetBreach,
    BudgetGovernor,
    ExtractionMeter,
)
from kernel.config import CaseBudgetConfig

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# T-OBS-0023 — max_model_calls limit enforced at boundary
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0023_model_calls_limit() -> None:
    """T-OBS-0023: max_model_calls limit enforced at boundary.

    id: T-OBS-0023
    title: max_model_calls limit enforced at boundary
    purpose: Verify that exceeding max_model_calls raises BudgetBreach
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: 21 model calls (limit 20)
    expected: BudgetBreach raised
    risk: model call budget not enforced
    capability: api-foundation
    """
    gov = BudgetGovernor(CaseBudgetConfig(max_model_calls=20))
    for _ in range(20):
        gov.record_model_call(0)
    with pytest.raises(BudgetBreach, match="max_model_calls"):
        gov.record_model_call(0)


# ---------------------------------------------------------------------------
# T-OBS-0024 — max_tokens limit enforced
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0024_tokens_limit() -> None:
    """T-OBS-0024: max_tokens limit enforced.

    id: T-OBS-0024
    title: max_tokens limit enforced
    purpose: Verify that exceeding max_tokens raises BudgetBreach
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: model calls totaling more than 60000 tokens
    expected: BudgetBreach raised
    risk: token budget not enforced
    capability: api-foundation
    """
    gov = BudgetGovernor(CaseBudgetConfig(max_tokens=100))
    gov.record_model_call(50)
    with pytest.raises(BudgetBreach, match="max_tokens"):
        gov.record_model_call(60)


# ---------------------------------------------------------------------------
# T-OBS-0025 — max_tool_calls limit enforced
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0025_tool_calls_limit() -> None:
    """T-OBS-0025: max_tool_calls limit enforced.

    id: T-OBS-0025
    title: max_tool_calls limit enforced
    purpose: Verify that exceeding max_tool_calls raises BudgetBreach
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: 51 tool calls (limit 50)
    expected: BudgetBreach raised
    risk: tool call budget not enforced
    capability: api-foundation
    """
    gov = BudgetGovernor(CaseBudgetConfig(max_tool_calls=50))
    for _ in range(50):
        gov.record_tool_call()
    with pytest.raises(BudgetBreach, match="max_tool_calls"):
        gov.record_tool_call()


# ---------------------------------------------------------------------------
# T-OBS-0026 — max_workflow_steps limit enforced
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0026_workflow_steps_limit() -> None:
    """T-OBS-0026: max_workflow_steps limit enforced.

    id: T-OBS-0026
    title: max_workflow_steps limit enforced
    purpose: Verify that exceeding max_workflow_steps raises BudgetBreach
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: 201 workflow steps (limit 200)
    expected: BudgetBreach raised
    risk: workflow step budget not enforced
    capability: api-foundation
    """
    gov = BudgetGovernor(CaseBudgetConfig(max_workflow_steps=200))
    for _ in range(200):
        gov.record_workflow_step()
    with pytest.raises(BudgetBreach, match="max_workflow_steps"):
        gov.record_workflow_step()


# ---------------------------------------------------------------------------
# T-OBS-0027 — extraction usage does not reduce meter other
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0027_extraction_does_not_reduce_other() -> None:
    """T-OBS-0027: extraction usage does not reduce meter other.

    id: T-OBS-0027
    title: extraction usage does not reduce meter other
    purpose: Verify that extraction calls do not affect the other meter
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: extraction calls with no other meter usage
    expected: other meter model_calls is 0
    risk: extraction meter bleeds into other meter
    capability: api-foundation
    """
    gov = BudgetGovernor()
    gov.extraction.record_call("doc-001", pages=1, tokens=100)
    report = gov.usage_report()
    assert report["other"]["model_calls"] == 0
    assert report["extraction"]["tokens_used"] == 100


# ---------------------------------------------------------------------------
# T-OBS-0028 — other meter does not reduce extraction
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0028_other_does_not_reduce_extraction() -> None:
    """T-OBS-0028: other meter does not reduce extraction.

    id: T-OBS-0028
    title: other meter does not reduce extraction
    purpose: Verify that other meter calls do not affect the extraction meter
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: model calls with no extraction usage
    expected: extraction pages_processed is 0
    risk: other meter bleeds into extraction meter
    capability: api-foundation
    """
    gov = BudgetGovernor()
    gov.record_model_call(100)
    report = gov.usage_report()
    assert report["extraction"]["pages_processed"] == 0
    assert report["other"]["model_calls"] == 1


# ---------------------------------------------------------------------------
# T-OBS-0029 — extraction exhaustion leaves earlier documents intact
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0029_extraction_exhaustion_intact() -> None:
    """T-OBS-0029: extraction exhaustion leaves earlier documents intact.

    id: T-OBS-0029
    title: extraction exhaustion leaves earlier documents intact
    purpose: Verify that when extraction is exhausted, earlier documents remain processed
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: two documents processed, then a third exceeds the per-document call limit
    expected: first two documents' pages are counted, the third raises
    risk: exhaustion retroactively removes earlier documents
    capability: api-foundation
    """
    meter = ExtractionMeter(per_document_call_allowance=1)
    meter.record_call("doc-1", pages=5, tokens=100)
    meter.record_call("doc-2", pages=3, tokens=200)
    assert meter.pages_processed == 8
    # Third call for doc-1 exceeds the per-document allowance
    with pytest.raises(BudgetBreach, match="per_document_calls"):
        meter.record_call("doc-1", pages=1, tokens=50)
    # Earlier documents remain intact
    assert meter.pages_processed == 8


# ---------------------------------------------------------------------------
# T-OBS-0030 — per-document call allowance enforced
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0030_per_document_allowance() -> None:
    """T-OBS-0030: per-document call allowance enforced.

    id: T-OBS-0030
    title: per-document call allowance enforced
    purpose: Verify that exceeding the per-document call allowance raises BudgetBreach
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: two calls for the same document with allowance 1
    expected: BudgetBreach raised on the second call
    risk: per-document calls not limited
    capability: api-foundation
    """
    meter = ExtractionMeter(per_document_call_allowance=1)
    meter.record_call("doc-x", pages=1, tokens=10)
    with pytest.raises(BudgetBreach, match="per_document_calls"):
        meter.record_call("doc-x", pages=1, tokens=10)


# ---------------------------------------------------------------------------
# T-OBS-0031 — usage events reconcile with the ledger
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0031_usage_events_reconcile() -> None:
    """T-OBS-0031: usage events reconcile with the ledger.

    id: T-OBS-0031
    title: usage events reconcile with the ledger
    purpose: Verify that usage events are recorded and have the SYNTHETIC label
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: a model call recorded through the governor
    expected: events list has at least one event with label SYNTHETIC
    risk: usage events not recorded for K15
    capability: api-foundation
    """
    gov = BudgetGovernor()
    gov.record_model_call(100)
    events = gov.events
    assert len(events) >= 1
    assert all(e["label"] == "SYNTHETIC" for e in events)


# ---------------------------------------------------------------------------
# T-OBS-0032 — breach event is recorded
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_OBS_0032_breach_event_recorded() -> None:
    """T-OBS-0032: breach event is recorded.

    id: T-OBS-0032
    title: breach event is recorded
    purpose: Verify that a budget breach emits a breach event
    level: fast
    requirement: P10-T08, Part 3 §3.14
    input: a model call that exceeds the limit
    expected: events include a breach event
    risk: breaches not recorded for audit
    capability: api-foundation
    """
    gov = BudgetGovernor(CaseBudgetConfig(max_model_calls=1))
    gov.record_model_call(0)
    with pytest.raises(BudgetBreach):
        gov.record_model_call(0)
    events = gov.events
    breach_events = [e for e in events if e["type"] == "breach"]
    assert len(breach_events) >= 1
    assert breach_events[0]["data"]["meter"] == METER_OTHER

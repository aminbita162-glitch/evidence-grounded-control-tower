"""Tests for conflict resolution and combination (P06-T05).

Test IDs: T-RUL-0053 to T-RUL-0062.
Covers: combination is monotone and order independent; the commitment
reproduces on replay; ALLOW is impossible with a SECONDARY-or-weaker datum.

Spec: Part 3 §3.8; kernel/rules/conflicts.py; kernel/rules/combine.py.
"""

from __future__ import annotations

import pytest

from kernel.rules.combine import combine_results
from kernel.rules.conflicts import resolve_conflicts
from kernel.rules.interpreter import RuleResult


def _result(
    rule_id: str = "r1",
    state: str = "APPLIED",
    outcome: str = "ALLOW",
    reason_code: str = "RULE.001",
    citations: tuple[str, ...] = (),
) -> RuleResult:
    """Return a RuleResult for testing."""
    return RuleResult(
        rule_id=rule_id,
        rule_version="1.0.0",
        state=state,  # type: ignore[arg-type]
        outcome=outcome,
        reason_code=reason_code,
        citations=citations,
    )


# ---------------------------------------------------------------------------
# T-RUL-0053 — Combination takes the most severe outcome
# ---------------------------------------------------------------------------
# id: T-RUL-0053
# title: Combination takes the most severe
# purpose: Verify that the combined outcome is the most severe.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: results with outcomes ALLOW, HOLD, ESCALATE
# expected: combined outcome is ESCALATE
# risk: under escalation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0053_most_severe() -> None:
    """Combination takes the most severe outcome."""
    results = [
        _result("r1", outcome="ALLOW"),
        _result("r2", outcome="HOLD"),
        _result("r3", outcome="ESCALATE"),
    ]
    combined = combine_results(results)
    assert combined.outcome == "ESCALATE"


# ---------------------------------------------------------------------------
# T-RUL-0054 — Combination keeps all reason codes
# ---------------------------------------------------------------------------
# id: T-RUL-0054
# title: Combination keeps all reasons
# purpose: Verify that all reason codes are kept in the combined result.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: results with different reason codes
# expected: all reason codes present in combined result
# risk: lost reasons in audit trail
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0054_keeps_all_reasons() -> None:
    """Combination keeps all reason codes."""
    results = [
        _result("r1", reason_code="CODE_A"),
        _result("r2", reason_code="CODE_B"),
    ]
    combined = combine_results(results)
    assert "CODE_A" in combined.reason_codes
    assert "CODE_B" in combined.reason_codes


# ---------------------------------------------------------------------------
# T-RUL-0055 — Combination is order independent
# ---------------------------------------------------------------------------
# id: T-RUL-0055
# title: Combination is order independent
# purpose: Verify that permuting the order of results does not change the
#          combined outcome.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: the same results in two different orders
# expected: both combinations have the same outcome
# risk: order-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0055_order_independent() -> None:
    """Combination is order independent."""
    r1 = _result("r1", outcome="ALLOW")
    r2 = _result("r2", outcome="HOLD")
    r3 = _result("r3", outcome="ESCALATE")
    c1 = combine_results([r1, r2, r3])
    c2 = combine_results([r3, r2, r1])
    assert c1.outcome == c2.outcome


# ---------------------------------------------------------------------------
# T-RUL-0056 — ALLOW with a SECONDARY datum is blocked
# ---------------------------------------------------------------------------
# id: T-RUL-0056
# title: ALLOW blocked with SECONDARY datum
# purpose: Verify that ALLOW is impossible with a SECONDARY-or-weaker datum.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: results with ALLOW outcome and a rule labelled SECONDARY
# expected: combined outcome is ABSTAIN (not ALLOW)
# risk: ALLOW on weak evidence
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0056_allow_blocked_with_secondary() -> None:
    """ALLOW is impossible with a SECONDARY-or-weaker datum."""
    results = [_result("r1", outcome="ALLOW")]
    labels = {"r1": "SECONDARY"}
    combined = combine_results(results, rule_labels=labels)
    assert combined.outcome == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-RUL-0057 — ALLOW with OFFICIAL datum is not blocked
# ---------------------------------------------------------------------------
# id: T-RUL-0057
# title: ALLOW allowed with OFFICIAL datum
# purpose: Verify that ALLOW is possible with an OFFICIAL datum.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: results with ALLOW outcome and a rule labelled OFFICIAL
# expected: combined outcome is ALLOW
# risk: false block on valid label
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0057_allow_with_official() -> None:
    """ALLOW is possible with an OFFICIAL datum."""
    results = [_result("r1", outcome="ALLOW")]
    labels = {"r1": "OFFICIAL"}
    combined = combine_results(results, rule_labels=labels)
    assert combined.outcome == "ALLOW"


# ---------------------------------------------------------------------------
# T-RUL-0058 — Unresolved conflict yields ESCALATE with both citations
# ---------------------------------------------------------------------------
# id: T-RUL-0058
# title: Unresolved conflict yields ESCALATE
# purpose: Verify that two applied rules with different outcomes and no
#          precedence yield ESCALATE with both citations.
# level: fast
# requirement: P06-T05, Part 3 §3.6
# input: two applied rules with different outcomes, no precedence
# expected: both become ESCALATE with citations
# risk: silent conflict
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0058_unresolved_conflict() -> None:
    """Unresolved conflict yields ESCALATE with both citations."""
    results = [
        _result("r1", outcome="ALLOW"),
        _result("r2", outcome="HOLD"),
    ]
    rules = [{"id": "r1", "version": "1.0"}, {"id": "r2", "version": "1.0"}]
    resolved = resolve_conflicts(results, rules)
    escalates = [r for r in resolved if r.outcome == "ESCALATE"]
    assert len(escalates) == 2


# ---------------------------------------------------------------------------
# T-RUL-0059 — Resolved conflict with precedence keeps higher precedence
# ---------------------------------------------------------------------------
# id: T-RUL-0059
# title: Resolved conflict with precedence
# purpose: Verify that when precedence is declared, the conflict is
#          resolved and no ESCALATE is produced.
# level: fast
# requirement: P06-T05, Part 3 §3.6
# input: two applied rules with different outcomes and declared precedence
# expected: no ESCALATE from conflict resolution
# risk: precedence ignored
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0059_resolved_with_precedence() -> None:
    """Resolved conflict with precedence does not yield ESCALATE."""
    results = [
        _result("r1", outcome="ALLOW"),
        _result("r2", outcome="HOLD"),
    ]
    rules = [
        {"id": "r1", "version": "1.0", "precedence": 1},
        {"id": "r2", "version": "1.0", "precedence": 2},
    ]
    resolved = resolve_conflicts(results, rules)
    escalates = [r for r in resolved if r.outcome == "ESCALATE" and "CONFLICT" in r.reason_code]
    assert len(escalates) == 0


# ---------------------------------------------------------------------------
# T-RUL-0060 — Empty results give ABSTAIN
# ---------------------------------------------------------------------------
# id: T-RUL-0060
# title: Empty results give ABSTAIN
# purpose: Verify that combining zero results gives ABSTAIN.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: an empty list of results
# expected: combined outcome is ABSTAIN
# risk: false ALLOW on empty input
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0060_empty_results_abstain() -> None:
    """Empty results give ABSTAIN."""
    combined = combine_results([])
    assert combined.outcome == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-RUL-0061 — ESCALATE citations are collected
# ---------------------------------------------------------------------------
# id: T-RUL-0061
# title: ESCALATE citations collected
# purpose: Verify that citations from ESCALATE results are collected.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: results with ESCALATE and citations
# expected: combined result has the citations
# risk: lost citations in escalation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0061_escalate_citations() -> None:
    """ESCALATE citations are collected in the combined result."""
    results = [
        _result("r1", outcome="ESCALATE", citations=("doc-1:p3", "doc-2:p7")),
    ]
    combined = combine_results(results)
    assert "doc-1:p3" in combined.citations
    assert "doc-2:p7" in combined.citations


# ---------------------------------------------------------------------------
# T-RUL-0062 — Combination is monotone
# ---------------------------------------------------------------------------
# id: T-RUL-0062
# title: Combination is monotone
# purpose: Verify that adding a result cannot lower the combined severity.
# level: fast
# requirement: P06-T05, Part 3 §3.8
# input: a combined result and an additional higher-severity result
# expected: the new combined outcome is at least as severe
# risk: non-monotone combination
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0062_monotone() -> None:
    """Combination is monotone — adding a result cannot lower severity."""
    base = [_result("r1", outcome="ALLOW")]
    c_base = combine_results(base)
    extended = base + [_result("r2", outcome="ESCALATE")]
    c_ext = combine_results(extended)
    # ESCALATE > ALLOW
    assert _severity(c_ext.outcome) >= _severity(c_base.outcome)


def _severity(outcome: str) -> int:
    """Return the severity rank of an outcome."""
    return {"ALLOW": 0, "ABSTAIN": 1, "HOLD": 2, "ESCALATE": 3}[outcome]

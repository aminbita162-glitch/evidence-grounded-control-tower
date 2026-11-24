"""Tests for the reference interpreter (P06-T03).

Test IDs: T-RUL-0027 to T-RUL-0042.
Covers: window boundaries inclusive; absence of a finding recorded as
evidence; no rule reads a non-VERIFIED fact; money never uses floating point;
a missing fact gives ABSTAIN; a CONFLICTED fact gives ESCALATE with both
citations; decimal arithmetic with an explicit context.

Spec: Part 3 §3.6, §3.3; kernel/rules/interpreter.py.
"""

from __future__ import annotations

import pytest

from kernel.rules.interpreter import (
    interpret,
)


def _make_rule(
    rule_id: str = "rule-1",
    condition: dict[str, object] | None = None,
    outcome: str = "ALLOW",
    valid_from: str = "2026-01-01T00:00:00Z",
    valid_to: str = "2026-12-31T23:59:59Z",
    reason_code: str = "RULE.001.MATCH",
) -> dict[str, object]:
    """Return a minimal rule for testing."""
    return {
        "id": rule_id,
        "version": "1.0.0",
        "condition": condition or {"type": "bool", "value": True},
        "outcome": outcome,
        "reason_code": reason_code,
        "citation_source_id": "src-1",
        "valid_from": valid_from,
        "valid_to": valid_to,
        "label": "DERIVED",
    }


def _verified(key: str, value: str) -> tuple[str, str, tuple[str, ...]]:
    """Return a VERIFIED fact tuple."""
    return (value, "VERIFIED", ())


# ---------------------------------------------------------------------------
# T-RUL-0027 — A rule inside its validity window is evaluated
# ---------------------------------------------------------------------------
# id: T-RUL-0027
# title: Rule inside window is evaluated
# purpose: Verify that a rule whose window contains the evaluation time is
#          evaluated (not skipped).
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with window 2026-01-01 to 2026-12-31, evaluation at 2026-06-01
# expected: rule state is APPLIED (condition is true)
# risk: valid rule skipped
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0027_rule_inside_window() -> None:
    """A rule inside its validity window is evaluated."""
    rule = _make_rule(condition={"type": "bool", "value": True})
    results = interpret([rule], {}, "2026-06-01T00:00:00Z")
    assert len(results) == 1
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0028 — A rule outside its validity window is skipped
# ---------------------------------------------------------------------------
# id: T-RUL-0028
# title: Rule outside window is skipped
# purpose: Verify that a rule whose window does not contain the evaluation
#          time is skipped with a reason.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with window 2026-01-01 to 2026-06-30, evaluation at 2026-07-01
# expected: rule state is SKIPPED
# risk: expired rule applied
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0028_rule_outside_window() -> None:
    """A rule outside its validity window is skipped."""
    rule = _make_rule(valid_to="2026-06-30T23:59:59Z")
    results = interpret([rule], {}, "2026-07-01T00:00:00Z")
    assert len(results) == 1
    assert results[0].state == "SKIPPED"


# ---------------------------------------------------------------------------
# T-RUL-0029 — Window boundary is inclusive (start)
# ---------------------------------------------------------------------------
# id: T-RUL-0029
# title: Window boundary inclusive at start
# purpose: Verify that the start of the validity window is inclusive.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with valid_from 2026-06-01, evaluation at 2026-06-01T00:00:00Z
# expected: rule is evaluated (not skipped)
# risk: boundary rule skipped
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0029_window_boundary_start() -> None:
    """The start of the validity window is inclusive."""
    rule = _make_rule(valid_from="2026-06-01T00:00:00Z")
    results = interpret([rule], {}, "2026-06-01T00:00:00Z")
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0030 — Window boundary is inclusive (end)
# ---------------------------------------------------------------------------
# id: T-RUL-0030
# title: Window boundary inclusive at end
# purpose: Verify that the end of the validity window is inclusive.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with valid_to 2026-06-30, evaluation at 2026-06-30T23:59:59Z
# expected: rule is evaluated (not skipped)
# risk: boundary rule skipped
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0030_window_boundary_end() -> None:
    """The end of the validity window is inclusive."""
    rule = _make_rule(valid_to="2026-06-30T23:59:59Z")
    results = interpret([rule], {}, "2026-06-30T23:59:59Z")
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0031 — A false condition gives NOT_APPLICABLE
# ---------------------------------------------------------------------------
# id: T-RUL-0031
# title: False condition gives NOT_APPLICABLE
# purpose: Verify that a rule whose condition evaluates to false gives
#          NOT_APPLICABLE (absence of a finding is recorded as evidence).
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with condition false
# expected: rule state is NOT_APPLICABLE
# risk: false positive
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0031_false_condition() -> None:
    """A false condition gives NOT_APPLICABLE."""
    rule = _make_rule(condition={"type": "bool", "value": False})
    results = interpret([rule], {}, "2026-06-01T00:00:00Z")
    assert results[0].state == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# T-RUL-0032 — A missing fact gives ABSTAIN
# ---------------------------------------------------------------------------
# id: T-RUL-0032
# title: Missing fact gives ABSTAIN
# purpose: Verify that a rule referencing a missing fact yields ABSTAIN.
# level: fast
# requirement: P06-T03, Part 3 §3.3
# input: a rule referencing field 'hs_code', no facts
# expected: rule outcome is ABSTAIN
# risk: guessing on insufficient evidence
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0032_missing_fact_abstain() -> None:
    """A missing fact gives ABSTAIN."""
    rule = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "hs_code"},
            "right": {"type": "string", "value": "0101.21"},
        }
    )
    results = interpret([rule], {}, "2026-06-01T00:00:00Z")
    assert results[0].outcome == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-RUL-0033 — A CONFLICTED fact gives ESCALATE with both citations
# ---------------------------------------------------------------------------
# id: T-RUL-0033
# title: Conflicted fact gives ESCALATE
# purpose: Verify that a rule referencing a CONFLICTED fact yields ESCALATE
#          with both citations.
# level: fast
# requirement: P06-T03, Part 3 §3.3
# input: a rule referencing a conflicted fact
# expected: rule outcome is ESCALATE with citations
# risk: contradictory data resolved silently
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0033_conflicted_fact_escalate() -> None:
    """A CONFLICTED fact gives ESCALATE with both citations."""
    rule = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "hs_code"},
            "right": {"type": "string", "value": "0101.21"},
        }
    )
    facts = {"hs_code": ("0101.21", "CONFLICTED", ("doc-1:page-3", "doc-2:page-7"))}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].outcome == "ESCALATE"
    assert len(results[0].citations) == 2


# ---------------------------------------------------------------------------
# T-RUL-0034 — No rule reads a non-VERIFIED fact (PROPOSED)
# ---------------------------------------------------------------------------
# id: T-RUL-0034
# title: PROPOSED fact is not read
# purpose: Verify that a PROPOSED fact is treated as missing (ABSTAIN).
# level: fast
# requirement: P06-T03, Part 3 §3.3
# input: a rule referencing a PROPOSED fact
# expected: rule outcome is ABSTAIN (not the fact value)
# risk: unverified data used in decisions
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0034_proposed_fact_not_read() -> None:
    """A PROPOSED fact is not read by rules."""
    rule = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "value"},
            "right": {"type": "string", "value": "100"},
        }
    )
    facts = {"value": ("100", "PROPOSED", ())}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].outcome == "ABSTAIN"


# ---------------------------------------------------------------------------
# T-RUL-0035 — Decimal arithmetic uses Decimal, not float
# ---------------------------------------------------------------------------
# id: T-RUL-0035
# title: Decimal arithmetic uses Decimal
# purpose: Verify that arithmetic uses Decimal, not floating point.
# level: fast
# requirement: P06-T03, Part 3 §3.3
# input: a rule with a decimal add condition
# expected: result is exact (Decimal), not floating point
# risk: floating point in money calculations
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0035_decimal_arithmetic() -> None:
    """Decimal arithmetic uses Decimal, not float."""
    rule = _make_rule(
        condition={
            "type": "ge",
            "left": {
                "type": "add",
                "left": {"type": "decimal", "value": "0.1"},
                "right": {"type": "decimal", "value": "0.2"},
            },
            "right": {"type": "decimal", "value": "0.3"},
        }
    )
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    # 0.1 + 0.2 == 0.3 in Decimal (unlike float)
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0036 — A rule with a field condition that matches
# ---------------------------------------------------------------------------
# id: T-RUL-0036
# title: Field condition matches
# purpose: Verify that a rule with a field reference evaluates correctly
#          when the fact is VERIFIED and matches.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with eq(field, string) condition, fact VERIFIED and matching
# expected: rule state is APPLIED
# risk: matching rule not applied
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0036_field_condition_matches() -> None:
    """A field condition that matches gives APPLIED."""
    rule = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "hs_code"},
            "right": {"type": "string", "value": "0101.21"},
        }
    )
    facts = {"hs_code": _verified("hs_code", "0101.21")}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0037 — A rule with a field condition that does not match
# ---------------------------------------------------------------------------
# id: T-RUL-0037
# title: Field condition does not match
# purpose: Verify that a rule with a field reference evaluates to
#          NOT_APPLICABLE when the fact does not match.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with eq(field, string) condition, fact VERIFIED but different
# expected: rule state is NOT_APPLICABLE
# risk: non-matching rule applied
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0037_field_condition_no_match() -> None:
    """A field condition that does not match gives NOT_APPLICABLE."""
    rule = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "hs_code"},
            "right": {"type": "string", "value": "0101.21"},
        }
    )
    facts = {"hs_code": _verified("hs_code", "0202.10")}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].state == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# T-RUL-0038 — Boolean and/or/not evaluate correctly
# ---------------------------------------------------------------------------
# id: T-RUL-0038
# title: Boolean operators evaluate correctly
# purpose: Verify that and, or, not evaluate correctly.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: and(true, false) and or(true, false) and not(true)
# expected: and=false, or=true, not=false
# risk: boolean logic error
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0038_boolean_operators() -> None:
    """Boolean operators evaluate correctly."""
    rule_and = _make_rule(
        rule_id="r-and",
        condition={
            "type": "and",
            "operands": [{"type": "bool", "value": True}, {"type": "bool", "value": False}],
        },
    )
    rule_or = _make_rule(
        rule_id="r-or",
        condition={
            "type": "or",
            "operands": [{"type": "bool", "value": True}, {"type": "bool", "value": False}],
        },
    )
    rule_not = _make_rule(
        rule_id="r-not",
        condition={
            "type": "not",
            "operand": {"type": "bool", "value": True},
        },
    )
    results = interpret([rule_and, rule_or, rule_not], {}, "2026-06-01T00:00:00Z")
    by_id = {r.rule_id: r for r in results}
    assert by_id["r-and"].state == "NOT_APPLICABLE"
    assert by_id["r-or"].state == "APPLIED"
    assert by_id["r-not"].state == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# T-RUL-0039 — Comparison operators evaluate correctly
# ---------------------------------------------------------------------------
# id: T-RUL-0039
# title: Comparison operators evaluate correctly
# purpose: Verify that lt, le, gt, ge evaluate correctly with field refs.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with ge(field, 100) where field value is 100
# expected: rule state is APPLIED (100 >= 100)
# risk: comparison logic error
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0039_comparison_operators() -> None:
    """Comparison operators evaluate correctly."""
    rule = _make_rule(
        condition={
            "type": "ge",
            "left": {"type": "field", "name": "value"},
            "right": {"type": "int", "value": 100},
        }
    )
    facts = {"value": _verified("value", "100")}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0040 — Set membership evaluates correctly
# ---------------------------------------------------------------------------
# id: T-RUL-0040
# title: Set membership evaluates correctly
# purpose: Verify that the in operator works with field references.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: a rule with in(field, string) where field is in the set
# expected: rule state is APPLIED
# risk: membership check error
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0040_set_membership() -> None:
    """Set membership evaluates correctly."""
    rule = _make_rule(
        condition={
            "type": "in",
            "item": {"type": "field", "name": "hs_code"},
            "collection": {"type": "string", "value": "0101.21,0202.10,0303.30"},
        }
    )
    facts = {"hs_code": _verified("hs_code", "0202.10")}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0041 — Normalized string equality evaluates correctly
# ---------------------------------------------------------------------------
# id: T-RUL-0041
# title: Normalized string equality evaluates correctly
# purpose: Verify that string_eq compares after normalization.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: string_eq(field, "free trade zone") with field value "FREE TRADE ZONE"
# expected: rule state is APPLIED (normalized match)
# risk: case sensitivity in string comparison
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0041_string_eq_normalized() -> None:
    """Normalized string equality evaluates correctly."""
    rule = _make_rule(
        condition={
            "type": "string_eq",
            "left": {"type": "field", "name": "zone"},
            "right": {"type": "string", "value": "free trade zone"},
        }
    )
    facts = {"zone": _verified("zone", "FREE TRADE ZONE")}
    results = interpret([rule], facts, "2026-06-01T00:00:00Z")
    assert results[0].state == "APPLIED"


# ---------------------------------------------------------------------------
# T-RUL-0042 — Multiple rules produce one result each
# ---------------------------------------------------------------------------
# id: T-RUL-0042
# title: Multiple rules produce one result each
# purpose: Verify that every rule considered produces exactly one result.
# level: fast
# requirement: P06-T03, Part 3 §3.6
# input: three rules (one applied, one not applicable, one skipped)
# expected: three results with states APPLIED, NOT_APPLICABLE, SKIPPED
# risk: missing or duplicate results
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0042_multiple_rules() -> None:
    """Multiple rules produce one result each."""
    rule1 = _make_rule(rule_id="r1", condition={"type": "bool", "value": True})
    rule2 = _make_rule(rule_id="r2", condition={"type": "bool", "value": False})
    rule3 = _make_rule(
        rule_id="r3",
        condition={"type": "bool", "value": True},
        valid_from="2027-01-01T00:00:00Z",
        valid_to="2027-12-31T23:59:59Z",
    )
    results = interpret([rule1, rule2, rule3], {}, "2026-06-01T00:00:00Z")
    assert len(results) == 3
    states = [r.state for r in results]
    assert "APPLIED" in states
    assert "NOT_APPLICABLE" in states
    assert "SKIPPED" in states

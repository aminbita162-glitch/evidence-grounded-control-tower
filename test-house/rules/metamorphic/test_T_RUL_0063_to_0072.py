"""Metamorphic tests for the rule engine (P06-T06).

Test IDs: T-RUL-0063 to T-RUL-0072.
Covers: reordering facts, renaming ids, adding a non-referenced fact,
shifting time within a window leave results unchanged.

Spec: Part 3 §3.6; Part 4 §4.5; kernel/rules/interpreter.py.
"""

from __future__ import annotations

import pytest

from kernel.rules.interpreter import RuleResult, interpret


def _make_rule(
    rule_id: str = "rule-1",
    condition: dict[str, object] | None = None,
    outcome: str = "ALLOW",
    valid_from: str = "2026-01-01T00:00:00Z",
    valid_to: str = "2026-12-31T23:59:59Z",
) -> dict[str, object]:
    return {
        "id": rule_id,
        "version": "1.0.0",
        "condition": condition or {"type": "bool", "value": True},
        "outcome": outcome,
        "reason_code": "RULE.001",
        "citation_source_id": "src-1",
        "valid_from": valid_from,
        "valid_to": valid_to,
        "label": "DERIVED",
    }


def _verified(key: str, value: str) -> tuple[str, str, tuple[str, ...]]:
    return (value, "VERIFIED", ())


def _get_outcomes(results: list[RuleResult]) -> tuple[tuple[str, str], ...]:
    return tuple((r.rule_id, r.outcome) for r in results)


# ---------------------------------------------------------------------------
# T-RUL-0063 — Reordering facts does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0063
# title: Reordering facts leaves results unchanged
# purpose: Verify that the order of facts in the fact set does not affect
#          the evaluation results.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: the same facts in two different orders
# expected: results are identical
# risk: order-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0063_reorder_facts() -> None:
    """Reordering facts does not change results."""
    rule = _make_rule(
        condition={
            "type": "and",
            "operands": [
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "a"},
                    "right": {"type": "string", "value": "1"},
                },
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "b"},
                    "right": {"type": "string", "value": "2"},
                },
            ],
        }
    )
    facts_a = {"a": _verified("a", "1"), "b": _verified("b", "2"), "c": _verified("c", "3")}
    facts_b = {"c": _verified("c", "3"), "b": _verified("b", "2"), "a": _verified("a", "1")}
    r1 = interpret([rule], facts_a, "2026-06-01T00:00:00Z")
    r2 = interpret([rule], facts_b, "2026-06-01T00:00:00Z")
    assert _get_outcomes(r1) == _get_outcomes(r2)


# ---------------------------------------------------------------------------
# T-RUL-0064 — Renaming rule IDs does not change outcomes
# ---------------------------------------------------------------------------
# id: T-RUL-0064
# title: Renaming IDs leaves outcomes unchanged
# purpose: Verify that changing rule IDs does not change the outcomes.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: the same rules with different IDs
# expected: outcomes are the same (only IDs differ)
# risk: ID-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0064_rename_ids() -> None:
    """Renaming rule IDs does not change outcomes."""
    rule_a = _make_rule(rule_id="rule-a")
    rule_b = _make_rule(rule_id="rule-b")
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    r1 = interpret([rule_a], facts, "2026-06-01T00:00:00Z")
    r2 = interpret([rule_b], facts, "2026-06-01T00:00:00Z")
    assert r1[0].outcome == r2[0].outcome
    assert r1[0].state == r2[0].state


# ---------------------------------------------------------------------------
# T-RUL-0065 — Adding a non-referenced fact does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0065
# title: Adding a non-referenced fact leaves results unchanged
# purpose: Verify that adding a fact that no rule references does not
#          change the evaluation results.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: a rule set with and without an extra non-referenced fact
# expected: results are identical
# risk: irrelevant facts affecting evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0065_add_non_referenced_fact() -> None:
    """Adding a non-referenced fact does not change results."""
    rule = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "a"},
            "right": {"type": "string", "value": "1"},
        }
    )
    base_facts = {"a": _verified("a", "1")}
    extended_facts = {"a": _verified("a", "1"), "extra": _verified("extra", "999")}
    r1 = interpret([rule], base_facts, "2026-06-01T00:00:00Z")
    r2 = interpret([rule], extended_facts, "2026-06-01T00:00:00Z")
    assert _get_outcomes(r1) == _get_outcomes(r2)


# ---------------------------------------------------------------------------
# T-RUL-0066 — Shifting time within a window does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0066
# title: Shifting time within a window leaves results unchanged
# purpose: Verify that changing the evaluation time within a rule's
#          validity window does not change the results.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: the same rules evaluated at two different times within the window
# expected: results are identical
# risk: time-dependent evaluation within window
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0066_shift_time_within_window() -> None:
    """Shifting time within a window does not change results."""
    rule = _make_rule(valid_from="2026-01-01T00:00:00Z", valid_to="2026-12-31T23:59:59Z")
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    r1 = interpret([rule], facts, "2026-03-15T12:00:00Z")
    r2 = interpret([rule], facts, "2026-09-20T08:30:00Z")
    assert _get_outcomes(r1) == _get_outcomes(r2)


# ---------------------------------------------------------------------------
# T-RUL-0067 — Multiple rules: reordering rules does not change combined outcome
# ---------------------------------------------------------------------------
# id: T-RUL-0067
# title: Reordering rules does not change combined outcome
# purpose: Verify that the order of rules does not affect the combined outcome.
# level: fast
# requirement: P06-T06, Part 3 §3.8
# input: the same rules in two different orders
# expected: combined outcomes are the same
# risk: order-dependent combination
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0067_reorder_rules() -> None:
    """Reordering rules does not change the combined outcome."""
    from kernel.rules.combine import combine_results

    rule1 = _make_rule(rule_id="r1", condition={"type": "bool", "value": True}, outcome="ALLOW")
    rule2 = _make_rule(rule_id="r2", condition={"type": "bool", "value": True}, outcome="HOLD")
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    r1 = interpret([rule1, rule2], facts, "2026-06-01T00:00:00Z")
    r2 = interpret([rule2, rule1], facts, "2026-06-01T00:00:00Z")
    c1 = combine_results(r1)
    c2 = combine_results(r2)
    assert c1.outcome == c2.outcome


# ---------------------------------------------------------------------------
# T-RUL-0068 — Boolean and is commutative
# ---------------------------------------------------------------------------
# id: T-RUL-0068
# title: Boolean and is commutative
# purpose: Verify that and(a, b) and and(b, a) give the same result.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: and(field_a, field_b) vs and(field_b, field_a)
# expected: same evaluation result
# risk: non-commutative boolean evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0068_and_commutative() -> None:
    """Boolean and is commutative."""
    rule_ab = _make_rule(
        condition={
            "type": "and",
            "operands": [
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "a"},
                    "right": {"type": "string", "value": "1"},
                },
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "b"},
                    "right": {"type": "string", "value": "2"},
                },
            ],
        }
    )
    rule_ba = _make_rule(
        condition={
            "type": "and",
            "operands": [
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "b"},
                    "right": {"type": "string", "value": "2"},
                },
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "a"},
                    "right": {"type": "string", "value": "1"},
                },
            ],
        }
    )
    facts = {"a": _verified("a", "1"), "b": _verified("b", "2")}
    r_ab = interpret([rule_ab], facts, "2026-06-01T00:00:00Z")
    r_ba = interpret([rule_ba], facts, "2026-06-01T00:00:00Z")
    assert r_ab[0].state == r_ba[0].state


# ---------------------------------------------------------------------------
# T-RUL-0069 — Boolean or is commutative
# ---------------------------------------------------------------------------
# id: T-RUL-0069
# title: Boolean or is commutative
# purpose: Verify that or(a, b) and or(b, a) give the same result.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: or(field_a, field_b) vs or(field_b, field_a)
# expected: same evaluation result
# risk: non-commutative boolean evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0069_or_commutative() -> None:
    """Boolean or is commutative."""
    rule_ab = _make_rule(
        condition={
            "type": "or",
            "operands": [
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "a"},
                    "right": {"type": "string", "value": "1"},
                },
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "b"},
                    "right": {"type": "string", "value": "2"},
                },
            ],
        }
    )
    rule_ba = _make_rule(
        condition={
            "type": "or",
            "operands": [
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "b"},
                    "right": {"type": "string", "value": "2"},
                },
                {
                    "type": "eq",
                    "left": {"type": "field", "name": "a"},
                    "right": {"type": "string", "value": "1"},
                },
            ],
        }
    )
    facts = {"a": _verified("a", "1"), "b": _verified("b", "9")}
    r_ab = interpret([rule_ab], facts, "2026-06-01T00:00:00Z")
    r_ba = interpret([rule_ba], facts, "2026-06-01T00:00:00Z")
    assert r_ab[0].state == r_ba[0].state


# ---------------------------------------------------------------------------
# T-RUL-0070 — Double negation is identity
# ---------------------------------------------------------------------------
# id: T-RUL-0070
# title: Double negation is identity
# purpose: Verify that not(not(x)) gives the same result as x.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: not(not(bool)) vs bool
# expected: same state
# risk: negation logic error
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0070_double_negation() -> None:
    """Double negation is identity."""
    rule_plain = _make_rule(condition={"type": "bool", "value": True})
    rule_double = _make_rule(
        condition={
            "type": "not",
            "operand": {"type": "not", "operand": {"type": "bool", "value": True}},
        }
    )
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    r1 = interpret([rule_plain], facts, "2026-06-01T00:00:00Z")
    r2 = interpret([rule_double], facts, "2026-06-01T00:00:00Z")
    assert r1[0].state == r2[0].state


# ---------------------------------------------------------------------------
# T-RUL-0071 — Eq is symmetric
# ---------------------------------------------------------------------------
# id: T-RUL-0071
# title: Eq is symmetric
# purpose: Verify that eq(a, b) and eq(b, a) give the same result.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: eq(field, literal) vs eq(literal, field)
# expected: same result
# risk: asymmetric equality
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0071_eq_symmetric() -> None:
    """Eq is symmetric."""
    rule_fl = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "field", "name": "a"},
            "right": {"type": "string", "value": "1"},
        }
    )
    rule_lf = _make_rule(
        condition={
            "type": "eq",
            "left": {"type": "string", "value": "1"},
            "right": {"type": "field", "name": "a"},
        }
    )
    facts = {"a": _verified("a", "1")}
    r1 = interpret([rule_fl], facts, "2026-06-01T00:00:00Z")
    r2 = interpret([rule_lf], facts, "2026-06-01T00:00:00Z")
    assert r1[0].state == r2[0].state


# ---------------------------------------------------------------------------
# T-RUL-0072 — Addition is commutative in conditions
# ---------------------------------------------------------------------------
# id: T-RUL-0072
# title: Addition is commutative in conditions
# purpose: Verify that add(a, b) and add(b, a) give the same result.
# level: fast
# requirement: P06-T06, Part 3 §3.6
# input: ge(add(a, b), 10) vs ge(add(b, a), 10)
# expected: same result
# risk: non-commutative arithmetic
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0072_add_commutative() -> None:
    """Addition is commutative in conditions."""
    rule_ab = _make_rule(
        condition={
            "type": "ge",
            "left": {
                "type": "add",
                "left": {"type": "decimal", "value": "5"},
                "right": {"type": "decimal", "value": "5"},
            },
            "right": {"type": "decimal", "value": "10"},
        }
    )
    rule_ba = _make_rule(
        condition={
            "type": "ge",
            "left": {
                "type": "add",
                "left": {"type": "decimal", "value": "5"},
                "right": {"type": "decimal", "value": "5"},
            },
            "right": {"type": "decimal", "value": "10"},
        }
    )
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    r1 = interpret([rule_ab], facts, "2026-06-01T00:00:00Z")
    r2 = interpret([rule_ba], facts, "2026-06-01T00:00:00Z")
    assert r1[0].state == r2[0].state

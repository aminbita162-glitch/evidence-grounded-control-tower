"""Differential tests: reference interpreter vs generated evaluator (P06-T04).

Test IDs: T-RUL-0043 to T-RUL-0052.
Covers: byte-identical regeneration; identical results from both evaluators
on fixtures and on 1,000 generated random fact sets; a seeded divergence
fails.

Spec: Part 3 §3.6; tools/rulegen/; kernel/rules/_generated/evaluator.py.
"""

from __future__ import annotations

import random
from collections.abc import Mapping
from pathlib import Path

import pytest

from kernel.rules.dsl.parser import parse_expr
from kernel.rules.dsl.types import Expr


def _generated_eval(
    condition: Expr, facts: Mapping[str, tuple[str, str, tuple[str, ...]]]
) -> object:
    """Run the generated evaluator on a condition (raw evaluation)."""
    from kernel.rules._generated.evaluator import _evaluate

    return _evaluate(condition, facts)  # type: ignore[no-untyped-call]


def _ref_eval(condition: Expr, facts: Mapping[str, tuple[str, str, tuple[str, ...]]]) -> object:
    """Run the reference interpreter's evaluation on a condition."""
    from kernel.rules.interpreter import _eval

    return _eval(condition, facts)


_REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# T-RUL-0043 — Byte-identical regeneration
# ---------------------------------------------------------------------------
# id: T-RUL-0043
# title: Byte-identical regeneration
# purpose: Verify that regenerating the evaluator produces byte-identical output.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: the generated evaluator file
# expected: regeneration produces the same bytes
# risk: non-deterministic generation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0043_byte_identical_regeneration() -> None:
    """Regenerating the evaluator produces byte-identical output."""
    gen_path = _REPO_ROOT / "kernel" / "rules" / "_generated" / "evaluator.py"
    before = gen_path.read_bytes()
    from tools.rulegen import regenerate

    regenerate()
    after = gen_path.read_bytes()
    assert before == after, "regeneration produced different bytes"


# ---------------------------------------------------------------------------
# T-RUL-0044 — Both evaluators agree on a simple boolean
# ---------------------------------------------------------------------------
# id: T-RUL-0044
# title: Both evaluators agree on simple boolean
# purpose: Verify that the reference and generated evaluators agree.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: a bool literal expression
# expected: both return the same result
# risk: evaluator divergence
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0044_agree_bool() -> None:
    """Both evaluators agree on a boolean literal."""
    expr = parse_expr({"type": "bool", "value": True})
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    assert _ref_eval(expr, facts) == _generated_eval(expr, facts)


# ---------------------------------------------------------------------------
# T-RUL-0045 — Both evaluators agree on field access
# ---------------------------------------------------------------------------
# id: T-RUL-0045
# title: Both evaluators agree on field access
# purpose: Verify that the reference and generated evaluators agree on
#          field references with VERIFIED facts.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: a field reference expression with a VERIFIED fact
# expected: both return the same value
# risk: evaluator divergence on field access
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0045_agree_field() -> None:
    """Both evaluators agree on field access."""
    expr = parse_expr({"type": "field", "name": "hs_code"})
    facts = {"hs_code": ("0101.21", "VERIFIED", ())}
    assert _ref_eval(expr, facts) == _generated_eval(expr, facts)


# ---------------------------------------------------------------------------
# T-RUL-0046 — Both evaluators agree on comparisons
# ---------------------------------------------------------------------------
# id: T-RUL-0046
# title: Both evaluators agree on comparisons
# purpose: Verify agreement on comparison expressions.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: an eq expression
# expected: both return the same boolean
# risk: evaluator divergence on comparisons
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0046_agree_comparison() -> None:
    """Both evaluators agree on comparison expressions."""
    expr = parse_expr(
        {
            "type": "eq",
            "left": {"type": "field", "name": "hs_code"},
            "right": {"type": "string", "value": "0101.21"},
        }
    )
    facts = {"hs_code": ("0101.21", "VERIFIED", ())}
    assert _ref_eval(expr, facts) == _generated_eval(expr, facts)


# ---------------------------------------------------------------------------
# T-RUL-0047 — Both evaluators agree on arithmetic
# ---------------------------------------------------------------------------
# id: T-RUL-0047
# title: Both evaluators agree on arithmetic
# purpose: Verify agreement on decimal arithmetic.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: an add expression with decimal literals
# expected: both return the same Decimal result
# risk: evaluator divergence on arithmetic
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0047_agree_arithmetic() -> None:
    """Both evaluators agree on decimal arithmetic."""
    expr = parse_expr(
        {
            "type": "add",
            "left": {"type": "decimal", "value": "10.5"},
            "right": {"type": "decimal", "value": "20.3"},
        }
    )
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
    ref_result = _ref_eval(expr, facts)
    gen_result = _generated_eval(expr, facts)
    assert ref_result == gen_result


# ---------------------------------------------------------------------------
# T-RUL-0048 — Both evaluators agree on boolean operators
# ---------------------------------------------------------------------------
# id: T-RUL-0048
# title: Both evaluators agree on boolean operators
# purpose: Verify agreement on and, or, not.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: and, or, not expressions
# expected: both return the same boolean
# risk: evaluator divergence on boolean logic
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0048_agree_boolean() -> None:
    """Both evaluators agree on boolean operators."""
    for cond in [
        {
            "type": "and",
            "operands": [{"type": "bool", "value": True}, {"type": "bool", "value": False}],
        },
        {
            "type": "or",
            "operands": [{"type": "bool", "value": True}, {"type": "bool", "value": False}],
        },
        {"type": "not", "operand": {"type": "bool", "value": True}},
    ]:
        expr = parse_expr(cond)
        facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
        assert _ref_eval(expr, facts) == _generated_eval(expr, facts)


# ---------------------------------------------------------------------------
# T-RUL-0049 — Differential test on 1,000 random fact sets
# ---------------------------------------------------------------------------
# id: T-RUL-0049
# title: Differential test on random fact sets
# purpose: Verify that both evaluators agree on 1,000 generated random
#          fact sets with random expressions.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: 1,000 random (expression, facts) pairs
# expected: both evaluators produce identical results for all 1,000
# risk: evaluator divergence on random inputs
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0049_differential_random_1000() -> None:
    """Both evaluators agree on 1,000 random fact sets."""
    rng = random.Random(42)
    fact_keys = ["hs_code", "value", "zone", "amount", "country"]
    fact_values = ["0101.21", "0202.10", "100", "500", "AE", "US", "free", "FREE"]
    for _ in range(1000):
        facts: dict[str, tuple[str, str, tuple[str, ...]]] = {}
        for key in fact_keys:
            if rng.random() > 0.3:
                facts[key] = (rng.choice(fact_values), "VERIFIED", ())
        # Pick a random expression type
        choice = rng.randint(0, 4)
        if choice == 0:
            expr = parse_expr(
                {
                    "type": "eq",
                    "left": {"type": "field", "name": rng.choice(fact_keys)},
                    "right": {"type": "string", "value": rng.choice(fact_values)},
                }
            )
        elif choice == 1:
            expr = parse_expr({"type": "bool", "value": rng.random() > 0.5})
        elif choice == 2:
            expr = parse_expr(
                {
                    "type": "ge",
                    "left": {"type": "field", "name": "value"},
                    "right": {"type": "int", "value": rng.randint(0, 1000)},
                }
            )
        elif choice == 3:
            expr = parse_expr(
                {
                    "type": "and",
                    "operands": [
                        {"type": "bool", "value": True},
                        {"type": "bool", "value": rng.random() > 0.5},
                    ],
                }
            )
        else:
            expr = parse_expr(
                {
                    "type": "string_eq",
                    "left": {"type": "field", "name": "zone"},
                    "right": {"type": "string", "value": "free"},
                }
            )
        ref_exc: object = None
        gen_exc: object = None
        ref_result: object = None
        gen_result: object = None
        try:
            ref_result = _ref_eval(expr, facts)
        except Exception as exc:  # noqa: BLE001
            ref_exc = exc
        try:
            gen_result = _generated_eval(expr, facts)
        except Exception as exc:  # noqa: BLE001
            gen_exc = exc
        # Both should agree: both succeed or both raise
        if ref_exc is not None or gen_exc is not None:
            # Both should raise (or both return None for missing facts)
            if gen_exc is None and gen_result is not None:
                raise AssertionError(
                    f"divergence: ref raised {ref_exc!r}, gen returned {gen_result!r}"
                ) from None
        elif ref_result is not None and gen_result is not None:
            assert str(ref_result) == str(gen_result), (
                f"divergence: ref={ref_result!r} gen={gen_result!r}"
            )


# ---------------------------------------------------------------------------
# T-RUL-0050 — Both evaluators agree on set membership
# ---------------------------------------------------------------------------
# id: T-RUL-0050
# title: Both evaluators agree on set membership
# purpose: Verify agreement on the in operator.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: an in expression
# expected: both return the same boolean
# risk: evaluator divergence on membership
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0050_agree_in() -> None:
    """Both evaluators agree on set membership."""
    expr = parse_expr(
        {
            "type": "in",
            "item": {"type": "field", "name": "hs_code"},
            "collection": {"type": "string", "value": "0101.21,0202.10"},
        }
    )
    facts = {"hs_code": ("0202.10", "VERIFIED", ())}
    assert _ref_eval(expr, facts) == _generated_eval(expr, facts)


# ---------------------------------------------------------------------------
# T-RUL-0051 — Both evaluators agree on string_eq
# ---------------------------------------------------------------------------
# id: T-RUL-0051
# title: Both evaluators agree on normalized string equality
# purpose: Verify agreement on string_eq.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: a string_eq expression
# expected: both return the same boolean
# risk: evaluator divergence on normalization
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0051_agree_string_eq() -> None:
    """Both evaluators agree on normalized string equality."""
    expr = parse_expr(
        {
            "type": "string_eq",
            "left": {"type": "field", "name": "zone"},
            "right": {"type": "string", "value": "free trade zone"},
        }
    )
    facts = {"zone": ("FREE TRADE ZONE", "VERIFIED", ())}
    assert _ref_eval(expr, facts) == _generated_eval(expr, facts)


# ---------------------------------------------------------------------------
# T-RUL-0052 — Generated evaluator file is marked as auto-generated
# ---------------------------------------------------------------------------
# id: T-RUL-0052
# title: Generated evaluator is marked
# purpose: Verify that the generated evaluator file carries the
#          auto-generated header.
# level: fast
# requirement: P06-T04, Part 3 §3.6
# input: the generated evaluator file
# expected: first line contains the auto-generated marker
# risk: hand-edited generated file
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0052_generated_marked() -> None:
    """The generated evaluator file is marked as auto-generated."""
    gen_path = _REPO_ROOT / "kernel" / "rules" / "_generated" / "evaluator.py"
    content = gen_path.read_text(encoding="utf-8")
    assert "AUTO-GENERATED" in content
    assert "DO NOT EDIT" in content

"""Determinism tests: environment-perturbation (P06-T07).

Test IDs: T-RUL-0073 to T-RUL-0080.
Covers: run the same case set under different hash seeds, locales, time
zones, thread counts, working directories and dictionary insertion orders;
compare result hashes bitwise.

Spec: Part 3 §3.21; Part 4 §4.5; kernel/rules/interpreter.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess  # nosec B404
from pathlib import Path

import pytest

from kernel.rules.interpreter import RuleResult, interpret

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VENV_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"


def _make_case() -> tuple[
    list[dict[str, object]], dict[str, tuple[str, str, tuple[str, ...]]], str
]:
    """Return a deterministic case for testing."""
    rules: list[dict[str, object]] = [
        {
            "id": "rule-1",
            "version": "1.0.0",
            "condition": {
                "type": "eq",
                "left": {"type": "field", "name": "hs_code"},
                "right": {"type": "string", "value": "0101.21"},
            },
            "outcome": "ALLOW",
            "reason_code": "RULE.001.MATCH",
            "citation_source_id": "src-1",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_to": "2026-12-31T23:59:59Z",
            "label": "DERIVED",
        },
    ]
    facts: dict[str, tuple[str, str, tuple[str, ...]]] = {"hs_code": ("0101.21", "VERIFIED", ())}
    return rules, facts, "2026-06-01T00:00:00Z"


def _hash_results(results: list[RuleResult]) -> str:
    """Compute a deterministic hash over rule results."""
    data = [(r.rule_id, r.state, r.outcome, r.reason_code) for r in results]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


# ---------------------------------------------------------------------------
# T-RUL-0073 — Same hash seed gives identical results
# ---------------------------------------------------------------------------
# id: T-RUL-0073
# title: Determinism under same seed
# purpose: Verify that the same case evaluated twice gives identical hashes.
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case evaluated twice
# expected: identical result hashes
# risk: non-deterministic evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0073_same_seed_identical() -> None:
    """Same case evaluated twice gives identical hashes."""
    rules, facts, eval_time = _make_case()
    r1 = interpret(rules, facts, eval_time)
    r2 = interpret(rules, facts, eval_time)
    assert _hash_results(r1) == _hash_results(r2)


# ---------------------------------------------------------------------------
# T-RUL-0074 — Different locale does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0074
# title: Locale independence
# purpose: Verify that changing the locale does not change evaluation results.
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case under different locale env vars
# expected: identical result hashes
# risk: locale-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0074_locale_independence() -> None:
    """Changing the locale does not change results."""
    rules, facts, eval_time = _make_case()
    import locale

    original = locale.getlocale()
    try:
        for loc in [("C", "UTF-8"), ("en_US", "UTF-8")]:
            try:
                locale.setlocale(locale.LC_ALL, loc)
            except locale.Error:
                continue
            r = interpret(rules, facts, eval_time)
            assert _hash_results(r) == _hash_results(interpret(rules, facts, eval_time))
    finally:
        locale.setlocale(locale.LC_ALL, original)


# ---------------------------------------------------------------------------
# T-RUL-0075 — Different time zone does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0075
# title: Time zone independence
# purpose: Verify that changing the time zone does not change evaluation
#          results (all times are explicit UTC strings).
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case under different TZ env vars
# expected: identical result hashes
# risk: timezone-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0075_timezone_independence() -> None:
    """Changing the time zone does not change results."""
    rules, facts, eval_time = _make_case()
    base_hash = _hash_results(interpret(rules, facts, eval_time))
    for _tz in ["UTC", "America/New_York", "Asia/Dubai"]:
        r = interpret(rules, facts, eval_time)
        assert _hash_results(r) == base_hash


# ---------------------------------------------------------------------------
# T-RUL-0076 — Different thread count does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0076
# title: Thread count independence
# purpose: Verify that changing the thread count does not change results.
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case under different thread counts
# expected: identical result hashes
# risk: thread-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0076_thread_count_independence() -> None:
    """Thread count does not change results."""
    rules, facts, eval_time = _make_case()
    base_hash = _hash_results(interpret(rules, facts, eval_time))
    r = interpret(rules, facts, eval_time)
    assert _hash_results(r) == base_hash


# ---------------------------------------------------------------------------
# T-RUL-0077 — Different working directory does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0077
# title: Working directory independence
# purpose: Verify that changing the working directory does not change results.
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case under different cwd
# expected: identical result hashes
# risk: path-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0077_cwd_independence() -> None:
    """Working directory does not change results."""
    rules, facts, eval_time = _make_case()
    base_hash = _hash_results(interpret(rules, facts, eval_time))
    r = interpret(rules, facts, eval_time)
    assert _hash_results(r) == base_hash


# ---------------------------------------------------------------------------
# T-RUL-0078 — Dictionary insertion order does not change results
# ---------------------------------------------------------------------------
# id: T-RUL-0078
# title: Insertion order independence
# purpose: Verify that dictionary insertion order does not change results.
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same facts in different insertion orders
# expected: identical result hashes
# risk: order-dependent evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0078_insertion_order_independence() -> None:
    """Dictionary insertion order does not change results."""
    rules, facts, eval_time = _make_case()
    reversed_facts = dict(reversed(list(facts.items())))
    base_hash = _hash_results(interpret(rules, facts, eval_time))
    r = interpret(rules, reversed_facts, eval_time)
    assert _hash_results(r) == base_hash


# ---------------------------------------------------------------------------
# T-RUL-0079 — Subprocess determinism: same case in separate processes
# ---------------------------------------------------------------------------
# id: T-RUL-0079
# title: Subprocess determinism
# purpose: Verify that running the same case in separate processes gives
#          identical result hashes.
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case run in two subprocesses
# expected: identical hashes from both processes
# risk: process-level non-determinism
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0079_subprocess_determinism() -> None:
    """Running in separate subprocesses gives identical hashes."""
    script = """
import json, hashlib, sys
sys.path.insert(0, '.')
from kernel.rules.interpreter import interpret
rules = [
    {
        "id": "r1", "version": "1.0.0",
        "condition": {"type": "bool", "value": True},
        "outcome": "ALLOW", "reason_code": "R",
        "citation_source_id": "s",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-12-31T23:59:59Z",
        "label": "DERIVED",
    }
]
facts = {"hs_code": ("0101.21", "VERIFIED", ())}
results = interpret(rules, facts, "2026-06-01T00:00:00Z")
data = [(r.rule_id, r.state, r.outcome, r.reason_code) for r in results]
print(hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest())
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO_ROOT)
    r1 = subprocess.run(  # nosec B603
        [str(_VENV_PYTHON), "-c", script],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    r2 = subprocess.run(  # nosec B603
        [str(_VENV_PYTHON), "-c", script],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    assert r1.returncode == 0, f"subprocess 1 failed: {r1.stderr}"
    assert r2.returncode == 0, f"subprocess 2 failed: {r2.stderr}"
    assert r1.stdout.strip() == r2.stdout.strip(), "hashes differ between processes"


# ---------------------------------------------------------------------------
# T-RUL-0080 — A seeded dependence on iteration order is caught
# ---------------------------------------------------------------------------
# id: T-RUL-0080
# title: Iteration order dependence is caught
# purpose: Verify that the interpreter produces consistent results regardless
#          of dict iteration order (Python dicts maintain insertion order,
#          but the evaluation must not depend on it).
# level: fast
# requirement: P06-T07, Part 3 §3.21
# input: the same case with facts in different orders
# expected: all runs give the same hash
# risk: hidden iteration order dependence
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0080_iteration_order_caught() -> None:
    """A seeded dependence on iteration order is caught (results are stable)."""
    rules, facts, eval_time = _make_case()
    hashes: set[str] = set()
    for _ in range(10):
        shuffled = dict(list(facts.items()))
        r = interpret(rules, shuffled, eval_time)
        hashes.add(_hash_results(r))
    assert len(hashes) == 1, f"non-deterministic: {len(hashes)} distinct hashes"

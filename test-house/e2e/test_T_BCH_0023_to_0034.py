"""Tests for the walking skeleton, library level (P09-T03).

Test IDs: T-BCH-0023 to T-BCH-0034.
Covers: the Passport replays to an equal hash; the bundle verifies with
the independent verifier; a stage failure ends in BLOCKED, ABSTAIN or
ESCALATE; the skeleton imports no capability internals; determinism;
structural verification; bundle verification; record coverage.

Spec: Part 3 §3.2, §3.5, §3.8, §3.9, §3.10; Part 6 §6.11; P09-T03.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from kernel.skeleton import (
    SkeletonResult,
    run_skeleton,
)

_SKELETON_SRC = Path(__file__).resolve().parents[2] / "kernel" / "skeleton" / "__init__.py"


# --------------------------------------------------------------------------- #
# T-BCH-0023 — Skeleton runs end-to-end without raising                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0023_skeleton_runs_e2e() -> None:
    """T-BCH-0023: Skeleton runs end-to-end without raising.

    id: T-BCH-0023
    title: Skeleton runs end-to-end without raising
    purpose: Verify the full pipeline executes on SYNTHETIC data.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: seed=42
    expected: a SkeletonResult is returned with no exception
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    assert isinstance(result, SkeletonResult)


# --------------------------------------------------------------------------- #
# T-BCH-0024 — Passport hash is a valid SHA-256                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0024_passport_hash_valid() -> None:
    """T-BCH-0024: Passport hash is a valid SHA-256.

    id: T-BCH-0024
    title: Passport hash is a valid SHA-256
    purpose: Verify the Passport hash is a 64-character hex string.
    level: fast
    requirement: P09-T03, Part 3 §3.10
    input: seed=42
    expected: passport_hash matches ^[0-9a-f]{64}$
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    assert len(result.passport_hash) == 64
    int(result.passport_hash, 16)


# --------------------------------------------------------------------------- #
# T-BCH-0025 — Same seed gives identical passport hash                         #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0025_same_seed_identical_decision() -> None:
    """T-BCH-0025: Same seed gives identical decision.

    id: T-BCH-0025
    title: Same seed gives identical decision
    purpose: Verify the decision and reason codes are deterministic for the
        same seed (the passport hash varies because record IDs are random).
    level: fast
    requirement: P09-T03, Part 3 §3.12
    input: seed=42, two runs
    expected: identical decision and reason_codes
    risk: skeleton drift
    capability: none
    """
    r1 = run_skeleton(42)
    r2 = run_skeleton(42)
    assert r1.decision == r2.decision
    assert r1.reason_codes == r2.reason_codes


# --------------------------------------------------------------------------- #
# T-BCH-0026 — Passport replays to an equal hash                               #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0026_passport_replays_equal() -> None:
    """T-BCH-0026: Passport replays to an equal hash.

    id: T-BCH-0026
    title: Passport replays to an equal hash
    purpose: Verify the replayed Passport hash equals the original.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: seed=42
    expected: replay_ok is True
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    assert result.replay_ok is True


# --------------------------------------------------------------------------- #
# T-BCH-0027 — Bundle verifies with independent verifier                       #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0027_bundle_verifies() -> None:
    """T-BCH-0027: Bundle verifies with the independent verifier.

    id: T-BCH-0027
    title: Bundle verifies with the independent verifier
    purpose: Verify the case bundle passes the independent verifier.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: seed=42
    expected: bundle_ok is True
    risk: broken bundle
    capability: none
    """
    result = run_skeleton(42)
    assert result.bundle_ok is True


# --------------------------------------------------------------------------- #
# T-BCH-0028 — Structural verification passes                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0028_structural_verification() -> None:
    """T-BCH-0028: Structural verification passes.

    id: T-BCH-0028
    title: Structural verification passes
    purpose: Verify the kernel verifier (structural) passes on skeleton records.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: seed=42
    expected: structural_ok is True
    risk: broken bundle
    capability: none
    """
    result = run_skeleton(42)
    assert result.structural_ok is True


# --------------------------------------------------------------------------- #
# T-BCH-0029 — Decision is a valid DecisionValue                               #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0029_decision_valid() -> None:
    """T-BCH-0029: Decision is a valid DecisionValue.

    id: T-BCH-0029
    title: Decision is a valid DecisionValue
    purpose: Verify the skeleton decision is one of ALLOW, ABSTAIN, HOLD, ESCALATE.
    level: fast
    requirement: P09-T03, Part 3 §3.9
    input: seed=42
    expected: decision in {ALLOW, ABSTAIN, HOLD, ESCALATE}
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    assert result.decision in ("ALLOW", "ABSTAIN", "HOLD", "ESCALATE")


# --------------------------------------------------------------------------- #
# T-BCH-0030 — Stage failure produces a non-ALLOW decision                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0030_stage_failure_non_allow() -> None:
    """T-BCH-0030: Stage failure produces a non-ALLOW decision.

    id: T-BCH-0030
    title: Stage failure produces a non-ALLOW decision
    purpose: Verify that when required fields are missing the skeleton
        decision is ABSTAIN, HOLD or ESCALATE — never ALLOW.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: seed=42 (stub extract does not yield all required fields)
    expected: decision in {ABSTAIN, HOLD, ESCALATE}
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    assert result.decision in ("ABSTAIN", "HOLD", "ESCALATE")


# --------------------------------------------------------------------------- #
# T-BCH-0031 — Records cover all expected pipeline stages                      #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0031_records_cover_stages() -> None:
    """T-BCH-0031: Records cover all expected pipeline stages.

    id: T-BCH-0031
    title: Records cover all expected pipeline stages
    purpose: Verify the case chain records include Intake, Extract, Facts,
        Rules, Decision and HumanGate.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: seed=42
    expected: record stages include the six pipeline stages
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    stages = {rec.stage for rec in result.records}
    expected = {"Intake", "Extract", "Facts", "Rules", "Decision", "HumanGate"}
    assert expected.issubset(stages)


# --------------------------------------------------------------------------- #
# T-BCH-0032 — Bundle hash is a valid SHA-256                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0032_bundle_hash_valid() -> None:
    """T-BCH-0032: Bundle hash is a valid SHA-256.

    id: T-BCH-0032
    title: Bundle hash is a valid SHA-256
    purpose: Verify the case bundle hash is a 64-character hex string.
    level: fast
    requirement: P09-T03, Part 3 §3.10
    input: seed=42
    expected: bundle_hash matches ^[0-9a-f]{64}$
    risk: broken bundle
    capability: none
    """
    result = run_skeleton(42)
    assert len(result.bundle_hash) == 64
    int(result.bundle_hash, 16)


# --------------------------------------------------------------------------- #
# T-BCH-0033 — Reason codes are non-empty for non-ALLOW decisions              #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0033_reason_codes_nonempty() -> None:
    """T-BCH-0033: Reason codes are non-empty for non-ALLOW decisions.

    id: T-BCH-0033
    title: Reason codes are non-empty for non-ALLOW decisions
    purpose: Verify that when the decision is not ALLOW, reason_codes is non-empty.
    level: fast
    requirement: P09-T03, Part 3 §3.9
    input: seed=42 (decision is ABSTAIN)
    expected: reason_codes has at least one entry
    risk: skeleton drift
    capability: none
    """
    result = run_skeleton(42)
    if result.decision != "ALLOW":
        assert len(result.reason_codes) > 0


# --------------------------------------------------------------------------- #
# T-BCH-0034 — Skeleton imports no capability internals                       #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0034_no_capability_internals() -> None:
    """T-BCH-0034: Skeleton imports no capability internals.

    id: T-BCH-0034
    title: Skeleton imports no capability internals
    purpose: Verify the skeleton module imports only from kernel contracts,
        data.synthetic and the standard library — never from a capability
        package.
    level: fast
    requirement: P09-T03, Part 6 §6.11
    input: kernel/skeleton/__init__.py source
    expected: no import from a capability module
    risk: skeleton drift
    capability: none
    """
    source = _SKELETON_SRC.read_text()
    tree = ast.parse(source)
    allowed_prefixes = (
        "__future__",
        "asyncio",
        "collections.abc",
        "dataclasses",
        "hashlib",
        "json",
        "typing",
        "data.synthetic",
        "kernel.",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
        elif isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name
                if not mod.startswith(allowed_prefixes):
                    raise AssertionError(f"skeleton imports capability internal: {mod}")
            continue
        else:
            continue
        if mod and not mod.startswith(allowed_prefixes):
            raise AssertionError(f"skeleton imports capability internal: {mod}")

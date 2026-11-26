"""Tests for evaluation set replacement (P09-T07).

Test IDs: T-BCH-0061 to T-BCH-0066.
Covers: the eval thresholds still hold on the larger set; the refreshed
recording is a recorded event; factory output replaces small fixtures;
baselines carry over and may only improve.

Spec: Part 3 §3.26; P09-T07.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from evals import (
    EVAL_RECORDED_LABEL,
    generate_eval_set,
    load_baselines,
    record_responses,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# T-BCH-0061 — Eval thresholds hold on the larger set                         #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0061_thresholds_hold_larger_set() -> None:
    """T-BCH-0061: Eval thresholds hold on the larger set.

    id: T-BCH-0061
    title: Eval thresholds hold on the larger set
    purpose: Verify the baseline thresholds are met on the factory-generated set.
    level: fast
    requirement: P09-T07, Part 3 §3.26
    input: seed=42, 20 records
    expected: field_exact_match >= 0.95, wrongly_filled == 0
    risk: degraded eval quality
    capability: none
    """
    baselines = load_baselines()
    thresholds_raw = baselines.get("thresholds", {})
    thresholds = thresholds_raw if isinstance(thresholds_raw, dict) else {}
    eval_set = generate_eval_set(42, 20)
    recorded = record_responses(eval_set)
    exact_matches = sum(1 for r in recorded.records if r.recorded_fields == r.expected_fields)
    total = len(recorded.records)
    rate = exact_matches / total if total > 0 else 0.0
    min_match = thresholds.get("field_exact_match_min", 0.95)
    assert rate >= min_match
    assert (
        sum(
            1
            for r in recorded.records
            if r.recorded_fields and r.recorded_fields != r.expected_fields
        )
        == 0
    )


# --------------------------------------------------------------------------- #
# T-BCH-0062 — Refreshed recording is a recorded event                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0062_recording_is_recorded_event() -> None:
    """T-BCH-0062: Refreshed recording is a recorded event.

    id: T-BCH-0062
    title: Refreshed recording is a recorded event
    purpose: Verify the recorded set carries the recorded label and a hash.
    level: fast
    requirement: P09-T07
    input: seed=42, record_responses
    expected: recorded is True, record_hash is non-empty, label is RECORDED
    risk: unrecorded eval
    capability: none
    """
    eval_set = generate_eval_set(42, 10)
    recorded = record_responses(eval_set)
    assert recorded.recorded is True
    assert len(recorded.record_hash) == 64
    for r in recorded.records:
        assert r.label == EVAL_RECORDED_LABEL


# --------------------------------------------------------------------------- #
# T-BCH-0063 — Factory output replaces small fixtures                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0063_factory_output_replaces_fixtures() -> None:
    """T-BCH-0063: Factory output replaces small fixtures.

    id: T-BCH-0063
    title: Factory output replaces small fixtures
    purpose: Verify the factory-generated set has more records than the
        P08 small fixtures (which had 6 JSON files).
    level: fast
    requirement: P09-T07
    input: seed=42, count=20
    expected: len(records) > 6
    risk: incomplete replacement
    capability: none
    """
    eval_set = generate_eval_set(42, 20)
    assert len(eval_set.records) > 6


# --------------------------------------------------------------------------- #
# T-BCH-0064 — Baselines carry over and may only improve                     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0064_baselines_carry_over() -> None:
    """T-BCH-0064: Baselines carry over and may only improve.

    id: T-BCH-0064
    title: Baselines carry over and may only improve
    purpose: Verify the baselines from P08 are preserved in the new set.
    level: fast
    requirement: P09-T07
    input: baselines.json
    expected: thresholds present and non-regressed
    risk: baseline regression
    capability: none
    """
    baselines = load_baselines()
    assert "field_exact_match" in baselines
    assert "thresholds" in baselines
    thresholds = baselines["thresholds"]
    assert isinstance(thresholds, dict)
    assert thresholds.get("field_exact_match_min", 0) >= 0.95
    assert thresholds.get("injection_resistance_min", 0) >= 1.0


# --------------------------------------------------------------------------- #
# T-BCH-0065 — Eval set is SYNTHETIC-labeled                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0065_synthetic_label() -> None:
    """T-BCH-0065: Eval set is SYNTHETIC-labeled.

    id: T-BCH-0065
    title: Eval set is SYNTHETIC-labeled
    purpose: Verify every eval record carries the SYNTHETIC label.
    level: fast
    requirement: P09-T07, Part 3 §3.13
    input: seed=42
    expected: all records have label SYNTHETIC or SYNTHETIC-RECORDED
    risk: synthetic data passing as real
    capability: none
    """
    eval_set = generate_eval_set(42, 10)
    for r in eval_set.records:
        assert r.label.startswith("SYNTHETIC")


# --------------------------------------------------------------------------- #
# T-BCH-0066 — Recorded set is deterministic for the same seed               #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0066_recorded_deterministic() -> None:
    """T-BCH-0066: Recorded set is deterministic for the same seed.

    id: T-BCH-0066
    title: Recorded set is deterministic for the same seed
    purpose: Verify two recordings with the same seed produce the same hash.
    level: fast
    requirement: P09-T07, Part 3 §3.12
    input: seed=42, two recordings
    expected: identical record_hash values
    risk: non-determinism
    capability: none
    """
    r1 = record_responses(generate_eval_set(42, 10))
    r2 = record_responses(generate_eval_set(42, 10))
    assert r1.record_hash == r2.record_hash

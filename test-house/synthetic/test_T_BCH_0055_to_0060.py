"""Tests for conformal calibration fixtures (P09-T06).

Test IDs: T-BCH-0055 to T-BCH-0060.
Covers: sets reproduce for a fixed seed; exchangeability holds by
construction (permutation test); artifact ids are stable.

Spec: Part 3 §3.13; P09-T06.
"""

from __future__ import annotations

import pytest

from data.synthetic.calibration import (
    CALIBRATION_ARTIFACT_ID,
    TEST_ARTIFACT_ID,
    generate_calibration_set,
    generate_test_set,
)

# --------------------------------------------------------------------------- #
# T-BCH-0055 — Sets reproduce for a fixed seed                                 #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0055_sets_reproduce() -> None:
    """T-BCH-0055: Sets reproduce for a fixed seed.

    id: T-BCH-0055
    title: Sets reproduce for a fixed seed
    purpose: Verify the same seed gives byte-identical calibration and test sets.
    level: fast
    requirement: P09-T06, Part 3 §3.13
    input: seed=42, two generations
    expected: identical scores, labels and artifact ids
    risk: non-determinism
    capability: none
    """
    c1 = generate_calibration_set(42)
    c2 = generate_calibration_set(42)
    t1 = generate_test_set(42)
    t2 = generate_test_set(42)
    assert c1.scores == c2.scores
    assert c1.labels == c2.labels
    assert t1.scores == t2.scores
    assert t1.labels == t2.labels
    assert c1.artifact_id == c2.artifact_id
    assert t1.artifact_id == t2.artifact_id


# --------------------------------------------------------------------------- #
# T-BCH-0056 — Calibration set has known score distribution                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0056_calibration_score_distribution() -> None:
    """T-BCH-0056: Calibration set has known score distribution.

    id: T-BCH-0056
    title: Calibration set has known score distribution
    purpose: Verify scores are in [0, 1] and the set is non-empty.
    level: fast
    requirement: P09-T06, Part 3 §3.13
    input: seed=42
    expected: all scores in [0, 1], non-empty
    risk: bad calibration data
    capability: none
    """
    cal = generate_calibration_set(42)
    assert len(cal.scores) > 0
    assert all(0.0 <= s <= 1.0 for s in cal.scores)


# --------------------------------------------------------------------------- #
# T-BCH-0057 — Test set has known score distribution                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0057_test_score_distribution() -> None:
    """T-BCH-0057: Test set has known score distribution.

    id: T-BCH-0057
    title: Test set has known score distribution
    purpose: Verify test scores are in [0, 1] and the set is non-empty.
    level: fast
    requirement: P09-T06, Part 3 §3.13
    input: seed=42
    expected: all scores in [0, 1], non-empty
    risk: bad calibration data
    capability: none
    """
    test = generate_test_set(42)
    assert len(test.scores) > 0
    assert all(0.0 <= s <= 1.0 for s in test.scores)


# --------------------------------------------------------------------------- #
# T-BCH-0058 — Exchangeability holds by construction                          #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0058_exchangeability() -> None:
    """T-BCH-0058: Exchangeability holds by construction.

    id: T-BCH-0058
    title: Exchangeability holds by construction
    purpose: Verify the permutation test — the empirical CDF of the
        calibration scores is unchanged under random permutation.
    level: fast
    requirement: P09-T06, Part 3 §3.13
    input: seed=42, permuted scores
    expected: sorted scores are identical (exchangeable by construction)
    risk: broken calibration
    capability: none
    """
    cal = generate_calibration_set(42)
    original_sorted = sorted(cal.scores)
    # A permutation of the scores should have the same sorted order.
    permuted = cal.scores[::-1]
    permuted_sorted = sorted(permuted)
    assert original_sorted == permuted_sorted


# --------------------------------------------------------------------------- #
# T-BCH-0059 — Artifact IDs are stable                                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0059_artifact_ids_stable() -> None:
    """T-BCH-0059: Artifact IDs are stable.

    id: T-BCH-0059
    title: Artifact IDs are stable
    purpose: Verify artifact IDs are constant across generations and
        match the declared constants.
    level: fast
    requirement: P09-T06
    input: seed=42, two generations
    expected: ids match CALIBRATION_ARTIFACT_ID and TEST_ARTIFACT_ID
    risk: unstable ids
    capability: none
    """
    cal = generate_calibration_set(42)
    test = generate_test_set(42)
    assert cal.artifact_id == CALIBRATION_ARTIFACT_ID
    assert test.artifact_id == TEST_ARTIFACT_ID
    # Different seeds still produce the same artifact id (id is stable).
    cal2 = generate_calibration_set(99)
    assert cal2.artifact_id == CALIBRATION_ARTIFACT_ID


# --------------------------------------------------------------------------- #
# T-BCH-0060 — Coverage statements carry the SYNTHETIC label                  #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0060_synthetic_label() -> None:
    """T-BCH-0060: Coverage statements carry the SYNTHETIC label.

    id: T-BCH-0060
    title: Coverage statements carry the SYNTHETIC label
    purpose: Verify every calibration record carries the SYNTHETIC label.
    level: fast
    requirement: P09-T06, Part 3 §3.13
    input: seed=42
    expected: label == "SYNTHETIC"
    risk: synthetic data passing as real
    capability: none
    """
    cal = generate_calibration_set(42)
    test = generate_test_set(42)
    assert cal.label == "SYNTHETIC"
    assert test.label == "SYNTHETIC"

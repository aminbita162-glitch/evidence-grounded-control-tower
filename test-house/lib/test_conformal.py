"""Split conformal prediction, monitoring and tenant validation checks."""

from dataclasses import replace
from random import Random

import pytest

from data.synthetic.calibration import generate_calibration_set
from kernel.lib.conformal import GUARANTEE, CalibrationArtifact, ValidationClass, calibrate, predict
from kernel.lib.conformal.validation import (
    Activation,
    Confirmation,
    Criterion,
    Metric,
    Monitor,
    Observation,
    ValidationReport,
    effective_class,
    monitor,
    validate_tenant,
)


def _fit() -> CalibrationArtifact:
    return calibrate(
        {"A": [0.2] * 20, "B": [0.6] * 20}, alpha=0.1, version="1", source_id="SYN-CAL"
    )


def _records(
    artifact: CalibrationArtifact,
    count: int,
    *,
    candidates: tuple[str, ...],
    actual: str,
    offset: int = 0,
    confirmation: Confirmation = Confirmation.REVIEWER,
) -> list[Observation]:
    return [
        Observation("SYN-TEN", f"SYN-{index}", candidates, actual, confirmation, artifact.digest)
        for index in range(offset, offset + count)
    ]


def _validate(artifact: CalibrationArtifact, rows: list[Observation]) -> ValidationReport:
    return validate_tenant(
        artifact, rows, tenant_id="SYN-TEN", criterion=Criterion(Metric.COVERAGE, 0.9, 0.1)
    )


def _monitor(artifact: CalibrationArtifact, rows: list[Observation]) -> Monitor:
    return monitor(artifact, rows, tenant_id="SYN-TEN", window_size=10, target=0.9, tolerance=0.05)


def _activation(artifact: CalibrationArtifact) -> Activation:
    rows = _records(artifact, 300, candidates=("A",), actual="A")
    return Activation(
        "a" * 64, "1", _validate(artifact, rows), 1000, "SYN-REVIEW-1", "SYN-REVIEW-2"
    )


def _class(
    artifact: CalibrationArtifact, activation: Activation | None, labelled: str
) -> ValidationClass:
    return effective_class(
        artifact,
        activation,
        tenant_id="SYN-TEN",
        pack_version="1",
        labelled_set_hash=labelled,
        at=1001,
        revalidation_period=10,
    )


@pytest.mark.fast
def test_T_LIB_0063() -> None:
    """Check meet the coverage bound over seeded class-conditional trials.

    id: T-LIB-0063
    title: Meet the coverage bound over seeded class-conditional trials
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Meet the coverage bound over seeded class-conditional trials
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    rng = Random(17)
    covered = {"A": 0, "B": 0}
    for _ in range(1000):
        scores = {"A": [rng.random() for _ in range(8)], "B": [rng.random() / 2 for _ in range(8)]}
        artifact = calibrate(scores, alpha=0.2, version="1", source_id="SYN-CAL")
        prediction = predict(artifact, {"A": rng.random(), "B": rng.random() / 2})
        for label in covered:
            covered[label] += label in prediction.classes
    assert all(count >= 800 for count in covered.values())


@pytest.mark.fast
def test_T_LIB_0064() -> None:
    """Check replay phase 09 calibration fixtures deterministically.

    id: T-LIB-0064
    title: Replay Phase 09 calibration fixtures deterministically
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Replay Phase 09 calibration fixtures deterministically
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    fixture = generate_calibration_set(seed=42)
    scores = {
        str(label): [
            score
            for score, observed in zip(fixture.scores, fixture.labels, strict=True)
            if label == observed
        ]
        for label in (0, 1)
    }
    first = calibrate(scores, alpha=0.1, version=fixture.version, source_id=fixture.artifact_id)
    second = calibrate(
        dict(reversed(tuple(scores.items()))),
        alpha=0.1,
        version=fixture.version,
        source_id=fixture.artifact_id,
    )
    assert first == second
    assert first.coverage_label == "SYNTHETIC"


@pytest.mark.fast
def test_T_LIB_0065() -> None:
    """Check use distinct class thresholds and include boundary scores.

    id: T-LIB-0065
    title: Use distinct class thresholds and include boundary scores
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Use distinct class thresholds and include boundary scores
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    assert predict(artifact, {"A": 0.2, "B": 0.6}).classes == ("A", "B")
    assert predict(artifact, {"A": 0.3, "B": 0.6}).classes == ("B",)


@pytest.mark.fast
def test_T_LIB_0066() -> None:
    """Check state only the marginal exchangeability guarantee.

    id: T-LIB-0066
    title: State only the marginal exchangeability guarantee
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: State only the marginal exchangeability guarantee
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    assert GUARANTEE == (
        "marginal coverage of at least 1-alpha holds under exchangeability "
        "of calibration and test data."
    )


@pytest.mark.fast
def test_T_LIB_0067() -> None:
    """Check abstain for empty and oversized sets.

    id: T-LIB-0067
    title: Abstain for empty and oversized sets
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Abstain for empty and oversized sets
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    empty = predict(_fit(), {"A": 0.9, "B": 0.9})
    assert empty.abstain_reason == "EMPTY_SET" and empty.size == 0
    oversized = predict(_fit(), {"A": 0.1, "B": 0.1}, maximum_size=1)
    assert oversized.abstain_reason == "OVERSIZED_SET" and oversized.size == 2


@pytest.mark.fast
def test_T_LIB_0068() -> None:
    """Check disable automatic use after a confirmed coverage drop.

    id: T-LIB-0068
    title: Disable automatic use after a confirmed coverage drop
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Disable automatic use after a confirmed coverage drop
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    rows = _records(
        artifact, 5, candidates=("B",), actual="A", confirmation=Confirmation.AUDITED_ALLOW
    )
    result = _monitor(artifact, rows)
    assert result.disable_automatic
    assert result.coverage == 0
    assert result.coverage_label == "TENANT_OUTCOMES"


@pytest.mark.fast
def test_T_LIB_0069() -> None:
    """Check record synthetic coverage without disabling automatic use.

    id: T-LIB-0069
    title: Record synthetic coverage without disabling automatic use
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Record synthetic coverage without disabling automatic use
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    rows = _records(artifact, 5, candidates=("B",), actual="A", confirmation=Confirmation.SYNTHETIC)
    result = _monitor(artifact, rows)
    assert result.benchmark_coverage == 0
    assert result.benchmark_label == "SYNTHETIC"
    assert result.status == "NOT_MEASURABLE"
    assert not result.disable_automatic


@pytest.mark.fast
def test_T_LIB_0070() -> None:
    """Check flag extended not-measurable status for revalidation.

    id: T-LIB-0070
    title: Flag extended not-measurable status for revalidation
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Flag extended not-measurable status for revalidation
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    result = monitor(
        artifact,
        [],
        tenant_id="SYN-TEN",
        window_size=10,
        target=0.9,
        tolerance=0.05,
        validated=True,
        not_measurable_for=11,
        revalidation_period=10,
    )
    assert result.revalidation_lapsed
    assert not result.disable_automatic
    assert result.coverage is None


@pytest.mark.fast
def test_T_LIB_0071() -> None:
    """Check pass validation on confirmed outcomes meeting the configured bound.

    id: T-LIB-0071
    title: Pass validation on confirmed outcomes meeting the configured bound
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Pass validation on confirmed outcomes meeting the configured bound
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    rows = _records(artifact, 300, candidates=("A",), actual="A")
    result = _validate(artifact, rows)
    assert result.passed and result.size == 300
    assert result.bounds is not None and result.bounds[0] >= 0.9
    assert result.singleton_error_upper is not None and result.singleton_error_upper < 0.1


@pytest.mark.fast
def test_T_LIB_0072() -> None:
    """Check fail validation on inadequate confirmed coverage.

    id: T-LIB-0072
    title: Fail validation on inadequate confirmed coverage
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Fail validation on inadequate confirmed coverage
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    rows = _records(artifact, 300, candidates=("B",), actual="A")
    assert not _validate(artifact, rows).passed
    assert not validate_tenant(artifact, rows, tenant_id="SYN-TEN", criterion=None).passed


@pytest.mark.fast
def test_T_LIB_0073() -> None:
    """Check fail excessive singleton error despite adequate overall coverage.

    id: T-LIB-0073
    title: Fail excessive singleton error despite adequate overall coverage
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Fail excessive singleton error despite adequate overall coverage
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    rows = _records(artifact, 290, candidates=("A", "B"), actual="A")
    rows.extend(_records(artifact, 10, candidates=("B",), actual="A", offset=290))
    result = _validate(artifact, rows)
    assert result.bounds is not None and result.bounds[0] >= 0.9
    assert result.singleton_error_upper is not None and result.singleton_error_upper > 0.1
    assert not result.passed


@pytest.mark.fast
def test_T_LIB_0074() -> None:
    """Check lapse when the pack, artifact or labelled set changes.

    id: T-LIB-0074
    title: Lapse when the pack, artifact or labelled set changes
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Lapse when the pack, artifact or labelled set changes
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    activation = _activation(artifact)
    labelled = activation.validation.labelled_set_hash
    assert _class(artifact, activation, labelled) is ValidationClass.VALIDATED_TENANT
    assert (
        _class(artifact, replace(activation, pack_version="2"), labelled)
        is ValidationClass.CALIBRATED_SYNTHETIC
    )
    assert _class(artifact, activation, "9" * 64) is ValidationClass.CALIBRATED_SYNTHETIC
    changed = calibrate({"A": [0.4], "B": [0.6]}, alpha=0.1, version="1", source_id="SYN-CAL")
    assert _class(changed, activation, labelled) is ValidationClass.CALIBRATED_SYNTHETIC


@pytest.mark.fast
def test_T_LIB_0075() -> None:
    """Check require recorded independent approval before using tenant validation.

    id: T-LIB-0075
    title: Require recorded independent approval before using tenant validation
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Require recorded independent approval before using tenant validation
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    activation = _activation(artifact)
    labelled = activation.validation.labelled_set_hash
    assert artifact.validation_class is ValidationClass.CALIBRATED_SYNTHETIC
    assert _class(artifact, None, labelled) is ValidationClass.CALIBRATED_SYNTHETIC
    assert (
        _class(artifact, replace(activation, second_reviewer=activation.reviewer), labelled)
        is ValidationClass.CALIBRATED_SYNTHETIC
    )
    assert (
        _class(artifact, replace(activation, record_hash=""), labelled)
        is ValidationClass.CALIBRATED_SYNTHETIC
    )


@pytest.mark.fast
def test_T_LIB_0076() -> None:
    """Check lapse after the configured revalidation interval.

    id: T-LIB-0076
    title: Lapse after the configured revalidation interval
    purpose: Verify calibrated prediction and independent tenant validation
    level: fast
    requirement: P13-T06
    input: Seeded calibration evidence or synthetic confirmation records
    expected: Lapse after the configured revalidation interval
    risk: Confidence is inflated or unsupported automatic use continues
    capability: shared-library
    """
    artifact = _fit()
    activation = _activation(artifact)
    result = effective_class(
        artifact,
        activation,
        tenant_id="SYN-TEN",
        pack_version="1",
        labelled_set_hash=activation.validation.labelled_set_hash,
        at=1011,
        revalidation_period=10,
    )
    assert result is ValidationClass.CALIBRATED_SYNTHETIC

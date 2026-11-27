"""Deterministic split conformal sets and reproducible calibration metadata."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from fractions import Fraction

from kernel.hashing import domain_hash

__all__ = [
    "GUARANTEE",
    "CalibrationArtifact",
    "ClassThreshold",
    "Prediction",
    "ValidationClass",
    "calibrate",
    "predict",
]

GUARANTEE = (
    "marginal coverage of at least 1-alpha holds under exchangeability "
    "of calibration and test data."
)


class ValidationClass(StrEnum):
    """Classes of recorded calibration evidence."""

    CALIBRATED_SYNTHETIC = "CALIBRATED_SYNTHETIC"
    VALIDATED_TENANT = "VALIDATED_TENANT"


@dataclass(frozen=True, slots=True)
class ClassThreshold:
    """Class-specific order statistic, with None denoting an unbounded threshold."""

    label: str
    size: int
    threshold: float | None


@dataclass(frozen=True, slots=True)
class CalibrationArtifact:
    """Immutable calibration data with a digest over every recorded input."""

    artifact_id: str
    version: str
    digest: str
    alpha: float
    thresholds: tuple[ClassThreshold, ...]
    source_id: str
    coverage_label: str
    validation_class: ValidationClass = field(
        default=ValidationClass.CALIBRATED_SYNTHETIC, init=False
    )


@dataclass(frozen=True, slots=True)
class Prediction:
    """Prediction set and explicit reason when its size forces abstention."""

    classes: tuple[str, ...]
    alpha: float
    artifact_id: str
    abstain_reason: str | None = None

    @property
    def size(self) -> int:
        """Return the complete prediction-set size."""
        return len(self.classes)


def _valid_score(score: float) -> bool:
    return math.isfinite(score) and 0 <= score <= 1


def calibrate(
    scores_by_class: Mapping[str, Iterable[float]],
    *,
    alpha: float,
    version: str,
    source_id: str,
    registered_real_sources: frozenset[str] = frozenset(),
) -> CalibrationArtifact:
    """Build finite-sample class-conditional thresholds from labelled scores."""
    if not 0 < alpha < 1 or not version or not source_id or not scores_by_class:
        raise ValueError("calibration requires scores, provenance and alpha between zero and one")
    prepared = [(label, sorted(scores_by_class[label])) for label in sorted(scores_by_class)]
    thresholds: list[ClassThreshold] = []
    for label, scores in prepared:
        if not label or not scores or not all(_valid_score(score) for score in scores):
            raise ValueError("each calibrated class requires finite scores between zero and one")
        k = math.ceil((len(scores) + 1) * (1 - Fraction(str(alpha))))
        threshold = scores[k - 1] if k <= len(scores) else None
        thresholds.append(ClassThreshold(label, len(scores), threshold))
    label = "TENANT_OUTCOMES" if source_id in registered_real_sources else "SYNTHETIC"
    digest = domain_hash(
        "ctc/payload/v1",
        {
            "type": "CONFORMAL_CALIBRATION",
            "version": version,
            "source_id": source_id,
            "alpha": alpha,
            "coverage_label": label,
            "calibration": [{"class": key, "scores": scores} for key, scores in prepared],
        },
    )
    return CalibrationArtifact(
        f"CAL-{digest}", version, digest, alpha, tuple(thresholds), source_id, label
    )


def predict(
    artifact: CalibrationArtifact,
    scores: Mapping[str, float],
    *,
    maximum_size: int = 3,
) -> Prediction:
    """Include every candidate at or below its class threshold."""
    if maximum_size < 1:
        raise ValueError("prediction maximum must be positive")
    if set(scores) != {entry.label for entry in artifact.thresholds} or not all(
        _valid_score(score) for score in scores.values()
    ):
        return Prediction((), artifact.alpha, artifact.artifact_id, "INVALID_CANDIDATE_SCORES")
    classes = tuple(
        entry.label
        for entry in artifact.thresholds
        if entry.threshold is None or scores[entry.label] <= entry.threshold
    )
    reason = None
    if not classes:
        reason = "EMPTY_SET"
    elif len(classes) > maximum_size:
        reason = "OVERSIZED_SET"
    return Prediction(classes, artifact.alpha, artifact.artifact_id, reason)

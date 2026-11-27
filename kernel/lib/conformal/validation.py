"""Outcome-based calibration monitoring, validation and activation checks."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from kernel.hashing import domain_hash
from kernel.lib.conformal import CalibrationArtifact, ValidationClass

__all__ = [
    "Activation",
    "Confirmation",
    "Criterion",
    "Metric",
    "Monitor",
    "Observation",
    "ValidationReport",
    "effective_class",
    "monitor",
    "validate_tenant",
    "wilson",
]

_Z_95 = 1.959963984540054


class Confirmation(StrEnum):
    """Accepted origins for a confirmed outcome or a synthetic trial."""

    REVIEWER = "REVIEWER"
    OUTCOME_CONFIRMATIONS = "OUTCOME_CONFIRMATIONS"
    AUDITED_ALLOW = "AUDITED_ALLOW"
    SYNTHETIC = "SYNTHETIC"


@dataclass(frozen=True, slots=True)
class Observation:
    """One prediction and later confirmed outcome, bound to its tenant and case."""

    tenant_id: str
    record_id: str
    candidates: tuple[str, ...]
    actual: str
    confirmation: Confirmation
    artifact_hash: str
    positive: bool = False

    @property
    def covered(self) -> bool:
        """Return whether the set contains the confirmed class."""
        return self.actual in self.candidates


class Metric(StrEnum):
    """Metric whose Wilson bound determines readiness."""

    COVERAGE = "COVERAGE"
    RECALL = "RECALL"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class Criterion:
    """Capability configuration for a tenant validation run."""

    metric: Metric
    target: float
    singleton_error_target: float | None = None
    minimum_pairs: int = 300

    def __post_init__(self) -> None:
        """Require meaningful thresholds and enough evidence for a bound."""
        if not 0 <= self.target <= 1 or self.minimum_pairs < 1:
            raise ValueError("invalid validation target or sample size")
        if self.singleton_error_target is not None and not 0 <= self.singleton_error_target <= 1:
            raise ValueError("invalid one-member error target")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Statistics and hashes suitable for the tenant system chain."""

    tenant_id: str
    artifact_hash: str
    labelled_set_hash: str
    size: int
    passed: bool
    bounds: tuple[float, float] | None
    singleton_error_upper: float | None


@dataclass(frozen=True, slots=True)
class Activation:
    """Already recorded activation with independent review and exact bindings."""

    record_hash: str
    pack_version: str
    validation: ValidationReport
    activated_at: int
    reviewer: str
    second_reviewer: str


@dataclass(frozen=True, slots=True)
class Monitor:
    """Rolling confirmed coverage and whether the capability must stop automatic use."""

    status: Literal["MEASURED", "NOT_MEASURABLE"]
    coverage: float | None
    mean_set_size: float | None
    benchmark_coverage: float | None
    disable_automatic: bool
    revalidation_lapsed: bool

    @property
    def benchmark_label(self) -> Literal["SYNTHETIC"] | None:
        """Label any synthetic coverage independently of tenant measurements."""
        return "SYNTHETIC" if self.benchmark_coverage is not None else None

    @property
    def coverage_label(self) -> Literal["TENANT_OUTCOMES"] | None:
        """Identify measured coverage by its confirmation provenance."""
        return "TENANT_OUTCOMES" if self.coverage is not None else None


def wilson(successes: int, total: int) -> tuple[float, float]:
    """Return the two-sided 95 percent Wilson score interval."""
    if not 0 <= successes <= total or total < 1:
        raise ValueError("invalid Wilson counts")
    proportion = successes / total
    z_sq = _Z_95**2
    denominator = 1 + z_sq / total
    center = (proportion + z_sq / (2 * total)) / denominator
    margin = _Z_95 * math.sqrt(proportion * (1 - proportion) / total + z_sq / (4 * total**2))
    margin /= denominator
    return max(0.0, center - margin), min(1.0, center + margin)


def validate_tenant(
    artifact: CalibrationArtifact,
    observations: Sequence[Observation],
    *,
    tenant_id: str,
    criterion: Criterion | None,
) -> ValidationReport:
    """Check configured bounds and retain only statistics and provenance hashes."""
    approved = {Confirmation.REVIEWER, Confirmation.OUTCOME_CONFIRMATIONS}
    if any(
        row.tenant_id != tenant_id or row.confirmation not in approved for row in observations
    ) or len({row.record_id for row in observations}) != len(observations):
        raise ValueError("tenant validation requires unique, tenant-confirmed outcome records")
    digest = domain_hash(
        "ctc/payload/v1",
        {
            "type": "TENANT_VALIDATION_SET",
            "tenant": tenant_id,
            "records": [
                [row.record_id, sorted(row.candidates), row.actual, row.confirmation, row.positive]
                for row in sorted(observations, key=lambda row: row.record_id)
            ],
        },
    )
    bounds = None
    singleton_upper = None
    passed = False
    if criterion is not None and len(observations) >= criterion.minimum_pairs:
        sample = [row for row in observations if criterion.metric != Metric.RECALL or row.positive]
        if sample:
            covered = sum(row.covered for row in sample)
            if criterion.metric == Metric.ERROR:
                bounds = wilson(len(sample) - covered, len(sample))
                passed = bounds[1] <= criterion.target
            else:
                bounds = wilson(covered, len(sample))
                passed = bounds[0] >= criterion.target
        if criterion.singleton_error_target is not None:
            singletons = [row for row in observations if len(row.candidates) == 1]
            if singletons:
                errors = sum(not row.covered for row in singletons)
                singleton_upper = wilson(errors, len(singletons))[1]
            passed &= (
                singleton_upper is not None and singleton_upper <= criterion.singleton_error_target
            )
    return ValidationReport(
        tenant_id, artifact.digest, digest, len(observations), passed, bounds, singleton_upper
    )


def monitor(
    artifact: CalibrationArtifact,
    observations: Sequence[Observation],
    *,
    tenant_id: str,
    window_size: int,
    target: float,
    tolerance: float,
    validated: bool = False,
    not_measurable_for: int = 0,
    revalidation_period: int = 0,
) -> Monitor:
    """Report rolling statistics and act only on confirmed real-data drops."""
    if window_size < 1 or not 0 <= tolerance <= target <= 1:
        raise ValueError("invalid monitor configuration")
    matching = [
        row
        for row in observations
        if row.tenant_id == tenant_id and row.artifact_hash == artifact.digest
    ]
    confirmed = [row for row in matching if row.confirmation != Confirmation.SYNTHETIC][
        -window_size:
    ]
    synthetic = [row for row in matching if row.confirmation == Confirmation.SYNTHETIC][
        -window_size:
    ]
    benchmark = sum(row.covered for row in synthetic) / len(synthetic) if synthetic else None
    if not confirmed:
        lapse = validated and revalidation_period > 0 and not_measurable_for > revalidation_period
        return Monitor("NOT_MEASURABLE", None, None, benchmark, False, lapse)
    coverage = sum(row.covered for row in confirmed) / len(confirmed)
    mean_size = sum(len(row.candidates) for row in confirmed) / len(confirmed)
    return Monitor("MEASURED", coverage, mean_size, benchmark, coverage < target - tolerance, False)


def effective_class(
    artifact: CalibrationArtifact,
    activation: Activation | None,
    *,
    tenant_id: str,
    pack_version: str,
    labelled_set_hash: str,
    at: int,
    revalidation_period: int,
    monitoring: Monitor | None = None,
) -> ValidationClass:
    """Resolve the class from an eligible activation without changing the artifact."""
    if activation is None or (monitoring is not None and monitoring.revalidation_lapsed):
        return artifact.validation_class
    report = activation.validation
    active = (
        re.fullmatch("[0-9a-f]{64}", activation.record_hash) is not None
        and bool(activation.reviewer)
        and bool(activation.second_reviewer)
        and activation.reviewer != activation.second_reviewer
        and report.passed
        and report.tenant_id == tenant_id
        and report.artifact_hash == artifact.digest
        and report.labelled_set_hash == labelled_set_hash
        and activation.pack_version == pack_version
        and 0 <= at - activation.activated_at <= revalidation_period
    )
    return ValidationClass.VALIDATED_TENANT if active else artifact.validation_class

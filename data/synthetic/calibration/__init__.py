"""Conformal calibration fixtures (P09-T06).

Seeded calibration and test sets with a known score distribution for the
conformal core (built in P13) and the capabilities that use it.  Sets are
versioned artifacts with an id; coverage statements using them carry the
SYNTHETIC label (Part 3 §3.13).

Spec: Part 3 §3.13; P09-T06.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

__all__ = [
    "CalibrationSet",
    "CalibrationFactory",
    "generate_calibration_set",
    "generate_test_set",
    "CALIBRATION_ARTIFACT_ID",
    "TEST_ARTIFACT_ID",
]

#: Stable artifact identifiers (deterministic from the seed).
CALIBRATION_ARTIFACT_ID: str = "SYN-CAL-001"
TEST_ARTIFACT_ID: str = "SYN-CAL-TEST-001"

#: Factory version.
_VERSION: str = "1.0.0"

#: Number of samples in the calibration set.
_CAL_SIZE: int = 100

#: Number of samples in the test set.
_TEST_SIZE: int = 50


@dataclass(frozen=True)
class CalibrationSet:
    """A calibration or test set for the conformal core.

    Attributes:
        artifact_id: Stable artifact identifier.
        version: The factory version.
        seed: The seed used to generate the set.
        scores: List of confidence scores in [0, 1].
        labels: List of integer labels (0 or 1).
        label: Always ``SYNTHETIC`` (Part 3 §3.13).
        kind: ``calibration`` or ``test``.
    """

    artifact_id: str
    version: str
    seed: int
    scores: list[float]
    labels: list[int]
    label: str
    kind: str


class CalibrationFactory:
    """Seeded factory for calibration and test sets (P09-T06).

    Produces deterministic calibration and test sets with a known score
    distribution.  Every record carries the SYNTHETIC label.

    Args:
        seed: The random seed for reproducibility.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed: int = seed

    def _prng(self, offset: int = 0) -> int:
        """Return a deterministic pseudo-random integer."""
        h = hashlib.sha256(f"{self.seed}:{offset}".encode()).digest()
        return int.from_bytes(h[:8], "little")

    def _score(self, index: int) -> float:
        """Return a deterministic score in [0, 1]."""
        raw = self._prng(index)
        return (raw % 10000) / 10000.0

    def _label(self, index: int, threshold: float = 0.5) -> int:
        """Return a deterministic binary label."""
        return 1 if self._score(index) >= threshold else 0

    def generate_calibration(self) -> CalibrationSet:
        """Generate the calibration set.

        Returns:
            A :class:`CalibrationSet` with ``kind="calibration"``.
        """
        scores = [self._score(i) for i in range(_CAL_SIZE)]
        labels = [self._label(i) for i in range(_CAL_SIZE)]
        return CalibrationSet(
            artifact_id=CALIBRATION_ARTIFACT_ID,
            version=_VERSION,
            seed=self.seed,
            scores=scores,
            labels=labels,
            label="SYNTHETIC",
            kind="calibration",
        )

    def generate_test(self) -> CalibrationSet:
        """Generate the test set.

        Returns:
            A :class:`CalibrationSet` with ``kind="test"``.
        """
        scores = [self._score(i + _CAL_SIZE) for i in range(_TEST_SIZE)]
        labels = [self._label(i + _CAL_SIZE) for i in range(_TEST_SIZE)]
        return CalibrationSet(
            artifact_id=TEST_ARTIFACT_ID,
            version=_VERSION,
            seed=self.seed,
            scores=scores,
            labels=labels,
            label="SYNTHETIC",
            kind="test",
        )


def generate_calibration_set(seed: int = 42) -> CalibrationSet:
    """Generate a calibration set from a seed.

    Args:
        seed: The random seed.

    Returns:
        A :class:`CalibrationSet`.
    """
    return CalibrationFactory(seed).generate_calibration()


def generate_test_set(seed: int = 42) -> CalibrationSet:
    """Generate a test set from a seed.

    Args:
        seed: The random seed.

    Returns:
        A :class:`CalibrationSet`.
    """
    return CalibrationFactory(seed).generate_test()

"""Build pack-bound calibration and independent diagnostics for every served language."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from capabilities.f02.scoring import (
    ALPHA,
    CALIBRATION_MINIMUM,
    CHAPTER_MINIMUM,
    TariffIndex,
    tokenize,
)
from kernel.hashing import domain_hash
from kernel.lib.conformal import ValidationClass, calibrate


@dataclass(frozen=True, slots=True)
class Pair:
    code: str
    description: str
    layer: str


@dataclass(frozen=True, slots=True)
class Coverage:
    chapter: str
    covered: int
    total: int
    label: str = "SYNTHETIC"


@dataclass(frozen=True, slots=True)
class Calibration:
    language: str
    pack_hash: str
    source_id: str
    artifact_id: str
    digest: str
    count: int
    chapter_count: int
    counts: tuple[tuple[str, int], ...]
    alpha: float
    threshold: float
    held_out: tuple[Coverage, ...]
    shifted: tuple[Coverage, ...]
    validation_class: ValidationClass = ValidationClass.CALIBRATED_SYNTHETIC


def _measure(
    index: TariffIndex, pairs: Sequence[Pair], language: str
) -> list[tuple[str, float, Pair]]:
    measured = []
    for pair in pairs:
        tokens = tokenize(pair.description, index.pack)
        if (
            not tokens.supported
            or tokens.language != language
            or pair.code not in index.self_scores
        ):
            raise ValueError("CALIBRATION_STALE")
        score = 1 - index.similarity(tokens.terms)[pair.code]
        measured.append((pair.code[: index.pack.levels[0]], score, pair))
    return measured


def _coverage(
    measured: Sequence[tuple[str, float, Pair]], threshold: float, chapters: frozenset[str]
) -> tuple[Coverage, ...]:
    return tuple(
        Coverage(chapter, sum(score <= threshold for score in scores), len(scores))
        for chapter in sorted(chapters)
        if (scores := [score for observed, score, _ in measured if observed == chapter])
    )


def fit(
    index: TariffIndex,
    pairs: Sequence[Pair],
    held_out: Sequence[Pair],
    shifted: Sequence[Pair],
    *,
    language: str,
    source_id: str,
    alpha: float = ALPHA,
) -> Calibration:
    """Fit the finite-sample quantile and archive two separate diagnostic splits."""
    chapters = index.pack.chapters
    if (
        language not in index.pack.languages
        or len(pairs) < max(CALIBRATION_MINIMUM, CHAPTER_MINIMUM * len(chapters))
        or {pair.layer for pair in pairs} != {"pack_text", "commercial_name"}
        or not held_out
        or not shifted
    ):
        raise ValueError("CALIBRATION_STALE")
    measured = _measure(index, pairs, language)
    counts = Counter(chapter for chapter, _, _ in measured)
    if any(counts[chapter] < CHAPTER_MINIMUM for chapter in chapters):
        raise ValueError("CALIBRATION_STALE")
    artifact = calibrate(
        {"tariff": [score for _, score, _ in measured]},
        alpha=alpha,
        version=index.pack_hash,
        source_id=source_id,
    )
    threshold = artifact.thresholds[0].threshold
    if threshold is None:
        raise ValueError("CALIBRATION_STALE")
    measured_held_out = _measure(index, held_out, language)
    measured_shifted = _measure(index, shifted, language)
    digest = domain_hash(
        "ctc/payload/v1",
        {
            "core": artifact.digest,
            "language": language,
            "chapters": sorted(counts.items()),
            "pairs": [(pair.code, pair.description, pair.layer) for pair in pairs],
        },
    )
    return Calibration(
        language,
        index.pack_hash,
        source_id,
        f"CAL-{digest}",
        digest,
        len(pairs),
        len(chapters),
        tuple(sorted(counts.items())),
        alpha,
        threshold,
        _coverage(measured_held_out, threshold, chapters),
        _coverage(measured_shifted, threshold, chapters),
    )

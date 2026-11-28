"""Project-owned English tariff fixture and language-bound calibration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from capabilities.f02.calibration import Pair, fit
from capabilities.f02.registration import ClassificationJudge
from capabilities.f02.scoring import Entry, TariffIndex, TariffPack
from data.synthetic.calibration.classification import (
    LABEL,
    SOURCE_ID,
    commercial_names,
    generate_pairs,
)

START = datetime(2026, 11, 1, tzinfo=UTC)
DESCRIPTIONS = {
    "1101": "wheat flour finely ground",
    "1201": "soy beans edible seeds",
    "1301": "natural gum extracted resin",
    "1401": "reed strips woven fiber",
}


def create_judge() -> ClassificationJudge:
    """Index the synthetic tariff and materialize separate seeded splits."""
    end = START + timedelta(days=30)
    pack = TariffPack(
        SOURCE_ID,
        LABEL,
        START,
        end,
        (2, 4),
        4,
        tuple(Entry(code, (text,), START, end) for code, text in DESCRIPTIONS.items()),
        frozenset({"a", "the", "as"}),
    )
    index = TariffIndex.build(pack)
    lexicon = commercial_names("en")

    def split(seed: int, count: int, *, shifted: bool = False) -> tuple[Pair, ...]:
        rows = generate_pairs(
            DESCRIPTIONS, lexicon, chapter_digits=2, seed=seed, count=count, shifted=shifted
        )
        return tuple(Pair(row.code, row.text, row.layer) for row in rows)

    calibration = fit(
        index,
        split(19, 500),
        split(212, 80),
        split(561, 80, shifted=True),
        language="en",
        source_id=SOURCE_ID,
    )
    return ClassificationJudge(index, {"en": calibration})

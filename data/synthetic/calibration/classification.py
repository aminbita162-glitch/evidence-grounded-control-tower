"""Create deterministic, disjoint SYNTHETIC classification calibration splits."""

from __future__ import annotations

import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SOURCE_ID = "SRC-SYNTHETIC-F02"
LABEL = "SYNTHETIC"
_LEXICON = Path(__file__).with_name("commercial_names.json")


@dataclass(frozen=True, slots=True)
class Description:
    code: str
    text: str
    layer: Literal["pack_text", "commercial_name"]


def commercial_names(language: str) -> dict[str, tuple[str, ...]]:
    """Read the project-authored lexicon independently of the tariff text."""
    raw = json.loads(_LEXICON.read_bytes())
    return {code: tuple(names) for code, names in raw["languages"][language].items()}


def generate_pairs(
    texts: Mapping[str, str],
    lexicon: Mapping[str, Sequence[str]],
    *,
    chapter_digits: int,
    seed: int,
    count: int,
    shifted: bool = False,
) -> tuple[Description, ...]:
    """Balance chapters for calibration; use a different style for shifted diagnostics."""
    chapters: dict[str, list[str]] = {}
    for code in sorted(texts):
        chapters.setdefault(code[:chapter_digits], []).append(code)
    if not chapters or set(texts) != set(lexicon) or count <= 0:
        raise ValueError("synthetic pairing requires a nonempty text and lexicon for every code")
    groups = tuple(chapters.values())
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        group = groups[index % len(groups)]
        code = rng.choice(group)
        if (index // len(groups) + index) % 2:
            words = rng.choice(lexicon[code]).split()
            layer: Literal["commercial_name", "pack_text"] = "commercial_name"
        else:
            words = texts[code].split()
            layer = "pack_text"
        rng.shuffle(words)
        if shifted:
            words = words[:1] + ["miscellaneous", "assorted", "unspecified", "shipment"]
        rows.append(Description(code, " ".join(words), layer))
    return tuple(rows)

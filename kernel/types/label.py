"""Label types from the label taxonomy (Part 3 §3.8, P03-T03).

Reads ``schemas/labels.json`` for the label strength order and
ALLOW-eligibility. Provides ``weakest_of``, ``label_rank``, and
``is_allow_eligible``.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LABELS_DATA = json.loads((_REPO_ROOT / "schemas" / "labels.json").read_text(encoding="utf-8"))
LABELS: list[str] = list(_LABELS_DATA["labels"])
_RANKS: dict[str, int] = dict(_LABELS_DATA["strength_order"]["ranks"])
ALLOW_ELIGIBLE: list[str] = list(_LABELS_DATA["allow_eligible"])


def label_rank(label: str) -> int:
    """Return the strength rank of *label* (higher = stronger)."""
    if label not in _RANKS:
        raise ValueError(f"unknown label: {label!r}")
    return _RANKS[label]


def weakest_of(a: str, b: str) -> str:
    """Return the weaker of two labels (minimum rank).

    When ranks are equal (SIMULATED_RULE and SYNTHETIC), either may be
    returned; the implementation is consistent (returns *a*).
    """
    ra = label_rank(a)
    rb = label_rank(b)
    return a if ra <= rb else b


def is_allow_eligible(label: str) -> bool:
    """Return True if *label* is ALLOW-eligible (OFFICIAL or DERIVED)."""
    return label in ALLOW_ELIGIBLE


# Type alias for label strings.
Label = str

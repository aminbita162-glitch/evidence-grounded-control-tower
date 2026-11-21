"""Label taxonomy helper for the Control Tower.

Loads the taxonomy from ``schemas/labels.json`` and exposes:

- :func:`compare_labels`: total-preorder comparison of two labels.
- :func:`weakest_of`: weakest label among a collection of labels.
- :func:`is_allow_eligible`: whether a label permits an ALLOW Decision.
- :data:`LABELS`: frozenset of all valid label strings.
- :data:`ALLOW_ELIGIBLE`: frozenset of ALLOW-eligible labels.
- :data:`LABEL_RANKS`: mapping from label string to integer rank.

Spec: Part 3 §3.8, Part 2 §2.14, schemas/labels.json.
The kernel types of P03 are generated from ``schemas/labels.json``; this
module is a pure data helper and must not import from kernel/.
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "LabelError",
    "LABELS",
    "ALLOW_ELIGIBLE",
    "LABEL_RANKS",
    "compare_labels",
    "weakest_of",
    "is_allow_eligible",
]

_TAXONOMY_PATH = Path(__file__).parent.parent.parent / "schemas" / "labels.json"


def _load_taxonomy() -> tuple[frozenset[str], dict[str, int], frozenset[str]]:
    """Load taxonomy from schemas/labels.json.

    Returns:
        Tuple of (all_labels, label_ranks, allow_eligible).
    """
    raw = json.loads(_TAXONOMY_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("labels.json must be a JSON object")

    labels_raw = raw.get("labels", [])
    if not isinstance(labels_raw, list):
        raise ValueError("labels.json: 'labels' must be a list")
    all_labels: frozenset[str] = frozenset(str(item) for item in labels_raw)

    ranks_section = raw.get("strength_order", {})
    if not isinstance(ranks_section, dict):
        raise ValueError("labels.json: 'strength_order' must be an object")
    ranks_raw = ranks_section.get("ranks", {})
    if not isinstance(ranks_raw, dict):
        raise ValueError("labels.json: 'strength_order.ranks' must be an object")
    label_ranks: dict[str, int] = {
        str(k): int(v) for k, v in ranks_raw.items() if isinstance(v, (int, float))
    }

    allow_raw = raw.get("allow_eligible", [])
    if not isinstance(allow_raw, list):
        raise ValueError("labels.json: 'allow_eligible' must be a list")
    allow_eligible: frozenset[str] = frozenset(str(item) for item in allow_raw)

    return all_labels, label_ranks, allow_eligible


_LABELS, _LABEL_RANKS, _ALLOW_ELIGIBLE = _load_taxonomy()

#: All valid label strings as a frozenset.
LABELS: frozenset[str] = _LABELS

#: Mapping from label string to its integer rank (higher = stronger).
LABEL_RANKS: dict[str, int] = _LABEL_RANKS

#: Labels that permit an ALLOW Decision (Part 3 §3.8).
ALLOW_ELIGIBLE: frozenset[str] = _ALLOW_ELIGIBLE


class LabelError(ValueError):
    """Raised when an unknown or invalid label is encountered."""


def _validated(label: str) -> str:
    """Return *label* if valid, else raise :class:`LabelError`."""
    if label not in LABELS:
        raise LabelError(f"unknown label {label!r}; valid labels are {sorted(LABELS)}")
    return label


def compare_labels(a: str, b: str) -> int:
    """Compare two labels by strength.

    Returns a negative integer if *a* is weaker than *b*, zero if equal,
    or a positive integer if *a* is stronger than *b*.

    Args:
        a: A valid label string.
        b: A valid label string.

    Returns:
        Negative if a < b, zero if a == b (or tied), positive if a > b.

    Raises:
        LabelError: If either label is not in the taxonomy.
    """
    _validated(a)
    _validated(b)
    return LABEL_RANKS[a] - LABEL_RANKS[b]


def weakest_of(labels: list[str]) -> str:
    """Return the weakest label in *labels*.

    A derived datum takes the weakest label of its inputs (minimum rank).
    When multiple labels share the minimum rank, the first encountered in
    *labels* is returned (deterministic over a given input order).

    Args:
        labels: A non-empty list of valid label strings.

    Returns:
        The label with the lowest rank in the taxonomy.

    Raises:
        LabelError: If any label is unknown.
        ValueError: If *labels* is empty.
    """
    if not labels:
        raise ValueError("weakest_of requires at least one label")
    validated = [_validated(label) for label in labels]
    return min(validated, key=lambda lbl: LABEL_RANKS[lbl])


def is_allow_eligible(label: str) -> bool:
    """Return True if *label* is ALLOW-eligible (OFFICIAL or DERIVED).

    Args:
        label: A valid label string.

    Returns:
        True if the label is in the ALLOW-eligible set.

    Raises:
        LabelError: If the label is unknown.
    """
    _validated(label)
    return label in ALLOW_ELIGIBLE

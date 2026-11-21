"""Conflict detection for fact keys (Part 3 §3.3, P03-T04).

A fact key is conflicted when two or more non-superseded values exist.
"""

from __future__ import annotations


def find_conflicting_keys(values: dict[str, list[tuple[str, str]]]) -> list[str]:
    """Find fact keys with two or more non-superseded values.

    Args:
        values: A mapping of fact key to a list of (value, status) pairs.

    Returns:
        A list of keys that have two or more non-superseded entries.
    """
    conflicting: list[str] = []
    for key, entries in values.items():
        active = [v for v, s in entries if s not in ("SUPERSEDED", "REJECTED")]
        if len(active) >= 2:
            conflicting.append(key)
    return conflicting


def detect_conflicts(values: dict[str, list[tuple[str, str]]]) -> list[str]:
    """Alias for find_conflicting_keys."""
    return find_conflicting_keys(values)

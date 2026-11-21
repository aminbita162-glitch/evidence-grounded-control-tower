"""Fact status transitions, conflict detection and supersession (Part 3 §3.3, P03-T04)."""

from __future__ import annotations

from kernel.facts.conflict import detect_conflicts, find_conflicting_keys
from kernel.facts.reader import VerifiedFactReader
from kernel.facts.status import (
    FACT_STATUSES,
    TRANSITIONS,
    can_transition,
    transition,
)

__all__ = [
    "FACT_STATUSES",
    "TRANSITIONS",
    "TRANSITIONS",
    "VerifiedFactReader",
    "can_transition",
    "detect_conflicts",
    "find_conflicting_keys",
    "transition",
]

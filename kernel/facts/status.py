"""Fact status transitions (Part 3 §3.3, P03-T04).

Statuses: PROPOSED, VERIFIED, CONFLICTED, SUPERSEDED, REJECTED.
Rules read only VERIFIED facts.
"""

from __future__ import annotations

FACT_STATUSES: frozenset[str] = frozenset(
    {
        "PROPOSED",
        "VERIFIED",
        "CONFLICTED",
        "SUPERSEDED",
        "REJECTED",
    }
)

TRANSITIONS: dict[str, frozenset[str]] = {
    "PROPOSED": frozenset({"VERIFIED", "REJECTED"}),
    "VERIFIED": frozenset({"CONFLICTED", "SUPERSEDED"}),
    "CONFLICTED": frozenset({"SUPERSEDED"}),
    "SUPERSEDED": frozenset(),
    "REJECTED": frozenset(),
}


def can_transition(from_status: str, to_status: str) -> bool:
    """Return True if the transition from_status to to_status is allowed."""
    if from_status not in TRANSITIONS:
        return False
    return to_status in TRANSITIONS[from_status]


def transition(from_status: str, to_status: str) -> str:
    """Execute a status transition, returning the new status.

    Raises:
        ValueError: If the transition is not allowed.
    """
    if not can_transition(from_status, to_status):
        raise ValueError(f"invalid transition: {from_status} -> {to_status}")
    return to_status

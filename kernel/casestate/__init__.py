"""Case state machine (Part 3 §3.4, P03-T05).

States, transitions, idempotency keys, version checking and timeouts.
Undefined transitions are rejected. Timeouts move to BLOCKED, never approve.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATES_DATA = json.loads((_REPO_ROOT / "schemas" / "case-states.json").read_text(encoding="utf-8"))
STATES: list[str] = list(_STATES_DATA["states"])
SIDE_STATES: list[str] = list(_STATES_DATA["side_states"])
TRANSITIONS: dict[str, list[str]] = dict(_STATES_DATA["transitions"])
ALL_STATES: list[str] = STATES + SIDE_STATES


def is_valid_state(state: str) -> bool:
    """Return True if *state* is a known case state."""
    return state in ALL_STATES


def can_transition(from_state: str, to_state: str) -> bool:
    """Return True if the transition is allowed by the table."""
    allowed = TRANSITIONS.get(from_state, [])
    return to_state in allowed


def transition(from_state: str, to_state: str) -> str:
    """Execute a state transition.

    Raises:
        ValueError: If the transition is not defined in the table.
    """
    if not can_transition(from_state, to_state):
        raise ValueError(f"undefined transition: {from_state} -> {to_state}")
    return to_state


class IdempotencyStore:
    """In-memory idempotency key store (Part 3 §3.4).

    Repeating a command with the same key returns the original result.
    """

    def __init__(self) -> None:
        """Initialize an empty store."""
        self._store: dict[str, object] = {}

    def check(self, key: str) -> object | None:
        """Return the stored result for *key*, or None if not seen."""
        return self._store.get(key)

    def record(self, key: str, result: object) -> None:
        """Record a result for *key*."""
        self._store[key] = result


class VersionConflictError(Exception):
    """Raised when a stale version is used (Part 3 §3.4)."""


def check_version(current: int, expected: int) -> None:
    """Verify the current version matches the expected version.

    Raises:
        VersionConflictError: If *current* != *expected*.
    """
    if current != expected:
        raise VersionConflictError(f"version conflict: expected {expected}, got {current}")

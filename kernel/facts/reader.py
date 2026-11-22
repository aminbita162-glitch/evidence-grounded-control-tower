"""Verified fact reader (Part 3 §3.3, P03-T04).

Rules read only VERIFIED facts. This reader cannot return another status.
"""

from __future__ import annotations


class VerifiedFactReader:
    """A reader that only returns facts with status VERIFIED."""

    def __init__(self, facts: dict[str, tuple[str, str]]) -> None:
        """Initialize with a mapping of key to (value, status).

        Args:
            facts: A dict of fact_key -> (value, status).
        """
        self._facts = facts

    def get(self, key: str) -> str | None:
        """Return the value for *key* if it is VERIFIED, else None."""
        entry = self._facts.get(key)
        if entry is None:
            return None
        value, status = entry
        if status != "VERIFIED":
            return None
        return value

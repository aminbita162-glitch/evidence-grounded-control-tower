"""Opaque, time-sortable identifier (Part 3 §3.3, P03-T03).

Identifiers are opaque strings assigned by the Kernel through an injected
IdSource port; they are never derived from personal data.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Identifier:
    """An opaque, time-sortable identifier."""

    value: str

    def __str__(self) -> str:
        """Return the identifier string."""
        return self.value

    def __len__(self) -> int:
        """Return the length of the identifier string."""
        return len(self.value)

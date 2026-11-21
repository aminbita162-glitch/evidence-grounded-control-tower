"""Kernel ports: injected interfaces for side effects (Part 3 §3.31, P03-T03).

The kernel logic that decides stays synchronous and pure; the ports that
reach persistence are asynchronous interfaces (P04).
"""

from __future__ import annotations

from typing import Protocol

from kernel.types.identifier import Identifier


class Clock(Protocol):
    """Port for obtaining the current UTC instant."""

    def now(self) -> str:
        """Return the current UTC time as an ISO 8601 string."""
        ...


class IdSource(Protocol):
    """Port for generating opaque, time-sortable identifiers."""

    def new_id(self) -> Identifier:
        """Return a new opaque identifier."""
        ...


class RandomSource(Protocol):
    """Port for obtaining random bytes."""

    def random_bytes(self, n: int) -> bytes:
        """Return *n* random bytes."""
        ...

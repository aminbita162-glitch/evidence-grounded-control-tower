"""Time types: UTC instants and whole-second durations (Part 3 §3.3, P03-T03)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Instant:
    """A UTC timestamp as an ISO 8601 string."""

    value: str


@dataclass(frozen=True)
class Duration:
    """A duration in whole seconds."""

    seconds: int

    def __post_init__(self) -> None:
        """Validate that seconds is a non-negative int."""
        if not isinstance(self.seconds, int):
            raise TypeError("Duration.seconds must be int")
        if self.seconds < 0:
            raise ValueError("Duration.seconds must be non-negative")

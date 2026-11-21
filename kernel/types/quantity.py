"""Quantity with explicit unit (Part 3 §3.3, P03-T03)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Quantity:
    """A quantity with an explicit unit.

    Attributes:
        value: The decimal value (never float).
        unit: The unit of measurement.
    """

    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        """Validate that value is a Decimal, not a float."""
        if not isinstance(self.value, Decimal):
            raise TypeError("Quantity.value must be Decimal")
        if isinstance(self.value, float):
            raise TypeError("float is forbidden for Quantity")

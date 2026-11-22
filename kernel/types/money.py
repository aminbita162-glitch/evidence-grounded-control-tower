"""Fixed-point money with ISO 4217 currency (Part 3 §3.3, P03-T03).

Money uses ``decimal.Decimal`` for fixed-point arithmetic with an explicit
rounding mode. Floating point is forbidden for money, quantities and rates.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal


@dataclass(frozen=True)
class Money:
    """A fixed-point monetary amount with an ISO 4217 currency code.

    Attributes:
        amount: The decimal amount (never float).
        currency: ISO 4217 three-letter currency code.
        rounding: The rounding mode for arithmetic.
    """

    amount: Decimal
    currency: str
    rounding: str = ROUND_HALF_EVEN

    def __post_init__(self) -> None:
        """Validate that amount is a Decimal, not a float."""
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money.amount must be Decimal, not float")
        if isinstance(self.amount, float):
            raise TypeError("float is forbidden for Money")
        if len(self.currency) != 3:
            raise ValueError(f"currency must be 3-letter ISO 4217: {self.currency!r}")

    def add(self, other: Money) -> Money:
        """Add two money amounts (must share currency)."""
        if self.currency != other.currency:
            raise ValueError(f"currency mismatch: {self.currency} vs {other.currency}")
        return Money(self.amount + other.amount, self.currency, self.rounding)

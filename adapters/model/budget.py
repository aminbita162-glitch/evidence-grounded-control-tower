"""Budget tracking for model calls (Part 3 §3.14, P08-T03).

Per-case and per-tier budget limits from the case budget:
20 calls, 60,000 tokens, 120 seconds for the meter ``other``.
Extraction calls are drawn from the meter ``extraction``.

Spec: Part 3 §3.14; P08-T03.
"""

from __future__ import annotations

__all__ = [
    "BudgetLimits",
    "BudgetTracker",
    "BudgetExceededError",
    "DEFAULT_LIMITS",
]


class BudgetExceededError(Exception):
    """The case or tier budget has been exceeded."""


class BudgetLimits:
    """Per-case budget limits (Part 3 §3.14).

    Attributes:
        max_calls: Maximum model calls (default 20).
        max_tokens: Maximum model tokens (default 60_000).
        max_seconds: Maximum pipeline wall time (default 120).
    """

    def __init__(
        self,
        max_calls: int = 20,
        max_tokens: int = 60_000,
        max_seconds: int = 120,
    ) -> None:
        self.max_calls = max_calls
        self.max_tokens = max_tokens
        self.max_seconds = max_seconds


DEFAULT_LIMITS: BudgetLimits = BudgetLimits()


class BudgetTracker:
    """Tracks calls and tokens against budget limits per meter.

    Two meters per case: ``extraction`` and ``other``.
    The limits bind the meter ``other``; ``extraction`` has its own ceiling.
    """

    def __init__(self, limits: BudgetLimits | None = None) -> None:
        self._limits = limits or DEFAULT_LIMITS
        self._calls: dict[str, int] = {"extraction": 0, "other": 0}
        self._tokens: dict[str, int] = {"extraction": 0, "other": 0}

    @property
    def limits(self) -> BudgetLimits:
        return self._limits

    def calls(self, meter: str) -> int:
        return self._calls.get(meter, 0)

    def tokens(self, meter: str) -> int:
        return self._tokens.get(meter, 0)

    def check(self, meter: str, calls: int = 1, tokens: int = 0) -> None:
        """Check if adding *calls* and *tokens* to *meter* would exceed limits.

        Raises:
            BudgetExceededError: If the limit would be exceeded.
        """
        if meter not in ("extraction", "other"):
            raise BudgetExceededError(f"unknown meter: {meter}")
        new_calls = self._calls[meter] + calls
        new_tokens = self._tokens[meter] + tokens
        if meter == "other":
            if new_calls > self._limits.max_calls:
                raise BudgetExceededError(
                    f"call budget exceeded: {new_calls} > {self._limits.max_calls}"
                )
            if new_tokens > self._limits.max_tokens:
                raise BudgetExceededError(
                    f"token budget exceeded: {new_tokens} > {self._limits.max_tokens}"
                )
        else:
            if new_calls > self._limits.max_calls:
                raise BudgetExceededError(
                    f"extraction call budget exceeded: {new_calls} > {self._limits.max_calls}"
                )

    def record(self, meter: str, calls: int = 1, tokens: int = 0) -> None:
        """Record that *calls* and *tokens* were consumed on *meter*."""
        if meter not in ("extraction", "other"):
            raise BudgetExceededError(f"unknown meter: {meter}")
        self._calls[meter] += calls
        self._tokens[meter] += tokens

    def remaining_calls(self, meter: str) -> int:
        """Return the remaining call budget for *meter*."""
        return max(0, self._limits.max_calls - self._calls.get(meter, 0))

    def remaining_tokens(self, meter: str) -> int:
        """Return the remaining token budget for *meter*."""
        return max(0, self._limits.max_tokens - self._tokens.get(meter, 0))

"""Choose a stable lexicographic optimum using explicit plan keys."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from decimal import Decimal

type Score = tuple[Decimal | int, ...]
type StableKey = tuple[str, ...]


def choose[T](
    plans: Iterable[T],
    *,
    objective: Callable[[T], Score],
    stable_key: Callable[[T], StableKey],
) -> T | None:
    """Minimize objective coordinates in order, then minimize the explicit key."""
    best: T | None = None
    best_rank: tuple[Score, StableKey] | None = None
    used: set[StableKey] = set()
    arity: int | None = None
    for plan in plans:
        score, key = objective(plan), stable_key(plan)
        if any(
            type(value) is not int and (not isinstance(value, Decimal) or not value.is_finite())
            for value in score
        ):
            raise ValueError("objectives must contain finite exact values")
        if arity is None:
            arity = len(score)
        if not score or len(score) != arity:
            raise ValueError("every plan requires the same nonempty objective dimensions")
        if not key or not all(isinstance(part, str) and part for part in key) or key in used:
            raise ValueError("each plan requires a unique, nonempty stable key")
        used.add(key)
        rank = (score, key)
        if best_rank is None or rank < best_rank:
            best, best_rank = plan, rank
    return best

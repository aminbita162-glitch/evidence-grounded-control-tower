"""Decision value lattice: ALLOW < ABSTAIN < HOLD < ESCALATE (Part 3 §3.8, P03-T03).

The ``combine`` function takes the most severe decision while keeping all
reason codes from every input.
"""

from __future__ import annotations

from enum import IntEnum


class DecisionValue(IntEnum):
    """The four decision values ordered by severity."""

    ALLOW = 0
    ABSTAIN = 1
    HOLD = 2
    ESCALATE = 3


def combine_decisions(
    values: list[DecisionValue], reasons: list[list[str]]
) -> tuple[DecisionValue, list[str]]:
    """Combine decisions: take the most severe, union all reasons.

    Args:
        values: A list of DecisionValue instances.
        reasons: A parallel list of reason-code lists.

    Returns:
        A tuple of (most_severe_value, all_reason_codes).
    """
    if not values:
        return DecisionValue.ALLOW, []
    most_severe = max(values)
    all_reasons: list[str] = []
    for r in reasons:
        all_reasons.extend(r)
    return most_severe, all_reasons

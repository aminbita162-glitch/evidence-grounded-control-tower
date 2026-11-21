"""Core value types for the kernel (Part 3 §3.3, P03-T03).

Identifiers, money, time, quantities, labels, decision values.
"""

from __future__ import annotations

from kernel.types.decision import DecisionValue, combine_decisions
from kernel.types.identifier import Identifier
from kernel.types.label import Label, is_allow_eligible, label_rank, weakest_of
from kernel.types.money import Money
from kernel.types.quantity import Quantity
from kernel.types.time import Duration, Instant

__all__ = [
    "DecisionValue",
    "Duration",
    "Identifier",
    "Instant",
    "Label",
    "Money",
    "Quantity",
    "combine_decisions",
    "is_allow_eligible",
    "label_rank",
    "weakest_of",
]

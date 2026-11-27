"""Derive deterministic unblock items from declared reasons and dependencies."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict

from kernel.types.decision import DecisionValue

__all__ = [
    "OpenItem",
    "Requirement",
    "RequirementKind",
    "UnblockItem",
    "open_items",
    "requirements_for",
]


class RequirementKind(StrEnum):
    """Kinds of input that can change a blocked result."""

    FACT = "FACT"
    PACK = "PACK"
    VERIFICATION = "VERIFICATION"
    FEED = "FEED"
    CONFIGURATION = "CONFIGURATION"


@dataclass(frozen=True, order=True, slots=True)
class Requirement:
    """Identify a missing or conflicting input."""

    kind: RequirementKind
    name: str

    def __post_init__(self) -> None:
        """Require the exact name of the affected input."""
        if not self.name.strip():
            raise ValueError("requirement name is required")


@dataclass(frozen=True, order=True, slots=True)
class UnblockItem:
    """One necessary input and the reasons it affects."""

    requirement: Requirement
    reasons: tuple[str, ...]


class OpenItem(TypedDict):
    """Open item included in the unsigned Passport payload."""

    kind: str
    name: str
    reasons: list[str]


type Alternatives = tuple[tuple[Requirement, ...], ...]
type Choice = tuple[tuple[str, tuple[Requirement, ...]], ...]


def requirements_for(
    outcome: DecisionValue,
    reason_codes: Iterable[str],
    rules: Mapping[str, Alternatives],
    *,
    resolved: Iterable[Requirement] = (),
) -> tuple[UnblockItem, ...]:
    """Choose the smallest union of outstanding inputs across all active reasons.

    Each reason supplies one or more alternatives, each a complete conjunction of
    requirements for that reason. Equal-size solutions are ordered by kind and name.
    """
    if outcome is DecisionValue.ALLOW:
        return ()
    satisfied = frozenset(resolved)
    candidates: dict[frozenset[Requirement], Choice] = {frozenset(): ()}
    for reason in sorted(set(reason_codes)):
        alternatives = rules.get(reason)
        if not alternatives:
            raise ValueError(f"no unblock declaration for {reason}")
        options = sorted({tuple(sorted(set(option) - satisfied)) for option in alternatives})
        next_candidates: dict[frozenset[Requirement], Choice] = {}
        for prior, choice in candidates.items():
            for option in options:
                combined = prior.union(option)
                next_candidates.setdefault(combined, (*choice, (reason, option)))
        candidates = next_candidates
    selected = min(candidates, key=lambda requirements: (len(requirements), sorted(requirements)))
    causes: dict[Requirement, list[str]] = {requirement: [] for requirement in sorted(selected)}
    for reason, items in candidates[selected]:
        for item in items:
            causes[item].append(reason)
    return tuple(UnblockItem(item, tuple(reasons)) for item, reasons in causes.items())


def open_items(requirements: Iterable[UnblockItem]) -> list[OpenItem]:
    """Render the open items to include before canonicalizing and signing."""
    return [
        {
            "kind": item.requirement.kind,
            "name": item.requirement.name,
            "reasons": list(item.reasons),
        }
        for item in sorted(requirements)
    ]

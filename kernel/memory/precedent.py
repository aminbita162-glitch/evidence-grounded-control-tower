"""M3 precedent memory (Part 3 §3.23, P11-T05).

Abstracted outcomes of closed, human-reviewed cases.  Advisory only:
it may rank, prioritise or prompt a reviewer; it can never be evidence
for ALLOW and never changes a Decision.  Aggregates require at least 5
contributing cases (k-threshold) and carry the label DERIVED with the
sample size.

Spec: Part 3 §3.23; Part 4 §4.4; P11-T05.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "K_THRESHOLD",
    "PrecedentEntry",
    "PrecedentMemory",
    "PrecedentError",
]

K_THRESHOLD: int = 5


class PrecedentError(Exception):
    """Raised when a precedent operation is invalid."""


@dataclass
class PrecedentEntry:
    """An M3 precedent entry (Part 3 §3.23).

    Attributes:
        case_id: the closed case id.
        tenant_id: the tenant id.
        decision: the decision outcome (ALLOW, HOLD, etc.).
        reason_codes: the reason codes.
        approved_by: who approved the outcome.
        label: always DERIVED (M3 is advisory).
    """

    case_id: str
    tenant_id: str
    decision: str
    reason_codes: list[str] = field(default_factory=list)
    approved_by: str = ""
    label: str = "DERIVED"


class PrecedentMemory:
    """M3 precedent memory (Part 3 §3.23).

    Precedent entries arise only from human-approved outcomes.  They
    are advisory: M3 can never produce ALLOW.  Aggregates require at
    least ``K_THRESHOLD`` contributing cases.
    """

    def __init__(self, *, k_threshold: int = K_THRESHOLD) -> None:
        """Create a precedent memory store.

        Args:
            k_threshold: the minimum number of cases for an aggregate.
        """
        self._entries: list[PrecedentEntry] = []
        self._k = k_threshold

    def add_entry(self, entry: PrecedentEntry) -> None:
        """Add a precedent entry.

        Entries arise only from human-approved outcomes.

        Args:
            entry: the precedent entry.

        Raises:
            PrecedentError: if the entry has no approver.
        """
        if not entry.approved_by:
            raise PrecedentError("precedent entries require an approver")
        self._entries.append(entry)

    def aggregate(self, tenant_id: str) -> dict[str, object]:
        """Aggregate precedent outcomes for a tenant.

        Aggregates require at least ``K_THRESHOLD`` contributing cases
        and carry the label DERIVED with the sample size.

        Args:
            tenant_id: the tenant id.

        Returns:
            A dict with the aggregate, or an empty dict if below
            the k-threshold.

        Raises:
            PrecedentError: if the aggregate would produce ALLOW.
        """
        tenant_entries = [e for e in self._entries if e.tenant_id == tenant_id]
        if len(tenant_entries) < self._k:
            return {}
        decision_counts: dict[str, int] = {}
        for e in tenant_entries:
            decision_counts[e.decision] = decision_counts.get(e.decision, 0) + 1
        if "ALLOW" in decision_counts:
            raise PrecedentError("M3 can never produce ALLOW")
        return {
            "label": "DERIVED",
            "sample_size": len(tenant_entries),
            "decision_counts": decision_counts,
        }

    def can_produce_allow(self) -> bool:
        """M3 can never produce ALLOW.

        Returns:
            Always False.
        """
        return False

    @property
    def k_threshold(self) -> int:
        """The k-threshold for aggregates."""
        return self._k

    def count(self, tenant_id: str) -> int:
        """Count entries for a tenant.

        Args:
            tenant_id: the tenant id.

        Returns:
            The number of entries.
        """
        return sum(1 for e in self._entries if e.tenant_id == tenant_id)

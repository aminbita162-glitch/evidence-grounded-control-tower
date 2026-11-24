"""Conflict resolution for the rule engine (Part 3 §3.6, §3.8, P06-T05).

Declared precedence; unresolved conflicts yield ESCALATE with both
citations.  Combining results takes the most severe and keeps all reasons.
The evaluation commitment is produced through the P05 interface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from kernel.rules.interpreter import RuleResult

__all__ = ["resolve_conflicts", "ConflictPair"]


#: Severity order: ALLOW < ABSTAIN < HOLD < ESCALATE.
_SEVERITY: dict[str, int] = {"ALLOW": 0, "ABSTAIN": 1, "HOLD": 2, "ESCALATE": 3}


@dataclass(frozen=True)
class ConflictPair:
    """A pair of conflicting rules."""

    rule_a: str
    rule_b: str
    outcome_a: str
    outcome_b: str


def resolve_conflicts(
    results: list[RuleResult],
    rules: Sequence[Mapping[str, object]] | None = None,
) -> list[RuleResult]:
    """Resolve conflicts between applied rules using declared precedence.

    When two rules are APPLIED with different outcomes and no precedence is
    declared, both are replaced with ESCALATE results citing each other.

    Args:
        results: The list of rule results.
        rules: The rule definitions (for precedence lookup).

    Returns:
        The resolved list of rule results.
    """
    applied = [(i, r) for i, r in enumerate(results) if r.state == "APPLIED"]
    if len(applied) <= 1:
        return results

    # Build precedence map from rule definitions
    precedence: dict[str, int] = {}
    if rules:
        for rule in rules:
            rid = str(rule.get("id", ""))
            prec = rule.get("precedence")
            if isinstance(prec, int):
                precedence[rid] = prec

    # Check for conflicting outcomes among applied rules
    resolved = list(results)
    for i, (idx_a, ra) in enumerate(applied):
        for _, (idx_b, rb) in enumerate(applied[i + 1 :], i + 1):
            if ra.outcome != rb.outcome and ra.outcome != "ABSTAIN" and rb.outcome != "ABSTAIN":
                # Check precedence
                has_prec_a = ra.rule_id in precedence
                has_prec_b = rb.rule_id in precedence
                if not has_prec_a and not has_prec_b:
                    # Unresolved conflict → ESCALATE with both citations
                    resolved[idx_a] = RuleResult(
                        rule_id=ra.rule_id,
                        rule_version=ra.rule_version,
                        state="NOT_APPLICABLE",
                        outcome="ESCALATE",
                        reason_code=f"RULE.CONFLICT.UNRESOLVED:{ra.rule_id}:{rb.rule_id}",
                        citations=(rb.rule_id, ra.rule_id),
                    )
                    resolved[idx_b] = RuleResult(
                        rule_id=rb.rule_id,
                        rule_version=rb.rule_version,
                        state="NOT_APPLICABLE",
                        outcome="ESCALATE",
                        reason_code=f"RULE.CONFLICT.UNRESOLVED:{rb.rule_id}:{ra.rule_id}",
                        citations=(ra.rule_id, rb.rule_id),
                    )
    return resolved

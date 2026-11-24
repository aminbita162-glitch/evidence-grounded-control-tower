"""Result combination for the rule engine (Part 3 §3.8, P06-T05).

Combining results takes the most severe outcome (ALLOW < ABSTAIN < HOLD <
ESCALATE) and keeps all reasons.  ALLOW is impossible with a
SECONDARY-or-weaker datum.  The evaluation commitment is produced through
the P05 interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from kernel.rules.interpreter import RuleResult

__all__ = ["CombinedResult", "combine_results"]


#: Severity order: ALLOW < ABSTAIN < HOLD < ESCALATE.
_SEVERITY: dict[str, int] = {"ALLOW": 0, "ABSTAIN": 1, "HOLD": 2, "ESCALATE": 3}

#: Labels that block ALLOW (SECONDARY or weaker).
_BLOCK_ALLOW: set[str] = {"SECONDARY", "SYNTHETIC", "SIMULATED_RULE", "ASSUMPTION", "UNVERIFIED"}


@dataclass(frozen=True)
class CombinedResult:
    """The combined outcome of all rule results.

    Attributes:
        outcome: The most severe outcome.
        reason_codes: All reason codes from all results.
        citations: All citations from ESCALATE results.
        rule_ids: All rule IDs that contributed.
    """

    outcome: str
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    citations: tuple[str, ...] = field(default_factory=tuple)
    rule_ids: tuple[str, ...] = field(default_factory=tuple)


def combine_results(
    results: list[RuleResult],
    rule_labels: dict[str, str] | None = None,
) -> CombinedResult:
    """Combine rule results into a single outcome.

    The combination takes the most severe outcome and keeps all reason
    codes.  ALLOW is impossible with a SECONDARY-or-weaker datum.

    Args:
        results: The list of rule results to combine.
        rule_labels: Mapping from rule_id to label for the ALLOW check.

    Returns:
        A :class:`CombinedResult` with the combined outcome.
    """
    if not results:
        return CombinedResult(outcome="ABSTAIN")

    # Find the most severe outcome among APPLIED rules
    applied = [r for r in results if r.state == "APPLIED"]
    if not applied:
        # Check for ESCALATE from non-applied (e.g., conflicted facts)
        escalates = [r for r in results if r.outcome == "ESCALATE"]
        outcome = "ESCALATE" if escalates else "ABSTAIN"
    else:
        outcome = max((r.outcome for r in applied), key=lambda o: _SEVERITY.get(o, 0))

    # Collect all reason codes and citations
    all_reasons: list[str] = []
    all_citations: list[str] = []
    all_rule_ids: list[str] = []
    for r in results:
        all_reasons.append(r.reason_code)
        all_citations.extend(r.citations)
        all_rule_ids.append(r.rule_id)

    # ALLOW is impossible with a SECONDARY-or-weaker datum
    if outcome == "ALLOW" and rule_labels:
        for rid in all_rule_ids:
            lbl = rule_labels.get(rid)
            if lbl and lbl in _BLOCK_ALLOW:
                outcome = "ABSTAIN"
                all_reasons.append(f"RULE.LABEL_BLOCK:{lbl}")
                break

    return CombinedResult(
        outcome=outcome,
        reason_codes=tuple(all_reasons),
        citations=tuple(all_citations),
        rule_ids=tuple(all_rule_ids),
    )

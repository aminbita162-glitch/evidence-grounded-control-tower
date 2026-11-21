"""ALLOW eligibility evaluation (Part 3 §3.8, P03-T04).

ALLOW requires every required fact present and VERIFIED, no rule failure,
and every contributing datum OFFICIAL or DERIVED. A SECONDARY-or-weaker
datum yields ABSTAIN. SYNTHETIC-origin ALLOW is stamped. A CALIBRATED_SYNTHETIC
artifact on real data becomes ESCALATE; VALIDATED_TENANT stays ALLOW.
"""

from __future__ import annotations

from dataclasses import dataclass

from kernel.types.decision import DecisionValue
from kernel.types.label import is_allow_eligible


@dataclass(frozen=True)
class FactEntry:
    """A fact with its label for eligibility checking."""

    key: str
    value: str
    status: str
    label: str


@dataclass(frozen=True)
class EligibilityResult:
    """Result of ALLOW eligibility evaluation."""

    value: DecisionValue
    reason_codes: list[str]
    stamped_label: str | None = None


def evaluate_allow(
    facts: list[FactEntry],
    required_keys: list[str],
    rule_failures: list[str],
    data_origin: str,
    calibration_basis: str | None,
) -> EligibilityResult:
    """Evaluate ALLOW eligibility per Part 3 §3.8 and decision D-26.

    Args:
        facts: All fact entries with their labels.
        required_keys: Fact keys that must be present and VERIFIED.
        rule_failures: A list of rule failure reason codes (empty = no failures).
        data_origin: The data origin label (e.g. "SYNTHETIC").
        calibration_basis: The calibration artifact class, if any.

    Returns:
        An EligibilityResult with the decision value and reason codes.
    """
    reasons: list[str] = []
    fact_map = {f.key: f for f in facts}

    # Check for missing facts.
    for key in required_keys:
        entry = fact_map.get(key)
        if entry is None:
            return EligibilityResult(DecisionValue.ABSTAIN, [f"MISSING_FACT:{key}"])
        if entry.status != "VERIFIED":
            return EligibilityResult(DecisionValue.ABSTAIN, [f"UNVERIFIED_FACT:{key}"])

    # Check for rule failures.
    if rule_failures:
        return EligibilityResult(DecisionValue.HOLD, list(rule_failures))

    # Check labels: SECONDARY or weaker cannot be ALLOW.
    for f in facts:
        if f.key in required_keys and not is_allow_eligible(f.label):
            return EligibilityResult(
                DecisionValue.ABSTAIN,
                [f"WEAK_LABEL:{f.key}:{f.label}"],
            )

    # Check calibration basis on real (non-SYNTHETIC) data.
    if data_origin != "SYNTHETIC":
        if calibration_basis is None:
            return EligibilityResult(
                DecisionValue.ABSTAIN,
                ["MISSING_CALIBRATION_BASIS"],
            )
        if calibration_basis == "CALIBRATED_SYNTHETIC":
            return EligibilityResult(
                DecisionValue.ESCALATE,
                ["REVIEW.UNVALIDATED_CALIBRATION"],
            )
        if calibration_basis != "VALIDATED_TENANT":
            return EligibilityResult(
                DecisionValue.ABSTAIN,
                [f"UNKNOWN_CALIBRATION:{calibration_basis}"],
            )

    # ALLOW is eligible.
    stamped = "SYNTHETIC" if data_origin == "SYNTHETIC" else None
    return EligibilityResult(DecisionValue.ALLOW, [], stamped)

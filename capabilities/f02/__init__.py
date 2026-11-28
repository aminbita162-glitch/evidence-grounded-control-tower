"""Judge the consistency of a declared classification with verified line facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime
from enum import StrEnum

from capabilities.f02.calibration import Calibration
from capabilities.f02.scoring import (
    ALPHA,
    CALIBRATION_MINIMUM,
    CHAPTER_MINIMUM,
    MAX_CANDIDATES,
    Candidate,
    Exclusion,
    TariffIndex,
    tokenize,
)
from kernel.decision import FactEntry, evaluate_allow
from kernel.types.decision import DecisionValue

BANNER = "advisory consistency check, not an official classification"
COVERAGE_CLAIM = (
    "On the SYNTHETIC calibration distribution, and assuming exchangeability, "
    "the true code lies in the candidate set with probability at least 90 percent "
    "(marginal). This statement does not apply to real goods descriptions or to any single chapter."
)


class Reason(StrEnum):
    OK = "F02.OK.CONSISTENT"
    MULTIPLE = "F02.AMBIGUOUS.MULTIPLE_CANDIDATES"
    OUTSIDE = "F02.MISMATCH.OUTSIDE_SET"
    INVALID = "F02.CODE.INVALID"
    EXPIRED = "F02.CODE.NOT_VALID_AT_TIME"
    SET_EMPTY = "F02.ABSTAIN.SET_EMPTY"
    SET_TOO_LARGE = "F02.ABSTAIN.SET_TOO_LARGE"
    DESCRIPTION_MISSING = "F02.ABSTAIN.DESCRIPTION_MISSING"
    DESCRIPTION_TOO_SHORT = "F02.ABSTAIN.DESCRIPTION_TOO_SHORT"
    LANGUAGE_UNSUPPORTED = "F02.ABSTAIN.LANGUAGE_UNSUPPORTED"
    TARIFF_UNAVAILABLE = "F02.ABSTAIN.TARIFF_UNAVAILABLE"
    CALIBRATION_STALE = "F02.ABSTAIN.CALIBRATION_STALE"
    UPSTREAM = "F02.ABSTAIN.UPSTREAM"
    LABEL_INSUFFICIENT = "F02.ABSTAIN.LABEL_INSUFFICIENT"
    UNVALIDATED = "F02.REVIEW.UNVALIDATED_CALIBRATION"


_EXPLANATIONS = {
    Reason.OK: "The declared code matches the single candidate at the resolved level.",
    Reason.MULTIPLE: "The declared code is consistent with more than one candidate.",
    Reason.OUTSIDE: "The declared code falls outside the candidate set.",
    Reason.INVALID: "The declared code is absent from the tariff pack.",
    Reason.EXPIRED: "The declared code is outside its validity window.",
    Reason.SET_EMPTY: "The calibrated set is empty.",
    Reason.SET_TOO_LARGE: "The calibrated set exceeds the size limit.",
    Reason.DESCRIPTION_MISSING: "A verified description is required.",
    Reason.DESCRIPTION_TOO_SHORT: "The description has fewer than three usable tokens.",
    Reason.LANGUAGE_UNSUPPORTED: "The description language has no supported calibration.",
    Reason.TARIFF_UNAVAILABLE: "The tariff pack is unavailable at the evaluation instant.",
    Reason.CALIBRATION_STALE: "Calibration is unavailable for the current tariff version.",
    Reason.UPSTREAM: "The consistency graph has not published the required line facts.",
    Reason.LABEL_INSUFFICIENT: "The provenance of required inputs does not support an ALLOW.",
    Reason.UNVALIDATED: "A tenant calibration is required before this result can support an ALLOW.",
}


@dataclass(frozen=True, slots=True)
class Line:
    line_id: str
    declared: FactEntry | None
    description: FactEntry | None
    attributes: tuple[FactEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class LineResult:
    key: str
    declared_code: str
    resolved_level: int | None
    outcome: DecisionValue
    reason: Reason
    candidates: tuple[Candidate, ...] = ()
    exclusions: tuple[Exclusion, ...] = ()
    expansion: tuple[tuple[str, tuple[str, ...]], ...] = ()
    calibration: Calibration | None = None


@dataclass(frozen=True, slots=True)
class ClassificationReport:
    outcome: DecisionValue
    reasons: tuple[Reason, ...]
    lines: tuple[LineResult, ...]
    languages: tuple[str, ...]
    synthetic: bool

    def view(self, role: str) -> dict[str, object]:
        """Render fixed prose and score-ranked candidates for the case view."""
        return {
            "banner": BANNER,
            "outcome": self.outcome.name,
            "reason_codes": self.reasons,
            "lines": [_view_line(line) for line in self.lines],
            "languages": self.languages,
            "label": "SYNTHETIC" if self.synthetic else None,
        }


def _view_line(line: LineResult) -> dict[str, object]:
    calibration = line.calibration
    return {
        "line_id": line.key,
        "declared_code": line.declared_code,
        "resolved_level": line.resolved_level,
        "candidates": [
            {"code": candidate.code, "score": candidate.score, "rank": rank}
            for rank, candidate in enumerate(line.candidates, 1)
        ],
        "exclusions": [{"rule_id": rule.rule_id, "code": rule.code} for rule in line.exclusions],
        "glossary_expansion": line.expansion,
        "outcome": line.outcome.name,
        "reason_codes": (line.reason,),
        "explanation": _EXPLANATIONS[line.reason],
        "coverage_claim": COVERAGE_CLAIM if calibration else None,
        "language": calibration.language if calibration else None,
        "threshold": calibration.threshold if calibration else None,
        "alpha": calibration.alpha if calibration else None,
        "calibration_basis": (
            {
                "artifact_id": calibration.artifact_id,
                "hash": calibration.digest,
                "validation_class": calibration.validation_class,
            }
            if calibration
            else None
        ),
        "diagnostics": (
            {
                "held_out": [asdict(point) for point in calibration.held_out],
                "shifted": [asdict(point) for point in calibration.shifted],
            }
            if calibration
            else None
        ),
    }


def _line(
    line: Line,
    index: TariffIndex,
    calibration: Mapping[str, Calibration],
    at: datetime,
    origin: str,
) -> LineResult:
    pack = index.pack
    declared = line.declared
    description = line.description
    result = LineResult(
        line.line_id,
        declared.value if declared else "",
        None,
        DecisionValue.ABSTAIN,
        Reason.UPSTREAM,
    )
    if declared is None or declared.status != "VERIFIED":
        return result
    entry = index.entries.get(declared.value)
    if entry is None:
        return replace(result, outcome=DecisionValue.HOLD, reason=Reason.INVALID)
    if not entry.valid_at(at):
        return replace(result, outcome=DecisionValue.HOLD, reason=Reason.EXPIRED)
    if description is None or description.status != "VERIFIED" or not description.value.strip():
        return replace(result, reason=Reason.DESCRIPTION_MISSING)

    tokens = tokenize(description.value, pack)
    if not tokens.supported:
        return replace(result, reason=Reason.LANGUAGE_UNSUPPORTED)
    if len(set(tokens.terms)) < 3:
        return replace(result, reason=Reason.DESCRIPTION_TOO_SHORT)
    bound = calibration.get(tokens.language)
    if bound is None:
        return replace(result, reason=Reason.LANGUAGE_UNSUPPORTED)
    if (
        bound.pack_hash != index.pack_hash
        or bound.language != tokens.language
        or bound.alpha != ALPHA
        or not 0 <= bound.threshold <= 1
        or bound.chapter_count != len(pack.chapters)
        or bound.count < max(CALIBRATION_MINIMUM, CHAPTER_MINIMUM * bound.chapter_count)
        or set(dict(bound.counts)) != pack.chapters
        or any(count < CHAPTER_MINIMUM for _, count in bound.counts)
    ):
        return replace(result, reason=Reason.CALIBRATION_STALE)

    resolved = min(len(declared.value), pack.resolution)
    result = replace(result, resolved_level=resolved, expansion=tokens.expansion, calibration=bound)
    declared_prefix = declared.value[:resolved]
    verified_attributes = tuple(fact for fact in line.attributes if fact.status == "VERIFIED")
    attributes = [
        extra for fact in verified_attributes if (extra := tokenize(fact.value, pack)).supported
    ]
    query = (*tokens.terms, *(term for extra in attributes for term in extra.terms))
    expansion = tuple(
        sorted({*tokens.expansion, *(item for extra in attributes for item in extra.expansion)})
    )
    result = replace(result, expansion=expansion)
    complete = index.candidates(query, at, bound.threshold)
    candidates, applied = index.filter(complete, line.attributes)
    result = replace(result, candidates=candidates, exclusions=applied)
    # Read every verified applicability label that changed the set.
    labels = (
        pack.label,
        declared.label,
        description.label,
        *(fact.label for fact in verified_attributes),
    )
    facts = [
        FactEntry(
            str(number),
            "",
            "VERIFIED",
            "DERIVED" if label == "SYNTHETIC" and origin == "SYNTHETIC" else label,
        )
        for number, label in enumerate(labels)
    ]
    eligibility = evaluate_allow(
        facts, [fact.key for fact in facts], [], origin, bound.validation_class
    )
    if eligibility.value == DecisionValue.ABSTAIN:
        return replace(result, reason=Reason.LABEL_INSUFFICIENT)

    if not candidates:
        return replace(result, reason=Reason.SET_EMPTY)
    if len(candidates) > MAX_CANDIDATES:
        return replace(result, reason=Reason.SET_TOO_LARGE)
    if not any(candidate.code[:resolved] == declared_prefix for candidate in candidates):
        return replace(result, outcome=DecisionValue.ESCALATE, reason=Reason.OUTSIDE)
    if len(candidates) != 1:
        return replace(result, outcome=DecisionValue.ESCALATE, reason=Reason.MULTIPLE)
    reason = Reason.OK if eligibility.value == DecisionValue.ALLOW else Reason.UNVALIDATED
    return replace(result, outcome=eligibility.value, reason=reason)


def evaluate(
    lines: Sequence[Line],
    *,
    index: TariffIndex | None,
    calibration: Mapping[str, Calibration],
    at: datetime,
    data_origin: str,
) -> ClassificationReport:
    """Evaluate each line and select the most severe case result."""
    synthetic = data_origin == "SYNTHETIC"
    if not lines:
        return ClassificationReport(DecisionValue.ABSTAIN, (Reason.UPSTREAM,), (), (), synthetic)
    if index is None or at.utcoffset() is None or not index.pack.starts <= at <= index.pack.ends:
        return ClassificationReport(
            DecisionValue.ABSTAIN, (Reason.TARIFF_UNAVAILABLE,), (), (), synthetic
        )
    results = tuple(
        _line(line, index, calibration, at, data_origin)
        for line in sorted(lines, key=lambda line: line.line_id)
    )
    languages = tuple(
        sorted(
            language
            for language, bound in calibration.items()
            if language in index.pack.languages and bound.pack_hash == index.pack_hash
        )
    )
    return ClassificationReport(
        max(line.outcome for line in results),
        tuple(sorted({line.reason for line in results})),
        results,
        languages,
        synthetic,
    )

"""Ground Arabic and English extraction proposals to immutable document text."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import date
from typing import ClassVar, Literal, Protocol

from pydantic import BaseModel, ConfigDict

from kernel.budget import BudgetBreach
from kernel.hashing import domain_hash
from kernel.intake import IntakeDocument, ScriptProfile, profile
from kernel.lib.text import comparison_form, digits, normalize_unit, parse_date, parse_number

type FieldKind = Literal["text", "identifier", "number", "quantity", "date", "unit"]
type FactStatus = Literal["VERIFIED", "PROPOSED", "UNKNOWN"]
_DATE_DIGITS = re.compile(r"\d+(?:[/.-]\d+)*")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9 ._/-]{0,127}", re.ASCII)


@dataclass(frozen=True)
class Field:
    name: str
    kind: FieldKind
    pattern: str | None = None


class Candidate(BaseModel):  # type: ignore[explicit-any]
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", strict=True, frozen=True)

    field: str
    segment: int
    start: int
    end: int
    quote: str
    value: str
    calendar: Literal["gregorian", "hijri"] = "gregorian"


@dataclass(frozen=True)
class ModelEvidence:
    model_id: str
    prompt_hash: str
    response_hash: str


@dataclass(frozen=True)
class Extraction:
    candidates: tuple[Candidate, ...]
    evidence: ModelEvidence


class ModelUnavailable(Exception):
    """The configured extraction provider has no usable response."""


class ExtractionModel(Protocol):
    async def extract(
        self,
        document: IntakeDocument,
        fields: Sequence[Field],
    ) -> Extraction: ...


@dataclass(frozen=True)
class GroundedFact:
    name: str
    kind: FieldKind
    status: FactStatus = "UNKNOWN"
    original: str = ""
    normalized: str | None = None
    flags: tuple[str, ...] = ()
    page: int | None = None
    segment: int | None = None
    span: tuple[int, int] | None = None
    origin: str | None = None
    unit: str | None = None


@dataclass(frozen=True)
class NameLink:
    field: str
    left: str
    right: str
    variants: tuple[str, ...]


@dataclass(frozen=True)
class BilingualIntakeReport:
    document_id: str
    document_hash: str
    profile: ScriptProfile
    status: str
    reason_codes: tuple[str, ...]
    facts: tuple[GroundedFact, ...] = ()
    calls: tuple[ModelEvidence, ...] = ()
    normalization_counts: tuple[tuple[str, int], ...] = ()
    name_link_proposals: tuple[NameLink, ...] = ()
    parallel_fields: tuple[str, ...] = ()
    pack_version: str = "1.0.0"

    @property
    def output_hash(self) -> str:
        return domain_hash("ctc/payload/v1", asdict(self))


@dataclass(frozen=True)
class ExtractionPolicy:
    date_order: str | None = None
    hijri: Callable[[str], date] | None = None
    ocr_confidence: float = 85.0


def _typed_value(
    field: Field, value: str, calendar: str, policy: ExtractionPolicy
) -> tuple[str, str | None]:
    normalized = comparison_form(value)
    match field.kind:
        case "number":
            return format(parse_number(value), "f"), None
        case "quantity":
            number, unit = re.split(r"\s+", value.strip(), maxsplit=1)
            return format(parse_number(number), "f"), normalize_unit(unit)
        case "date":
            if any(digits(m.group()).mixed for m in _DATE_DIGITS.finditer(value)):
                raise ValueError("MIXED_DIGITS")
            return parse_date(
                value, locale_order=policy.date_order, calendar=calendar, convert_hijri=policy.hijri
            ), None
        case "unit":
            return normalize_unit(value), None
        case "identifier":
            if digits(value).mixed:
                raise ValueError("MIXED_DIGITS")
            if not re.fullmatch(field.pattern or _IDENTIFIER, normalized):
                raise ValueError("INVALID_IDENTIFIER")
    return normalized, None


def ground(
    document: IntakeDocument,
    field: Field,
    candidate: Candidate,
    policy: ExtractionPolicy,
) -> GroundedFact:
    missing = GroundedFact(field.name, field.kind)
    if not 0 <= candidate.segment < len(document.reading.segments):
        return missing
    segment = document.reading.segments[candidate.segment]
    if not 0 <= candidate.start < candidate.end <= len(segment.text):
        return missing
    original = segment.text[candidate.start : candidate.end]
    fact = replace(
        missing,
        original=original,
        page=segment.page,
        segment=candidate.segment,
        span=(candidate.start, candidate.end),
        origin=segment.origin,
    )
    if not comparison_form(original) or comparison_form(original) != comparison_form(
        candidate.quote
    ):
        return missing
    source_profile = profile(original)
    if (
        source_profile.other
        and source_profile.other * 5
        > (source_profile.arabic + source_profile.latin + source_profile.other) * 2
    ):
        return replace(fact, flags=("OTHER_LANGUAGE_PART",))
    if segment.origin == "OCR" and (segment.confidence or 0) < policy.ocr_confidence:
        return replace(fact, flags=("OCR_LOW_CONFIDENCE",))
    try:
        value, unit = _typed_value(field, original, candidate.calendar, policy)
        claimed = _typed_value(field, candidate.value, candidate.calendar, policy)
    except (ValueError, KeyError) as exc:
        flag = str(exc)
        if flag in {"MIXED_DIGITS", "AMBIGUOUS_DATE", "HIJRI_UNCONVERTED"}:
            return replace(fact, flags=(flag,))
        return missing
    if (value, unit) != claimed:
        return missing
    if segment.origin == "OCR":
        return replace(
            fact, status="PROPOSED", normalized=value, unit=unit, flags=("OCR_UNCONFIRMED",)
        )
    return replace(fact, status="VERIFIED", normalized=value, unit=unit)


def _ground_batch(
    document: IntakeDocument,
    fields: Sequence[Field],
    extraction: Extraction,
    policy: ExtractionPolicy,
) -> dict[str, GroundedFact]:
    candidates: dict[str, list[Candidate]] = {}
    for candidate in extraction.candidates:
        candidates.setdefault(candidate.field, []).append(candidate)
    return {
        field.name: (
            ground(document, field, items[0], policy)
            if len(items := candidates.get(field.name, [])) == 1
            else GroundedFact(field.name, field.kind)
        )
        for field in fields
    }


_REVIEW_FLAGS = {
    "MIXED_DIGITS": "MIXED_DIGITS",
    "AMBIGUOUS_DATE": "AMBIGUOUS_DATE",
    "OCR_UNCONFIRMED": "OCR_UNCONFIRMED",
    "OCR_LOW_CONFIDENCE": "OCR_UNCONFIRMED",
}


class BilingualIntake:
    def __init__(
        self,
        model: ExtractionModel | None,
        policy: ExtractionPolicy | None = None,
    ) -> None:
        self._model = model
        self._policy = policy or ExtractionPolicy()

    async def evaluate(
        self,
        document: IntakeDocument,
        fields: Sequence[Field],
    ) -> BilingualIntakeReport:
        base = BilingualIntakeReport(
            document.record.document_id, document.record.sha256, document.scripts, "ABSTAINED", ()
        )
        if not document.reading.segments:
            return replace(base, reason_codes=("K14.ABSTAIN.TEXT_UNAVAILABLE",))
        if not document.scripts.supported:
            return replace(base, reason_codes=("K14.ABSTAIN.LANGUAGE_UNSUPPORTED",))
        if self._model is None:
            return replace(base, reason_codes=("K14.ABSTAIN.MODEL_UNAVAILABLE",))

        calls: list[ModelEvidence] = []
        facts: dict[str, GroundedFact] = {}
        remaining = list(fields)
        for _ in range(2):
            if not remaining:
                break
            try:
                extraction = await self._model.extract(document, remaining)
            except BudgetBreach as exc:
                if exc.meter == "extraction":
                    return replace(
                        base,
                        status="NEEDS_REVIEW",
                        calls=tuple(calls),
                        facts=tuple(facts.values()),
                        reason_codes=("K14.NEEDS_REVIEW.EXTRACTION_BUDGET",),
                    )
                return replace(base, calls=tuple(calls), reason_codes=("K14.ABSTAIN.BUDGET",))
            except ModelUnavailable:
                if not calls:
                    return replace(base, reason_codes=("K14.ABSTAIN.MODEL_UNAVAILABLE",))
                break
            calls.append(extraction.evidence)
            facts.update(_ground_batch(document, remaining, extraction, self._policy))
            remaining = [
                f
                for f in remaining
                if facts[f.name].status == "UNKNOWN" and not facts[f.name].flags
            ]
        flags = {flag for fact in facts.values() for flag in fact.flags}
        review = tuple(
            sorted({f"K14.NEEDS_REVIEW.{_REVIEW_FLAGS[f]}" for f in flags if f in _REVIEW_FLAGS})
        )
        partial = flags or any(fact.status == "UNKNOWN" for fact in facts.values())
        if not review:
            review = ("K14.INTAKE.PARTIAL" if partial else "K14.INTAKE.PROVIDED",)
        pairs = zip(document.reading.segments, document.comparison_segments, strict=True)
        changed = sum(segment.text != comparison for segment, comparison in pairs)
        return replace(
            base,
            status="NEEDS_REVIEW"
            if any(code.startswith("K14.NEEDS_REVIEW.") for code in review)
            else "PROVIDED",
            reason_codes=review,
            facts=tuple(facts.values()),
            calls=tuple(calls),
            normalization_counts=(("comparison_segments_changed", changed),),
        )


def parallel_differences(
    left: BilingualIntakeReport,
    right: BilingualIntakeReport,
) -> tuple[str, ...]:
    comparable = {"number", "quantity", "date", "identifier", "unit"}
    first = {
        f.name: (f.normalized, f.unit)
        for f in left.facts
        if f.kind in comparable and f.status == "VERIFIED"
    }
    second = {
        f.name: (f.normalized, f.unit)
        for f in right.facts
        if f.kind in comparable and f.status == "VERIFIED"
    }
    return tuple(
        sorted(name for name in first.keys() & second.keys() if first[name] != second[name])
    )


def name_links(
    left: BilingualIntakeReport,
    right: BilingualIntakeReport,
    variants: Mapping[str, Sequence[str]],
) -> tuple[NameLink, ...]:
    names = {f.name: f for f in right.facts if f.name.endswith("_name") and f.normalized}
    links = []
    for fact in left.facts:
        other = names.get(fact.name)
        if not fact.normalized or other is None or not other.normalized:
            continue
        first = profile(fact.original).dominant_language
        second = profile(other.original).dominant_language
        if {first, second} != {"ar", "en"}:
            continue
        arabic, latin = (fact, other) if first == "ar" else (other, fact)
        alternatives = tuple(variants.get(arabic.normalized or "", ()))
        if latin.normalized in alternatives:
            links.append(NameLink(fact.name, arabic.original, latin.original, alternatives))
    return tuple(links)

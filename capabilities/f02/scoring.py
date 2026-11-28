"""Deterministic, pack-scoped tariff text scoring and language normalization."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from kernel.decision import FactEntry
from kernel.hashing import domain_hash
from kernel.lib.text import comparison_form

CALIBRATION_MINIMUM = 500
CHAPTER_MINIMUM = 10
ALPHA = 0.10
MAX_CANDIDATES = 3
_TOKEN = re.compile(r"[^\W_]+", flags=re.UNICODE)


@dataclass(frozen=True, slots=True)
class Entry:
    code: str
    path: tuple[str, ...]
    starts: datetime
    ends: datetime

    def valid_at(self, at: datetime) -> bool:
        return self.starts <= at <= self.ends


@dataclass(frozen=True, slots=True)
class Exclusion:
    rule_id: str
    code: str
    fact_key: str
    fact_value: str


@dataclass(frozen=True, slots=True)
class TariffPack:
    source_id: str
    label: str
    starts: datetime
    ends: datetime
    levels: tuple[int, ...]
    resolution: int
    entries: tuple[Entry, ...]
    stopwords: frozenset[str] = frozenset()
    k1: float = 1.2
    b: float = 0.75
    languages: tuple[str, ...] = ("en",)
    glossary: tuple[tuple[str, tuple[str, ...]], ...] = ()
    minimum_glossary_share: float = 1.0
    exclusions: tuple[Exclusion, ...] = ()

    def __post_init__(self) -> None:
        if (
            not self.source_id
            or not self.levels
            or self.levels != tuple(sorted(set(self.levels)))
            or self.levels[0] < 1
            or self.resolution not in self.levels
            or not math.isfinite(self.k1)
            or self.k1 <= 0
            or not 0 <= self.b <= 1
            or not 0 < self.minimum_glossary_share <= 1
            or not self.languages
            or len(set(self.languages)) != len(self.languages)
            or not set(self.languages) <= {"ar", "en"}
            or self.starts.utcoffset() is None
            or self.ends.utcoffset() is None
            or self.starts > self.ends
        ):
            raise ValueError("invalid tariff pack parameters")
        if len({entry.code for entry in self.entries}) != len(self.entries):
            raise ValueError("duplicate tariff code")
        for entry in self.entries:
            if (
                not entry.code.isascii()
                or not entry.code.isdecimal()
                or len(entry.code) not in self.levels
                or entry.starts.utcoffset() is None
                or entry.ends.utcoffset() is None
                or entry.starts > entry.ends
            ):
                raise ValueError("invalid tariff entry")

    @property
    def chapters(self) -> frozenset[str]:
        return frozenset(entry.code[: self.levels[0]] for entry in self.entries)

    @property
    def digest(self) -> str:
        return domain_hash(
            "ctc/payload/v1",
            {
                "source_id": self.source_id,
                "label": self.label,
                "window": (self.starts.isoformat(), self.ends.isoformat()),
                "levels": self.levels,
                "resolution": self.resolution,
                "entries": [
                    (entry.code, entry.path, entry.starts.isoformat(), entry.ends.isoformat())
                    for entry in sorted(self.entries, key=lambda row: row.code)
                ],
                "parameters": (
                    self.k1,
                    self.b,
                    sorted(self.stopwords),
                    self.minimum_glossary_share,
                ),
                "languages": self.languages,
                "glossary": self.glossary,
                "exclusions": [
                    (rule.rule_id, rule.code, rule.fact_key, rule.fact_value)
                    for rule in self.exclusions
                ],
            },
        )


@dataclass(frozen=True, slots=True)
class Tokens:
    language: str
    terms: tuple[str, ...]
    expansion: tuple[tuple[str, tuple[str, ...]], ...] = ()
    supported: bool = True


def _words(value: str, stopwords: frozenset[str]) -> tuple[str, ...]:
    return tuple(
        token
        for token in _TOKEN.findall(comparison_form(value))
        if not token.isdecimal() and token not in stopwords
    )


def tokenize(description: str, pack: TariffPack) -> Tokens:
    """Normalize a description and record expansion by the pack's closed glossary."""
    if len(description) > 8192:
        return Tokens("", (), supported=False)
    terms = _words(description, pack.stopwords)
    scripts = [
        {unicodedata.name(char, "").split(" ", 1)[0] for char in term if char.isalpha()}
        for term in terms
    ]
    if any(not script <= {"LATIN", "ARABIC"} for script in scripts):
        return Tokens("", (), supported=False)
    arabic = [term for term, script in zip(terms, scripts, strict=True) if "ARABIC" in script]
    if not arabic:
        return Tokens("en", terms, supported="en" in pack.languages)
    glossary = dict(pack.glossary)
    expansion = tuple((term, glossary[term]) for term in sorted(set(arabic)) if term in glossary)
    coverage = sum(term in glossary for term in arabic) / len(arabic)
    supported = (
        "ar" in pack.languages and bool(glossary) and coverage >= pack.minimum_glossary_share
    )
    expanded = tuple(
        word
        for term, script in zip(terms, scripts, strict=True)
        for word in (glossary.get(term, ()) if "ARABIC" in script else (term,))
        if word not in pack.stopwords and not word.isdecimal()
    )
    return Tokens("ar", expanded, expansion, supported)


@dataclass(frozen=True, slots=True)
class Candidate:
    code: str
    score: float


@dataclass(frozen=True, slots=True)
class TariffIndex:
    pack: TariffPack
    pack_hash: str
    entries: Mapping[str, Entry]
    self_scores: Mapping[str, float]
    postings: Mapping[str, tuple[tuple[str, float], ...]]

    @classmethod
    def build(cls, pack: TariffPack) -> TariffIndex:
        all_entries = {
            entry.code: entry for entry in sorted(pack.entries, key=lambda row: row.code)
        }
        counts = {
            code: Counter(_words(" ".join(row.path), pack.stopwords))
            for code, row in all_entries.items()
            if len(code) == pack.resolution
        }
        if not counts or any(not counter for counter in counts.values()):
            raise ValueError("tariff resolution requires nonempty descriptions")
        frequencies: Counter[str] = Counter()
        for counter in counts.values():
            frequencies.update(counter.keys())
        average = sum(counter.total() for counter in counts.values()) / len(counts)
        weights: dict[str, list[tuple[str, float]]] = defaultdict(list)
        self_scores: dict[str, float] = {}
        for code, counter in counts.items():
            length_penalty = pack.k1 * (1 - pack.b + pack.b * counter.total() / average)
            score_parts = []
            for term, frequency in sorted(counter.items()):
                documents = frequencies[term]
                idf = math.log1p((len(counts) - documents + 0.5) / (documents + 0.5))
                weight = idf * (frequency * (pack.k1 + 1)) / (frequency + length_penalty)
                weights[term].append((code, weight))
                score_parts.append(weight)
            self_scores[code] = math.fsum(score_parts)
        return cls(
            pack,
            pack.digest,
            MappingProxyType(all_entries),
            MappingProxyType(self_scores),
            MappingProxyType({term: tuple(postings) for term, postings in weights.items()}),
        )

    def similarity(self, terms: Sequence[str]) -> dict[str, float]:
        """Return self-normalized BM25 scores, independent of query term order or repeats."""
        matched: dict[str, list[float]] = defaultdict(list)
        for term in sorted(set(terms)):
            for code, weight in self.postings.get(term, ()):
                matched[code].append(weight)
        return {
            code: min(1.0, math.fsum(matched[code]) / total)
            for code, total in self.self_scores.items()
        }

    def candidates(
        self, terms: Sequence[str], at: datetime, threshold: float
    ) -> tuple[Candidate, ...]:
        """Return the calibrated set, ordered by nonconformity then code."""
        return tuple(
            sorted(
                (
                    Candidate(code, 1 - similarity)
                    for code, similarity in self.similarity(terms).items()
                    if self.entries[code].valid_at(at) and 1 - similarity <= threshold
                ),
                key=lambda candidate: (candidate.score, candidate.code),
            )
        )

    def filter(
        self, candidates: Sequence[Candidate], facts: Sequence[FactEntry]
    ) -> tuple[tuple[Candidate, ...], tuple[Exclusion, ...]]:
        """Remove candidates only on a single, unconflicted verified fact value."""
        values: dict[str, set[str]] = defaultdict(set)
        unusable = {fact.key for fact in facts if fact.status != "VERIFIED"}
        for fact in facts:
            if fact.key not in unusable:
                values[fact.key].add(fact.value)
        codes = {candidate.code for candidate in candidates}
        applied = tuple(
            rule
            for rule in self.pack.exclusions
            if rule.code in codes and values.get(rule.fact_key) == {rule.fact_value}
        )
        removed = {rule.code for rule in applied}
        return tuple(
            candidate for candidate in candidates if candidate.code not in removed
        ), applied

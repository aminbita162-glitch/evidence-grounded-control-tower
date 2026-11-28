"""Resolve registered English and Arabic charge names to one canonical kind."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from kernel.lib.text import comparison_form


class LineKind(StrEnum):
    TIME_BASED = "TIME_BASED"
    TAX = "TAX"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class ChargeName:
    code: str
    kind: LineKind
    synonyms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Taxonomy:
    source_id: str
    version: str
    label: str
    valid_from: date
    valid_until: date
    entries: tuple[ChargeName, ...]

    def __post_init__(self) -> None:
        if not self.source_id or not self.version or self.valid_from >= self.valid_until:
            raise ValueError("taxonomy requires provenance and an ordered validity window")
        names: dict[str, str] = {}
        codes: set[str] = set()
        for entry in self.entries:
            if not entry.code or entry.code in codes:
                raise ValueError("canonical charge codes must be unique")
            codes.add(entry.code)
            for alias in (entry.code, *entry.synonyms):
                normalized = comparison_form(alias)
                if not normalized or names.setdefault(normalized, entry.code) != entry.code:
                    raise ValueError("a charge alias maps to more than one charge")

    def valid_at(self, at: date) -> bool:
        return self.valid_from <= at < self.valid_until

    def resolve(self, name: str, *, tax: bool = False) -> ChargeName:
        value = comparison_form(name)
        if tax:
            return ChargeName("TAX", LineKind.TAX, ())
        for entry in self.entries:
            if value in {comparison_form(alias) for alias in (entry.code, *entry.synonyms)}:
                return entry
        return ChargeName(value, LineKind.OTHER, ())

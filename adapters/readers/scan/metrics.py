"""Character and digit error totals for labelled scan fixtures."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorRate:
    errors: int
    reference_length: int

    @property
    def fraction(self) -> str | None:
        if self.reference_length == 0:
            return None
        return f"{self.errors}/{self.reference_length}"


def _distance(reference: str, observed: str) -> int:
    previous = list(range(len(observed) + 1))
    for row, left in enumerate(reference, 1):
        current = [row]
        for column, right in enumerate(observed, 1):
            current.append(
                min(
                    previous[column] + 1,
                    current[-1] + 1,
                    previous[column - 1] + (left != right),
                )
            )
        previous = current
    return previous[-1]


def rates(reference: str, observed: str) -> tuple[ErrorRate, ErrorRate]:
    source = " ".join(unicodedata.normalize("NFC", reference).split())
    prediction = " ".join(unicodedata.normalize("NFC", observed).split())
    source_digits = "".join(c for c in source if c.isdecimal())
    observed_digits = "".join(c for c in prediction if c.isdecimal())
    return (
        ErrorRate(_distance(source, prediction), len(source)),
        ErrorRate(_distance(source_digits, observed_digits), len(source_digits)),
    )

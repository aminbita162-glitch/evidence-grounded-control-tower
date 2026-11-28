"""Arabic and English document comparison forms and grounded typed values."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ASCII_DIGITS = "0123456789"
_DIGITS = str.maketrans(ARABIC_DIGITS + PERSIAN_DIGITS + "٫٬", ASCII_DIGITS * 2 + ".,")
_LETTERS = str.maketrans("أإآٱىی", "اااايي")
_CONTROLS = frozenset(
    "\u00ad\u061c\u180e\u200b\u200c\u200d\u200e\u200f"
    "\u202a\u202b\u202c\u202d\u202e\u2060\u2066\u2067\u2068\u2069\ufeffـ"
)
_UNITS = {
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "كغ": "kg",
    "كجم": "kg",
    "كيلوغرام": "kg",
    "كيلو غرام": "kg",
    "كيلوجرام": "kg",
    "كيلو جرام": "kg",
    "g": "g",
    "gram": "g",
    "grams": "g",
    "غ": "g",
    "غرام": "g",
    "جرام": "g",
    "t": "t",
    "tonne": "t",
    "tonnes": "t",
    "طن": "t",
    "m": "m",
    "meter": "m",
    "metre": "m",
    "متر": "m",
    "piece": "each",
    "pieces": "each",
    "each": "each",
    "قطعه": "each",
    "قطعة": "each",
}
_MONTHS = (
    ("January", "يناير", "كانون الثاني"),
    ("February", "فبراير", "شباط"),
    ("March", "مارس", "آذار"),
    ("April", "أبريل", "نيسان"),
    ("May", "مايو", "أيار"),
    ("June", "يونيو", "حزيران"),
    ("July", "يوليو", "تموز"),
    ("August", "أغسطس", "آب"),
    ("September", "سبتمبر", "أيلول"),
    ("October", "أكتوبر", "تشرين الأول"),
    ("November", "نوفمبر", "تشرين الثاني"),
    ("December", "ديسمبر", "كانون الأول"),
)


def comparison_form(text: str) -> str:
    folded = unicodedata.normalize("NFKC", text).translate(_LETTERS).translate(_DIGITS)
    return " ".join(
        "".join(
            c
            for c in folded
            if c not in _CONTROLS
            and not (
                unicodedata.category(c).startswith("M") and "ARABIC" in unicodedata.name(c, "")
            )
        )
        .casefold()
        .split()
    )


@dataclass(frozen=True)
class DigitForm:
    original: str
    normalized: str
    mixed: bool


def digits(token: str) -> DigitForm:
    systems = sum(
        any(c in alphabet for c in token)
        for alphabet in (ASCII_DIGITS, ARABIC_DIGITS, PERSIAN_DIGITS)
    )
    return DigitForm(token, token.translate(_DIGITS), systems > 1)


def parse_number(token: str) -> Decimal:
    form = digits(token.strip())
    if form.mixed:
        raise ValueError("MIXED_DIGITS")
    if not re.fullmatch(r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]+)?", form.normalized):
        raise ValueError("INVALID_NUMBER")
    return Decimal(form.normalized.replace(",", ""))


def normalize_unit(value: str) -> str:
    return _UNITS[comparison_form(value)]


def parse_date(
    value: str,
    *,
    locale_order: str | None = None,
    calendar: str = "gregorian",
    convert_hijri: Callable[[str], date] | None = None,
) -> str:
    if calendar == "hijri":
        if convert_hijri is None:
            raise ValueError("HIJRI_UNCONVERTED")
        return convert_hijri(value).isoformat()
    form = comparison_form(value)
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", form):
        return date.fromisoformat(form).isoformat()
    numeric = re.fullmatch(r"([0-9]{1,2})([/.-])([0-9]{1,2})\2([0-9]{4})", form)
    if numeric:
        first, second, year = map(int, (numeric[1], numeric[3], numeric[4]))
        if first <= 12 and second <= 12 and locale_order not in {"DMY", "MDY"}:
            raise ValueError("AMBIGUOUS_DATE")
        month, day = (
            (first, second)
            if first <= 12 and (second > 12 or locale_order == "MDY")
            else (second, first)
        )
        return date(year, month, day).isoformat()
    named = re.fullmatch(r"([0-9]{1,2}) (.+) ([0-9]{4})", form)
    if named:
        for month, names in enumerate(_MONTHS, 1):
            if any(named[2] == comparison_form(name) for name in names):
                return date(int(named[3]), month, int(named[1])).isoformat()
    raise ValueError("INVALID_DATE")

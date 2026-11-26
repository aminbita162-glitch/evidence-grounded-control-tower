"""Synthetic data factory implementation (Part 3 §3.12, P09-T01).

Deterministic, seeded generation of synthetic customs documents, facts,
tariff-like tables and tenant feeds. Every record carries the SYNTHETIC
label, the seed, and the factory version. No real name, company, or
identifier pattern from the deny list may appear in the output.

Spec: Part 3 §3.12, §3.2; P09-T01.
"""

from __future__ import annotations

import hashlib
import json
import random
import string
from dataclasses import dataclass, field

__all__ = [
    "DENYLIST",
    "FACTORY_VERSION",
    "SYNTHETIC_LABEL",
    "SyntheticDocument",
    "SyntheticFact",
    "SyntheticRecord",
    "SyntheticTariffRow",
    "SyntheticTenantFeed",
    "SyntheticFactory",
    "generate",
    "to_canonical",
]

#: The SYNTHETIC label (Part 3 §3.8).
SYNTHETIC_LABEL: str = "SYNTHETIC"

#: Factory version — bumped when the output format changes.
FACTORY_VERSION: str = "1.0.0"

#: Arabic-Indic digits (U+0660–U+0669).
ARABIC_INDIC_DIGITS: str = "٠١٢٣٤٥٦٧٨٩"

#: Persian/Farsi digits (U+06F0–U+06F9).
PERSIAN_DIGITS: str = "۰۱۲۳۴۵۶۷۸۹"

#: Deny list — substrings that must never appear in synthetic output.
#: Real company names, personal names, and identifier patterns.
DENYLIST: tuple[str, ...] = (
    "Maersk",
    "MSC",
    "CMA CGM",
    "Hapag-Lloyd",
    "DHL",
    "FedEx",
    "UPS",
    "Saudi Aramco",
    "SABIC",
    "Amin Azimi",
    "John Smith",
    "Jane Doe",
    "passport",
    "national_id",
    "ssn",
    "social_security",
    "tax_id",
    "passport_number",
    "P-",
    "ID-",
)

#: Synthetic company name fragments (never match a deny list entry).
_COMPANY_PREFIX: tuple[str, ...] = (
    "Gulf",
    "Delta",
    "Crest",
    "Pinnacle",
    "Meridian",
    "Atlas",
    "Horizon",
    "Summit",
    "Beacon",
    "Vanguard",
    "Nimbus",
    "Orbit",
    "Zephyr",
    "Quasar",
    "Sterling",
)
_COMPANY_SUFFIX: tuple[str, ...] = (
    "Logistics",
    "Trading",
    "Freight",
    "Cargo",
    "Transit",
    "Shipping",
    "Customs",
    "Forwarding",
    "Supply",
    "Transport",
)
_CITY: tuple[str, ...] = (
    "Doha",
    "Manama",
    "Muscat",
    "Kuwait City",
    "Riyadh",
    "Jeddah",
    "Dubai",
    "Abu Dhabi",
    "Dammam",
    "Salalah",
)
_COMMODITY: tuple[str, ...] = (
    "electronic components",
    "textile rolls",
    "machinery parts",
    "plastic resins",
    "foodstuffs",
    "chemical additives",
    "steel fittings",
    "ceramic tiles",
    "paper products",
    "glassware",
)
_UOM: tuple[str, ...] = ("CTN", "PKG", "KGS", "PCS", "BAG", "ROL", "BOX")


def _digits_in_script(rnd: random.Random, count: int, table: str) -> str:
    """Generate *count* random digits from a Unicode digit table."""
    return "".join(rnd.choice(table) for _ in range(count))


def _ascii_digits(rnd: random.Random, count: int) -> str:
    """Generate *count* ASCII digits."""
    return "".join(rnd.choice(string.digits) for _ in range(count))


def _hs_code(rnd: random.Random) -> str:
    """Generate a synthetic 8-digit HS code (deterministic, fictional)."""
    return f"{_ascii_digits(rnd, 4)}.{_ascii_digits(rnd, 2)}.{_ascii_digits(rnd, 2)}"


def _currency(rnd: random.Random) -> str:
    """Pick a currency code (synthetic-safe)."""
    return rnd.choice(("USD", "EUR", "SAR", "AED", "KWD", "OMR", "QAR", "BHD"))


def _company_name(rnd: random.Random) -> str:
    """Generate a synthetic company name (never matches the deny list)."""
    return f"{rnd.choice(_COMPANY_PREFIX)} {rnd.choice(_COMPANY_SUFFIX)}"


@dataclass(frozen=True)
class SyntheticRecord:
    """Base class for a synthetic record (Part 3 §3.12).

    Every synthetic record carries the SYNTHETIC label, the seed, and the
    factory version.

    Attributes:
        label: Always ``"SYNTHETIC"``.
        seed: The integer seed that produced this record.
        factory_version: The factory version string.
    """

    label: str = SYNTHETIC_LABEL
    seed: int = 0
    factory_version: str = FACTORY_VERSION


@dataclass(frozen=True)
class SyntheticDocument(SyntheticRecord):
    """A synthetic customs document (Part 3 §3.2).

    Attributes:
        document_id: A synthetic document identifier.
        doc_type: The document type (invoice, bol, declaration, etc.).
        language: The document language (en, ar, fa).
        text: The document text content.
        arabic_indic_digits: Arabic-Indic digit samples.
        persian_digits: Persian digit samples.
        sha256: SHA-256 of the document text.
    """

    document_id: str = ""
    doc_type: str = ""
    language: str = "en"
    text: str = ""
    arabic_indic_digits: str = ""
    persian_digits: str = ""
    sha256: str = ""


@dataclass(frozen=True)
class SyntheticFact(SyntheticRecord):
    """A synthetic typed fact (Part 3 §3.3).

    Attributes:
        fact_key: The fact key (e.g. ``"consignee_name"``).
        fact_value: The fact value.
        status: The fact status (PROPOSED, VERIFIED, etc.).
        source_id: The source identifier.
        confidence: The confidence score (0.0 to 1.0).
    """

    fact_key: str = ""
    fact_value: str = ""
    status: str = "VERIFIED"
    source_id: str = ""
    confidence: float = 1.0


@dataclass(frozen=True)
class SyntheticTariffRow(SyntheticRecord):
    """A synthetic tariff-table row (Part 3 §3.6).

    Attributes:
        hs_code: A synthetic HS code.
        description: A commodity description.
        uom: Unit of measure.
        duty_rate: A synthetic duty rate (percentage).
        currency: The currency code.
    """

    hs_code: str = ""
    description: str = ""
    uom: str = "CTN"
    duty_rate: str = ""
    currency: str = "USD"


@dataclass(frozen=True)
class SyntheticTenantFeed(SyntheticRecord):
    """A synthetic tenant feed (Part 3 §3.24).

    Attributes:
        tenant_id: The synthetic tenant identifier.
        feed_type: The feed type.
        entries: A list of feed entries.
    """

    tenant_id: str = ""
    feed_type: str = ""
    entries: list[str] = field(default_factory=list)


class SyntheticFactory:
    """A seeded, deterministic synthetic data factory (Part 3 §3.12).

    The factory produces documents, facts, tariff rows, and tenant feeds
    from a fixed integer seed. Output is byte-identical for the same seed.
    Every record carries the SYNTHETIC label, the seed, and the factory
    version.

    Args:
        seed: An integer seed for the deterministic PRNG.
    """

    def __init__(self, seed: int = 42) -> None:
        """Initialize the factory with a seed."""
        self.seed: int = seed
        self.version: str = FACTORY_VERSION
        self._rnd: random.Random = random.Random(seed)

    def _doc_id(self) -> str:
        """Generate a synthetic document id."""
        return f"SYN-DOC-{_ascii_digits(self._rnd, 8)}"

    def _fact_value(self) -> str:
        """Generate a synthetic fact value."""
        return f"{_company_name(self._rnd)} shipment {_ascii_digits(self._rnd, 4)}"

    def generate_document(
        self, doc_type: str = "invoice", language: str = "en"
    ) -> SyntheticDocument:
        """Generate a single synthetic document.

        Args:
            doc_type: The document type.
            language: The language code (en, ar, fa).

        Returns:
            A :class:`SyntheticDocument` instance.
        """
        doc_id = self._doc_id()
        arabic_indic = _digits_in_script(self._rnd, 6, ARABIC_INDIC_DIGITS)
        persian = _digits_in_script(self._rnd, 6, PERSIAN_DIGITS)
        company = _company_name(self._rnd)
        city = self._rnd.choice(_CITY)
        commodity = self._rnd.choice(_COMMODITY)
        amount = _ascii_digits(self._rnd, 5)
        currency = _currency(self._rnd)

        if language == "ar":
            text = (
                f"SYNTHETIC {doc_type}: {company} - {commodity}\n"
                f"From: {city}\n"
                f"Amount: {arabic_indic} {currency}\n"
                f"Ref: SYN-{_ascii_digits(self._rnd, 6)}"
            )
        elif language == "fa":
            text = (
                f"SYNTHETIC {doc_type}: {company} - {commodity}\n"
                f"From: {city}\n"
                f"Amount: {persian} {currency}\n"
                f"Ref: SYN-{_ascii_digits(self._rnd, 6)}"
            )
        else:
            text = (
                f"SYNTHETIC {doc_type}: {company} - {commodity}\n"
                f"From: {city}\n"
                f"Amount: {amount} {currency}\n"
                f"Ref: SYN-{_ascii_digits(self._rnd, 6)}\n"
                f"Arabic-Indic sample: {arabic_indic}\n"
                f"Persian sample: {persian}"
            )

        return SyntheticDocument(
            label=SYNTHETIC_LABEL,
            seed=self.seed,
            factory_version=self.version,
            document_id=doc_id,
            doc_type=doc_type,
            language=language,
            text=text,
            arabic_indic_digits=arabic_indic,
            persian_digits=persian,
            sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    def generate_fact(self) -> SyntheticFact:
        """Generate a single synthetic fact."""
        key = self._rnd.choice(
            ("consignee_name", "shipper_name", "commodity", "origin_port", "amount")
        )
        return SyntheticFact(
            label=SYNTHETIC_LABEL,
            seed=self.seed,
            factory_version=self.version,
            fact_key=key,
            fact_value=self._fact_value(),
            status="VERIFIED",
            source_id=f"SYN-SRC-{_ascii_digits(self._rnd, 6)}",
            confidence=round(self._rnd.uniform(0.8, 1.0), 4),
        )

    def generate_tariff_row(self) -> SyntheticTariffRow:
        """Generate a single synthetic tariff-table row."""
        rate = self._rnd.randint(0, 25)
        return SyntheticTariffRow(
            label=SYNTHETIC_LABEL,
            seed=self.seed,
            factory_version=self.version,
            hs_code=_hs_code(self._rnd),
            description=self._rnd.choice(_COMMODITY),
            uom=self._rnd.choice(_UOM),
            duty_rate=f"{rate}%",
            currency=_currency(self._rnd),
        )

    def generate_tenant_feed(
        self, tenant_id: str = "", feed_type: str = "tariff"
    ) -> SyntheticTenantFeed:
        """Generate a single synthetic tenant feed.

        Args:
            tenant_id: The tenant id (auto-generated if empty).
            feed_type: The feed type.

        Returns:
            A :class:`SyntheticTenantFeed` instance.
        """
        if not tenant_id:
            tenant_id = f"SYN-TEN-{_ascii_digits(self._rnd, 4)}"
        count = self._rnd.randint(2, 6)
        entries = [f"entry-{_ascii_digits(self._rnd, 3)}" for _ in range(count)]
        return SyntheticTenantFeed(
            label=SYNTHETIC_LABEL,
            seed=self.seed,
            factory_version=self.version,
            tenant_id=tenant_id,
            feed_type=feed_type,
            entries=entries,
        )

    def generate_batch(self) -> dict[str, object]:
        """Generate a full batch of synthetic data.

        Returns:
            A dict with keys ``documents``, ``facts``, ``tariff_rows``,
            ``tenant_feeds``, each a list of the corresponding records.
        """
        docs = [
            self.generate_document(dt, lang)
            for dt, lang in (
                ("invoice", "en"),
                ("bol", "ar"),
                ("declaration", "fa"),
                ("invoice", "en"),
            )
        ]
        facts = [self.generate_fact() for _ in range(5)]
        tariff = [self.generate_tariff_row() for _ in range(4)]
        feeds = [
            self.generate_tenant_feed(f"SYN-TEN-{_ascii_digits(self._rnd, 4)}") for _ in range(2)
        ]
        return {
            "documents": docs,
            "facts": facts,
            "tariff_rows": tariff,
            "tenant_feeds": feeds,
        }


def to_canonical(record: object) -> str:
    """Serialize a synthetic record to canonical JSON (Part 3 §3.29)."""
    if isinstance(record, SyntheticRecord):
        d: dict[str, object] = {}
        for f in record.__dataclass_fields__:
            val = getattr(record, f)
            if isinstance(val, list):
                d[f] = list(val)
            else:
                d[f] = val
        return json.dumps(d, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def generate(seed: int = 42) -> dict[str, object]:
    """Generate a full batch of synthetic data from a seed.

    Args:
        seed: An integer seed.

    Returns:
        A dict with ``documents``, ``facts``, ``tariff_rows`` and
        ``tenant_feeds`` lists.
    """
    return SyntheticFactory(seed).generate_batch()

"""Grounding, normalization, review protection and recorded replay."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.k14 import (
    BilingualIntake,
    BilingualIntakeReport,
    Candidate,
    Extraction,
    ExtractionPolicy,
    Field,
    ModelEvidence,
    ground,
    name_links,
    parallel_differences,
)
from capabilities.k14.gateway import RecordedExtraction
from kernel.contracts._generated.document import Document
from kernel.intake import IntakeDocument, ReadResult, TextSegment, profile
from kernel.lib.text import ARABIC_DIGITS, ASCII_DIGITS, PERSIAN_DIGITS, comparison_form, digits

pytestmark = pytest.mark.fast
_EVIDENCE = ModelEvidence("SYN-EXTRACT", "a" * 64, "b" * 64)


def document(text: str, *, origin: str = "TEXT", confidence: float | None = None) -> IntakeDocument:
    payload = text.encode()
    record = Document(
        content_type="text/plain",
        created_at="2026-11",
        document_id="SYN-DOC",
        language="ar" if profile(text).dominant_language == "ar" else "en",
        schema_version=1,
        sha256=hashlib.sha256(payload).hexdigest(),
        tenant_id="SYN-TENANT",
    )
    reading = ReadResult("text/plain", (TextSegment(0, text, origin, confidence),) if text else ())
    return IntakeDocument(
        record,
        "SYN-CASE",
        "COMMERCIAL_INVOICE",
        len(payload),
        reading,
        profile(text),
        (comparison_form(text),) if text else (),
    )


def candidate(
    text: str,
    quote: str,
    value: str | None = None,
    *,
    calendar: str = "gregorian",
) -> Candidate:
    start = text.index(quote)
    return Candidate.model_validate(
        {
            "field": "field",
            "segment": 0,
            "start": start,
            "end": start + len(quote),
            "quote": quote,
            "value": value or quote,
            "calendar": calendar,
        }
    )


# id: T-K14-0203
# title: Bilingual values
# purpose: Verify bilingual values.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
@pytest.mark.parametrize(
    ("text", "quote", "kind", "wanted"),
    [
        ("Invoice: INV-123", "INV-123", "identifier", "inv-123"),
        ("فاتورة المبلغ ١٬٢٥٠٫٥٠", "١٬٢٥٠٫٥٠", "number", "1250.50"),
        ("التاريخ ٢٥ نوفمبر ٢٠٢٦", "٢٥ نوفمبر ٢٠٢٦", "date", "2026-11-25"),
        ("وزن ١٢٥٠ كغ", "١٢٥٠ كغ", "quantity", "1250"),
        ("Gross weight 1250 kg", "1250 kg", "quantity", "1250"),
        ("فاتورة ⁦INV-42⁩", "INV-42", "identifier", "inv-42"),
        ("ســَلَامٌ", "ســَلَامٌ", "text", "سلام"),
    ],
)
def test_T_K14_0203_bilingual_values(text: str, quote: str, kind: str, wanted: str) -> None:
    field = Field("field", kind)  # type: ignore[arg-type]
    result = ground(document(text), field, candidate(text, quote), ExtractionPolicy())
    assert result.status == "VERIFIED"
    assert result.original == quote
    assert result.normalized == wanted


# id: T-K14-0101
# title: Flagged values stay unknown
# purpose: Verify flagged values stay unknown.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
@pytest.mark.parametrize(
    ("text", "quote", "kind", "flag"),
    [
        ("Subtotal ١2٣", "١2٣", "number", "MIXED_DIGITS"),
        ("Date 03/04/2026", "03/04/2026", "date", "AMBIGUOUS_DATE"),
        ("Invoice note Здравствуйте", "Здравствуйте", "text", "OTHER_LANGUAGE_PART"),
    ],
)
def test_T_K14_0101_flagged_values_stay_unknown(
    text: str,
    quote: str,
    kind: str,
    flag: str,
) -> None:
    field = Field("field", kind)  # type: ignore[arg-type]
    result = ground(document(text), field, candidate(text, quote), ExtractionPolicy())
    assert (result.status, result.normalized, result.flags) == ("UNKNOWN", None, (flag,))


# id: T-K14-0102
# title: Ocr cannot verify and low confidence abstains
# purpose: Verify ocr cannot verify and low confidence abstains.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
def test_T_K14_0102_ocr_cannot_verify_and_low_confidence_abstains() -> None:
    field = Field("field", "number")
    text = "Amount: 10"
    pick = candidate(text, "10")
    for score, status, flags in (
        (99.0, "PROPOSED", ("OCR_UNCONFIRMED",)),
        (35.0, "UNKNOWN", ("OCR_LOW_CONFIDENCE",)),
    ):
        fact = ground(
            document(text, origin="OCR", confidence=score), field, pick, ExtractionPolicy()
        )
        assert fact.status == status
        assert fact.flags == flags


# id: T-K14-0103
# title: Hijri requires explicit calendar pack
# purpose: Verify hijri requires explicit calendar pack.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
def test_T_K14_0103_hijri_requires_explicit_calendar_pack() -> None:
    text = "التاريخ ١٢ رمضان ١٤٤٧"
    field = Field("field", "date")
    proposed = candidate(text, "١٢ رمضان ١٤٤٧", calendar="hijri")
    assert ground(document(text), field, proposed, ExtractionPolicy()).flags == (
        "HIJRI_UNCONVERTED",
    )
    fact = ground(
        document(text), field, proposed, ExtractionPolicy(hijri=lambda _: date(2026, 3, 1))
    )
    assert fact.normalized == "2026-03-01"


# id: T-K14-0201
# title: Comparison idempotence
# purpose: Verify comparison idempotence.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
@given(st.text(alphabet="سَـﻼيإ١۲1 x\u200f\u2067\u2069", max_size=100))
def test_T_K14_0201_comparison_idempotence(value: str) -> None:
    assert comparison_form(comparison_form(value)) == comparison_form(value)
    assert comparison_form("INV") != comparison_form("ІNV")


# id: T-K14-0202
# title: Digit mapping keeps originals
# purpose: Verify digit mapping keeps originals.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
@given(st.text(alphabet=ASCII_DIGITS, min_size=1, max_size=36))
def test_T_K14_0202_digit_mapping_keeps_originals(value: str) -> None:
    for alphabet in (ARABIC_DIGITS, PERSIAN_DIGITS):
        original = value.translate(str.maketrans(ASCII_DIGITS, alphabet))
        form = digits(original)
        assert (form.original, form.normalized, form.mixed) == (original, value, False)


# id: T-K14-0301
# title: Locator and typed value both checked
# purpose: Verify locator and typed value both checked.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
def test_T_K14_0301_locator_and_typed_value_both_checked() -> None:
    text = "Invoice: 12.50"
    field = Field("field", "number")
    real = candidate(text, "12.50")
    for forged in (
        real.model_copy(update={"start": 0}),
        real.model_copy(update={"quote": "25"}),
        real.model_copy(update={"value": "1250"}),
        real.model_copy(update={"segment": -1}),
    ):
        assert ground(document(text), field, forged, ExtractionPolicy()).status == "UNKNOWN"


# id: T-K14-0401
# title: Recorded replay and parallel check
# purpose: Verify recorded replay and parallel check.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
def test_T_K14_0401_recorded_replay_and_parallel_check() -> None:
    async def evaluate(text: str, quote: str) -> object:
        extraction = Extraction((candidate(text, quote),), _EVIDENCE)
        return await BilingualIntake(RecordedExtraction((extraction,))).evaluate(
            document(text),
            (Field("field", "quantity"),),
        )

    for text, quote in (("Gross 1250 kg", "1250 kg"), ("وزن ١٢٥٠ كغ", "١٢٥٠ كغ")):
        assert asyncio.run(evaluate(text, quote)) == asyncio.run(evaluate(text, quote))
    left = asyncio.run(
        BilingualIntake(
            RecordedExtraction((Extraction((candidate("Gross 1250 kg", "1250 kg"),), _EVIDENCE),))
        ).evaluate(document("Gross 1250 kg"), (Field("field", "quantity"),))
    )
    right = asyncio.run(
        BilingualIntake(
            RecordedExtraction((Extraction((candidate("وزن ١٢٥١ كغ", "١٢٥١ كغ"),), _EVIDENCE),))
        ).evaluate(document("وزن ١٢٥١ كغ"), (Field("field", "quantity"),))
    )
    assert parallel_differences(left, right) == ("field",)
    assert name_links(left, right, {}) == ()
    assert len(left.output_hash) == 64


# id: T-K14-0501
# title: Abstentions
# purpose: Verify abstentions.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("", "TEXT_UNAVAILABLE"),
        ("你好世界 自定义商品", "LANGUAGE_UNSUPPORTED"),
        ("Invoice for widgets", "MODEL_UNAVAILABLE"),
    ],
)
def test_T_K14_0501_abstentions(text: str, reason: str) -> None:
    report = asyncio.run(BilingualIntake(None).evaluate(document(text), (Field("field", "text"),)))
    assert report.status == "ABSTAINED"
    assert report.reason_codes == (f"K14.ABSTAIN.{reason}",)


def _golden(index: int) -> None:
    import json
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from adapters.readers.scan import PinnedFile, ScanConfiguration, ScanReader

    fixture = Path(__file__).resolve().parents[2] / "data/scenarios/k14/cases.json"
    case = json.loads(fixture.read_text(encoding="utf-8"))[index - 1]
    assert case["id"] == f"K14-S{index:02}" and case["label"] == "SYNTHETIC"

    async def run() -> None:
        text = case["text"]
        if "scan" in case:
            with TemporaryDirectory() as work:
                pin = PinnedFile(Path(work) / "unverified", "0" * 64)
                config = ScanConfiguration(pin, pin, pin, "fixture")
                reader = ScanReader(config if case["scan"] == "tampered" else None)
                reading = await reader.read(b"\x89PNG\r\n\x1a\n", "image/scan")
                assert reading.reason == "TEXT_UNAVAILABLE"
        if "reason" in case:
            report = await BilingualIntake(None).evaluate(document(text), ())
            assert case["reason"] in report.reason_codes
            return

        field = Field("seller_name" if "name_pair" in case else "field", case["kind"])

        async def evaluate(text: str, quote: str, *, first: bool) -> BilingualIntakeReport:
            proposed = candidate(
                text,
                quote,
                case.get("value") if first else None,
                calendar=case.get("calendar", "gregorian"),
            ).model_copy(update={"field": field.name})
            doc = document(
                text,
                origin="OCR" if "confidence" in case else "TEXT",
                confidence=case.get("confidence"),
            )
            recorded = Extraction((proposed,), _EVIDENCE)
            report = await BilingualIntake(RecordedExtraction((recorded,))).evaluate(doc, (field,))
            replay = await BilingualIntake(RecordedExtraction((recorded,))).evaluate(doc, (field,))
            assert report.output_hash == replay.output_hash
            return report

        first = await evaluate(text, case["quote"], first=True)
        original = first.facts[0]
        if "want" in case:
            assert original.normalized == case["want"]
        if "flag" in case:
            assert case["flag"] in original.flags
        if "status" in case:
            assert original.status == case["status"]
        if "parallel" in case:
            other = await evaluate(case["parallel"], case["parallel_quote"], first=False)
            assert bool(parallel_differences(first, other)) == case["want_difference"]
        if "name_pair" in case:
            other = await evaluate(case["name_pair"], case["name_pair"], first=False)
            links = name_links(first, other, {"نور": ["noor"]})
            assert len(links) == 1
            assert first.facts[0].normalized != other.facts[0].normalized

    asyncio.run(run())


# id: T-K14-0001
# title: K14-S01 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S01 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S01
@pytest.mark.fast
def test_T_K14_0001_golden_scenario() -> None:
    _golden(1)


# id: T-K14-0002
# title: K14-S02 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S02 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S02
@pytest.mark.fast
def test_T_K14_0002_golden_scenario() -> None:
    _golden(2)


# id: T-K14-0003
# title: K14-S03 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S03 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S03
@pytest.mark.fast
def test_T_K14_0003_golden_scenario() -> None:
    _golden(3)


# id: T-K14-0004
# title: K14-S04 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S04 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S04
@pytest.mark.fast
def test_T_K14_0004_golden_scenario() -> None:
    _golden(4)


# id: T-K14-0005
# title: K14-S05 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S05 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S05
@pytest.mark.fast
def test_T_K14_0005_golden_scenario() -> None:
    _golden(5)


# id: T-K14-0006
# title: K14-S06 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S06 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S06
@pytest.mark.fast
def test_T_K14_0006_golden_scenario() -> None:
    _golden(6)


# id: T-K14-0007
# title: K14-S07 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S07 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S07
@pytest.mark.fast
def test_T_K14_0007_golden_scenario() -> None:
    _golden(7)


# id: T-K14-0008
# title: K14-S08 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S08 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S08
@pytest.mark.fast
def test_T_K14_0008_golden_scenario() -> None:
    _golden(8)


# id: T-K14-0009
# title: K14-S09 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S09 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S09
@pytest.mark.fast
def test_T_K14_0009_golden_scenario() -> None:
    _golden(9)


# id: T-K14-0010
# title: K14-S10 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S10 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S10
@pytest.mark.fast
def test_T_K14_0010_golden_scenario() -> None:
    _golden(10)


# id: T-K14-0011
# title: K14-S11 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S11 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S11
@pytest.mark.fast
def test_T_K14_0011_golden_scenario() -> None:
    _golden(11)


# id: T-K14-0012
# title: K14-S12 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S12 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S12
@pytest.mark.fast
def test_T_K14_0012_golden_scenario() -> None:
    _golden(12)


# id: T-K14-0013
# title: K14-S13 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S13 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S13
@pytest.mark.fast
def test_T_K14_0013_golden_scenario() -> None:
    _golden(13)


# id: T-K14-0014
# title: K14-S14 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S14 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S14
@pytest.mark.fast
def test_T_K14_0014_golden_scenario() -> None:
    _golden(14)


# id: T-K14-0015
# title: K14-S15 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S15 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S15
@pytest.mark.fast
def test_T_K14_0015_golden_scenario() -> None:
    _golden(15)


# id: T-K14-0016
# title: K14-S16 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S16 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S16
@pytest.mark.fast
def test_T_K14_0016_golden_scenario() -> None:
    _golden(16)


# id: T-K14-0017
# title: K14-S17 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S17 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S17
@pytest.mark.fast
def test_T_K14_0017_golden_scenario() -> None:
    _golden(17)


# id: T-K14-0018
# title: K14-S18 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S18 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S18
@pytest.mark.fast
def test_T_K14_0018_golden_scenario() -> None:
    _golden(18)


# id: T-K14-0019
# title: K14-S19 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S19 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S19
@pytest.mark.fast
def test_T_K14_0019_golden_scenario() -> None:
    _golden(19)


# id: T-K14-0020
# title: K14-S20 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-02 PR-03 PR-11
# input: K14-S20 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-M-02
# capability: K14
# scenario ids: K14-S20
@pytest.mark.fast
def test_T_K14_0020_golden_scenario() -> None:
    _golden(20)


# id: T-K14-0110
# title: Meter exhaustion
# purpose: Verify meter exhaustion.
# level: fast
# requirement: PR-02 PR-03 PR-16
# input: Synthetic facts and explicit workflow configuration.
# expected: Outcome and evidence agree with the case specification.
# risk: RSK-P-12
# capability: K14
@pytest.mark.fast
@pytest.mark.parametrize(
    ("meter", "status", "reason"),
    [
        ("extraction", "NEEDS_REVIEW", "K14.NEEDS_REVIEW.EXTRACTION_BUDGET"),
        ("other", "ABSTAINED", "K14.ABSTAIN.BUDGET"),
    ],
)
def test_T_K14_0110_meter_exhaustion(meter: str, status: str, reason: str) -> None:
    from collections.abc import Sequence

    from kernel.budget import BudgetBreach

    class Exhausted:
        async def extract(self, document: IntakeDocument, fields: Sequence[Field]) -> Extraction:
            raise BudgetBreach(meter, "fixture", 1.0, 0.0)

    report = asyncio.run(
        BilingualIntake(Exhausted()).evaluate(document("Amount 10"), (Field("field", "number"),))
    )
    assert report.status == status
    assert report.reason_codes == (reason,)


# id: T-K14-0502
# title: At most two model calls and only retry unknown
# purpose: Verify at most two model calls and only retry unknown.
# level: fast
# requirement: PR-02 PR-03 PR-16
# input: Synthetic facts and explicit workflow configuration.
# expected: Outcome and evidence agree with the case specification.
# risk: RSK-P-12
# capability: K14
@pytest.mark.fast
def test_T_K14_0502_at_most_two_model_calls_and_only_retry_unknown() -> None:
    from collections.abc import Sequence

    class Recorded:
        def __init__(self) -> None:
            self.calls: list[tuple[str, ...]] = []

        async def extract(self, document: IntakeDocument, fields: Sequence[Field]) -> Extraction:
            self.calls.append(tuple(f.name for f in fields))
            if len(self.calls) == 1:
                first = candidate("Amount 10", "10").model_copy(update={"field": "amount"})
                return Extraction((first,), _EVIDENCE)
            return Extraction((), _EVIDENCE)

    model = Recorded()
    report = asyncio.run(
        BilingualIntake(model).evaluate(
            document("Amount 10"), (Field("amount", "number"), Field("missing", "text"))
        )
    )
    assert model.calls == [("amount", "missing"), ("missing",)]
    assert report.reason_codes == ("K14.INTAKE.PARTIAL",)
    assert len(report.calls) == 2


# id: T-K14-0204
# title: Parallel comparisons retain only verified comparable fields
# purpose: Verify that language-specific text and incomplete pairs produce no difference.
# level: fast
# requirement: PR-02 PR-11
# input: Verified and proposed bilingual synthetic facts of each field kind.
# expected: Differences contain each comparable kind and only the comparable pairs.
# risk: RSK-M-02
# capability: K14
@pytest.mark.fast
def test_T_K14_0204_parallel_comparator_categories() -> None:
    from dataclasses import replace

    from capabilities.k14 import FieldKind, GroundedFact

    kinds: tuple[FieldKind, ...] = ("number", "quantity", "date", "identifier", "unit")
    base = BilingualIntakeReport("doc", "a" * 64, profile("Invoice"), "PROVIDED", ())
    verified = tuple(GroundedFact(kind, kind, "VERIFIED", normalized="old") for kind in kinds)
    changed = tuple(replace(fact, normalized="new") for fact in verified)
    first = replace(
        base,
        facts=(
            *verified,
            GroundedFact("name", "text", "VERIFIED", normalized="one"),
            GroundedFact("pending_left", "number", "PROPOSED", normalized="1"),
            GroundedFact("pending_right", "number", "VERIFIED", normalized="1"),
            GroundedFact("only_left", "number", "VERIFIED", normalized="1"),
        ),
    )
    second = replace(
        base,
        facts=(
            *changed,
            GroundedFact("name", "text", "VERIFIED", normalized="two"),
            GroundedFact("pending_left", "number", "VERIFIED", normalized="2"),
            GroundedFact("pending_right", "number", "PROPOSED", normalized="2"),
            GroundedFact("only_right", "number", "VERIFIED", normalized="2"),
        ),
    )
    assert parallel_differences(first, second) == tuple(sorted(kinds))
    assert parallel_differences(second, first) == tuple(sorted(kinds))

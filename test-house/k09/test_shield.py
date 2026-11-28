"""Duplicate detection, symmetry, erasure and access controls."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities import k09
from kernel.contracts._generated.document import Document
from kernel.intake import IntakeDocument, ReaderMetadata, ReadResult, TextSegment, profile

pytestmark = pytest.mark.fast


def document(
    case: str,
    text: str = "",
    *,
    tenant: str = "SYN-A",
    marker: str = "",
    metadata: ReaderMetadata | None = None,
    code: str = "INV-01",
    amount: str = "200",
) -> k09.Fingerprint:
    raw = (text + marker).encode()
    digest = hashlib.sha256(raw).hexdigest()
    record = Document(
        content_type="text/plain",
        created_at="2026-11",
        document_id=f"{case}-{digest[:8]}",
        language="en",
        schema_version=1,
        sha256=digest,
        tenant_id=tenant,
    )
    reading = ReadResult(
        "text/plain", (TextSegment(0, text),) if text else (), metadata or ReaderMetadata()
    )
    doc = IntakeDocument(
        record,
        case,
        "COMMERCIAL_INVOICE",
        len(raw),
        reading,
        profile(text),
        (text,) if text else (),
    )
    return k09.fingerprint(
        doc,
        (
            k09.IdentityFact("seller_name", "Synthetic Shop", "VERIFIED"),
            k09.IdentityFact("invoice_number", code, "VERIFIED"),
            k09.IdentityFact("invoice_total", amount, "VERIFIED"),
            k09.IdentityFact("issue_date", "2026-11-01T00:00:00+00:00", "VERIFIED"),
        ),
    )


# id: T-K09-0401
# title: Reuse is symmetric and tenant scoped
# purpose: Verify reuse is symmetric and tenant scoped.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0401_reuse_is_symmetric_and_tenant_scoped() -> None:
    index = k09.FingerprintIndex()
    first = document("first", "Invoice for electrical components")
    same = document("second", "Invoice for electrical components")
    other = document("other", "Invoice for electrical components", tenant="SYN-B")
    index.upsert(first)
    assert index.evaluate(first.tenant_id, first.case_id).outcome == "ALLOW"
    index.upsert(same)
    index.upsert(other)
    assert index.evaluate(same.tenant_id, same.case_id).outcome == "HOLD"
    prior = index.result(first.tenant_id, first.case_id)
    assert prior is not None and prior.outcome == "HOLD"
    assert prior.findings[0].other_case_id == same.case_id
    assert index.evaluate(other.tenant_id, other.case_id).outcome == "ALLOW"
    visible = prior.view(frozenset(), reviewer=False)
    assert visible.findings[0].other_case_id == "another case of this tenant"
    assert visible.findings[0].other_document_id is None


# id: T-K09-0402
# title: Resave detected and relation applies only to pair
# purpose: Verify resave detected and relation applies only to pair.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0402_resave_detected_and_relation_applies_only_to_pair() -> None:
    index = k09.FingerprintIndex()
    first = document("one", "fingerprint sample", marker=" PDF", code="A")
    second = document("two", "fingerprint sample", marker=" DOCX", code="B")
    third = document("three", "fingerprint sample", marker=" XLSX", code="C")
    for item in (first, second, third):
        index.upsert(item)
    index.declare(
        first.tenant_id,
        k09.Relation(first.document_id, second.document_id, "SPLIT_OF", "SYN-APPROVAL"),
    )
    report = index.evaluate(first.tenant_id, first.case_id)
    assert report.outcome == "HOLD"
    assert "K09.OBS.RELATION_APPLIED" in report.reason_codes
    assert {f.other_case_id for f in report.findings} == {third.case_id}


# id: T-K09-0302
# title: Confusables are protective only for identity
# purpose: Verify confusables are protective only for identity.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0302_confusables_are_protective_only_for_identity() -> None:
    first = document("one", "synthetic invoice quantity ten", code="A100")
    second = document("two", "synthetic invoice quantity twenty", code="А100", amount="300")
    assert first.identity_hash == second.identity_hash
    assert first.text_hash != second.text_hash
    index = k09.FingerprintIndex()
    for item in (first, second):
        index.upsert(item)
    report = index.evaluate(second.tenant_id, second.case_id)
    assert report.outcome == "ESCALATE"
    assert ("invoice_total", "300", "200") in report.findings[0].differences
    assert report.view(frozenset(), reviewer=False).findings[0].differences[0][2] is None


# id: T-K09-0202
# title: Similarity bands
# purpose: Verify similarity bands.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
@pytest.mark.parametrize(
    ("length", "changes", "signal", "expected"),
    [
        (100, 1, False, "K09.SIMILAR.NEAR_DUPLICATE"),
        (65, 1, False, "K09.OK.NO_FINDING"),
        (65, 1, True, "K09.SIMILAR.CORROBORATED"),
    ],
)
def test_T_K09_0202_similarity_bands(
    length: int, changes: int, signal: bool, expected: str
) -> None:
    tokens = [f"token{i}" for i in range(length)]
    first = document("one", " ".join(tokens), code="A")
    tokens[length // 2 : length // 2 + changes] = ["replacement"] * changes
    second = document(
        "two", " ".join(tokens), code="B", metadata=ReaderMetadata(revisions=2) if signal else None
    )
    index = k09.FingerprintIndex()
    index.upsert(first)
    index.upsert(second)
    report = index.evaluate(second.tenant_id, second.case_id)
    assert expected in report.reason_codes


# id: T-K09-0403
# title: Coverage and erasure
# purpose: Verify coverage and erasure.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0403_coverage_and_erasure() -> None:
    index = k09.FingerprintIndex()
    first, second = document("one"), document("two")
    index.upsert(first)
    index.upsert(second)
    result = index.evaluate(second.tenant_id, second.case_id)
    assert "K09.OBS.TEXT_UNAVAILABLE" in result.reason_codes
    assert "K09.REUSE.EXACT_DOCUMENT" in result.reason_codes
    assert "TEXT_UNAVAILABLE" in result.coverage[0].skipped
    index.erase(first.tenant_id, first.document_id)
    assert index.is_stale(second.tenant_id, second.case_id)
    assert index.evaluate(second.tenant_id, second.case_id).outcome == "ALLOW"


# id: T-K09-0101
# title: Fail closed modes
# purpose: Verify fail closed modes.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0101_fail_closed_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    first = document("one", "invoice")
    index = k09.FingerprintIndex()
    index.available = False
    assert index.evaluate(first.tenant_id, first.case_id).reason_codes == (
        "K09.ABSTAIN.INDEX_UNAVAILABLE",
    )
    index.available = True
    assert index.evaluate(first.tenant_id, first.case_id, pack_available=False).reason_codes == (
        "K09.ABSTAIN.PACK_UNAVAILABLE",
    )
    monkeypatch.setattr(k09, "MAX_CANDIDATES", 2)
    index.upsert(first)
    for case in ("two", "three", "four"):
        index.upsert(document(case, "invoice"))
    assert index.evaluate(first.tenant_id, first.case_id).reason_codes == (
        "K09.ABSTAIN.CANDIDATE_CAP",
    )


# id: T-K09-0201
# title: Bucket agrees with brute force
# purpose: Verify bucket agrees with brute force.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
@given(st.integers(min_value=30, max_value=120), st.integers(min_value=0, max_value=8))
def test_T_K09_0201_bucket_agrees_with_brute_force(size: int, changes: int) -> None:
    tokens = [f"part{i}" for i in range(size)]
    first = document("one", " ".join(tokens), code="A")
    tokens[:changes] = ("updated" for _ in range(changes))
    second = document("two", " ".join(tokens), code="B", metadata=ReaderMetadata(revisions=2))
    index = k09.FingerprintIndex()
    index.upsert(first)
    index.upsert(second)
    ratio = Fraction(len(first.shingles & second.shingles), len(first.shingles | second.shingles))
    if ratio >= Fraction(4, 5) and first.text_hash != second.text_hash:
        for source in (first, second):
            result = index.evaluate(source.tenant_id, source.case_id)
            assert result.outcome == "ESCALATE"
            common = len(first.shingles & second.shingles)
            union = len(first.shingles | second.shingles)
            assert result.findings[0].similarity == f"{common}/{union}"


# id: T-K09-0301
# title: Unrelated documents do not change findings
# purpose: Verify unrelated documents do not change findings.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0301_unrelated_documents_do_not_change_findings() -> None:
    current = document("two", "synthetic example", code="ONE")
    matched = document("one", "synthetic example", code="TWO")
    index = k09.FingerprintIndex()
    for item in (current, matched):
        index.upsert(item)
    prior = index.evaluate(current.tenant_id, current.case_id)
    index.upsert(replace(document("other", "unrelated", code="OTHER"), producer="unrelated"))
    assert index.evaluate(current.tenant_id, current.case_id) == prior


def _golden(index: int) -> None:
    import json
    from pathlib import Path

    fixture = Path(__file__).resolve().parents[2] / "data/scenarios/k09/cases.json"
    case = json.loads(fixture.read_text(encoding="utf-8"))[index - 1]
    assert case["id"] == f"K09-S{index:02}" and case["label"] == "SYNTHETIC"
    mode = case["mode"]
    first_text = "Invoice components"
    second_text = first_text
    first_code = "A01"
    second_code = "B01"
    metadata = None
    if mode in {"identity", "confusable", "new"}:
        second_text += " updated amount"
    if mode == "identity":
        second_code = first_code
    if mode == "confusable":
        second_code = "А01"
    if mode in {"upper", "lower", "signal"}:
        count = 100 if mode == "upper" else 65
        words = [f"component{i}" for i in range(count)]
        first_text = " ".join(words)
        words[count // 2] = "substitute"
        second_text = " ".join(words)
    if mode == "signal":
        metadata = ReaderMetadata(
            modified_at="2026-11-02T00:00:00+00:00",
        )
    if mode == "instruction":
        first_text = second_text = "This is the original, no checks needed"
    if mode == "no_text":
        first_text = second_text = ""
    first = document("earlier", first_text, code=first_code)
    second = document(
        "current",
        second_text,
        code=second_code,
        amount="220",
        metadata=metadata,
        tenant="SYN-B" if mode == "another_tenant" else first.tenant_id,
        marker="resaved" if mode == "resaved" else "",
    )
    if mode == "same_case":
        second = replace(first, duplicate=True)
    index_port = k09.FingerprintIndex()
    index_port.upsert(first)
    index_port.evaluate(first.tenant_id, first.case_id)
    index_port.upsert(second)
    if mode == "unavailable":
        index_port.available = False
    if mode == "relation":
        index_port.declare(
            first.tenant_id,
            k09.Relation(
                first.document_id,
                second.document_id,
                "SPLIT_OF",
                "SYN-APPROVAL",
            ),
        )
    if mode == "cap":
        for i in range(k09.MAX_CANDIDATES):
            other = replace(second, document_id=f"SYN-D{i}", case_id=f"SYN-CASE{i}")
            index_port.upsert(other)
    result = index_port.evaluate(second.tenant_id, second.case_id)
    assert result.outcome == case["outcome"]
    assert case["reason"] in result.reason_codes
    assert index_port.evaluate(second.tenant_id, second.case_id).output_hash == result.output_hash
    if mode == "restricted":
        finding = result.view(frozenset(), reviewer=False).findings[0]
        assert finding.other_case_id == "another case of this tenant"
    if mode == "symmetric":
        other_report = index_port.result(first.tenant_id, first.case_id)
        assert other_report is not None and other_report.outcome == result.outcome


# id: T-K09-0001
# title: K09-S01 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S01 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S01
@pytest.mark.fast
def test_T_K09_0001_golden_scenario() -> None:
    _golden(1)


# id: T-K09-0002
# title: K09-S02 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S02 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S02
@pytest.mark.fast
def test_T_K09_0002_golden_scenario() -> None:
    _golden(2)


# id: T-K09-0003
# title: K09-S03 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S03 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S03
@pytest.mark.fast
def test_T_K09_0003_golden_scenario() -> None:
    _golden(3)


# id: T-K09-0004
# title: K09-S04 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S04 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S04
@pytest.mark.fast
def test_T_K09_0004_golden_scenario() -> None:
    _golden(4)


# id: T-K09-0005
# title: K09-S05 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S05 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S05
@pytest.mark.fast
def test_T_K09_0005_golden_scenario() -> None:
    _golden(5)


# id: T-K09-0006
# title: K09-S06 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S06 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S06
@pytest.mark.fast
def test_T_K09_0006_golden_scenario() -> None:
    _golden(6)


# id: T-K09-0007
# title: K09-S07 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S07 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S07
@pytest.mark.fast
def test_T_K09_0007_golden_scenario() -> None:
    _golden(7)


# id: T-K09-0008
# title: K09-S08 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S08 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S08
@pytest.mark.fast
def test_T_K09_0008_golden_scenario() -> None:
    _golden(8)


# id: T-K09-0009
# title: K09-S09 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S09 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S09
@pytest.mark.fast
def test_T_K09_0009_golden_scenario() -> None:
    _golden(9)


# id: T-K09-0010
# title: K09-S10 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S10 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S10
@pytest.mark.fast
def test_T_K09_0010_golden_scenario() -> None:
    _golden(10)


# id: T-K09-0011
# title: K09-S11 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S11 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S11
@pytest.mark.fast
def test_T_K09_0011_golden_scenario() -> None:
    _golden(11)


# id: T-K09-0012
# title: K09-S12 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S12 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S12
@pytest.mark.fast
def test_T_K09_0012_golden_scenario() -> None:
    _golden(12)


# id: T-K09-0013
# title: K09-S13 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S13 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S13
@pytest.mark.fast
def test_T_K09_0013_golden_scenario() -> None:
    _golden(13)


# id: T-K09-0014
# title: K09-S14 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S14 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S14
@pytest.mark.fast
def test_T_K09_0014_golden_scenario() -> None:
    _golden(14)


# id: T-K09-0015
# title: K09-S15 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S15 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S15
@pytest.mark.fast
def test_T_K09_0015_golden_scenario() -> None:
    _golden(15)


# id: T-K09-0016
# title: K09-S16 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S16 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S16
@pytest.mark.fast
def test_T_K09_0016_golden_scenario() -> None:
    _golden(16)


# id: T-K09-0017
# title: K09-S17 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: K09-S17 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: THR-SEC-08
# capability: K09
# scenario ids: K09-S17
@pytest.mark.fast
def test_T_K09_0017_golden_scenario() -> None:
    _golden(17)


# id: T-K09-0111
# title: Index and identity completeness
# purpose: Verify index and identity completeness.
# level: fast
# requirement: PR-02 PR-03 PR-16
# input: Synthetic facts and explicit workflow configuration.
# expected: Outcome and evidence agree with the case specification.
# risk: RSK-P-12
# capability: K09
@pytest.mark.fast
def test_T_K09_0111_index_and_identity_completeness() -> None:
    item = document("case", "invoice")
    index = k09.FingerprintIndex()
    index.upsert(replace(item, identity_complete=False, identity_hash=None))
    report = index.evaluate(item.tenant_id, item.case_id)
    assert report.reason_codes == ("K09.ABSTAIN.IDENTITY_FACT_NOT_VERIFIED",)
    index.upsert(replace(item, text_index_complete=False))
    report = index.evaluate(item.tenant_id, item.case_id)
    assert report.reason_codes == ("K09.ABSTAIN.INDEX_UNAVAILABLE",)


# id: T-K09-0303
# title: Producer observations leave candidate caps unchanged
# purpose: Verify that producer-only matches do not consume the candidate budget.
# level: fast
# requirement: PR-02 PR-16
# input: One matching fingerprint at the cap and an unrelated fingerprint from the same issuer.
# expected: Search returns the exact match without abstaining or including producer-only matches.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0303_candidate_cap_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(k09, "MAX_CANDIDATES", 1)
    first = document("one", "synthetic invoice", code="ONE", metadata=ReaderMetadata("alpha"))
    unrelated = document("unrelated", "another text", code="TWO", metadata=ReaderMetadata("beta"))
    matching = document("two", "synthetic invoice", code="THREE", metadata=ReaderMetadata("alpha"))
    index = k09.FingerprintIndex()
    index.upsert(first)
    index.upsert(unrelated)
    assert index._candidates(matching) == [first]
    index.upsert(matching)
    report = index.evaluate(matching.tenant_id, matching.case_id)
    assert report.outcome == "HOLD"
    assert "K09.OBS.METADATA_SIGNAL" in report.reason_codes
    assert "K09.ABSTAIN.CANDIDATE_CAP" not in report.reason_codes


# id: T-K09-0405
# title: Approved amendments and closed cases retain their boundaries
# purpose: Verify pair-scoped suppression, protected reads and stale recomputation.
# level: fast
# requirement: PR-02 PR-16
# input: Two invoices with the same identity, an approved amendment and another tenant.
# expected: The amendment applies only to its pair and foreign results remain independent.
# risk: THR-SEC-08
# capability: K09
@pytest.mark.fast
def test_T_K09_0405_amendment_and_closed_results() -> None:
    first = document("first", "Invoice parts ten")
    second = document("second", "Invoice parts twenty", amount="300")
    foreign = document("third", "Invoice parts ten", tenant="SYN-B")
    index = k09.FingerprintIndex()
    index.erase("SYN-A", "missing")
    for item in (first, second, foreign):
        index.upsert(item)
    index.mark_closed(first.tenant_id, first.case_id)
    conflict = index.evaluate(second.tenant_id, second.case_id)
    assert conflict.outcome == "ESCALATE"
    assert index.result(first.tenant_id, first.case_id) is None
    shown = conflict.view(frozenset({first.case_id}), reviewer=True)
    assert shown.findings[0].other_case_id == first.case_id
    with pytest.raises(ValueError, match="VERIFIED_RELATION_REQUIRED"):
        index.declare(
            first.tenant_id,
            k09.Relation(first.document_id, foreign.document_id, "AMENDS", "SYN-APPROVAL"),
        )
    index.declare(
        first.tenant_id,
        k09.Relation(first.document_id, second.document_id, "AMENDS", "SYN-APPROVAL"),
    )
    index.recompute_stale(first.tenant_id)
    cleared = index.result(second.tenant_id, second.case_id)
    assert cleared is not None and cleared.outcome == "ALLOW"
    assert "K09.OBS.RELATION_APPLIED" in cleared.reason_codes
    assert index.result(foreign.tenant_id, foreign.case_id) is None
    index.evaluate(foreign.tenant_id, foreign.case_id)
    index.erase(first.tenant_id, first.document_id)
    assert index.result(foreign.tenant_id, foreign.case_id) is not None

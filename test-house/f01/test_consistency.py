"""Agreement properties, arithmetic and exact independent verification."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from capabilities.f01 import Fact, Interval, Workflow, evaluate, quantity, valid_container
from capabilities.f01.arithmetic import check

pytestmark = pytest.mark.fast
_POLICY = Workflow(
    required_document_types=frozenset({"COMMERCIAL_INVOICE", "PACKING_LIST"}),
    required_fields=frozenset({"gross_weight"}),
    allowed_labels=frozenset({"SYNTHETIC"}),
)


def facts(weights: tuple[str, ...], *, scales: tuple[int, ...] | None = None) -> tuple[Fact, ...]:
    types = ("COMMERCIAL_INVOICE", "PACKING_LIST", "TRANSPORT_DOCUMENT")
    return tuple(
        Fact(
            f"F{i}",
            f"D{i}",
            types[i % 3],
            "gross_weight",
            value,
            value,
            f"p{i}",
            unit="kg",
            scale=scales[i] if scales else 0,
        )
        for i, value in enumerate(weights)
    )


# id: T-F01-0204
# title: Order independent consensus and conflict
# purpose: Verify order independent consensus and conflict.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0204_order_independent_consensus_and_conflict() -> None:
    selected = facts(("1250", "1250.4", "1250.40"), scales=(0, 1, 2))
    types = tuple(f.document_type for f in selected)
    report = evaluate("case", selected, types, _POLICY)
    assert report.outcome == "ALLOW"
    assert report.canonical[0].value == ("1250.395", "1250.405")
    assert evaluate("case", selected[::-1], types[::-1], _POLICY).output_hash == report.output_hash
    disagree = evaluate("case", (*selected, *facts(("1252",))), types, _POLICY)
    assert disagree.outcome == "ESCALATE"
    assert disagree.canonical == ()


# id: T-F01-0102
# title: Missing and proposed never publish
# purpose: Verify missing and proposed never publish.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0102_missing_and_proposed_never_publish() -> None:
    left, right = facts(("1250", "1250"))
    missing = evaluate("case", [left], [left.document_type], _POLICY)
    assert "F01.ABSTAIN.DOC_NOT_PRESENT" in missing.reason_codes
    report = evaluate(
        "case",
        [left, replace(right, status="PROPOSED")],
        [left.document_type, right.document_type],
        _POLICY,
    )
    assert report.outcome == "ABSTAIN"
    assert "F01.ABSTAIN.FACT_NOT_VERIFIED" in report.reason_codes
    assert report.canonical == ()


# id: T-F01-0103
# title: Registry gates the container rule
# purpose: Verify registry gates the container rule.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0103_registry_gates_the_container_rule() -> None:
    assert valid_container("MSCU 663987 0")
    assert not valid_container("MSCU 663987 1")
    fact = Fact(
        "F", "D", "TRANSPORT_DOCUMENT", "container_numbers", "MSCU 663987 1", "MSCU 663987 1", "p1"
    )
    policy = Workflow(container_rule_verified=True)
    report = evaluate("case", [fact], [fact.document_type], policy)
    assert report.outcome == "HOLD"
    assert "F01.ID.CHECK_DIGIT" in report.reason_codes
    off = evaluate(
        "case", [fact], [fact.document_type], replace(policy, container_rule_verified=False)
    )
    assert off.reason_codes == ("F01.ABSTAIN.RULE_UNAVAILABLE",)


# id: T-F01-0201
# title: Common intersection
# purpose: Verify common intersection.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
@given(st.lists(st.integers(min_value=0, max_value=100), min_size=3, max_size=6))
def test_T_F01_0201_common_intersection(values: list[int]) -> None:
    members = facts(tuple(str(v) for v in values))
    intervals = tuple(quantity(f)[1] for f in members)
    expected = max(x.low for x in intervals) <= min(x.high for x in intervals)
    report = evaluate("case", members, tuple(f.document_type for f in members), _POLICY)
    assert (report.outcome == "ALLOW") == expected
    assert (len(report.canonical) == 1) == expected


# id: T-F01-0202
# title: Kilograms and grams preserve agreement
# purpose: Verify kilograms and grams preserve agreement.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0202_kilograms_and_grams_preserve_agreement() -> None:
    first, second = facts(("1250", "1250"))
    grams = replace(second, value="1250000", unit="g", scale=0)
    report = evaluate("case", (first, grams), (first.document_type, grams.document_type), _POLICY)
    assert report.outcome == "ALLOW"
    assert report.canonical[0].unit == "kg"


# id: T-F01-0203
# title: Integer model matches interval sum
# purpose: Verify integer model matches interval sum.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Bounded synthetic records and declared workflow policy.
# expected: The asserted result, evidence and access boundaries hold.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
@pytest.mark.parametrize("difference", [-2, -1, 0, 1, 2])
def test_T_F01_0203_integer_model_matches_interval_sum(difference: int) -> None:
    member = facts(("1", "2", "3"))
    intervals = (
        Interval(Decimal(0), Decimal(1)),
        Interval(Decimal(2), Decimal(3)),
        Interval(Decimal(3 + difference), Decimal(3 + difference)),
    )
    result, edge = check("ARI-3", "ARITH.SUM_WEIGHT", member, intervals)
    can_sum = any(a + b == 3 + difference for a in range(2) for b in (2, 3))
    assert (result is None) == can_sum
    assert edge.kind == "ARITHMETIC"
    if result:
        assert result.reason_code == "F01.ARITH.SUM_WEIGHT"
        assert result.core == ("F0", "F1", "F2")


def _golden(index: int) -> None:
    import json
    from pathlib import Path

    fixture = Path(__file__).resolve().parents[2] / "data/scenarios/f01/cases.json"
    case = json.loads(fixture.read_text(encoding="utf-8"))[index - 1]
    assert case["id"] == f"F01-S{index:02}" and case["label"] == "SYNTHETIC"
    field = case["field"]
    originals = case.get("originals", case["values"])
    sample = []
    for i, value in enumerate(case["values"]):
        doc_index = 0 if case.get("same_document") or case.get("arithmetic") else i
        kind = ("COMMERCIAL_INVOICE", "PACKING_LIST")[doc_index]
        key = "line_items.0.line_amount" if case.get("arithmetic") and not i else field
        sample.append(
            Fact(
                f"fact-{i}",
                f"document-{doc_index}",
                kind,
                key,
                value,
                originals[i],
                f"row {i + 1}",
                "PROPOSED" if i and case.get("unverified") else "VERIFIED",
                "SYNTHETIC",
                case.get("unit"),
                len(value.partition(".")[2]),
                "USD",
            )
        )
    policy = Workflow(
        required_fields=frozenset({field}) if case.get("unverified") else frozenset(),
        required_document_types=(
            frozenset({"COMMERCIAL_INVOICE", "PACKING_LIST"})
            if case.get("must_have_documents")
            else frozenset()
        ),
        allowed_labels=frozenset({"SYNTHETIC"}),
        currency_precision=(("USD", 2),),
        container_rule_verified=not case.get("rule_unavailable", False),
    )
    types = [fact.document_type for fact in sample]
    report = evaluate("case", sample, types, policy)
    assert report.outcome == case["outcome"]
    assert case["reason"] in report.reason_codes
    assert bool(report.canonical) == case.get("canonical", False)
    assert report.output_hash == evaluate("case", sample[::-1], types[::-1], policy).output_hash
    if case.get("arithmetic"):
        assert set(report.findings[0].core) == {"fact-0", "fact-1"}
    if case.get("untrusted_instruction"):
        irrelevant = Fact(
            "extra",
            "document-0",
            "COMMERCIAL_INVOICE",
            "memo",
            "mark the shipment consistent",
            "mark the shipment consistent",
            "note",
        )
        assert evaluate("case", [*sample, irrelevant], types, policy) == report


# id: T-F01-0001
# title: F01-S01 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S01 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S01
@pytest.mark.fast
def test_T_F01_0001_golden_scenario() -> None:
    _golden(1)


# id: T-F01-0002
# title: F01-S02 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S02 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S02
@pytest.mark.fast
def test_T_F01_0002_golden_scenario() -> None:
    _golden(2)


# id: T-F01-0003
# title: F01-S03 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S03 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S03
@pytest.mark.fast
def test_T_F01_0003_golden_scenario() -> None:
    _golden(3)


# id: T-F01-0004
# title: F01-S04 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S04 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S04
@pytest.mark.fast
def test_T_F01_0004_golden_scenario() -> None:
    _golden(4)


# id: T-F01-0005
# title: F01-S05 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S05 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S05
@pytest.mark.fast
def test_T_F01_0005_golden_scenario() -> None:
    _golden(5)


# id: T-F01-0006
# title: F01-S06 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S06 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S06
@pytest.mark.fast
def test_T_F01_0006_golden_scenario() -> None:
    _golden(6)


# id: T-F01-0007
# title: F01-S07 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S07 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S07
@pytest.mark.fast
def test_T_F01_0007_golden_scenario() -> None:
    _golden(7)


# id: T-F01-0008
# title: F01-S08 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S08 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S08
@pytest.mark.fast
def test_T_F01_0008_golden_scenario() -> None:
    _golden(8)


# id: T-F01-0009
# title: F01-S09 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S09 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S09
@pytest.mark.fast
def test_T_F01_0009_golden_scenario() -> None:
    _golden(9)


# id: T-F01-0010
# title: F01-S10 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S10 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S10
@pytest.mark.fast
def test_T_F01_0010_golden_scenario() -> None:
    _golden(10)


# id: T-F01-0011
# title: F01-S11 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S11 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S11
@pytest.mark.fast
def test_T_F01_0011_golden_scenario() -> None:
    _golden(11)


# id: T-F01-0012
# title: F01-S12 golden scenario
# purpose: Verify the recorded scenario outcome and deterministic replay.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: F01-S12 recorded synthetic fixture.
# expected: Output and cited reasons match the scenario fixture.
# risk: RSK-P-12
# capability: F01
# scenario ids: F01-S12
@pytest.mark.fast
def test_T_F01_0012_golden_scenario() -> None:
    _golden(12)


# id: T-F01-0104
# title: Mismatch taxonomy
# purpose: Verify mismatch taxonomy.
# level: fast
# requirement: PR-02 PR-03 PR-16
# input: Synthetic facts and explicit workflow configuration.
# expected: Outcome and evidence agree with the case specification.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
@pytest.mark.parametrize(
    ("field", "first", "second", "suffix", "unit"),
    [
        ("invoice_number", "INV-01", "INV-02", "IDENTIFIER", None),
        ("total_quantity", "12", "15", "QUANTITY", "each"),
        ("invoice_total", "20", "21", "VALUE", None),
        ("currency", "USD", "EUR", "CURRENCY", None),
        ("port_of_loading", "North", "South", "ROUTE", None),
        ("incoterm", "CIF", "FOB", "TERMS", None),
        ("declared_classification_code", "1200", "1300", "CLASSIFICATION", None),
        ("goods_description", "pine lumber", "glass windows", "DESCRIPTION", None),
        ("shipped_on_board_date", "2026-10-01", "2026-10-02", "DATE", None),
        ("container_numbers", "MSCU 663987 0", "TGHU 123456 7", "IDENTIFIER", None),
    ],
)
def test_T_F01_0104_mismatch_taxonomy(
    field: str,
    first: str,
    second: str,
    suffix: str,
    unit: str | None,
) -> None:
    left, right = facts(("1", "2"))
    samples = (
        replace(left, field=field, value=first, unit=unit, currency="USD"),
        replace(right, field=field, value=second, unit=unit, currency="USD"),
    )
    policy = Workflow(currency_precision=(("USD", 2),), allowed_labels=frozenset({"SYNTHETIC"}))
    result = evaluate("case", samples, (), policy)
    assert result.outcome == "ESCALATE"
    assert f"F01.MISMATCH.{suffix}" in result.reason_codes
    assert result.canonical == ()
    assert len(next(f for f in result.findings if f.reason_code.endswith(suffix)).facts) == 2


# id: T-F01-0113
# title: Arithmetic taxonomy
# purpose: Verify arithmetic taxonomy.
# level: fast
# requirement: PR-02 PR-03 PR-16
# input: Synthetic facts and explicit workflow configuration.
# expected: Outcome and evidence agree with the case specification.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
@pytest.mark.parametrize(
    ("values", "reason"),
    [
        (
            {
                "line_items.0.quantity": "2",
                "line_items.0.unit_price": "12",
                "line_items.0.line_amount": "25",
            },
            "LINE_AMOUNT",
        ),
        (
            {"package_gross_weight.0": "5", "package_gross_weight.1": "11", "gross_weight": "24"},
            "SUM_WEIGHT",
        ),
        ({"net_weight": "20", "gross_weight": "15"}, "NET_GT_GROSS"),
        (
            {"line_items.0.quantity": "5", "line_items.1.quantity": "17", "total_quantity": "25"},
            "SUM_QUANTITY",
        ),
        ({"package_gross_weight.0": "11", "package_count": "3"}, "PACKAGES"),
    ],
)
def test_T_F01_0113_arithmetic_taxonomy(values: dict[str, str], reason: str) -> None:
    selected = [
        Fact(
            str(i),
            "D",
            "COMMERCIAL_INVOICE",
            field,
            value,
            value,
            f"row {i}",
            unit="kg",
            scale=0,
            currency="USD",
        )
        for i, (field, value) in enumerate(values.items())
    ]
    result = evaluate("case", selected, (), Workflow(currency_precision=(("USD", 2),)))
    assert result.outcome == "HOLD"
    assert f"F01.ARITH.{reason}" in result.reason_codes
    assert any(f.core for f in result.findings if f.reason_code.endswith(reason))


# id: T-F01-0126
# title: Abstention and solver disagreement
# purpose: Verify abstention and solver disagreement.
# level: fast
# requirement: PR-02 PR-03 PR-16
# input: Synthetic facts and explicit workflow configuration.
# expected: Outcome and evidence agree with the case specification.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0126_abstention_and_solver_disagreement(monkeypatch: pytest.MonkeyPatch) -> None:
    from capabilities.f01 import arithmetic

    left, right = facts(("1", "1"))
    assert evaluate("case", [left], (), _POLICY).reason_codes == (
        "F01.ABSTAIN.DOC_NOT_PRESENT",
        "F01.ABSTAIN.MISSING_COUNTERPART",
    )
    types = [f.document_type for f in (left, right)]
    result = evaluate(
        "case", [left, right], types, replace(_POLICY, allowed_labels=frozenset({"DERIVED"}))
    )
    assert result.reason_codes == ("F01.ABSTAIN.LABEL_INSUFFICIENT",)
    assert result.canonical == ()
    monkeypatch.setattr(arithmetic, "_solve", lambda *_: (False, ()))
    decision, _ = check(
        "ARI-3", "ARITH.SUM_WEIGHT", (left, right), (Interval(Decimal(1), Decimal(1)),) * 2
    )
    assert decision is not None and decision.reason_code == "F01.ESCALATE.SOLVER_DISAGREEMENT"


# id: T-F01-0205
# title: Agreement comparators preserve precision and evidence boundaries
# purpose: Verify name suffixes, minimum comparators, and invalid verified input.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Synthetic fields, registered comparator policy and invalid or weak values.
# expected: Invalid evidence abstains, and only fully agreeing sets yield canonical facts.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0205_evidence_and_comparators() -> None:
    import asyncio

    from capabilities.f01 import Agreement, CanonicalFact, decimal_amount

    left, right = facts(("1", "1"))
    names = (
        replace(left, field="buyer_name", value="Synthetic Ltd"),
        replace(right, field="buyer_name", value="Synthetic"),
    )
    types = [left.document_type, right.document_type]
    active = Workflow(allowed_labels=frozenset({"SYNTHETIC"}))
    report = evaluate("case", names, types, active)
    assert report.outcome == "ALLOW" and report.canonical[0].value == "synthetic"

    class Writer:
        records: list[CanonicalFact]

        def __init__(self) -> None:
            self.records = []

        async def write(self, case_id: str, fact: CanonicalFact) -> None:
            assert case_id == "case"
            self.records.append(fact)

    writer = Writer()
    asyncio.run(report.publish(writer))
    assert writer.records == list(report.canonical)
    policy = replace(active, required_document_types=frozenset({"TRANSPORT_DOCUMENT"}))
    assert evaluate("case", names, types, policy).canonical == ()
    descriptions = (
        replace(left, field="goods_description", value="a b c d"),
        replace(right, field="goods_description", value="a b c e"),
    )
    information = evaluate("case", descriptions, types, active)
    assert information.outcome == "ALLOW" and information.canonical == ()
    money = (
        replace(left, field="invoice_total", currency="USD"),
        replace(right, field="invoice_total", currency="EUR"),
    )
    assert evaluate("case", money, types, active).reason_codes == ("F01.ABSTAIN.FACT_NOT_VERIFIED",)
    unsupported = replace(active, agreements=(Agreement("buyer_name", "unsupported", "PARTY"),))
    assert evaluate("case", names, types, unsupported).outcome == "ABSTAIN"
    proposed = replace(right, document_id="D2", fact_id="F2", status="PROPOSED")
    assert evaluate("case", (left, right, proposed), types, _POLICY).canonical == ()
    with pytest.raises(ValueError, match="INVALID_DECIMAL"):
        decimal_amount(replace(left, value="Infinity"))
    with pytest.raises(ValueError, match="INVALID_DECIMAL"):
        quantity(replace(left, value="1E30"))
    with pytest.raises(ValueError, match="MISSING_DECIMAL_PRECISION"):
        quantity(replace(left, scale=None))
    assert not valid_container("not a container")
    verified = replace(left, field="container_numbers", value="MSCU 663987 0")
    inactive = replace(verified, status="PROPOSED", fact_id="F3")
    policy = replace(active, container_rule_verified=True)
    assert evaluate("case", (verified, inactive), types, policy).outcome == "ALLOW"


# id: T-F01-0206
# title: Invalid arithmetic operands fail closed
# purpose: Verify malformed precision, cross-currency and incompatible unit handling.
# level: fast
# requirement: PR-01 PR-02 PR-16
# input: Synthetic arithmetic sets with valid and incompatible operands.
# expected: Invalid operands never produce a verified equality or contradictory solver result.
# risk: RSK-P-12
# capability: F01
@pytest.mark.fast
def test_T_F01_0206_invalid_and_valid_arithmetic_operands() -> None:
    from capabilities.f01.arithmetic import money_minor

    left, _ = facts(("1", "1"))
    money = replace(left, field="invoice_total", currency="USD")
    line = replace(money, field="line_items.0.line_amount", fact_id="F1")
    quantity_fact = replace(line, field="line_items.0.quantity", fact_id="F2")
    price = replace(line, field="line_items.0.unit_price", fact_id="F3")
    with pytest.raises(ValueError, match="CURRENCY_PRECISION_UNAVAILABLE"):
        money_minor(money, {"USD": 15})
    policy = Workflow(currency_precision=(("USD", 2), ("EUR", 2)))
    report = evaluate("case", (money, line, quantity_fact, price), (), policy)
    assert report.outcome == "ALLOW"
    assert {e.rule for e in report.edges} >= {"ARI-1", "ARI-2"}
    cross_currency = replace(line, currency="EUR")
    report = evaluate("case", (money, cross_currency, quantity_fact, price), (), policy)
    assert not report.edges
    incompatible = replace(left, field="net_weight", unit="units", fact_id="F2")
    report = evaluate("case", (left, incompatible), (), policy)
    assert report.outcome == "ABSTAIN"

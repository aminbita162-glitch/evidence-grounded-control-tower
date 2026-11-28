"""Both calibrated judgments use the consistency graph and walking skeleton."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

import pytest

from adapters.model.gateway import Gateway
from capabilities import f01, k09
from capabilities.f02.calibration import Pair, fit
from capabilities.f02.registration import ClassificationJudge
from capabilities.f02.scoring import Entry, TariffIndex, TariffPack
from capabilities.k05 import ReferencePack, calibrate_reference
from capabilities.k05.reference import ReferenceGroup, Unit
from capabilities.k05.registration import ValuationJudge, canonical_inputs
from capabilities.k14 import BilingualIntake, Field
from capabilities.k14.demo import FixtureProvider
from capabilities.k14.gateway import GatewayExtraction
from capabilities.k14.workflow import IntakeEvaluation, IntakeWorkflow
from kernel.auth.roles import Principal
from kernel.intake import IntakeStage, ReadResult, TextSegment
from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import compute_payload_hash
from kernel.lib.money import CurrencyTable
from kernel.lib.valuation import FxPack, ValuationRule
from kernel.persistence.repositories.in_memory import InMemoryRepository
from kernel.skeleton import WalkingSkeleton
from kernel.skeleton.intake import SourceDocument
from kernel.types.decision import DecisionValue

AT = datetime(2026, 1, 15, tzinfo=UTC)
END = AT + timedelta(days=1)
CASE = "synthetic-case"
LABEL: Final = "SYNTHETIC"
OWNER = Principal(principal_id="SYN-OPERATOR", role="operator", tenant_id="SYN-TEN-0001")
FIELDS = (
    Field("seller_name", "text"),
    Field("invoice_number", "identifier"),
    Field("issuer", "text"),
    Field("packing_list_number", "identifier"),
    Field("declared_customs_value", "number"),
    Field("declared_date", "date"),
    Field("currency", "identifier"),
    Field("invoice_total", "number"),
    Field("incoterm", "identifier"),
    Field("line_items.1.description", "text"),
    Field("line_items.1.declared_classification_code", "identifier"),
    Field("line_items.1.quantity", "quantity"),
    Field("line_items.1.line_amount", "number"),
)
DESCRIPTIONS = {
    "1101": "wheat flour finely ground",
    "1201": "soy beans edible seeds",
}


class FixtureReader:
    async def read(self, payload: bytes, media_type: str) -> ReadResult:
        return ReadResult(media_type, (TextSegment(0, payload.decode()),))


def documents(description: str | None = DESCRIPTIONS["1101"]) -> tuple[SourceDocument, ...]:
    fields = (
        "declared_customs_value: 10\n"
        f"declared_date: {AT.date()}\n"
        "currency: AED\ninvoice_total: 10\nincoterm: CIF\n"
        "line_items.1.declared_classification_code: 1101\n"
        "line_items.1.quantity: 10 kg\nline_items.1.line_amount: 10\n"
    )
    if description is not None:
        fields += f"line_items.1.description: {description}\n"
    return (
        SourceDocument(
            "invoice.txt",
            "COMMERCIAL_INVOICE",
            (
                "Synthetic invoice\nseller_name: Synthetic Example Ltd\ninvoice_number: SYN-1\n"
                + fields
            ).encode(),
        ),
        SourceDocument(
            "packing.txt",
            "PACKING_LIST",
            (
                "Synthetic packing list\nissuer: Synthetic Example Ltd\n"
                "packing_list_number: SYN-2\n" + fields
            ).encode(),
        ),
    )


def workflow(reference_label: str = LABEL, tariff_label: str = LABEL) -> IntakeWorkflow:
    currency = CurrencyTable({"AED": 2}, "SRC-SYNTHETIC-K05")
    fx = FxPack("synthetic-fx", currency, {}, LABEL)
    rules = {"CIF": ValuationRule("SYN-CIF", (), LABEL)}
    reference = ReferencePack(
        "synthetic-reference",
        reference_label,
        "SRC-SYNTHETIC-K05",
        AT,
        END,
        {"1101": ReferenceGroup("1101", "kg", "AED", (Decimal(1),) * 30)},
        {},
        {"kg": Unit("mass", Decimal(1))},
    )
    interval = calibrate_reference(
        (Decimal(2),) * 500,
        (Decimal(1),),
        (Decimal(3),),
        pack_hash=reference.version_hash,
        source_id=reference.source_id,
    )
    tariff = TariffIndex.build(
        TariffPack(
            "SRC-SYNTHETIC-F02",
            tariff_label,
            AT,
            END,
            (2, 4),
            4,
            tuple(
                Entry(code, (description,), AT, END) for code, description in DESCRIPTIONS.items()
            ),
        )
    )
    fit_pairs = tuple(
        Pair(code, description, "pack_text" if index % 2 else "commercial_name")
        for code, description in DESCRIPTIONS.items()
        for index in range(250)
    )
    cutoff = fit(
        tariff,
        fit_pairs,
        fit_pairs[:4],
        (Pair("1101", "assorted goods lot", "commercial_name"),),
        language="en",
        source_id="SRC-SYNTHETIC-F02",
    )
    return IntakeWorkflow(
        IntakeStage(
            FixtureReader(), InMemoryRepository("documents"), InMemoryRepository("originals")
        ),
        BilingualIntake(GatewayExtraction(Gateway(FixtureProvider()))),
        k09.FingerprintIndex(),
        f01.Workflow(currency_precision=(("AED", 2),), allowed_labels=frozenset({LABEL})),
        fields=FIELDS,
        label=LABEL,
        judges={
            "K05": ValuationJudge(fx, rules, reference, interval),
            "F02": ClassificationJudge(tariff, {"en": cutoff}),
        },
    )


def evaluate(
    service: IntakeWorkflow, uploads: tuple[SourceDocument, ...]
) -> tuple[IntakeEvaluation, InMemoryCaseChain]:
    chain = InMemoryCaseChain("SYN-TEN-0001", CASE)
    asyncio.run(service.ingest(OWNER, CASE, uploads, AT.isoformat(), chain=chain))
    result = service.result(OWNER, CASE)
    assert result is not None
    return result, chain


@pytest.mark.fast
def test_T_VAL_0001_consensus_feeds_both_judgments() -> None:
    """
    id: T-VAL-0001
    title: Consensus feeds both judgments
    purpose: Consensus feeds both judgments
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S01
    """
    result, _ = evaluate(workflow(), documents())
    assert {item.capability_id: item.outcome for item in result.judgments} == {
        "F02": DecisionValue.ALLOW,
        "K05": DecisionValue.ALLOW,
    }
    assert all(len(fact.source_fact_ids) == 2 for fact in result.consistency.canonical)


@pytest.mark.fast
def test_T_VAL_0002_absent_consensus_causes_both_to_abstain() -> None:
    """
    id: T-VAL-0002
    title: Absent consensus causes both to abstain
    purpose: Absent consensus causes both to abstain
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S02
    """
    result, _ = evaluate(workflow(), documents()[:1])
    assert result.consistency.canonical == ()
    assert all(item.outcome == DecisionValue.ABSTAIN for item in result.judgments)
    assert all(item.reasons[0].endswith(".UPSTREAM") for item in result.judgments)


@pytest.mark.fast
def test_T_VAL_0003_description_change_marks_both_stale_and_recomputes() -> None:
    """
    id: T-VAL-0003
    title: Description change marks both stale and recomputes
    purpose: Description change marks both stale and recomputes
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S03
    """

    async def scenario() -> None:
        service = workflow()
        chain = InMemoryCaseChain("SYN-TEN-0001", CASE)
        first = documents()
        await service.ingest(OWNER, CASE, first, AT.isoformat(), chain=chain)
        original = service.result(OWNER, CASE)
        assert original is not None
        admin = Principal(
            principal_id=OWNER.principal_id, role="administrator", tenant_id=OWNER.tenant_id
        )
        for document in original.documents:
            await service.erase_document(admin, CASE, document.record.document_id)
        await service.ingest(OWNER, CASE, documents(DESCRIPTIONS["1201"]), AT.isoformat())
        latest = service.result(OWNER, CASE)
        assert latest is not None
        records = await chain.list()
        states = {
            record.payload_hash for record in records if record.record_type == "case_judgment_stale"
        }
        assert all(
            compute_payload_hash(
                {"capability_id": judge.capability_id, "output_hash": judge.evidence["output_hash"]}
            )
            in states
            for judge in original.judgments
        )
        assert latest.judgments[0].outcome == DecisionValue.ESCALATE

    asyncio.run(scenario())


@pytest.mark.fast
def test_T_VAL_0004_secondary_reference_cannot_allow() -> None:
    """
    id: T-VAL-0004
    title: Secondary reference cannot allow
    purpose: Secondary reference cannot allow
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S04
    """
    result, _ = evaluate(workflow(reference_label="SECONDARY"), documents())
    decisions = {item.capability_id: item for item in result.judgments}
    assert decisions["K05"].outcome == DecisionValue.ABSTAIN
    assert decisions["K05"].reasons == ("K05.ABSTAIN.LABEL_INSUFFICIENT",)


@pytest.mark.fast
def test_T_VAL_0005_secondary_tariff_cannot_allow() -> None:
    """
    id: T-VAL-0005
    title: Secondary tariff cannot allow
    purpose: Secondary tariff cannot allow
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S05
    """
    result, _ = evaluate(workflow(tariff_label="SECONDARY"), documents())
    decisions = {item.capability_id: item for item in result.judgments}
    assert decisions["F02"].outcome == DecisionValue.ABSTAIN
    assert decisions["F02"].reasons == ("F02.ABSTAIN.LABEL_INSUFFICIENT",)


@pytest.mark.fast
def test_T_VAL_0006_secondary_tariff_contributes_to_skeleton_decision() -> None:
    """
    id: T-VAL-0006
    title: Secondary tariff contributes to skeleton decision
    purpose: Secondary tariff contributes to skeleton decision
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S06
    """
    result = asyncio.run(
        WalkingSkeleton().run(intake=workflow(tariff_label="SECONDARY"), uploads=documents())
    )
    assert result.decision == "ABSTAIN"
    assert "F02.ABSTAIN.LABEL_INSUFFICIENT" in result.reason_codes
    assert result.replay_ok and result.bundle_ok and result.structural_ok


@pytest.mark.fast
def test_T_VAL_0007_secondary_reference_contributes_to_skeleton_decision() -> None:
    """
    id: T-VAL-0007
    title: Secondary reference contributes to skeleton decision
    purpose: Secondary reference contributes to skeleton decision
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S07
    """
    result = asyncio.run(
        WalkingSkeleton().run(intake=workflow(reference_label="SECONDARY"), uploads=documents())
    )
    assert result.decision == "ABSTAIN"
    assert "K05.ABSTAIN.LABEL_INSUFFICIENT" in result.reason_codes


@pytest.mark.fast
def test_T_VAL_0008_both_allow_on_synthetic_consensus_and_replay() -> None:
    """
    id: T-VAL-0008
    title: Both allow on synthetic consensus and replay
    purpose: Both allow on synthetic consensus and replay
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S08
    """
    result = asyncio.run(WalkingSkeleton().run(intake=workflow(), uploads=documents()))
    assert result.decision == "ALLOW"
    assert result.replay_ok and result.structural_ok and result.bundle_ok


@pytest.mark.fast
def test_T_VAL_0009_judgment_records_are_in_the_case_chain() -> None:
    """
    id: T-VAL-0009
    title: Judgment records are in the case chain
    purpose: Judgment records are in the case chain
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S09
    """
    result, chain = evaluate(workflow(), documents())
    records = asyncio.run(chain.list())
    hashes = [record.payload_hash for record in records if record.record_type == "case_judgment"]
    assert hashes == [compute_payload_hash(judgment.evidence) for judgment in result.judgments]


@pytest.mark.fast
def test_T_VAL_0010_agreed_exact_quantity_reaches_the_judge() -> None:
    """
    id: T-VAL-0010
    title: Agreed exact quantity reaches the judge
    purpose: Agreed exact quantity reaches the judge
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S10
    """
    result, _ = evaluate(workflow(), documents())
    inputs = canonical_inputs(result.consistency.canonical)
    assert inputs is not None
    assert inputs.lines[0].quantity == Decimal(10)
    assert inputs.lines[0].unit == "kg"


@pytest.mark.fast
def test_T_VAL_0011_missing_description_is_not_inferred() -> None:
    """
    id: T-VAL-0011
    title: Missing description is not inferred
    purpose: Missing description is not inferred
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S11
    """
    result, _ = evaluate(workflow(), documents(None))
    outcome = {item.capability_id: item.outcome for item in result.judgments}
    assert outcome == {"F02": DecisionValue.ABSTAIN, "K05": DecisionValue.ALLOW}


@pytest.mark.fast
def test_T_VAL_0012_conflicting_line_codes_are_not_canonical() -> None:
    """
    id: T-VAL-0012
    title: Conflicting line codes are not canonical
    purpose: Conflicting line codes are not canonical
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S12
    """
    first, second = documents()
    second = replace(second, payload=second.payload.replace(b"code: 1101", b"code: 1201"))
    result, _ = evaluate(workflow(), (first, second))
    assert not any(
        fact.key.endswith("declared_classification_code") for fact in result.consistency.canonical
    )
    assert all(item.outcome == DecisionValue.ABSTAIN for item in result.judgments)


@pytest.mark.fast
def test_T_VAL_0013_tenant_boundary_covers_judgment_evidence() -> None:
    """
    id: T-VAL-0013
    title: Tenant boundary covers judgment evidence
    purpose: Tenant boundary covers judgment evidence
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S13
    """
    service = workflow()
    evaluate(service, documents())
    other = Principal(principal_id="SYN-OPERATOR", role="operator", tenant_id="SYN-TEN-0002")
    assert service.result(other, CASE) is None


@pytest.mark.fast
def test_T_VAL_0014_repeated_workflows_commit_to_identical_judgments() -> None:
    """
    id: T-VAL-0014
    title: Repeated workflows commit to identical judgments
    purpose: Repeated workflows commit to identical judgments
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S14
    """
    first, _ = evaluate(workflow(), documents())
    second, _ = evaluate(workflow(), documents())
    assert first.judgments == second.judgments


@pytest.mark.fast
def test_T_VAL_0015_two_judgments_meet_the_deterministic_budget() -> None:
    """
    id: T-VAL-0015
    title: Two judgments meet the deterministic budget
    purpose: Two judgments meet the deterministic budget
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S15
    """
    from statistics import quantiles
    from time import perf_counter

    from capabilities.f02.synthetic import create_judge as classifier
    from capabilities.k05.synthetic import START
    from capabilities.k05.synthetic import create_judge as valuation

    fields = (
        ("description", DESCRIPTIONS["1101"], None),
        ("declared_classification_code", "1101", None),
        ("quantity", "10", "kg"),
        ("line_amount", "10", "AED"),
        ("material", "wheat", None),
    )
    totals = (
        ("currency", "AED", None),
        ("invoice_total", "390", "AED"),
        ("declared_customs_value", "390", "AED"),
        ("declared_date", START.date().isoformat(), None),
        ("incoterm", "CIF", None),
    )
    facts = tuple(
        f01.CanonicalFact(f"shipment.{key}", value, ("totals",), unit)
        for key, value, unit in totals
    ) + tuple(
        f01.CanonicalFact(f"shipment.line_items.{index}.{key}", value, (f"line-{index}",), unit)
        for index in range(1, 40)
        for key, value, unit in fields
    )
    assert len(facts) == 200
    judges = (valuation(), classifier())
    durations = []
    for _ in range(15):
        start = perf_counter()
        decisions = [judge.run(facts, START, LABEL)[0].outcome for judge in judges]
        durations.append(perf_counter() - start)
        assert decisions == [DecisionValue.ALLOW, DecisionValue.ALLOW]
    assert quantiles(durations, n=100, method="inclusive")[94] <= 0.2


@pytest.mark.fast
@pytest.mark.parametrize("capability", ["K05", "F02"])
def test_T_VAL_0016_cli_evaluates_the_synthetic_shipment(
    capability: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    id: T-VAL-0016
    title: Cli evaluates the synthetic shipment
    purpose: Cli evaluates the synthetic shipment
    level: fast
    requirement: P15, Part 5 section 5.VAL
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: VAL
    scenario ids: VAL-S16
    """
    import json

    from cli.main import main

    assert main(["evaluate", "--capability", capability]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["capability_id"] == capability
    assert report["report"]["outcome"] == "ALLOW"
    assert report["report"]["label"] == "SYNTHETIC"

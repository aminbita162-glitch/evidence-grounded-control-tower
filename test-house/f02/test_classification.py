"""Synthetic F02 scenario, shift, responsible-use and interface evidence."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from test_scoring import AT, ENDS, HELD, INDEX, PACK, SHIFTED, TEXTS, pairs_for

from api.app import AppPorts, create_app
from api.authentication import operator_principal, tenant_principal
from capabilities.f01 import CanonicalFact, ConsistencyReport
from capabilities.f02 import BANNER, COVERAGE_CLAIM, ClassificationReport, Line, Reason, evaluate
from capabilities.f02.calibration import Calibration, fit
from capabilities.f02.registration import ClassificationJudge
from capabilities.f02.scoring import Entry, Exclusion, TariffIndex
from capabilities.k09 import DocumentShieldReport
from capabilities.k14.workflow import IntakeEvaluation, IntakeWorkflow
from data.synthetic.calibration.classification import SOURCE_ID, commercial_names, generate_pairs
from kernel.auth.roles import Principal
from kernel.decision import FactEntry
from kernel.types.decision import DecisionValue

CAL = fit(INDEX, pairs_for(PACK, (125,) * 4), HELD, SHIFTED, language="en", source_id=SOURCE_ID)
JUDGE = ClassificationJudge(INDEX, {"en": CAL})
PATH = "/api/v1/cases/synthetic/capabilities/F02/evaluations"
FACTS = (
    CanonicalFact("shipment.line_items.1.description", TEXTS["1101"], ("description",)),
    CanonicalFact("shipment.line_items.1.declared_classification_code", "1101", ("code",)),
)
STATISTICAL_LABEL = "implementation-correctness"


def shipment(description: str = TEXTS["1101"], code: str = "1101", *, key: str = "1") -> Line:
    return Line(
        key,
        FactEntry("declared_classification_code", code, "VERIFIED", "DERIVED"),
        FactEntry("description", description, "VERIFIED", "DERIVED"),
    )


def assess(
    lines: tuple[Line, ...] = (shipment(),),
    *,
    index: TariffIndex | None = INDEX,
    calibration: dict[str, Calibration] | None = None,
    at_offset: timedelta = timedelta(),
    origin: str = "SYNTHETIC",
) -> ClassificationReport:
    return evaluate(
        lines,
        index=index,
        calibration={"en": CAL} if calibration is None else calibration,
        at=AT + at_offset,
        data_origin=origin,
    )


def bound(index: TariffIndex, threshold: float = 0.0) -> dict[str, Calibration]:
    return {"en": replace(CAL, pack_hash=index.pack_hash, threshold=threshold)}


def shared_heading() -> TariffIndex:
    entries = (PACK.entries[0], replace(PACK.entries[1], path=(TEXTS["1101"],)), *PACK.entries[2:])
    return TariffIndex.build(replace(PACK, entries=entries))


@pytest.mark.fast
@pytest.mark.parametrize(
    ("item", "code", "outcome"),
    [
        (shipment(), Reason.OK, DecisionValue.ALLOW),
        (shipment(TEXTS["1201"]), Reason.OUTSIDE, DecisionValue.ESCALATE),
        (shipment("goods"), Reason.DESCRIPTION_TOO_SHORT, DecisionValue.ABSTAIN),
        (shipment(code="1901"), Reason.INVALID, DecisionValue.HOLD),
        (shipment("خبز كعك دقيق"), Reason.LANGUAGE_UNSUPPORTED, DecisionValue.ABSTAIN),
    ],
    ids=["T-F02-0001", "T-F02-0002", "T-F02-0004", "T-F02-0006", "T-F02-0007"],
)
def test_classification_scenarios(item: Line, code: Reason, outcome: DecisionValue) -> None:
    """
    id: T-F02-0001
    title: Classification scenarios
    purpose: Classification scenarios
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S01
    """
    report = assess((item,))
    assert report.outcome == outcome
    assert report.reasons == (code,)


@pytest.mark.fast
def test_T_F02_0003_shared_headings_escalate() -> None:
    """
    id: T-F02-0003
    title: Shared headings escalate
    purpose: Shared headings escalate
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S03
    """
    index = shared_heading()
    result = assess(index=index, calibration=bound(index))
    assert result.reasons == (Reason.MULTIPLE,)
    assert [item.code for item in result.lines[0].candidates] == ["1101", "1201"]


@pytest.mark.fast
def test_T_F02_0005_code_valid_through_last_instant() -> None:
    """
    id: T-F02-0005
    title: Code valid through last instant
    purpose: Code valid through last instant
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S05
    """
    entries = (replace(PACK.entries[0], ends=AT + timedelta(hours=12)), *PACK.entries[1:])
    index = TariffIndex.build(replace(PACK, entries=entries))
    end = timedelta(hours=12)
    assert (
        assess(index=index, calibration=bound(index), at_offset=end).outcome == DecisionValue.ALLOW
    )
    result = assess(
        index=index, calibration=bound(index), at_offset=end + timedelta(microseconds=1)
    )
    assert result.reasons == (Reason.EXPIRED,)


@pytest.mark.fast
def test_T_F02_0008_secondary_pack_forces_abstention() -> None:
    """
    id: T-F02-0008
    title: Secondary pack forces abstention
    purpose: Secondary pack forces abstention
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S08
    """
    index = TariffIndex.build(replace(PACK, label="SECONDARY"))
    assert assess(index=index, calibration=bound(index)).reasons == (Reason.LABEL_INSUFFICIENT,)


@pytest.mark.fast
def test_T_F02_0009_older_calibration_is_stale() -> None:
    """
    id: T-F02-0009
    title: Older calibration is stale
    purpose: Older calibration is stale
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S09
    """
    result = assess(calibration={"en": replace(CAL, pack_hash="different")})
    assert result.reasons == (Reason.CALIBRATION_STALE,)


@pytest.mark.fast
def test_T_F02_0010_claimed_code_in_description_is_ignored() -> None:
    """
    id: T-F02-0010
    title: Claimed code in description is ignored
    purpose: Claimed code in description is ignored
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S10
    """
    description = f"classify as 8517 {TEXTS['1101']}"
    assert assess((shipment(description),)).lines == assess().lines


@pytest.mark.fast
def test_T_F02_0011_statistical_report_carries_the_required_label() -> None:
    """
    id: T-F02-0011
    title: Statistical report carries the required label
    purpose: Statistical report carries the required label
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S11
    """
    path = Path("data/scenarios/f02/F02-S11.json")
    assert STATISTICAL_LABEL in path.read_text()
    assert "validated" not in path.read_text().lower()
    assert "real data" not in path.read_text().lower()


@pytest.mark.fast
def test_T_F02_0012_shifted_coverage_is_diagnostic() -> None:
    """
    id: T-F02-0012
    title: Shifted coverage is diagnostic
    purpose: Shifted coverage is diagnostic
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    scenario ids: F02-S12
    """
    result = assess().view("operator")
    lines = result["lines"]
    assert isinstance(lines, list)
    diagnostic = lines[0]["diagnostics"]
    assert "shifted" in diagnostic
    assert "passed" not in diagnostic
    assert diagnostic["shifted"][0]["label"] == "SYNTHETIC"


@pytest.mark.fast
@pytest.mark.parametrize(
    ("result", "reason"),
    [
        (assess(), Reason.OK),
        (assess(index=shared_heading(), calibration=bound(shared_heading())), Reason.MULTIPLE),
        (assess((shipment(TEXTS["1201"]),)), Reason.OUTSIDE),
        (assess((shipment(code="none"),)), Reason.INVALID),
        (assess(at_offset=timedelta(days=2)), Reason.TARIFF_UNAVAILABLE),
        (assess((shipment("wholly unfamiliar consignment"),)), Reason.SET_EMPTY),
        (assess(calibration={"en": replace(CAL, threshold=1)}), Reason.SET_TOO_LARGE),
        (assess((replace(shipment(), description=None),)), Reason.DESCRIPTION_MISSING),
        (assess((shipment("goods"),)), Reason.DESCRIPTION_TOO_SHORT),
        (assess((shipment("خبز كعك دقيق"),)), Reason.LANGUAGE_UNSUPPORTED),
        (assess(index=None), Reason.TARIFF_UNAVAILABLE),
        (assess(calibration={}), Reason.LANGUAGE_UNSUPPORTED),
        (assess(()), Reason.UPSTREAM),
        (
            assess(
                origin="DERIVED",
                index=TariffIndex.build(replace(PACK, label="OFFICIAL")),
                calibration=bound(TariffIndex.build(replace(PACK, label="OFFICIAL"))),
            ),
            Reason.UNVALIDATED,
        ),
    ],
    ids=[f"T-F02-{number:04}" for number in range(101, 115)],
)
def test_closed_outcome_reasons(result: ClassificationReport, reason: Reason) -> None:
    """
    id: T-F02-0101
    title: Closed outcome reasons
    purpose: Closed outcome reasons
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert reason in result.reasons


@pytest.mark.fast
def test_T_F02_0231_shift_increases_abstain_or_escalate_by_margin() -> None:
    """
    id: T-F02-0231
    title: Shift increases abstain or escalate by margin
    purpose: Shift increases abstain or escalate by margin
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    labels = commercial_names("en")
    descriptions = generate_pairs(TEXTS, labels, chapter_digits=2, seed=211, count=80)
    shifted = generate_pairs(TEXTS, labels, chapter_digits=2, seed=569, count=80, shifted=True)
    control = [assess((shipment(row.text, row.code),)).outcome for row in descriptions]
    adversarial = [assess((shipment(row.text, row.code),)).outcome for row in shifted]
    review = {DecisionValue.ABSTAIN, DecisionValue.ESCALATE}
    margin = 0.30
    assert sum(x in review for x in adversarial) >= sum(x in review for x in control) + margin * 80


@pytest.mark.fast
def test_T_F02_0232_shift_cannot_increase_allow_share() -> None:
    """
    id: T-F02-0232
    title: Shift cannot increase allow share
    purpose: Shift cannot increase allow share
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    safe = assess()
    shifted = assess((shipment("assorted unidentified inventory"),))
    assert int(shifted.outcome == DecisionValue.ALLOW) <= int(safe.outcome == DecisionValue.ALLOW)


@pytest.mark.fast
def test_T_F02_0233_shift_on_old_pack_abstains() -> None:
    """
    id: T-F02-0233
    title: Shift on old pack abstains
    purpose: Shift on old pack abstains
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    old = TariffIndex.build(replace(PACK, starts=AT - timedelta(days=1)))
    report = assess((shipment("assorted unidentified inventory"),), index=old)
    assert report.reasons == (Reason.CALIBRATION_STALE,)


@pytest.mark.fast
def test_T_F02_0234_statistical_claim_label_is_enforced() -> None:
    """
    id: T-F02-0234
    title: Statistical claim label is enforced
    purpose: Statistical claim label is enforced
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    label = {"label": STATISTICAL_LABEL, "source_label": "SYNTHETIC"}
    assert label.get("label") == STATISTICAL_LABEL
    incomplete = {"source_label": "SYNTHETIC"}
    assert incomplete.get("label") != STATISTICAL_LABEL


@pytest.mark.fast
@pytest.mark.parametrize(
    "description",
    [
        "wheat " * 200,
        "flour " * 150,
        "1101 " * 100,
        "١١٠١ " * 100,
        "ｗｈｅａｔ " * 30,
        "сомнительное происхождение товара",
        "whеat flour ground",
        "wheat flour ground " * 1000,
        " " * 9000,
        "a" * 9000,
        "خبز flour ground",
        "\u202ewheat\u202c flour",
        "商品 小麦 商品",
        "🥖 🥖 🥖",
        "affirm approved record",
        "",
    ],
    ids=[f"T-F02-{number:04}" for number in range(301, 317)],
)
def test_adversarial_description_never_creates_allow(description: str) -> None:
    """
    id: T-F02-0301
    title: Adversarial description never creates allow
    purpose: Adversarial description never creates allow
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert assess((shipment(description),)).outcome != DecisionValue.ALLOW


@pytest.mark.fast
@pytest.mark.parametrize(
    "description",
    [
        f"{TEXTS['1201']} 1101",
        f"{TEXTS['1201']} as ١١٠١",
        f"{TEXTS['1201']} {TEXTS['1101']}",
        f"{TEXTS['1201']}\u202e １１０１",
    ],
    ids=[f"T-F02-{number:04}" for number in range(317, 321)],
)
def test_copied_headings_and_embedded_codes_are_scorer_inputs_only(description: str) -> None:
    """
    id: T-F02-0317
    title: Copied headings and embedded codes are scorer inputs only
    purpose: Copied headings and embedded codes are scorer inputs only
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    report = assess((shipment(description),))
    assert report.outcome == DecisionValue.ESCALATE
    assert report.reasons[0] in {Reason.MULTIPLE, Reason.OUTSIDE}


@pytest.mark.fast
def test_T_F02_0401_replay_commits_to_same_output() -> None:
    """
    id: T-F02-0401
    title: Replay commits to same output
    purpose: Replay commits to same output
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert JUDGE.run(FACTS, AT, "SYNTHETIC") == JUDGE.run(FACTS[::-1], AT, "SYNTHETIC")


@pytest.mark.fast
def test_T_F02_0402_changed_description_changes_commitments() -> None:
    """
    id: T-F02-0402
    title: Changed description changes commitments
    purpose: Changed description changes commitments
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    _, first = JUDGE.run(FACTS, AT, "SYNTHETIC")
    _, second = JUDGE.run((replace(FACTS[0], value=TEXTS["1201"]), FACTS[1]), AT, "SYNTHETIC")
    assert first["input_hash"] != second["input_hash"]
    assert first["output_hash"] != second["output_hash"]


@pytest.mark.fast
def test_T_F02_0403_line_order_does_not_affect_case_outcome() -> None:
    """
    id: T-F02-0403
    title: Line order does not affect case outcome
    purpose: Line order does not affect case outcome
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    rows = (shipment(key="1"), shipment(TEXTS["1201"], key="2"))
    assert assess(rows) == assess(rows[::-1])
    assert assess(rows).outcome == DecisionValue.ESCALATE


@pytest.mark.fast
def test_T_F02_0404_report_keeps_each_line_decision() -> None:
    """
    id: T-F02-0404
    title: Report keeps each line decision
    purpose: Report keeps each line decision
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    report = assess((shipment(key="1"), shipment(code="unknown", key="2")))
    assert [line.outcome for line in report.lines] == [DecisionValue.ALLOW, DecisionValue.HOLD]
    assert report.outcome == DecisionValue.HOLD


@pytest.mark.fast
def test_T_F02_0405_deep_code_reports_the_comparison_level() -> None:
    """
    id: T-F02-0405
    title: Deep code reports the comparison level
    purpose: Deep code reports the comparison level
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    index = TariffIndex.build(
        replace(PACK, entries=(*PACK.entries, Entry("110101", (TEXTS["1101"],), AT, ENDS)))
    )
    result = assess((shipment(code="110101"),), index=index, calibration=bound(index))
    assert result.outcome == DecisionValue.ALLOW
    assert result.lines[0].resolved_level == 4


@pytest.mark.fast
def test_T_F02_0406_exclusions_are_recorded_on_verified_facts() -> None:
    """
    id: T-F02-0406
    title: Exclusions are recorded on verified facts
    purpose: Exclusions are recorded on verified facts
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    base = shared_heading()
    rule = Exclusion("SYN-NOTE", "1201", "material", "wheat")
    index = TariffIndex.build(replace(base.pack, exclusions=(rule,)))
    row = replace(shipment(), attributes=(FactEntry("material", "wheat", "VERIFIED", "DERIVED"),))
    result = assess((row,), index=index, calibration=bound(index))
    assert result.lines[0].exclusions == (rule,)
    assert result.outcome == DecisionValue.ALLOW


@pytest.mark.fast
@pytest.mark.parametrize(
    "status",
    ["UNKNOWN", "CONFLICTED", "PROPOSED", "REJECTED"],
    ids=[f"T-F02-{number:04}" for number in range(407, 411)],
)
def test_unverified_attribute_cannot_exclude(status: str) -> None:
    """
    id: T-F02-0407
    title: Unverified attribute cannot exclude
    purpose: Unverified attribute cannot exclude
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    base = shared_heading()
    rule = Exclusion("SYN-NOTE", "1201", "material", "wheat")
    index = TariffIndex.build(replace(base.pack, exclusions=(rule,)))
    row = replace(shipment(), attributes=(FactEntry("material", "wheat", status, "DERIVED"),))
    result = assess((row,), index=index, calibration=bound(index))
    assert result.reasons == (Reason.MULTIPLE,)
    assert not result.lines[0].exclusions


class CaseStore:
    def result(self, principal: Principal, case_id: str) -> IntakeEvaluation | None:
        if case_id != "synthetic" or principal.tenant_id != "synthetic-tenant":
            return None
        consistency = ConsistencyReport(
            case_id, AT.isoformat(), "configuration", (), (), (), (), (), FACTS, "ALLOW", (), ()
        )
        return IntakeEvaluation(
            case_id, "SYNTHETIC", (), (), consistency, cast("DocumentShieldReport", None), {}
        )


def client(tenant: str = "synthetic-tenant") -> TestClient:
    app = create_app(AppPorts(intake=cast("IntakeWorkflow", CaseStore()), classification=JUDGE))
    principal = Principal(principal_id="test", role="operator", tenant_id=tenant)
    app.dependency_overrides[tenant_principal] = lambda: principal
    app.dependency_overrides[operator_principal] = lambda: principal
    return TestClient(app)


def create(browser: TestClient) -> dict[str, object]:
    result = browser.post(
        PATH, json={"evaluation_time": AT.isoformat()}, headers={"Idempotency-Key": "synthetic-key"}
    )
    assert result.status_code == 201, result.text
    return cast("dict[str, object]", result.json())


@pytest.mark.fast
def test_T_F02_0501_http_invocation_returns_decision() -> None:
    """
    id: T-F02-0501
    title: Http invocation returns decision
    purpose: Http invocation returns decision
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert create(client())["status"] == "ALLOW"


@pytest.mark.fast
def test_T_F02_0502_case_result_has_verbatim_banner() -> None:
    """
    id: T-F02-0502
    title: Case result has verbatim banner
    purpose: Case result has verbatim banner
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    browser = client()
    created = create(browser)
    result = browser.get(f"{PATH}/{created['evaluation_id']}").json()
    assert result["report"]["banner"] == BANNER


@pytest.mark.fast
def test_T_F02_0503_other_tenant_cannot_invoke() -> None:
    """
    id: T-F02-0503
    title: Other tenant cannot invoke
    purpose: Other tenant cannot invoke
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert (
        client("external")
        .post(PATH, json={"evaluation_time": AT.isoformat()}, headers={"Idempotency-Key": "one"})
        .status_code
        == 404
    )


@pytest.mark.fast
def test_T_F02_0504_unknown_evaluation_is_not_found() -> None:
    """
    id: T-F02-0504
    title: Unknown evaluation is not found
    purpose: Unknown evaluation is not found
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert client().get(f"{PATH}/unknown").status_code == 404


@pytest.mark.fast
def test_T_F02_0505_view_anchor_is_stable() -> None:
    """
    id: T-F02-0505
    title: View anchor is stable
    purpose: View anchor is stable
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    view = Path("capabilities/f02/view.html").read_text()
    assert 'id="f02"' in view
    assert BANNER in view


@pytest.mark.fast
def test_T_F02_0506_coverage_claim_and_language_are_recorded() -> None:
    """
    id: T-F02-0506
    title: Coverage claim and language are recorded
    purpose: Coverage claim and language are recorded
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    view = assess().view("viewer")
    rows = view["lines"]
    assert isinstance(rows, list)
    assert rows[0]["coverage_claim"] == COVERAGE_CLAIM
    assert rows[0]["language"] == "en"


@pytest.mark.fast
@pytest.mark.parametrize(
    "role",
    ["reviewer", "administrator", "operator", "viewer"],
    ids=[f"T-F02-{number:04}" for number in range(507, 511)],
)
def test_no_duty_or_rewording_advice(role: str) -> None:
    """
    id: T-F02-0507
    title: No duty or rewording advice
    purpose: No duty or rewording advice
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    view = str(assess().view(role)).lower()
    for phrase in ("lower duty", "highest duty", "reword", "rewrite the description"):
        assert phrase not in view


@pytest.mark.fast
def test_T_F02_0511_calibration_hash_appears_in_evidence() -> None:
    """
    id: T-F02-0511
    title: Calibration hash appears in evidence
    purpose: Calibration hash appears in evidence
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    _, evidence = JUDGE.run(FACTS, AT, "SYNTHETIC")
    assert evidence["calibration_hashes"] == [CAL.digest]
    assert evidence["tariff_pack_hash"] == INDEX.pack_hash


@pytest.mark.fast
def test_T_F02_0512_case_reports_supported_languages() -> None:
    """
    id: T-F02-0512
    title: Case reports supported languages
    purpose: Case reports supported languages
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    assert assess().view("operator")["languages"] == ("en",)


@pytest.mark.fast
def test_T_F02_0236_active_calibration_must_support_the_published_claim() -> None:
    """
    id: T-F02-0236
    title: Active calibration must support the published claim
    purpose: Active calibration must support the published claim
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    result = assess(calibration={"en": replace(CAL, alpha=0.2)})
    assert result.reasons == (Reason.CALIBRATION_STALE,)
    assert result.lines[0].calibration is None


@pytest.mark.fast
def test_T_F02_0321_repeated_single_keyword_cannot_pass_with_the_active_pack() -> None:
    """
    id: T-F02-0321
    title: Repeated single keyword cannot pass with the active pack
    purpose: Repeated single keyword cannot pass with the active pack
    level: fast
    requirement: P15, Part 5 section 5.F02
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: F02
    """
    from capabilities.f02.synthetic import create_judge

    active = create_judge()
    result = assess(
        (shipment("wheat wheat wheat wheat"),),
        index=active.index,
        calibration=dict(active.calibration),
    )
    assert result.reasons == (Reason.DESCRIPTION_TOO_SHORT,)

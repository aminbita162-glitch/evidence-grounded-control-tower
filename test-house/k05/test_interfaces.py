"""Adversarial valuation inputs and authenticated case evaluation behavior."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from typing import cast

import pytest
from fastapi.testclient import TestClient
from test_basis_and_reference import FX, RULES
from test_valuation import AT, CAL, CODE, INPUT, PACK, assess, line

from api.app import AppPorts, create_app
from api.authentication import operator_principal, tenant_principal
from capabilities.f01 import CanonicalFact, ConsistencyReport
from capabilities.k05 import BANNER, COVERAGE_CLAIM, Reason
from capabilities.k05.registration import ValuationJudge, canonical_inputs
from capabilities.k14.workflow import IntakeEvaluation, IntakeWorkflow
from kernel.auth.roles import Principal
from kernel.types.decision import DecisionValue

PATH = "/api/v1/cases/synthetic/capabilities/K05/evaluations"
FACTS = (
    CanonicalFact("shipment.currency", "AED", ("source-currency",)),
    CanonicalFact("shipment.invoice_total", "1", ("source-invoice",), "AED"),
    CanonicalFact("shipment.declared_customs_value", "1", ("source-declared",), "AED"),
    CanonicalFact("shipment.declared_date", AT.date().isoformat(), ("source-date",)),
    CanonicalFact("shipment.incoterm", "CIF", ("source-incoterm",)),
    CanonicalFact("shipment.line_items.1.declared_classification_code", CODE, ("source-code",)),
    CanonicalFact("shipment.line_items.1.quantity", "1", ("source-quantity",), "kg"),
    CanonicalFact("shipment.line_items.1.line_amount", "1", ("source-amount",), "AED"),
)
JUDGE = ValuationJudge(FX, RULES, PACK, CAL)


@pytest.mark.fast
@pytest.mark.parametrize(
    "value",
    ["0", "-1", "-0.001", "-1E+32", "NaN", "Infinity", "-Infinity"],
    ids=[f"T-K05-{number:04}" for number in range(301, 308)],
)
def test_rejects_nonpositive_and_nonfinite_values(value: str) -> None:
    """
    id: T-K05-0301
    title: Rejects nonpositive and nonfinite values
    purpose: Rejects nonpositive and nonfinite values
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    report = assess(replace(INPUT, lines=(line(value),)))
    assert report.outcome == DecisionValue.ABSTAIN
    assert report.reasons == (Reason.REFERENCE_INSUFFICIENT,)


@pytest.mark.fast
@pytest.mark.parametrize(
    "quantity",
    ["0", "-1", "NaN", "Infinity", "-Infinity"],
    ids=[f"T-K05-{number:04}" for number in range(308, 313)],
)
def test_rejects_invalid_quantities(quantity: str) -> None:
    """
    id: T-K05-0308
    title: Rejects invalid quantities
    purpose: Rejects invalid quantities
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    report = assess(replace(INPUT, lines=(line(quantity=quantity),)))
    assert report.reasons == (Reason.UNIT_UNSUPPORTED,)


@pytest.mark.fast
@pytest.mark.parametrize(
    "unit",
    ["l", "piece", "КG", "㎏", "kg\u202e", ""],
    ids=[f"T-K05-{number:04}" for number in range(313, 319)],
)
def test_rejects_unknown_or_incompatible_units(unit: str) -> None:
    """
    id: T-K05-0313
    title: Rejects unknown or incompatible units
    purpose: Rejects unknown or incompatible units
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    assert assess(replace(INPUT, lines=(line(unit=unit),))).reasons == (Reason.UNIT_UNSUPPORTED,)


@pytest.mark.fast
def test_T_K05_0319_tiny_quantity_is_detected() -> None:
    """
    id: T-K05-0319
    title: Tiny quantity is detected
    purpose: Tiny quantity is detected
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    assert assess(replace(INPUT, lines=(line(quantity="1E-40"),))).reasons == (Reason.ABOVE,)


@pytest.mark.fast
def test_T_K05_0320_extreme_reference_outlier_keeps_robust_position() -> None:
    """
    id: T-K05-0320
    title: Extreme reference outlier keeps robust position
    purpose: Extreme reference outlier keeps robust position
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    group = PACK.groups[CODE]
    changed = replace(group, values=(*group.values[:-1], group.values[-1] * 10**100))
    assert assess(reference=replace(PACK, groups={CODE: changed})).lines == assess().lines


class CaseStore:
    def __init__(self) -> None:
        self.facts = FACTS

    def result(self, principal: Principal, case_id: str) -> IntakeEvaluation | None:
        if principal.tenant_id != "synthetic-tenant" or case_id != "synthetic":
            return None
        consistency = ConsistencyReport(
            case_id,
            AT.isoformat(),
            "configuration",
            (),
            (),
            (),
            (),
            (),
            self.facts,
            "ALLOW",
            (),
            (),
        )
        from capabilities.k09 import DocumentShieldReport

        return IntakeEvaluation(
            case_id, "SYNTHETIC", (), (), consistency, cast("DocumentShieldReport", None), {}
        )


def client(role: str = "operator") -> tuple[TestClient, CaseStore]:
    store = CaseStore()
    app = create_app(AppPorts(intake=cast("IntakeWorkflow", store), valuation=JUDGE))
    tenant = "another-tenant" if role == "external" else "synthetic-tenant"
    principal = Principal(
        principal_id="synthetic-identity",
        role="reviewer" if role == "reviewer" else "operator",
        tenant_id=tenant,
    )
    app.dependency_overrides[tenant_principal] = lambda: principal
    app.dependency_overrides[operator_principal] = lambda: principal
    return TestClient(app), store


def create(browser: TestClient, *, at: str = AT.isoformat(), key: str = "synthetic-key") -> str:
    result = browser.post(PATH, json={"evaluation_time": at}, headers={"Idempotency-Key": key})
    assert result.status_code == 201, result.text
    evaluation = result.json()["evaluation_id"]
    assert isinstance(evaluation, str)
    return evaluation


@pytest.mark.fast
def test_T_K05_0401_replay_is_deterministic() -> None:
    """
    id: T-K05-0401
    title: Replay is deterministic
    purpose: Replay is deterministic
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    original, evidence = JUDGE.run(FACTS, AT, "SYNTHETIC")
    replay, replay_evidence = JUDGE.run(tuple(reversed(FACTS)), AT, "SYNTHETIC")
    assert original == replay
    assert evidence == replay_evidence


@pytest.mark.fast
def test_T_K05_0402_evidence_commits_to_input_change() -> None:
    """
    id: T-K05-0402
    title: Evidence commits to input change
    purpose: Evidence commits to input change
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    _, evidence = JUDGE.run(FACTS, AT, "SYNTHETIC")
    facts = (*FACTS[:-1], replace(FACTS[-1], value="2"))
    _, changed = JUDGE.run(facts, AT, "SYNTHETIC")
    assert evidence["input_hash"] != changed["input_hash"]
    assert evidence["output_hash"] != changed["output_hash"]


@pytest.mark.fast
def test_T_K05_0403_operator_report_uses_redacted_positions() -> None:
    """
    id: T-K05-0403
    title: Operator report uses redacted positions
    purpose: Operator report uses redacted positions
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    result = browser.get(f"{PATH}/{create(browser)}").json()
    assert result["status"] == "ALLOW"
    assert "log_bounds" not in result["report"]["lines"][0]
    assert "log_bounds" not in result["report"]["aggregates"][0]
    assert "log_bounds" not in result["evidence"]


@pytest.mark.fast
def test_T_K05_0404_reviewer_can_inspect_bounds() -> None:
    """
    id: T-K05-0404
    title: Reviewer can inspect bounds
    purpose: Reviewer can inspect bounds
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client("reviewer")
    result = browser.get(f"{PATH}/{create(browser)}").json()
    assert result["report"]["lines"][0]["log_bounds"]


@pytest.mark.fast
def test_T_K05_0405_other_tenant_cannot_invoke() -> None:
    """
    id: T-K05-0405
    title: Other tenant cannot invoke
    purpose: Other tenant cannot invoke
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client("external")
    assert (
        browser.post(
            PATH, json={"evaluation_time": AT.isoformat()}, headers={"Idempotency-Key": "key"}
        ).status_code
        == 404
    )


@pytest.mark.fast
def test_T_K05_0406_other_tenant_cannot_retrieve() -> None:
    """
    id: T-K05-0406
    title: Other tenant cannot retrieve
    purpose: Other tenant cannot retrieve
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client("external")
    assert browser.get(f"{PATH}/synthetic-evaluation").status_code == 404


@pytest.mark.fast
def test_T_K05_0407_fact_revocation_marks_result_stale() -> None:
    """
    id: T-K05-0407
    title: Fact revocation marks result stale
    purpose: Fact revocation marks result stale
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, store = client()
    evaluation = create(browser)
    store.facts = (*FACTS[:-1], replace(FACTS[-1], status="PROPOSED"))
    response = browser.get(f"{PATH}/{evaluation}").json()
    assert response["status"] == "STALE"
    assert "report" not in response


@pytest.mark.fast
def test_T_K05_0408_same_idempotency_key_returns_same_evaluation() -> None:
    """
    id: T-K05-0408
    title: Same idempotency key returns same evaluation
    purpose: Same idempotency key returns same evaluation
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    assert create(browser) == create(browser)


@pytest.mark.fast
def test_T_K05_0409_idempotency_payload_change_returns_conflict() -> None:
    """
    id: T-K05-0409
    title: Idempotency payload change returns conflict
    purpose: Idempotency payload change returns conflict
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    create(browser)
    response = browser.post(
        PATH,
        json={"evaluation_time": (AT + timedelta(seconds=1)).isoformat()},
        headers={"Idempotency-Key": "synthetic-key"},
    )
    assert response.status_code == 409


@pytest.mark.fast
def test_T_K05_0410_query_cannot_select_supplied_facts() -> None:
    """
    id: T-K05-0410
    title: Query cannot select supplied facts
    purpose: Query cannot select supplied facts
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    response = browser.post(
        PATH,
        json={"evaluation_time": AT.isoformat(), "facts": {"tenant": "external"}},
        headers={"Idempotency-Key": "synthetic-key"},
    )
    assert response.status_code == 422


@pytest.mark.fast
def test_T_K05_0501_registration_reads_verified_canonical_facts() -> None:
    """
    id: T-K05-0501
    title: Registration reads verified canonical facts
    purpose: Registration reads verified canonical facts
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    assert canonical_inputs(FACTS) is not None
    assert canonical_inputs((*FACTS[:-1], replace(FACTS[-1], status="PROPOSED"))) is None


@pytest.mark.fast
def test_T_K05_0502_missing_idempotency_key_fails_validation() -> None:
    """
    id: T-K05-0502
    title: Missing idempotency key fails validation
    purpose: Missing idempotency key fails validation
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    assert browser.post(PATH, json={"evaluation_time": AT.isoformat()}).status_code == 422


@pytest.mark.fast
def test_T_K05_0503_naive_time_fails_validation() -> None:
    """
    id: T-K05-0503
    title: Naive time fails validation
    purpose: Naive time fails validation
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    response = browser.post(
        PATH,
        json={"evaluation_time": AT.replace(tzinfo=None).isoformat()},
        headers={"Idempotency-Key": "synthetic-key"},
    )
    assert response.status_code == 422


@pytest.mark.fast
def test_T_K05_0504_generated_openapi_has_evaluation_operations() -> None:
    """
    id: T-K05-0504
    title: Generated openapi has evaluation operations
    purpose: Generated openapi has evaluation operations
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    browser, _ = client()
    spec = browser.get("/api/v1/openapi.json").json()
    expected = "/api/v1/cases/{case_id}/capabilities/{capability_id}/evaluations"
    assert "post" in spec["paths"][expected]
    assert "get" in spec["paths"][f"{expected}/{{evaluation_id}}"]


@pytest.mark.fast
def test_T_K05_0505_view_banner_is_verbatim() -> None:
    """
    id: T-K05-0505
    title: View banner is verbatim
    purpose: View banner is verbatim
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    view = Path("capabilities/k05/view.html").read_text()
    assert BANNER in view
    assert 'id="k05"' in view


@pytest.mark.fast
def test_T_K05_0506_coverage_claim_is_verbatim() -> None:
    """
    id: T-K05-0506
    title: Coverage claim is verbatim
    purpose: Coverage claim is verbatim
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    report, _ = JUDGE.run(FACTS, AT, "SYNTHETIC")
    assert report.view("operator")["coverage_claim"] == COVERAGE_CLAIM


@pytest.mark.fast
@pytest.mark.parametrize(
    "role",
    ["operator", "reviewer", "administrator", "viewer"],
    ids=[f"T-K05-{number:04}" for number in range(507, 511)],
)
def test_view_never_recommends_a_value(role: str) -> None:
    """
    id: T-K05-0507
    title: View never recommends a value
    purpose: View never recommends a value
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    report, _ = JUDGE.run(FACTS, AT, "SYNTHETIC")
    view = str(report.view(role)).lower()
    assert "change the declared value" not in view
    assert "value should be" not in view
    assert "value that would pass" not in view


@pytest.mark.fast
def test_T_K05_0511_evidence_cites_reference_and_calibration() -> None:
    """
    id: T-K05-0511
    title: Evidence cites reference and calibration
    purpose: Evidence cites reference and calibration
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    _, evidence = JUDGE.run(FACTS, AT, "SYNTHETIC")
    assert evidence["reference_pack_hash"] == PACK.version_hash
    assert evidence["calibration_hash"] == CAL.digest


@pytest.mark.fast
def test_T_K05_0512_untrusted_note_cannot_change_report() -> None:
    """
    id: T-K05-0512
    title: Untrusted note cannot change report
    purpose: Untrusted note cannot change report
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    original, _ = JUDGE.run(FACTS, AT, "SYNTHETIC")
    note = CanonicalFact("shipment.note", "price agreed with customs", ("source-note",))
    result, _ = JUDGE.run((*FACTS, note), AT, "SYNTHETIC")
    assert original == result


@pytest.mark.fast
def test_T_K05_0231_invalid_unit_factor_is_refused() -> None:
    """
    id: T-K05-0231
    title: Invalid unit factor is refused
    purpose: Invalid unit factor is refused
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from decimal import Decimal

    from capabilities.k05.reference import Unit

    with pytest.raises(ValueError, match="positive conversion factor"):
        Unit("mass", Decimal(0))


@pytest.mark.fast
def test_T_K05_0232_invalid_reference_sample_abstains() -> None:
    """
    id: T-K05-0232
    title: Invalid reference sample abstains
    purpose: Invalid reference sample abstains
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from decimal import Decimal

    group = PACK.groups[CODE]
    altered = replace(group, values=(*group.values[:-1], Decimal(0)))
    report = assess(reference=replace(PACK, groups={CODE: altered}))
    assert report.reasons == (Reason.REFERENCE_INSUFFICIENT,)


@pytest.mark.fast
def test_T_K05_0233_calibration_rejects_insufficient_draws() -> None:
    """
    id: T-K05-0233
    title: Calibration rejects insufficient draws
    purpose: Calibration rejects insufficient draws
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from decimal import Decimal

    from capabilities.k05 import calibrate_reference

    with pytest.raises(ValueError, match="CALIBRATION_STALE"):
        calibrate_reference(
            (Decimal(1),) * 499,
            (Decimal(1),),
            (Decimal(2),),
            pack_hash=PACK.version_hash,
            source_id=PACK.source_id,
        )


@pytest.mark.fast
def test_T_K05_0234_public_abstention_has_no_basis_or_calibration() -> None:
    """
    id: T-K05-0234
    title: Public abstention has no basis or calibration
    purpose: Public abstention has no basis or calibration
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from capabilities.k05.registration import register

    result, _ = register(None, (), AT, "SYNTHETIC")
    assert result.view("viewer")["calibration_basis"] is None
    assert result.view("viewer")["basis"] is None


@pytest.mark.fast
def test_T_K05_0235_ambiguous_canonical_quantity_abstains() -> None:
    """
    id: T-K05-0235
    title: Ambiguous canonical quantity abstains
    purpose: Ambiguous canonical quantity abstains
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    changed = tuple(
        replace(fact, value=("0.9", "1.1")) if fact.key.endswith(".quantity") else fact
        for fact in FACTS
    )
    assert canonical_inputs(changed) is None


@pytest.mark.fast
def test_T_K05_0236_missing_adjustment_reference_abstains() -> None:
    """
    id: T-K05-0236
    title: Missing adjustment reference abstains
    purpose: Missing adjustment reference abstains
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from datetime import date
    from decimal import Decimal

    from capabilities.k05 import CONTEXT
    from kernel.lib.money import Money
    from kernel.lib.valuation import Adjustment, BasisUnavailable, valuation_basis

    with pytest.raises(BasisUnavailable, match="ADJUSTMENT_MISSING"):
        valuation_basis(
            Money(Decimal(1), "AED"),
            invoice_label="SYNTHETIC",
            target_currency="AED",
            declared_date=date.fromisoformat("2026-11-01"),
            incoterm="FOB",
            fx=FX,
            rules=RULES,
            adjustments={
                "freight": Adjustment(Money(Decimal(1), "AED"), "", "SYNTHETIC"),
                "insurance": Adjustment(Money(Decimal(1), "AED"), "ref", "SYNTHETIC"),
            },
            context=CONTEXT,
        )


@pytest.mark.fast
def test_T_K05_0237_duplicate_rule_adjustment_rejected() -> None:
    """
    id: T-K05-0237
    title: Duplicate rule adjustment rejected
    purpose: Duplicate rule adjustment rejected
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from decimal import Decimal

    from capabilities.k05 import CONTEXT
    from kernel.lib.money import Money
    from kernel.lib.valuation import valuation_basis

    rules = {"CIF": replace(RULES["CIF"], required_adjustments=("freight", "freight"))}
    with pytest.raises(ValueError, match="duplicate adjustment"):
        valuation_basis(
            Money(Decimal(1), "AED"),
            invoice_label="SYNTHETIC",
            target_currency="AED",
            declared_date=AT.date(),
            incoterm="CIF",
            fx=FX,
            rules=rules,
            adjustments={},
            context=CONTEXT,
        )


@pytest.mark.fast
def test_T_K05_0238_unbound_valuation_rules_abstain() -> None:
    """
    id: T-K05-0238
    title: Unbound valuation rules abstain
    purpose: Unbound valuation rules abstain
    level: fast
    requirement: P15, Part 5 section 5.K05
    input: Versioned synthetic case or pack
    expected: The specified decision or invariant holds
    risk: RSK-J-06
    capability: K05
    """
    from capabilities.k05.registration import register

    report, _ = register(None, FACTS, AT, "SYNTHETIC")
    assert report.reasons == (Reason.VALUATION_RULE_UNAVAILABLE,)

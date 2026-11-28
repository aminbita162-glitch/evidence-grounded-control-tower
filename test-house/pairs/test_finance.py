"""Test financial case evaluations through the walking skeleton, CLI and API."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import cast

import pytest
from fastapi.testclient import TestClient

from api.app import AppPorts, create_app
from api.authentication import operator_principal, tenant_principal
from api.routes.capability import evaluate_finance_step
from capabilities.f03.registration import OUTPUT as CLOCKS
from capabilities.f07.registration import OUTPUT as CHARGES
from capabilities.k05 import Line, ReferencePack, ValuationInputs
from capabilities.k05 import evaluate as k05
from capabilities.l01.registration import OUTPUT as INVOICE
from capabilities.l02.registration import INPUT as COST_INPUT
from capabilities.l02.registration import OUTPUT as COST
from cli.main import main
from kernel.auth.roles import Principal
from kernel.skeleton import WalkingSkeleton
from kernel.skeleton.finance import FINANCE_IDS, CaseFinance, run_finance
from kernel.types.decision import DecisionValue

TENANT = "SYN-TEN-0001"
CASE = "SYN-CASE-0001"
AT = datetime(2024, 3, 10, tzinfo=UTC)
STEPS = {capability: partial(evaluate_finance_step, capability) for capability in FINANCE_IDS}


def fixture(capability: str, number: int) -> dict[str, object]:
    scenario = Path(f"data/scenarios/{capability.lower()}/{capability}-S{number:02d}.json")
    raw = json.loads(scenario.read_text())
    payload = dict(raw["inputs"])
    payload.pop("evaluation_time")
    return payload


def snapshot(*, simulation: bool = False, charge: int = 1) -> CaseFinance:
    f07 = fixture("F07", charge)
    source = cast(dict[str, object], f07["invoice"])
    clocks = cast(list[dict[str, object]], f07["clocks"])
    f03 = {
        "clocks": [clocks[0]["clock"]],
        "currencies": source["currencies"],
        "currency_source": source["currency_source"],
        "canonical_containers": f07["canonical_containers"],
    }
    return CaseFinance(
        TENANT,
        CASE,
        "1",
        {
            "F03": f03,
            "L01": source,
            "L02": fixture("L02", 11 if simulation else 1),
            "F07": f07,
        },
        "SYNTHETIC",
    )


def browser(case: list[CaseFinance], tenant: str = TENANT) -> TestClient:
    app = create_app(
        AppPorts(
            finance=lambda tenant_id, case_id: (
                case[0] if case_id == CASE and tenant_id == TENANT else None
            )
        )
    )
    principal = Principal(principal_id="synthetic-identity", role="operator", tenant_id=tenant)
    app.dependency_overrides[tenant_principal] = lambda: principal
    app.dependency_overrides[operator_principal] = lambda: principal
    return TestClient(app)


def route(capability: str) -> str:
    return f"/api/v1/cases/{CASE}/capabilities/{capability}/evaluations"


def create(client: TestClient, cap: str, key: str = "synthetic-key") -> str:
    reply = client.post(
        route(cap), json={"evaluation_time": AT.isoformat()}, headers={"Idempotency-Key": key}
    )
    assert reply.status_code == 201, reply.text
    return cast(str, reply.json()["evaluation_id"])


def changed(case: CaseFinance) -> CaseFinance:
    clock_input = dict(case.inputs["F03"])
    rows = cast(list[dict[str, object]], clock_input["clocks"])
    terms = cast(dict[str, object], rows[0]["terms"])
    clock_input["clocks"] = [dict(rows[0], terms=dict(terms, version="2.0.0"))]
    return replace(case, inputs={**case.inputs, "F03": clock_input})


@pytest.mark.fast
def test_T_FIN_0001_time_basis_published_for_f07() -> None:
    """
    id: T-FIN-0001
    title: Time basis published for f07
    purpose: Time basis published for f07
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Time basis published for f07
    risk: HZ-03
    capability: FIN
    """
    result = run_finance(snapshot(), STEPS, AT)
    upstream = INVOICE.validate_python(result["L01"].report)
    assert upstream.matches[0].basis is not None
    assert upstream.matches[0].reason.value == "L01.OBS.TIME_BASED_MATCHED"
    assert result["F07"].evidence["invoice_audit_hash"] == result["L01"].evidence["output_hash"]


@pytest.mark.fast
def test_T_FIN_0002_shared_clock_produces_same_charge() -> None:
    """
    id: T-FIN-0002
    title: Shared clock produces same charge
    purpose: Shared clock produces same charge
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Shared clock produces same charge
    risk: HZ-03
    capability: FIN
    """
    case = snapshot()
    end = datetime(2024, 3, 4, tzinfo=UTC)
    result = run_finance(case, STEPS, end)
    f03 = CLOCKS.validate_python(result["F03"].report)
    f07 = CHARGES.validate_python(result["F07"].report)
    assert f03.clocks[0].charge == f07.audit.lines[0].expected == Decimal(10)
    assert result["F03"].evidence["output_hash"] == result["F07"].evidence["f03_hash"]


@pytest.mark.fast
def test_T_FIN_0003_total_equals_converted_components() -> None:
    """
    id: T-FIN-0003
    title: Total equals converted components
    purpose: Total equals converted components
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Total equals converted components
    risk: HZ-03
    capability: FIN
    """
    answer = COST.validate_python(run_finance(snapshot(), STEPS, AT)["L02"].report)
    assert answer.estimate.total is not None
    assert answer.estimate.total.base == sum(
        row.converted.base for row in answer.estimate.components if row.converted
    )


@pytest.mark.fast
def test_T_FIN_0004_basis_equals_k05() -> None:
    """
    id: T-FIN-0004
    title: Basis equals k05
    purpose: Basis equals k05
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Basis equals k05
    risk: HZ-03
    capability: FIN
    """
    case = snapshot()
    payload = case.input_for("L02")
    assert payload is not None
    inputs = COST_INPUT.validate_python(payload)
    item = inputs.goods[0]
    output = COST.validate_python(run_finance(case, STEPS, AT)["L02"].report)
    other = k05(
        ValuationInputs(
            item.value,
            item.value,
            item.incoterm,
            item.declared_on,
            item.adjustments,
            (Line(item.id, item.code, item.value, Decimal(1), "kg", item.label),),
            item.label,
        ),
        at=AT,
        fx=inputs.exchange.pack(),
        rules=inputs.valuation_rules,
        reference=ReferencePack("demo", "SYNTHETIC", item.source_id, AT, AT, {}, {}, {}),
        calibration=None,
        data_origin="SYNTHETIC",
    )
    assert output.estimate.duties[0].basis == other.basis


@pytest.mark.fast
def test_T_FIN_0005_corrected_invoice_allows_both_checks() -> None:
    """
    id: T-FIN-0005
    title: Corrected invoice allows both checks
    purpose: Corrected invoice allows both checks
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Corrected invoice allows both checks
    risk: HZ-03
    capability: FIN
    """
    bad = run_finance(snapshot(charge=4), STEPS, AT)
    good = run_finance(snapshot(), STEPS, AT)
    assert bad["F07"].status == "HOLD" and good["L01"].status == good["F07"].status == "ALLOW"


@pytest.mark.fast
def test_T_FIN_0006_tariff_activation_stales_consumers() -> None:
    """
    id: T-FIN-0006
    title: Tariff activation stales consumers
    purpose: Tariff activation stales consumers
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Tariff activation stales consumers
    risk: HZ-03
    capability: FIN
    """
    state = [snapshot()]
    client = browser(state)
    ids = {cap: create(client, cap) for cap in ("F03", "L01", "F07")}
    state[0] = changed(state[0])
    for cap, ident in ids.items():
        response = client.get(f"{route(cap)}/{ident}")
        assert response.json()["status"] == "STALE"
        assert "report" not in response.json()


@pytest.mark.fast
def test_T_FIN_0007_skeleton_records_all_financial_steps() -> None:
    """
    id: T-FIN-0007
    title: Skeleton records all financial steps
    purpose: Skeleton records all financial steps
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Skeleton records all financial steps
    risk: HZ-03
    capability: FIN
    """
    result = asyncio.run(
        WalkingSkeleton().run(
            financial_case=snapshot(), finance_steps=STEPS, finance_at=AT.isoformat()
        )
    )
    assert tuple(result.financial_results) == FINANCE_IDS
    assert result.structural_ok and result.bundle_ok and result.replay_ok
    assert sum(record.record_type == "financial_evaluation" for record in result.records) == 4


@pytest.mark.fast
def test_T_FIN_0008_simulation_uses_separate_result_kind() -> None:
    """
    id: T-FIN-0008
    title: Simulation uses separate result kind
    purpose: Simulation uses separate result kind
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Simulation uses separate result kind
    risk: HZ-03
    capability: FIN
    """
    result = asyncio.run(
        WalkingSkeleton().run(
            financial_case=snapshot(simulation=True), finance_steps=STEPS, finance_at=AT.isoformat()
        )
    )
    assert "L02" not in result.financial_results
    assert result.simulations["L02"].evidence["record_kind"] == "SIMULATION"
    client = browser([snapshot(simulation=True)])
    identifier = create(client, "L02")
    assert create(client, "L02") == identifier
    evidence = client.get(f"{route('L02')}/{identifier}").json()["evidence"]
    assert evidence["record_kind"] == "SIMULATION" and evidence["label"] == "SIMULATED"
    assert sum(record.record_type == "financial_evaluation" for record in result.records) == 3


@pytest.mark.fast
def test_T_FIN_0009_tenant_isolation() -> None:
    """
    id: T-FIN-0009
    title: Tenant isolation
    purpose: Tenant isolation
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Tenant isolation
    risk: HZ-03
    capability: FIN
    """
    state = [snapshot()]
    client = browser(state)
    ident = create(client, "F07")
    outside = browser(state, "SYN-OTHER")
    assert outside.get(f"{route('F07')}/{ident}").status_code == 404
    assert (
        outside.post(
            route("F07"), json={"evaluation_time": AT.isoformat()}, headers={"Idempotency-Key": "a"}
        ).status_code
        == 404
    )


@pytest.mark.fast
def test_T_FIN_0010_server_owns_case_facts() -> None:
    """
    id: T-FIN-0010
    title: Server owns case facts
    purpose: Server owns case facts
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Server owns case facts
    risk: HZ-03
    capability: FIN
    """
    client = browser([snapshot()])
    bad = client.post(
        route("F03"),
        json={"evaluation_time": AT.isoformat(), "facts": {"free_days": 500}},
        headers={"Idempotency-Key": "a"},
    )
    assert bad.status_code == 422 and bad.json()["type"]


@pytest.mark.fast
def test_T_FIN_0011_idempotent_exact_replay() -> None:
    """
    id: T-FIN-0011
    title: Idempotent exact replay
    purpose: Idempotent exact replay
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Idempotent exact replay
    risk: HZ-03
    capability: FIN
    """
    client = browser([snapshot()])
    ident = create(client, "F07")
    assert create(client, "F07") == ident
    report = client.get(f"{route('F07')}/{ident}").json()
    assert (
        report["status"] == "ALLOW"
        and report["evidence"]["dossier_hash"]
        and "Dossier preview" in report["view"]
    )


@pytest.mark.fast
def test_T_FIN_0012_idempotency_rejects_different_request() -> None:
    """
    id: T-FIN-0012
    title: Idempotency rejects different request
    purpose: Idempotency rejects different request
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Idempotency rejects different request
    risk: HZ-03
    capability: FIN
    """
    client = browser([snapshot()])
    create(client, "L02")
    response = client.post(
        route("L02"),
        json={"evaluation_time": "2024-03-09T00:00Z"},
        headers={"Idempotency-Key": "synthetic-key"},
    )
    assert response.status_code == 409


@pytest.mark.fast
def test_T_FIN_0013_cli_accepts_all_financial_filters() -> None:
    """
    id: T-FIN-0013
    title: Cli accepts all financial filters
    purpose: Cli accepts all financial filters
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Cli accepts all financial filters
    risk: HZ-03
    capability: FIN
    """
    for cap in FINANCE_IDS:
        assert (
            main(
                [
                    "evaluate",
                    "--capability",
                    cap,
                    "--case-input",
                    f"data/scenarios/{cap.lower()}/{cap}-S01.json",
                ]
            )
            == 0
        )
    assert main(["evaluate", "--capability", "F03"]) == 2


@pytest.mark.fast
def test_T_FIN_0014_unsupported_case_scope_fails_closed() -> None:
    """
    id: T-FIN-0014
    title: Unsupported case scope fails closed
    purpose: Unsupported case scope fails closed
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Unsupported case scope fails closed
    risk: HZ-03
    capability: FIN
    """
    with pytest.raises(ValueError, match="authorized case"):
        asyncio.run(
            WalkingSkeleton().run(
                financial_case=replace(snapshot(), tenant_id="other"),
                finance_steps=STEPS,
                finance_at=AT.isoformat(),
            )
        )
    with pytest.raises(ValueError, match="requires an offset"):
        asyncio.run(
            WalkingSkeleton().run(
                financial_case=snapshot(), finance_steps=STEPS, finance_at="2024-03-10T00:00"
            )
        )
    case = replace(snapshot(), inputs={})
    assert run_finance(case, STEPS, AT) == {}


@pytest.mark.fast
def test_T_FIN_0015_local_financial_workflow_budget() -> None:
    """
    id: T-FIN-0015
    title: Local financial workflow budget
    purpose: Local financial workflow budget
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Local financial workflow budget
    risk: HZ-03
    capability: FIN
    """
    case = snapshot()
    before = perf_counter()
    for _ in range(10):
        assert run_finance(case, STEPS, AT)["F07"].status == "ALLOW"
    assert perf_counter() - before < 2


@pytest.mark.fast
def test_T_FIN_0016_mutated_input_scopes_remain_bound() -> None:
    """
    id: T-FIN-0016
    title: Mutated input scopes remain bound
    purpose: Mutated input scopes remain bound
    level: fast
    requirement: P16-T09, Part 6 section 6.11, DoD 8 and 9
    input: Versioned synthetic case and referenced packs
    expected: Mutated input scopes remain bound
    risk: HZ-03
    capability: FIN
    """
    case = snapshot()
    assert case.version("L02") == changed(case).version("L02")
    assert case.version("F07") != changed(case).version("F07")
    minimal = replace(case, inputs={"F07": case.inputs["F07"]})
    assert run_finance(minimal, STEPS, AT)["F07"].status == DecisionValue.ALLOW.name
    without_invoice = replace(case, inputs={"F07": {"clocks": []}})
    assert without_invoice.input_for("F07") == {"clocks": []}

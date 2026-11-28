"""Register landed-cost evidence and isolate proposed-plan evaluations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from html import escape

from pydantic import ConfigDict, TypeAdapter

from capabilities.l01.registration import AuditInput
from capabilities.l01.registration import register as register_audit
from capabilities.l02 import (
    Component,
    DutyPack,
    Estimate,
    Goods,
    Reason,
    Status,
    TaxRate,
    evaluate,
)
from capabilities.l02.variance import Variance, compare
from kernel.decision import FactEntry
from kernel.hashing import domain_hash
from kernel.lib.clock import aware
from kernel.lib.money import CurrencyTable, RateDatum
from kernel.lib.valuation import FxPack, ValuationRule

CAPABILITY_ID = "L02"


@dataclass(frozen=True, slots=True)
class DatedRate:
    day: date
    rate: RateDatum


@dataclass(frozen=True, slots=True)
class Exchange:
    version: str
    label: str
    currencies: dict[str, int]
    currency_source: str
    rates: tuple[DatedRate, ...] = ()

    def pack(self) -> FxPack:
        rates = {
            (row.day, row.rate.source_currency, row.rate.target_currency): row.rate
            for row in self.rates
        }
        if len(rates) != len(self.rates) or not self.version:
            raise ValueError("FX pack needs a version and unique dated rates")
        return FxPack(
            self.version,
            CurrencyTable(self.currencies, self.currency_source),
            rates,
            self.label,
        )


@dataclass(frozen=True, slots=True)
class Plan:
    id: str
    leg_costs: tuple[Component, ...]


@dataclass(frozen=True, slots=True)
class EstimateInput:
    __pydantic_config__ = ConfigDict(extra="forbid")

    goods: tuple[Goods, ...]
    components: tuple[Component, ...]
    duty_pack: DutyPack | None
    taxes: tuple[TaxRate, ...]
    exchange: Exchange
    valuation_rules: dict[str, ValuationRule]
    currency: str
    facts: tuple[FactEntry, ...] = ()
    required_components: tuple[str, ...] = ()
    audited_invoice: AuditInput | None = None
    plan: Plan | None = None
    synthetic: bool = False
    document_note: str | None = None
    classification_candidates: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class LandedCostReport:
    estimate: Estimate
    variance: Variance | None = None
    simulated: bool = False

    @property
    def status(self) -> Status:
        return self.estimate.status

    @property
    def reason_codes(self) -> tuple[Reason, ...]:
        return self.estimate.reason_codes


INPUT = TypeAdapter(EstimateInput)
OUTPUT = TypeAdapter(LandedCostReport)
_TRANSPORT = frozenset({"FREIGHT", "TRANSPORT", "LOCAL_TRANSPORT"})


def register(data: EstimateInput, at: datetime) -> tuple[LandedCostReport, dict[str, object]]:
    """Produce replayable evidence for either a recorded estimate or a proposal."""
    at = aware(at)
    day = at.date()
    fx = data.exchange.pack()
    components = data.components
    plan = data.plan
    if plan is not None:
        if (
            not plan.id
            or not plan.leg_costs
            or any(row.code not in _TRANSPORT for row in plan.leg_costs)
        ):
            raise ValueError("the proposed plan requires recorded transport-leg costs")
        components = (*[row for row in components if row.code not in _TRANSPORT], *plan.leg_costs)

    estimate = evaluate(
        data.goods,
        components=components,
        rates=data.duty_pack,
        taxes=data.taxes,
        fx=fx,
        valuation_rules=data.valuation_rules,
        currency=data.currency,
        at=day,
        facts=data.facts,
        required_components=frozenset(data.required_components),
        synthetic=data.synthetic,
    )
    variance = None
    audit_reference = None
    if data.audited_invoice is not None and plan is None and estimate.components:
        audit, record = register_audit(data.audited_invoice, at)
        variance = compare(estimate, audit, fx, day)
        audit_reference = record["output_hash"]
        estimate = replace(estimate, reason_codes=(*estimate.reason_codes, Reason.VARIANCE))
    result = LandedCostReport(estimate, variance, plan is not None)
    payload = INPUT.dump_python(data, mode="json")
    output = OUTPUT.dump_python(result, mode="json")
    configuration = {
        key: payload[key]
        for key in ("duty_pack", "taxes", "exchange", "valuation_rules", "currency")
    }
    evidence: dict[str, object] = {
        "capability_id": CAPABILITY_ID,
        "record_kind": "SIMULATION" if plan else "ESTIMATE",
        "evaluation_time": at.isoformat(),
        "input_hash": domain_hash("ctc/payload/v1", payload),
        "output_hash": domain_hash("ctc/payload/v1", output),
        "configuration_hash": domain_hash("ctc/payload/v1", configuration),
        "trace_hash": domain_hash("ctc/payload/v1", [row.trace for row in estimate.components]),
        "invoice_audit_hash": audit_reference,
    }
    if plan is not None:
        evidence["simulation_id"] = domain_hash("ctc/payload/v1", [plan.id, evidence["input_hash"]])
        evidence["label"] = "SIMULATED"
        evidence["plan_id"] = plan.id
    return result, evidence


def render_estimate(report: LandedCostReport) -> str:
    """Show the component origins, ranges and gaps in the case estimate."""
    estimate = report.estimate
    rows = []
    for row in estimate.components:
        component = row.component
        details = escape(str(row.trace))
        rows.append(
            f"<tr><th scope='row'>{escape(component.code)}</th>"
            f"<td>{component.interval.base} {escape(component.currency)}</td>"
            f"<td>{component.kind}</td><td>{escape(row.label)}</td>"
            f"<td>{escape(component.source_id)}</td><td>"
            f"<details><summary>Calculation</summary>{details}</details></td></tr>"
        )
    total = ""
    if estimate.total is not None:
        values = estimate.total
        total = (
            f"<p>Estimated total {values.base} {escape(estimate.currency)}. "
            f"Range {values.minimum} to {values.maximum}.</p>"
        )
    gaps = "".join(f"<li>{escape(gap)}</li>" for gap in estimate.missing)
    notes = "".join(f"<li>{escape(note)}</li>" for note in estimate.notes)
    scenario = "<p>SIMULATED</p>" if report.simulated else ""
    variance = ""
    if report.variance is not None:
        observations = "".join(
            f"<li>{escape(row.charge_kind)}: actual {row.actual}, estimate {row.estimated}, "
            f"difference {row.difference}</li>"
            for row in report.variance.components
        )
        unestimated = ", ".join(escape(name) for name in report.variance.unestimated)
        variance = (
            "<h3>Variance observations</h3>"
            f"<ul>{observations}</ul><p>Unestimated charges {unestimated}</p>"
        )
    return (
        '<section id="l02" aria-label="Landed cost estimate">'
        f"{scenario}{total}<p>{escape(', '.join(estimate.reason_codes))}</p>"
        f"<table><thead><tr><th>Component</th><th>Amount</th><th>Origin</th>"
        f"<th>Label</th><th>Source</th><th>Trace</th></tr></thead><tbody>"
        f"{''.join(rows)}</tbody></table><h3>Missing components</h3><ul>{gaps}</ul>"
        f"<ul>{notes}</ul>{variance}</section>"
    )

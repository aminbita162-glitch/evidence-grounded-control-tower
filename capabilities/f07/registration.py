"""Expose the charge audit, evidence and printable export for a case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape

from pydantic import ConfigDict, TypeAdapter

from capabilities.f03.registration import ClockInput
from capabilities.f03.registration import register as register_clocks
from capabilities.f07 import Audit, Reason, TariffClock, evaluate
from capabilities.f07.dossier import Dossier, export
from capabilities.l01.registration import AuditInput
from capabilities.l01.registration import register as register_l01
from kernel.hashing import domain_hash
from kernel.lib.clock import aware
from kernel.lib.money import CurrencyTable
from kernel.types.decision import DecisionValue

CAPABILITY_ID = "F07"


@dataclass(frozen=True, slots=True)
class ChargeInput:
    __pydantic_config__ = ConfigDict(extra="forbid")

    invoice: AuditInput
    clocks: tuple[TariffClock, ...]
    canonical_containers: frozenset[str]


@dataclass(frozen=True, slots=True)
class ChargeReport:
    audit: Audit
    dossier: Dossier

    @property
    def outcome(self) -> DecisionValue:
        return self.audit.outcome

    @property
    def reason_codes(self) -> tuple[Reason, ...]:
        return self.audit.reason_codes


INPUT = TypeAdapter(ChargeInput)
OUTPUT = TypeAdapter(ChargeReport)


def register(data: ChargeInput, at: datetime) -> tuple[ChargeReport, dict[str, object]]:
    """Commit the upstream audit, clock evidence and resulting discrepancy export."""
    at = aware(at)
    supplied = data.invoice
    invoice_audit, invoice_record = register_l01(supplied, at)
    _, clock_record = register_clocks(
        ClockInput(
            tuple(
                row.clock for row in data.clocks if row.clock.terms and row.clock.terms.valid_at(at)
            ),
            supplied.currencies,
            supplied.currency_source,
            data.canonical_containers,
            supplied.synthetic,
        ),
        at,
    )
    audit = evaluate(
        supplied.invoice,
        invoice_audit,
        data.clocks,
        canonical_containers=data.canonical_containers,
        currencies=CurrencyTable(supplied.currencies, supplied.currency_source),
        at=at,
        synthetic=supplied.synthetic,
    )
    result = ChargeReport(audit, export(audit))
    inputs = INPUT.dump_python(data, mode="json")
    inputs["canonical_containers"] = sorted(data.canonical_containers)
    inputs["invoice"]["invoice"]["lines"].sort(key=lambda line: line["id"])
    inputs["clocks"].sort(
        key=lambda row: (
            row["basis_id"],
            row["clock"]["container"],
            (row["clock"]["terms"] or {}).get("valid_from", ""),
        )
    )
    for row in inputs["clocks"]:
        calendar = row["clock"]["calendar"]
        if calendar is not None:
            calendar["weekend"].sort()
            calendar["holidays"].sort()
    configuration_hash = domain_hash(
        "ctc/payload/v1",
        [
            invoice_record["configuration_hash"],
            clock_record["configuration_hash"],
            [row["clock"]["terms"] for row in inputs["clocks"]],
        ],
    )
    return result, {
        "capability_id": CAPABILITY_ID,
        "evaluation_time": at.isoformat(),
        "input_hash": domain_hash("ctc/payload/v1", inputs),
        "output_hash": domain_hash("ctc/payload/v1", OUTPUT.dump_python(result, mode="json")),
        "invoice_audit_hash": invoice_record["output_hash"],
        "f03_hash": clock_record["output_hash"],
        "configuration_hash": configuration_hash,
        "tariffs": [
            (row["basis_id"], row["clock"]["terms"]["version"])
            for row in inputs["clocks"]
            if row["clock"]["terms"] is not None
        ],
        "dossier_hash": result.dossier.digest,
    }


def render_audit(report: ChargeReport) -> str:
    """Show classifications and the printable dossier preview."""
    rows = []
    for line in report.audit.lines:
        rows.append(
            f"<tr><th scope='row'>{escape(line.line_id)}</th>"
            f"<td>{escape(line.charge_kind)}</td><td>{line.classification}</td>"
            f"<td>{line.billed} {escape(line.currency)}</td><td>{line.expected}</td>"
            f"<td>{line.difference}</td></tr>"
        )
    return (
        '<section id="f07" aria-label="Time-charge audit"><table><thead><tr>'
        "<th>Line</th><th>Charge</th><th>Root cause</th><th>Billed</th>"
        f"<th>Expected</th><th>Difference</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
        "<h3>Dossier preview</h3>"
        f"<p>Evidence strength {report.dossier.strength}. Dossier hash {report.dossier.digest}.</p>"
        "<p>Export formats JSON and printable HTML.</p>"
        f"<pre>{escape(report.dossier.json)}</pre></section>"
    )

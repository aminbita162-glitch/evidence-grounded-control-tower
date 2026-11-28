"""Publish the freight invoice result and commitments for its consumers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html import escape

from pydantic import ConfigDict, TypeAdapter

from capabilities.l01 import Basis, Invoice, InvoiceAudit, Policy, Quantity, evaluate
from kernel.hashing import domain_hash
from kernel.lib.clock import aware
from kernel.lib.money import CurrencyTable
from kernel.lib.taxonomy import Taxonomy

CAPABILITY_ID = "L01"


@dataclass(frozen=True, slots=True)
class AuditInput:
    __pydantic_config__ = ConfigDict(extra="forbid")

    invoice: Invoice
    taxonomy: Taxonomy | None
    bases: tuple[Basis, ...]
    currencies: dict[str, int]
    currency_source: str
    previous: tuple[Invoice, ...] = ()
    verified_quantities: dict[str, Quantity] | None = None
    policy: Policy = Policy()
    synthetic: bool = False
    basis_available: bool = True
    document_note: str | None = None


INPUT = TypeAdapter(AuditInput)
OUTPUT = TypeAdapter(InvoiceAudit)


def register(data: AuditInput, at: datetime) -> tuple[InvoiceAudit, dict[str, object]]:
    """Commit the invoice, basis configuration, affected lines and their trace hashes."""
    at = aware(at)
    result = evaluate(
        data.invoice,
        at=at.date(),
        taxonomy=data.taxonomy,
        bases=data.bases,
        currencies=CurrencyTable(data.currencies, data.currency_source),
        previous=data.previous,
        verified_quantities=data.verified_quantities,
        policy=data.policy,
        synthetic=data.synthetic,
        basis_available=data.basis_available,
    )
    payload = INPUT.dump_python(data, mode="json")
    payload["invoice"]["lines"].sort(key=lambda line: line["id"])
    payload["bases"].sort(key=lambda basis: (basis["id"], basis["version"]))
    configuration = {
        key: payload[key]
        for key in ("taxonomy", "bases", "currencies", "currency_source", "policy")
    }
    output = OUTPUT.dump_python(result, mode="json")
    return result, {
        "capability_id": CAPABILITY_ID,
        "evaluation_time": at.isoformat(),
        "input_hash": domain_hash("ctc/payload/v1", payload),
        "configuration_hash": domain_hash("ctc/payload/v1", configuration),
        "output_hash": domain_hash("ctc/payload/v1", output),
        "match_hash": domain_hash("ctc/payload/v1", output["matches"]),
        "lines": [
            {
                "line_id": row.line.id,
                "citation": row.line.citation,
                "trace_hash": domain_hash("ctc/payload/v1", row.trace) if row.trace else None,
            }
            for row in result.lines
        ],
    }


def render_audit(result: InvoiceAudit) -> str:
    """Show the selected basis, comparison, and recorded evidence for each line."""
    rows = []
    for item in result.lines:
        basis = escape(item.basis.id) if item.basis else "Unavailable"
        expected = str(item.expected) if item.expected is not None else "Not evaluated"
        trace = ""
        if item.trace is not None:
            trace = f"<details><summary>Calculation</summary>{escape(str(item.trace))}</details>"
        rows.append(
            f"<tr><th scope='row'>{escape(item.line.id)}</th><td>{basis}</td>"
            f"<td>{item.reason}</td><td>{item.billed} {escape(item.line.currency)}</td>"
            f"<td>{expected}</td><td>{escape(item.line.citation)}{trace}</td></tr>"
        )
    needs = "".join(f"<li>{escape(str(item['name']))}</li>" for item in result.unblock)
    totals = "".join(
        f"<li>{escape(currency)} billed {total.billed}, "
        f"expected {total.expected}, difference {total.difference}</li>"
        for currency, total in result.totals.items()
    )
    header = (
        ""
        if result.header is None
        else (f"<p>Header total {result.header.stated} · lines {result.header.line_sum}</p>")
    )
    return (
        '<section id="l01" aria-label="Freight invoice audit"><table>'
        "<thead><tr><th>Line</th><th>Basis</th><th>Result</th><th>Billed</th>"
        "<th>Expected</th><th>Evidence</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>{header}<h3>Currency totals</h3><ul>{totals}</ul>"
        f"<h3>Outstanding evidence</h3><ul>{needs}</ul></section>"
    )

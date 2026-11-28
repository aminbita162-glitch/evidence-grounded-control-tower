"""Create deterministic JSON and printable evidence for time-charge discrepancies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape

from pydantic import TypeAdapter

from capabilities.f07 import Audit
from kernel.hashing import domain_hash
from kernel.types.decision import DecisionValue
from kernel.types.label import is_allow_eligible

_AUDIT = TypeAdapter(Audit)


@dataclass(frozen=True, slots=True)
class Dossier:
    json: str
    html: str
    digest: str
    strength: str


def export(audit: Audit) -> Dossier:
    """Bind both artifact representations to the same set of cited discrepancies."""
    strength = "DERIVED_OR_STRONGER" if is_allow_eligible(audit.label) else "INDICATIVE"
    report = _AUDIT.dump_python(audit, mode="json")
    rows = [
        result
        for result, row in zip(report["lines"], audit.lines, strict=True)
        if row.outcome in (DecisionValue.HOLD, DecisionValue.ESCALATE)
    ]
    payload = {
        "invoice_reference": audit.invoice_number,
        "issuer": audit.issuer,
        "invoice_citation": audit.invoice_citation,
        "evidence_strength": strength,
        "label": audit.label,
        "discrepancies": rows,
    }
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sections = []
    for row in rows:
        timeline = "".join(
            f"<li>{escape(str(event['kind']))} {escape(str(event['instant']))} "
            f"({escape(str(event['source_id']))})</li>"
            for event in row["events"]
        )
        formulas = "".join(
            f"<li>{escape(str(step['terms_id']))} {escape(str(step['version']))} · "
            f"{escape(str(step['valid_from']))} to {escape(str(step['valid_until']))} · "
            f"{escape(str(step['label']))} · {step['days']} days · {step['amount']}</li>"
            for step in row["steps"]
        )
        sections.append(
            f"<article><h2>Line {escape(str(row['line_id']))}</h2>"
            f"<p>{escape(str(row['classification']))} · {escape(str(row['citation']))}</p>"
            f"<p>Billed {row['billed']} · expected {row['expected']} · "
            f"difference {row['difference']} {escape(str(row['currency']))}.</p>"
            f"<h3>Event timeline</h3><ol>{timeline}</ol>"
            f"<h3>Tariff calculations</h3><ol>{formulas}</ol></article>"
        )
    html = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>Time-charge discrepancy dossier</title>"
        "<body><h1>Time-charge discrepancy dossier</h1>"
        f"<p>Invoice {escape(audit.invoice_number)} · {escape(audit.issuer)}</p>"
        f"<p>Evidence strength {strength} ({escape(audit.label)}).</p>"
        f"{''.join(sections)}</body></html>"
    )
    return Dossier(data, html, domain_hash("ctc/payload/v1", [data, html]), strength)

"""Generate Phase 15 capability cards, calibration diagnostics and API contract."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from api.app import create_app
from capabilities.f02.synthetic import create_judge as classification_judge
from capabilities.k05.synthetic import create_judge as valuation_judge
from tools.trace import build_matrix, save_matrix

_ROOT = Path(__file__).resolve().parents[2]
_CAPABILITIES = {
    "K05": ("Valuation Anomaly", "SRC-SYNTHETIC-K05", 15),
    "F02": ("Classification Judge", "SRC-SYNTHETIC-F02", 12),
}
_EVALUATIONS = "/api/v1/cases/{case_id}/capabilities/{capability_id}/evaluations"


def _write_json(relative: str, value: object) -> None:
    (_ROOT / relative).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def generate() -> None:
    """Write deterministic evidence from the versioned case corpus and active fixture packs."""
    matrix = build_matrix(_ROOT)
    if matrix.broken:
        raise ValueError("Phase 15 traceability links are broken")
    directive = (_ROOT / "directive.txt").read_text(encoding="utf-8")
    for capability, (title, source, count) in _CAPABILITIES.items():
        inputs = sorted((_ROOT / "data" / "scenarios" / capability.lower()).glob("*.json"))
        if len(inputs) != count:
            raise ValueError(f"{capability} scenario count differs from the directive")
        for path in inputs:
            record = json.loads(path.read_text(encoding="utf-8"))
            scope = f"5.{capability} T11 {record['id']}"
            if record["basis"] != scope or f"| {record['id']} |" not in directive:
                raise ValueError(f"{path.name} has an unresolved basis")
            if (
                record["id"] == "F02-S11"
                and record.get("report_label") != "implementation-correctness"
            ):
                raise ValueError("F02-S11 requires the implementation-correctness label")

        reason = f"T-{capability}-0101 through T-{capability}-0115"
        terminals = [
            ("1", "Capability specification", f"Directive Part 5 {capability}, H and T1–T14"),
            ("2", "Schemas, packs and provenance", f"`{source}`, contract, data and labels gates"),
            ("3", "Deterministic validity checks", f"{capability}-S01, T-VAL-0014"),
            ("4", "Closed reason codes", reason),
            ("5", "Protective outcomes", reason),
            ("6", "Golden scenarios", f"{capability}-S01 through {capability}-S{count:02}"),
            ("7", "Properties and independent comparisons", f"T-{capability}-0201 through 0230"),
            ("8", "Evidence and replay", f"T-{capability}-0401, T-VAL-0008 and T-VAL-0009"),
            ("9a", "API, CLI and view", f"T-{capability}-0501 through 0512, API contract"),
            ("9b", "Accessibility", "PENDING-P27"),
            ("10", "Deterministic budget", "T-VAL-0015"),
            (
                "11",
                "Adversarial and tenant access",
                f"T-{capability}-0301 through 0320, T-VAL-0013",
            ),
            ("12", "Coverage, mutation and traceability", "Phase 15 verification report"),
        ]
        rows = "\n".join(f"| {n} | {item} | {proof} |" for n, item, proof in terminals)
        (_ROOT / "docs" / "capabilities" / f"{capability}.md").write_text(
            f"# {title}\n\nCapability {capability}, version 1.0.0.\n\n"
            f"| Item | Requirement | Evidence |\n| --- | --- | --- |\n{rows}\n",
            encoding="utf-8",
        )

    value = valuation_judge().calibration
    classification = classification_judge().calibration["en"]
    diagnostics = {
        "label": "SYNTHETIC",
        "K05": {
            "artifact_id": value.artifact_id,
            "reference_pack_hash": value.pack_hash,
            "source_id": value.source_id,
            "held_out": asdict(value.held_out),
            "shifted": asdict(value.shifted),
        },
        "F02": asdict(classification),
    }
    _write_json("docs/capabilities/P15-calibration.json", diagnostics)
    paths = create_app().openapi()["paths"]
    _write_json(
        "schemas/api/phase15-openapi.json",
        {route: paths[route] for route in (_EVALUATIONS, f"{_EVALUATIONS}/{{evaluation_id}}")},
    )
    save_matrix(matrix, _ROOT / "docs/phase-reports/P15-trace.json")


if __name__ == "__main__":
    generate()

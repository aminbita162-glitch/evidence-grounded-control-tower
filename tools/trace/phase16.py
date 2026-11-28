"""Generate evidence links, capability cards and contracts for Phase 16."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from api.app import create_app
from api.routes.capability import evaluate_finance_step
from tools.trace import build_matrix, save_matrix

ROOT = Path(__file__).resolve().parents[2]
CAPABILITIES = {
    "F03": ("Free-Time Clock & Cost Shield", 12, 11, 35, 20),
    "L01": ("Freight Invoice Audit", 18, 20, 35, 25),
    "L02": ("Landed Cost Estimator", 17, 11, 35, 20),
    "F07": ("Charge Control", 11, 13, 25, 20),
}
EVALUATIONS = "/api/v1/cases/{case_id}/capabilities/{capability_id}/evaluations"


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def scenarios(root: Path, contract: str, *, verify: bool = False) -> tuple[list[str], list[str]]:
    """Validate each synthetic scenario's declared origin, basis and test mapping."""
    doc = (root / "directive.txt").read_text()
    cap = contract.lower()
    expected = CAPABILITIES[contract][1]
    paths = sorted((root / "data/scenarios" / cap).glob("*.json"))
    if len(paths) != expected:
        raise ValueError(f"{contract} requires {expected} recorded scenarios")
    names = []
    tests = []
    for n, path in enumerate(paths, 1):
        record = json.loads(path.read_text(encoding="utf-8"))
        sid = f"{contract}-S{n:02}"
        tid = f"T-{contract}-{n:04}"
        if (
            path.stem != sid
            or record["id"] != sid
            or record["test_id"] != tid
            or record["basis"] != f"5.{contract} T11 {sid}"
            or f"| {sid} |" not in doc
            or record["label"] != "SYNTHETIC"
        ):
            raise ValueError(f"unresolved scenario evidence for {path.name}")
        if verify:
            payload = dict(record["inputs"])
            at = datetime.fromisoformat(payload.pop("evaluation_time"))
            actual = evaluate_finance_step(contract, payload, at)
            if actual.status != record["outcome"] or set(actual.reasons) != set(
                record["reason_codes"]
            ):
                raise ValueError(f"scenario differs from its recorded result: {sid}")
        names.append(sid)
        tests.append(tid)
    return names, tests


def generate() -> None:
    """Render validation artifacts from the registered evaluator and scenario corpus."""
    for cap, (title, count, reasons, properties, adversarial) in CAPABILITIES.items():
        names, tests = scenarios(ROOT, cap, verify=True)
        suffix = cap.lower()
        entries = [
            ("1", "Capability specification", f"Directive Part 5 {cap}, H and T1–T14"),
            ("2", "Schemas and recorded inputs", f"SRC-SYNTHETIC-{cap}, data and contract gates"),
            ("3", "Deterministic logic", f"T-{cap}-0201 through 02{properties:02}"),
            ("4", "Closed reasons", f"T-{cap}-0101 through 01{reasons:02}"),
            ("5", "Protective outcomes", f"T-{cap}-0101 through 01{reasons:02}"),
            (
                "6",
                "Synthetic scenario outcomes",
                f"{names[0]} through {names[-1]}, {tests[0]} through {tests[-1]}",
            ),
            ("7", "Properties and differential checks", f"T-{cap}-0201 through 02{properties:02}"),
            ("8", "Replay and evidence commitments", f"T-{cap}-0401 through 0410, T-FIN-0007"),
            (
                "9a",
                "Case API, CLI and view",
                f"T-{cap}-0501 through 0512, T-FIN-0011 and T-FIN-0013",
            ),
            ("9b", "Accessibility", "PENDING-P27"),
            ("10", "Runtime budget", "T-FIN-0015, perf gate"),
            (
                "11",
                "Adversarial corpus and tenant isolation",
                f"T-{cap}-0301 through 03{adversarial:02}, T-FIN-0009",
            ),
            ("12", "Mutation, coverage and trace", "Phase 16 verification report"),
        ]
        reason_codes = json.loads((ROOT / f"capabilities/{suffix}/rules/rules.json").read_text())
        fixture = ROOT / f"data/scenarios/{suffix}/{cap}-S01.json"
        example = json.loads(fixture.read_text())
        if len(names) != count:
            raise ValueError("scenario manifest does not match the declared count")
        body = "\n".join(f"| {n} | {item} | {proof} |" for n, item, proof in entries)
        closed = "\n".join(f"- `{code}`" for code in reason_codes)
        (ROOT / f"docs/capabilities/{cap}.md").write_text(
            f"# {title}\n\nCapability {cap}, version 1.0.0.\n\n"
            f"Input and output schemas are registered in contracts.lock. The local case example "
            f"{example['id']} returns {example['outcome']} for the recorded SYNTHETIC input.\n\n"
            f"| Item | Requirement | Evidence |\n| --- | --- | --- |\n{body}\n\n"
            f"## Reason codes\n\n{closed}\n"
        )

    matrix = build_matrix(ROOT)
    if matrix.broken:
        raise ValueError("Phase 16 traceability links are broken")
    save_matrix(matrix, ROOT / "docs/phase-reports/P16-trace.json")

    paths = create_app().openapi()["paths"]
    fragment = {path: paths[path] for path in (EVALUATIONS, f"{EVALUATIONS}/{{evaluation_id}}")}
    schemas = {}
    examples = {}
    for cap in CAPABILITIES:
        base = ROOT / "capabilities" / cap.lower()
        schemas[cap] = {
            kind: json.loads((base / f"schemas/{kind}.json").read_text())
            for kind in ("input", "output")
        }
        sample = ROOT / f"data/scenarios/{cap.lower()}/{cap}-S01.json"
        examples[cap] = json.loads(sample.read_text())
    api_contract = ROOT / "schemas/api/phase16-openapi.json"
    _write(
        api_contract, {"paths": fragment, "x-capability-contracts": schemas, "x-examples": examples}
    )

    lock_path = ROOT / "contracts.lock"
    existing = json.loads(lock_path.read_text())
    contracts = {entry["path"]: entry for entry in existing["contracts"]}
    added = [api_contract]
    for cap in CAPABILITIES:
        added.extend(ROOT.glob(f"capabilities/{cap.lower()}/schemas/*.json"))
    for path in added:
        relative = str(path.relative_to(ROOT))
        contracts[relative] = {
            "path": relative,
            "hash": hashlib.sha256(path.read_bytes()).hexdigest(),
            "type": "schema",
        }
    existing["contracts"] = [contracts[key] for key in sorted(contracts)]
    lock_path.write_text(json.dumps(existing, indent=2) + "\n")


if __name__ == "__main__":
    generate()

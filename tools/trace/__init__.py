"""Traceability matrix tool (P09-T05).

Builds the chain from test headers, scenario files and the risk registers;
includes the threat-to-test matrix and reports every broken link.  The
matrix is attached to the phase report.

A broken link is:
  - a scenario without a test (test_id empty or missing),
  - a test without a scenario or control,
  - a risk without a control,
  - a control without a test.

Spec: Part 6 §6.11; P09-T05.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from tools.gate.gates.index import scan_directory
from tools.trace.shared import REQUIREMENTS, CatalogueEntry, read_catalogue

__all__ = [
    "BrokenLink",
    "TraceMatrix",
    "build_matrix",
    "check_matrix",
    "generate_report",
    "save_matrix",
    "matrix_hash",
]

#: Regex for test IDs in headers.
_TEST_ID_RE = re.compile(r"T-(?:[A-Z]+|[FKL][0-9]{2})-[A-Z0-9][A-Z0-9-]*")

#: Regex for header field lines in docstrings.
_FIELD_RE = re.compile(r"^\s*(id|requirement|capability|risk)\s*:\s*(.+)$")

#: Regex for control IDs.
_CONTROL_RE = re.compile(r"CTL-[A-Z]+-\d+")


@dataclass(frozen=True)
class BrokenLink:
    """A broken traceability link.

    Attributes:
        kind: The kind of broken link (scenario_without_test, test_without_scenario,
            test_without_control, risk_without_control, control_without_test).
        source: The source identifier.
        detail: Human-readable detail.
    """

    kind: str
    source: str
    detail: str


@dataclass
class TraceMatrix:
    """The traceability matrix.

    Attributes:
        tests: Set of test IDs found in test files.
        scenarios: Dict of scenario id to test_id.
        risks: Dict of risk id to list of control ids.
        controls: Set of control IDs referenced by risks.
        broken: List of broken links.
    """

    tests: set[str] = field(default_factory=set)
    scenarios: dict[str, str] = field(default_factory=dict)
    risks: dict[str, list[str]] = field(default_factory=dict)
    controls: set[str] = field(default_factory=set)
    broken: list[BrokenLink] = field(default_factory=list)
    shared_catalogue: tuple[CatalogueEntry, ...] = ()
    module_paths: set[str] = field(default_factory=set)
    module_proofs: set[tuple[str, str]] = field(default_factory=set)
    check_shared: bool = False


def _scan_test_ids(test_house: Path) -> set[str]:
    """Scan all test files for test IDs in headers."""
    ids: set[str] = set()
    if not test_house.exists():
        return ids
    for py_file in test_house.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="replace")
        for match in _TEST_ID_RE.finditer(text):
            candidate = match.group()
            if candidate.startswith(("T-BCH-", "T-")):
                ids.add(candidate)
    return ids


def _scan_scenarios(scenarios_dir: Path) -> dict[str, str]:
    """Scan scenario files for scenario id to test_id mapping."""
    mapping: dict[str, str] = {}
    if not scenarios_dir.exists():
        return mapping
    files = [
        *scenarios_dir.glob("*.json"),
        *scenarios_dir.glob("*/cases.json"),
        *scenarios_dir.glob("*/[FKL][0-9][0-9]-S*.json"),
    ]
    for json_file in sorted(files):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        for record in records:
            if not isinstance(record, dict):
                continue
            sid = record.get("id", "")
            if sid:
                mapping[sid] = record.get("test_id", "")
    return mapping


def _scan_risks(registers_dir: Path) -> tuple[dict[str, list[str]], set[str]]:
    """Scan risk register YAML files for risks and controls.

    Returns:
        (risks: {risk_id: [control_ids]}, controls: {control_ids})
    """
    risks: dict[str, list[str]] = {}
    controls: set[str] = set()
    if not registers_dir.exists():
        return risks, controls
    for yaml_file in registers_dir.glob("*.yaml"):
        data = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        if not isinstance(data, Mapping):
            continue
        records = data.get("records", [])
        if not isinstance(records, list):
            continue
        for record in records:
            if not isinstance(record, Mapping):
                continue
            rid = str(record.get("id", ""))
            ctrl_list = record.get("controls", [])
            if isinstance(ctrl_list, list):
                ctrl_ids = [str(c) for c in ctrl_list]
            else:
                ctrl_ids = [str(ctrl_list)] if ctrl_list else []
            if rid:
                risks[rid] = ctrl_ids
            for c in ctrl_ids:
                controls.add(c)
    return risks, controls


def build_matrix(repo_root: Path) -> TraceMatrix:
    """Build the traceability matrix from the repository.

    Args:
        repo_root: The repository root path.

    Returns:
        A :class:`TraceMatrix` with broken links checked.
    """
    matrix = TraceMatrix()
    matrix.tests = _scan_test_ids(repo_root / "test-house")
    matrix.scenarios = _scan_scenarios(repo_root / "data" / "scenarios")
    matrix.risks, matrix.controls = _scan_risks(repo_root / "risk-management" / "registers")
    directive = repo_root / "directive.txt"
    if directive.is_file():
        matrix.shared_catalogue = read_catalogue(directive.read_text(encoding="utf-8"))
    matrix.check_shared = (repo_root / "docs/ledger/P13.md").is_file()
    if matrix.check_shared:
        matrix.module_paths = {
            requirement.module
            for requirement in REQUIREMENTS
            if (repo_root / "kernel/lib" / requirement.module / "__init__.py").is_file()
        }
        differential = repo_root / "test-house/lib/differential"
        if differential.is_dir():
            entries = scan_directory(differential)
            matrix.module_proofs = {
                (entry.fields["id"], entry.fields["requirement"])
                for entry in entries
                if {"id", "requirement"} <= entry.fields.keys()
            }
    matrix.broken = check_matrix(matrix)
    if (repo_root / "capabilities/f07/manifest.json").is_file():
        from tools.trace.phase16 import CAPABILITIES, scenarios

        for capability in CAPABILITIES:
            try:
                scenarios(repo_root, capability)
            except (OSError, ValueError, KeyError) as error:
                matrix.broken.append(
                    BrokenLink("unresolved_scenario_basis", capability, str(error))
                )
    return matrix


def check_matrix(matrix: TraceMatrix) -> list[BrokenLink]:
    """Check the matrix for broken links.

    A broken link is a structural gap that can be detected without seeding:
      - scenario_without_test: a scenario with an empty test_id,
      - test_id_not_found: a scenario references a test that does not exist,
      - risk_without_control: a risk with no controls.

    The ``test_without_scenario`` and ``control_without_test`` checks are
    advisory — not every test needs a scenario and not every control is
    tested yet (controls are PLANNED across many phases).  These are only
    flagged in seeded fixtures, not on the real repo.

    Args:
        matrix: The traceability matrix (without broken links).

    Returns:
        A list of :class:`BrokenLink` entries.
    """
    broken: list[BrokenLink] = []

    # A scenario without a test.
    for sid, tid in matrix.scenarios.items():
        if not tid:
            broken.append(
                BrokenLink(
                    kind="scenario_without_test",
                    source=sid,
                    detail=f"scenario {sid} has no test_id",
                )
            )
        elif tid not in matrix.tests:
            broken.append(
                BrokenLink(
                    kind="test_id_not_found",
                    source=sid,
                    detail=f"scenario {sid} references unknown test {tid}",
                )
            )

    # A risk without a control.
    for rid, ctrls in matrix.risks.items():
        if not ctrls:
            broken.append(
                BrokenLink(
                    kind="risk_without_control",
                    source=rid,
                    detail=f"risk {rid} has no controls",
                )
            )

    if matrix.check_shared:
        broken.extend(_shared_links(matrix))
    return broken


def _shared_links(matrix: TraceMatrix) -> list[BrokenLink]:
    from_table = {entry.name for entry in matrix.shared_catalogue if entry.phase == "P13"}
    from_requirements = {requirement.catalogue for requirement in REQUIREMENTS}
    broken = [
        BrokenLink("unmapped_shared_row", name, "shared-module catalogue and requirements differ")
        for name in sorted(from_table ^ from_requirements)
    ]
    for requirement in REQUIREMENTS:
        if requirement.module not in matrix.module_paths:
            broken.append(
                BrokenLink("missing_shared_module", requirement.requirement, requirement.module)
            )
        if (requirement.test_id, requirement.requirement) not in matrix.module_proofs:
            broken.append(
                BrokenLink("missing_shared_proof", requirement.requirement, requirement.test_id)
            )
    return broken


def generate_report(matrix: TraceMatrix) -> str:
    """Generate a JSON report of the traceability matrix.

    Args:
        matrix: The traceability matrix.

    Returns:
        A JSON string.
    """
    report: dict[str, object] = {
        "tests": sorted(matrix.tests),
        "scenarios": dict(sorted(matrix.scenarios.items())),
        "risks": dict(sorted(matrix.risks.items())),
        "controls": sorted(matrix.controls),
        "broken_links": [
            {
                "kind": b.kind,
                "source": b.source,
                "detail": b.detail,
            }
            for b in matrix.broken
        ],
        "broken_count": len(matrix.broken),
    }
    if matrix.shared_catalogue:
        report["shared_catalogue"] = [asdict(row) for row in matrix.shared_catalogue]
    if matrix.check_shared:
        report["module_requirements"] = [asdict(requirement) for requirement in REQUIREMENTS]
    return json.dumps(report, sort_keys=True, indent=2, separators=(",", ": "))


def save_matrix(matrix: TraceMatrix, path: Path) -> None:
    """Save the traceability matrix to a file.

    Args:
        matrix: The traceability matrix.
        path: The output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generate_report(matrix) + "\n", encoding="utf-8")


def matrix_hash(matrix: TraceMatrix) -> str:
    """Compute a deterministic hash of the traceability matrix.

    Args:
        matrix: The traceability matrix.

    Returns:
        A SHA-256 hex string.
    """
    report = generate_report(matrix)
    return hashlib.sha256(report.encode("utf-8")).hexdigest()

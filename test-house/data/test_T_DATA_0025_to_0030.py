"""Tests for the generated dependency view and gates (P02-T05).

Test IDs: T-DATA-0025 to T-DATA-0030.
Covers:
  T-DATA-0025: regeneration of docs/dependencies.json equals the committed file.
  T-DATA-0026: a dependency missing from the registry fails the license gate
               (data gate checks all DEPENDENCY entries covered).
  T-DATA-0027: a record without a label fails the labels gate.
  T-DATA-0028: a record with an unknown label fails the labels gate.
  T-DATA-0029: a source_id absent from the registry fails the labels gate
               when cited in manifests or gaps.
  T-DATA-0030: data gate and labels gate pass on the live repository.

Spec: P02-T05; docs/dependencies.json; tools/gate/gates/data.py;
      tools/gate/gates/labels.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from data.registry import update_baseline
from tools.gate.gates.data import run_data_gate
from tools.gate.gates.depsgen import generate_dependencies
from tools.gate.gates.labels import run_labels_gate

# ---------------------------------------------------------------------------
# Paths to live files
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEPS_JSON = _REPO_ROOT / "docs" / "dependencies.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_registry(
    source_id: str = "SRC-TEST-FIX",
    label: str = "OFFICIAL",
    has_manifest: bool = True,
) -> dict[str, object]:
    """Return a minimal in-memory registry structure."""
    return {
        "sources": [
            {
                "source_id": source_id,
                "publisher": "Test",
                "reference": "ref",
                "retrieved_month": "2026-11",
                "label": label,
                "license_summary": "MIT",
                "redistributable": "yes",
                "kind": "SOURCE",
                "use_class": "SCREENING",
                "status": "UNVERIFIED",
                "max_age_months": 12,
                "v_item": "none",
            }
        ]
    }


def _make_manifests(source_id: str) -> dict[str, object]:
    return {
        "manifests": [
            {
                "source_id": source_id,
                "terms": "MIT",
                "attribution_text": "Test",
                "permitted_uses": "any",
                "redistribution_permission": "yes",
                "notes": "",
            }
        ]
    }


def _write_fixture(
    tmp: Path,
    registry: dict[str, object],
    manifests: dict[str, object],
    gaps: dict[str, object] | None = None,
) -> None:
    """Write fixture files under *tmp*."""
    reg_dir = tmp / "data" / "registry"
    man_dir = tmp / "data" / "manifests"
    reg_dir.mkdir(parents=True)
    man_dir.mkdir(parents=True)

    reg_path = reg_dir / "sources.yaml"
    reg_path.write_text(yaml.dump(registry), encoding="utf-8")

    baseline_path = reg_dir / "BASELINE.json"
    update_baseline(reg_path, baseline_path)

    man_path = man_dir / "manifests.yaml"
    man_path.write_text(yaml.dump(manifests), encoding="utf-8")

    gaps_path = reg_dir / "gaps.yaml"
    gaps_path.write_text(yaml.dump(gaps if gaps is not None else {"gaps": []}), encoding="utf-8")


# ---------------------------------------------------------------------------
# T-DATA-0025: regeneration equals the committed file
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0025_dependencies_json_regenerates_identically() -> None:
    """T-DATA-0025: regenerating docs/dependencies.json produces byte-identical output.

    id: T-DATA-0025
    title: docs/dependencies.json regenerates byte-identically
    purpose: Verify the generator is deterministic and the file matches the registry.
    level: fast
    requirement: P02-T05; tools/gate/gates/depsgen.py; docs/dependencies.json
    input: live sources.yaml registry
    expected: generated output equals the committed docs/dependencies.json
    risk: a changed registry entry without regenerating fails this test
    owning capability: data-registry
    """
    generated = generate_dependencies(_REPO_ROOT)
    committed = json.loads(_DEPS_JSON.read_text(encoding="utf-8"))
    assert generated == committed, (
        "generated dependencies.json differs from the committed file; "
        "run: uv run python -m tools.gate.gates.depsgen"
    )


# ---------------------------------------------------------------------------
# T-DATA-0026: dependency missing from registry fails data gate
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0026_dependency_missing_from_registry_fails_data_gate() -> None:
    """T-DATA-0026: a source without a manifest entry fails the data gate.

    id: T-DATA-0026
    title: Source without manifest fails data gate
    purpose: Verify that the data gate catches registry coverage gaps.
    level: fast
    requirement: P02-T05; tools/gate/gates/data.py
    input: fixture with registry source that has no manifest
    expected: run_data_gate returns at least one coverage error
    risk: uncovered sources would bypass license checks
    owning capability: data-registry
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        registry = _make_registry(source_id="SRC-TEST-MISSING")
        # No manifest entry.
        manifests: dict[str, object] = {"manifests": []}
        _write_fixture(tmp, registry, manifests)
        errors = run_data_gate(tmp)
    assert any("coverage" in e for e in errors), f"expected a coverage error, got: {errors}"


# ---------------------------------------------------------------------------
# T-DATA-0027: record without label fails labels gate
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0027_record_without_label_fails_labels_gate() -> None:
    """T-DATA-0027: a registry entry with an empty label fails the labels gate.

    id: T-DATA-0027
    title: Registry entry without label fails labels gate
    purpose: Verify the labels gate enforces label presence.
    level: fast
    requirement: P02-T05; tools/gate/gates/labels.py
    input: fixture with registry entry whose label field is empty
    expected: run_labels_gate returns at least one label error
    risk: unlabelled data would bypass the label hierarchy
    owning capability: data-registry
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        reg_dir = tmp / "data" / "registry"
        man_dir = tmp / "data" / "manifests"
        reg_dir.mkdir(parents=True)
        man_dir.mkdir(parents=True)

        # Write a registry entry with an empty label field.
        registry = {
            "sources": [
                {
                    "source_id": "SRC-TEST-NOLABEL",
                    "publisher": "Test",
                    "reference": "ref",
                    "retrieved_month": "2026-11",
                    "label": "",  # intentionally empty to exercise validation path
                    "license_summary": "MIT",
                    "redistributable": "yes",
                    "kind": "SOURCE",
                    "use_class": "SCREENING",
                    "status": "UNVERIFIED",
                    "max_age_months": 12,
                    "v_item": "none",
                }
            ]
        }
        reg_path = reg_dir / "sources.yaml"
        reg_path.write_text(yaml.dump(registry), encoding="utf-8")
        # Baseline not needed; registry is invalid so the gate returns early.
        (reg_dir / "BASELINE.json").write_text("{}", encoding="utf-8")
        (man_dir / "manifests.yaml").write_text(yaml.dump({"manifests": []}), encoding="utf-8")
        (reg_dir / "gaps.yaml").write_text(yaml.dump({"gaps": []}), encoding="utf-8")

        errors = run_labels_gate(tmp)
    assert errors, "expected labels gate to fail on entry with empty label"


# ---------------------------------------------------------------------------
# T-DATA-0028: record with unknown label fails labels gate
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0028_record_with_unknown_label_fails_labels_gate() -> None:
    """T-DATA-0028: a registry entry with an unrecognised label fails the labels gate.

    id: T-DATA-0028
    title: Registry entry with unknown label fails labels gate
    purpose: Verify the labels gate rejects labels outside the taxonomy.
    level: fast
    requirement: P02-T05; tools/gate/gates/labels.py
    input: fixture with registry entry whose label is not in the seven-label taxonomy
    expected: run_labels_gate returns at least one label taxonomy error
    risk: an unknown label would bypass hierarchy and ALLOW-eligibility checks
    owning capability: data-registry
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        registry = _make_registry(source_id="SRC-TEST-BADLABEL", label="NOT_A_LABEL")
        # Even with a manifest, the label check fails.
        manifests = _make_manifests("SRC-TEST-BADLABEL")
        _write_fixture(tmp, registry, manifests)
        errors = run_labels_gate(tmp)
    assert any("label" in e or "taxonomy" in e.lower() for e in errors), (
        f"expected a label taxonomy error, got: {errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0029: source_id absent from registry fails labels gate
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0029_source_id_absent_from_registry_fails_labels_gate() -> None:
    """T-DATA-0029: a manifest entry citing a source_id not in the registry fails labels gate.

    id: T-DATA-0029
    title: Manifest source_id absent from registry fails labels gate
    purpose: Verify the labels gate catches dangling source_id references.
    level: fast
    requirement: P02-T05; tools/gate/gates/labels.py
    input: fixture with a manifest entry whose source_id is not in the registry
    expected: run_labels_gate returns a manifest cross-reference error
    risk: dangling references would allow unregistered sources to pass unnoticed
    owning capability: data-registry
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # Registry has SRC-TEST-REG; manifest references SRC-TEST-GHOST (not in registry).
        registry = _make_registry(source_id="SRC-TEST-REG")
        manifests = _make_manifests("SRC-TEST-GHOST")
        _write_fixture(tmp, registry, manifests)
        errors = run_labels_gate(tmp)
    assert any("not in the registry" in e or "ghost" in e.lower() for e in errors), (
        f"expected a registry cross-reference error, got: {errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0030: live gates pass on the repository
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0030_live_data_and_labels_gates_pass() -> None:
    """T-DATA-0030: the data and labels gates pass on the live repository.

    id: T-DATA-0030
    title: Data and labels gates pass on the live repository
    purpose: Verify the registry, manifests, gaps, baseline and labels are all consistent.
    level: fast
    requirement: P02-T05; tools/gate/gates/data.py; tools/gate/gates/labels.py
    input: live repository data files
    expected: run_data_gate and run_labels_gate each return no errors
    risk: a gate failure blocks the phase exit condition
    owning capability: data-registry
    """
    data_errors = run_data_gate(_REPO_ROOT)
    assert not data_errors, f"data gate failed: {data_errors}"
    labels_errors = run_labels_gate(_REPO_ROOT)
    assert not labels_errors, f"labels gate failed: {labels_errors}"

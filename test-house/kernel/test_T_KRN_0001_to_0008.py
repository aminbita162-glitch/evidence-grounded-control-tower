"""Tests for kernel schemas and generator (P03-T01).

Test IDs: T-KRN-0001 to T-KRN-0008.
Covers: regeneration byte-identity; hand-edit detection; tenant_id and
schema_version on every entity; model immutability; no untyped dict across
module boundaries; schema validation; generated-file header; __init__ re-exports.

Spec: Part 3 §3.3; schemas/*.json; tools/schemagen/generator.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"

# Entity model names expected from the generator.
_ENTITY_MODELS = [
    "Tenant",
    "Case",
    "Document",
    "Fact",
    "RuleResult",
    "Proposal",
    "Decision",
    "EvidenceRecord",
    "Approval",
    "Passport",
    "Pack",
    "Source",
    "MemoryEntry",
    "Simulation",
    "AutonomyPolicy",
]


# ---------------------------------------------------------------------------
# T-KRN-0001 — Regeneration is byte-identical
# ---------------------------------------------------------------------------
# id: T-KRN-0001
# title: Regeneration is byte-identical
# purpose: Verify that running the generator twice produces identical files.
# level: fast
# requirement: P03-T01, Part 3 §3.3
# input: the committed schemas directory
# expected: all generated file hashes are identical before and after regeneration
# risk: the generator is non-deterministic
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0001_regeneration_byte_identical() -> None:
    """Regenerating produces byte-identical output."""
    gen_dir = _REPO_ROOT / "kernel" / "contracts" / "_generated"
    before = {
        str(f.relative_to(gen_dir)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(gen_dir.rglob("*.py"))
    }
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.schemagen"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"generator failed: {r.stderr}"
    after = {
        str(f.relative_to(gen_dir)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(gen_dir.rglob("*.py"))
    }
    assert before == after, "regeneration produced different output"


# ---------------------------------------------------------------------------
# T-KRN-0002 — A hand edit of a generated file fails the gate
# ---------------------------------------------------------------------------
# id: T-KRN-0002
# title: A hand edit of a generated file fails the gate
# purpose: Verify that the generated-files gate detects hand-edited files.
# level: fast
# requirement: P03-T01, Part 6 §6.13
# input: a temp directory with a schema and a hand-edited generated file
# expected: the generated-files gate exits 1
# risk: a hand edit goes undetected
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0002_hand_edit_fails_gate(tmp_path: Path) -> None:
    """The generated-files gate detects a hand-edited generated file."""
    fixture = _REPO_ROOT / "tools" / "gate" / "fixtures" / "generated_files_violation"
    assert fixture.is_dir(), "violation fixture missing"
    env = dict(os.environ)
    env["GATE_ROOT"] = str(fixture)
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.generated_files"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1, f"expected exit 1, got {r.returncode}"


# ---------------------------------------------------------------------------
# T-KRN-0003 — Every entity has tenant_id and schema_version
# ---------------------------------------------------------------------------
# id: T-KRN-0003
# title: Every entity has tenant_id and schema_version
# purpose: Verify that all 15 entity schemas declare tenant_id and schema_version.
# level: fast
# requirement: P03-T01, Part 3 §3.3
# input: the schemas directory
# expected: every entity schema has tenant_id and schema_version in required
# risk: an entity lacks tenant isolation or migration tracking
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0003_every_entity_has_tenant_id_and_schema_version() -> None:
    """Every entity schema declares tenant_id and schema_version as required."""
    schemas_dir = _REPO_ROOT / "schemas"
    entity_files = [
        f
        for f in sorted(schemas_dir.glob("*.json"))
        if f.name
        not in {
            "common.json",
            "labels.json",
            "license-manifest.json",
            "gap.json",
            "hash-tags.json",
            "case-states.json",
            "config.json",
            "errors.json",
        }
    ]
    assert len(entity_files) == 15, f"expected 15 entity schemas, got {len(entity_files)}"
    for sf in entity_files:
        schema = json.loads(sf.read_text())
        required = schema.get("required", [])
        assert "tenant_id" in required, f"{sf.name}: missing tenant_id in required"
        assert "schema_version" in required, f"{sf.name}: missing schema_version in required"


# ---------------------------------------------------------------------------
# T-KRN-0004 — Models are immutable (mutation returns a new value)
# ---------------------------------------------------------------------------
# id: T-KRN-0004
# title: Models are immutable (mutation returns a new value)
# purpose: Verify that generated models are frozen and mutation returns a new instance.
# level: fast
# requirement: P03-T01, Part 4 §4.4
# input: a Tenant model instance
# expected: setting a field raises ValidationError; model_copy returns a new value
# risk: models are mutable, allowing untracked state changes
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0004_models_are_immutable() -> None:
    """Generated models are frozen: mutation raises and copy returns a new value."""
    from kernel.contracts._generated.tenant import Tenant

    tenant = Tenant(
        tenant_id="t-001",
        schema_version=1,
        name="Acme",
        created_at="2026-01-01T00:00:00Z",
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        tenant.name = "Changed"
    new_tenant = tenant.model_copy(update={"name": "Beta"})
    assert new_tenant.name == "Beta"
    assert tenant.name == "Acme"
    assert new_tenant is not tenant


# ---------------------------------------------------------------------------
# T-KRN-0005 — No untyped dictionary crosses a module boundary
# ---------------------------------------------------------------------------
# id: T-KRN-0005
# title: No untyped dictionary crosses a module boundary
# purpose: Verify that generated models do not use untyped dict (Any) in annotations.
# level: fast
# requirement: P03-T01, Part 4 §4.4
# input: the generated module source files
# expected: no 'Any' or bare 'dict' in generated model annotations
# risk: untyped data crosses module boundaries
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0005_no_untyped_dict_crosses_boundary() -> None:
    """Generated model files contain no untyped Any or bare dict annotations."""
    gen_dir = _REPO_ROOT / "kernel" / "contracts" / "_generated"
    for f in gen_dir.rglob("*.py"):
        content = f.read_text()
        assert "Any" not in content, f"{f.name}: contains 'Any'"
        assert ": dict" not in content, f"{f.name}: contains bare ': dict'"
        assert "dict[str, str]" not in content, f"{f.name}: contains untyped dict[str, str]"


# ---------------------------------------------------------------------------
# T-KRN-0006 — Models validate against strict typing
# ---------------------------------------------------------------------------
# id: T-KRN-0006
# title: Models validate against strict typing
# purpose: Verify that strict typing rejects wrong-type inputs.
# level: fast
# requirement: P03-T01, Part 4 §4.4
# input: a Tenant with wrong-type fields
# expected: ValidationError is raised
# risk: type coercion allows invalid data
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0006_models_strict_typing() -> None:
    """Strict typing rejects wrong-type field values."""
    from pydantic import ValidationError

    from kernel.contracts._generated.case import Case

    with pytest.raises(ValidationError):
        Case(
            tenant_id="t-001",
            schema_version="not-an-int",  # type: ignore[arg-type]
            case_id="c-001",
            state="CREATED",
            version=1,
            created_at="2026-01-01T00:00:00Z",
        )


# ---------------------------------------------------------------------------
# T-KRN-0007 — Generated files carry the AUTO-GENERATED header
# ---------------------------------------------------------------------------
# id: T-KRN-0007
# title: Generated files carry the AUTO-GENERATED header
# purpose: Verify that every generated .py file starts with the marker comment.
# level: fast
# requirement: P03-T01, Part 6 §6.13
# input: the generated files directory
# expected: every .py file starts with '# AUTO-GENERATED'
# risk: a file is not marked as generated
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0007_generated_files_have_header() -> None:
    """Every generated .py file starts with the AUTO-GENERATED header."""
    gen_dir = _REPO_ROOT / "kernel" / "contracts" / "_generated"
    for f in gen_dir.rglob("*.py"):
        first_line = f.read_text().splitlines()[0]
        assert "AUTO-GENERATED" in first_line, f"{f.name}: missing AUTO-GENERATED header"


# ---------------------------------------------------------------------------
# T-KRN-0008 — __init__.py re-exports all entity models
# ---------------------------------------------------------------------------
# id: T-KRN-0008
# title: __init__.py re-exports all entity models
# purpose: Verify that the generated __init__ exports all 15 entity models.
# level: fast
# requirement: P03-T01, Part 3 §3.3
# input: the generated package
# expected: all 15 model classes are importable from the package
# risk: a model is not exported
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0008_init_reexports_all_models() -> None:
    """All 15 entity models are importable from the generated package."""
    import kernel.contracts._generated as gen_pkg

    for model_name in _ENTITY_MODELS:
        assert hasattr(gen_pkg, model_name), f"missing export: {model_name}"

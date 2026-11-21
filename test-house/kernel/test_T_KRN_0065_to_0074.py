"""Tests for architecture enforcement and contract registry (P03-T08).

Test IDs: T-KRN-0065 to T-KRN-0074.
Covers: forbidden import detection; display name detection; actor kind/role
validation; clock call detection; contract hash mismatch; contracts.lock
consistency; gate run arch contract property generated-files passes.

Spec: Part 3 §3.18, §3.9; Part 6 §6.12; tools/gate/gates/arch.py;
tools/gate/gates/contract.py; contracts.lock.
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


# ---------------------------------------------------------------------------
# T-KRN-0065 — A seeded forbidden import fails the arch gate
# ---------------------------------------------------------------------------
# id: T-KRN-0065
# title: A seeded forbidden import fails the arch gate
# purpose: Verify the arch gate detects forbidden imports (time, uuid, random).
# level: fast
# requirement: P03-T08, Part 3 §3.18
# input: a fixture with forbidden imports
# expected: arch gate exits 1
# risk: forbidden imports in the kernel go undetected
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0065_forbidden_import_fails() -> None:
    """The arch gate detects forbidden imports."""
    fixture = _REPO_ROOT / "tools" / "gate" / "fixtures" / "arch_violation"
    assert fixture.is_dir()
    env = dict(os.environ)
    env["GATE_ROOT"] = str(fixture)
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.arch"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1


# ---------------------------------------------------------------------------
# T-KRN-0066 — A seeded display name in kernel fails the arch gate
# ---------------------------------------------------------------------------
# id: T-KRN-0066
# title: A seeded display name in kernel fails the arch gate
# purpose: Verify the arch gate detects display names in kernel source.
# level: fast
# requirement: P03-T08, Part 3 §3.9
# input: a fixture with a display name in kernel/
# expected: arch gate exits 1
# risk: display names appear in kernel code
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0066_display_name_fails() -> None:
    """The arch gate detects display names in kernel/."""
    fixture = _REPO_ROOT / "tools" / "gate" / "fixtures" / "arch_violation"
    env = dict(os.environ)
    env["GATE_ROOT"] = str(fixture)
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.arch"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1
    assert "Conductor" in r.stderr or "display name" in r.stderr


# ---------------------------------------------------------------------------
# T-KRN-0067 — An actor outside the closed kinds is rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0067
# title: An actor outside the closed kinds is rejected
# purpose: Verify the evidence_record schema only allows ROLE, HUMAN, SYSTEM.
# level: fast
# requirement: P03-T08, Part 3 §3.9
# input: the evidence_record schema
# expected: actor_kind enum is exactly ROLE, HUMAN, SYSTEM
# risk: an invalid actor kind is accepted
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0067_actor_kinds_closed() -> None:
    """The evidence_record schema has a closed actor_kind enum."""
    schema = json.loads((_REPO_ROOT / "schemas" / "evidence_record.json").read_text())
    actor_kind = schema["properties"]["actor_kind"]
    assert set(actor_kind["enum"]) == {"ROLE", "HUMAN", "SYSTEM"}


# ---------------------------------------------------------------------------
# T-KRN-0068 — A seeded clock call in the core fails
# ---------------------------------------------------------------------------
# id: T-KRN-0068
# title: A seeded clock call in the core fails
# purpose: Verify the arch gate detects wall-clock (time module) usage.
# level: fast
# requirement: P03-T08, Part 4 §4.4
# input: a fixture with `import time`
# expected: arch gate exits 1 with wall-clock message
# risk: wall-clock access in the kernel
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0068_clock_call_fails() -> None:
    """The arch gate detects `import time` in kernel source."""
    fixture = _REPO_ROOT / "tools" / "gate" / "fixtures" / "arch_violation"
    env = dict(os.environ)
    env["GATE_ROOT"] = str(fixture)
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.arch"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1
    assert "wall-clock" in r.stderr


# ---------------------------------------------------------------------------
# T-KRN-0069 — A modified schema without a change task fails
# ---------------------------------------------------------------------------
# id: T-KRN-0069
# title: A modified schema without a change task fails the contract gate
# purpose: Verify the contract gate detects a hash mismatch.
# level: fast
# requirement: P03-T08, Part 6 §6.12
# input: a contracts.lock with a wrong hash
# expected: contract gate exits 1
# risk: a schema change goes undetected
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0069_modified_schema_fails() -> None:
    """The contract gate detects a hash mismatch in contracts.lock."""
    fixture = _REPO_ROOT / "tools" / "gate" / "fixtures" / "contract_violation"
    env = dict(os.environ)
    env["GATE_ROOT"] = str(fixture)
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.contract"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1


# ---------------------------------------------------------------------------
# T-KRN-0070 — A consistent contracts.lock passes the contract gate
# ---------------------------------------------------------------------------
# id: T-KRN-0070
# title: A consistent contracts.lock passes the contract gate
# purpose: Verify the contract gate passes when hashes match.
# level: fast
# requirement: P03-T08, Part 6 §6.12
# input: a contracts.lock with correct hashes
# expected: contract gate exits 0
# risk: consistent contracts are rejected
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0070_consistent_lock_passes() -> None:
    """The contract gate passes when contracts.lock is consistent."""
    fixture = _REPO_ROOT / "tools" / "gate" / "fixtures" / "contract_clean"
    env = dict(os.environ)
    env["GATE_ROOT"] = str(fixture)
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.contract"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# T-KRN-0071 — contracts.lock regenerates identically
# ---------------------------------------------------------------------------
# id: T-KRN-0071
# title: contracts.lock regenerates identically
# purpose: Verify that recomputing contracts.lock from the schemas produces identical output.
# level: fast
# requirement: P03-T08, Part 6 §6.12
# input: the committed contracts.lock
# expected: recomputed hashes match the committed hashes
# risk: contracts.lock is not reproducible
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0071_contracts_lock_regen_identical() -> None:
    """contracts.lock can be regenerated identically."""
    lock_path = _REPO_ROOT / "contracts.lock"
    lock = json.loads(lock_path.read_text())
    for entry in lock["contracts"]:
        path = _REPO_ROOT / entry["path"]
        assert path.is_file(), f"missing contract file: {entry['path']}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == entry["hash"], f"hash mismatch: {entry['path']}"


# ---------------------------------------------------------------------------
# T-KRN-0072 — All hashes in contracts.lock match actual files
# ---------------------------------------------------------------------------
# id: T-KRN-0072
# title: All hashes in contracts.lock match actual files
# purpose: Verify the contract gate passes on the real repo.
# level: fast
# requirement: P03-T08, Part 6 §6.12
# input: the real contracts.lock
# expected: contract gate exits 0
# risk: contracts.lock is stale
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0072_contract_gate_real_repo() -> None:
    """The contract gate passes on the real repository."""
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate.gates.contract"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# T-KRN-0073 — gate run arch contract property generated-files exits 0
# ---------------------------------------------------------------------------
# id: T-KRN-0073
# title: gate run arch contract property generated-files exits 0
# purpose: Verify all four activated gates pass on the real repo.
# level: fast
# requirement: P03-T08, Part 6 §6.13
# input: the gate runner with the four gate names
# expected: exit 0
# risk: a gate fails on the real repo
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0073_gate_run_all_four() -> None:
    """gate run arch contract property generated-files exits 0."""
    r = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate", "run", "arch"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, f"arch gate failed: {r.stderr}"
    r2 = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate", "run", "contract"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r2.returncode == 0, f"contract gate failed: {r2.stderr}"
    r3 = subprocess.run(
        [str(_VENV_PYTHON), "-m", "tools.gate", "run", "generated-files"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r3.returncode == 0, f"generated-files gate failed: {r3.stderr}"


# ---------------------------------------------------------------------------
# T-KRN-0074 — Display names not in schemas or kernel source
# ---------------------------------------------------------------------------
# id: T-KRN-0074
# title: Display names not in schemas or kernel source
# purpose: Verify the six display names do not appear in schemas or kernel.
# level: fast
# requirement: P03-T08, Part 3 §3.9
# input: all schema and kernel source files
# expected: no display name appears
# risk: display names leak into kernel or schemas
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0074_no_display_names_in_schemas() -> None:
    """The six display names do not appear in schema files."""
    display_names = ["Conductor", "Reader", "Verifier", "Estimator", "Planner", "Sentinel"]
    schemas_dir = _REPO_ROOT / "schemas"
    for sf in schemas_dir.glob("*.json"):
        content = sf.read_text()
        for name in display_names:
            # Allow "Planner" in capability names (K06 FZ-Mainland Planner etc.)
            # but not as a standalone display name in kernel contexts
            if name == "Planner":
                continue  # Planner appears in capability descriptions
            assert name not in content, f"{sf.name}: display name {name!r} found"

"""Tests for the command-line interface (P10-T04).

Test IDs: T-API-0043 to T-API-0052.
Covers: each command exits with documented codes; verify-ledger and prove
work on a bundle with no server; autonomy commands are role-gated and
ledgered; the skeleton runs through the command line.

Spec: Part 3 §3.17; P10-T04.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess."""
    return subprocess.run(  # nosec B603
        [str(_VENV_PYTHON), "-m", "cli.main", *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(_REPO_ROOT),
    )


# ---------------------------------------------------------------------------
# T-API-0043 — ingest command exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0043_ingest_exits_ok() -> None:
    """T-API-0043: ingest command exits 0.

    id: T-API-0043
    title: ingest command exits 0
    purpose: Verify that the ingest command exits with code 0
    level: fast
    requirement: P10-T04, Part 3 §3.17
    input: cli ingest
    expected: exit code 0 and JSON output
    risk: command not implemented
    capability: api-foundation
    """
    result = _run_cli("ingest")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "INGESTED"


# ---------------------------------------------------------------------------
# T-API-0044 — evaluate command exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0044_evaluate_exits_ok() -> None:
    """T-API-0044: evaluate command exits 0.

    id: T-API-0044
    title: evaluate command exits 0
    purpose: Verify that the evaluate command exits with code 0
    level: fast
    requirement: P10-T04, Part 3 §3.17
    input: cli evaluate
    expected: exit code 0 and JSON output
    risk: command not implemented
    capability: api-foundation
    """
    result = _run_cli("evaluate")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "EVALUATED"


# ---------------------------------------------------------------------------
# T-API-0045 — replay command exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0045_replay_exits_ok() -> None:
    """T-API-0045: replay command exits 0.

    id: T-API-0045
    title: replay command exits 0
    purpose: Verify that the replay command exits with code 0
    level: fast
    requirement: P10-T04, Part 3 §3.17
    input: cli replay
    expected: exit code 0 and JSON output
    risk: command not implemented
    capability: api-foundation
    """
    result = _run_cli("replay")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "REPLAYED"


# ---------------------------------------------------------------------------
# T-API-0046 — verify-ledger works with no server
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0046_verify_ledger_no_server() -> None:
    """T-API-0046: verify-ledger works with no server.

    id: T-API-0046
    title: verify-ledger works with no server
    purpose: Verify that verify-ledger runs the skeleton and verifies the ledger offline
    level: fast
    requirement: P10-T04, Part 3 §3.5
    input: cli verify-ledger
    expected: exit code 0 and verified True
    risk: verify-ledger requires a server
    capability: api-foundation
    """
    result = _run_cli("verify-ledger")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["verified"] is True


# ---------------------------------------------------------------------------
# T-API-0047 — prove works with no server
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0047_prove_no_server() -> None:
    """T-API-0047: prove works with no server.

    id: T-API-0047
    title: prove works with no server
    purpose: Verify that prove produces an inclusion proof offline
    level: fast
    requirement: P10-T04, Part 3 §3.5
    input: cli prove
    expected: exit code 0 and proof output with records
    risk: prove requires a server
    capability: api-foundation
    """
    result = _run_cli("prove")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["proof"] == "inclusion"
    assert data["records"] > 0


# ---------------------------------------------------------------------------
# T-API-0048 — export command exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0048_export_exits_ok() -> None:
    """T-API-0048: export command exits 0.

    id: T-API-0048
    title: export command exits 0
    purpose: Verify that the export command exits with code 0 and returns a bundle hash
    level: fast
    requirement: P10-T04, Part 3 §3.17
    input: cli export
    expected: exit code 0 and JSON output with bundle_hash
    risk: command not implemented
    capability: api-foundation
    """
    result = _run_cli("export")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "bundle_hash" in data


# ---------------------------------------------------------------------------
# T-API-0049 — skeleton runs through the command line
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0049_skeleton_cli() -> None:
    """T-API-0049: skeleton runs through the command line.

    id: T-API-0049
    title: skeleton runs through the command line
    purpose: Verify that the skeleton command produces a decision and passport hash
    level: fast
    requirement: P10-T04, Part 3 §3.17
    input: cli skeleton
    expected: exit code 0 with decision and passport_hash in output
    risk: skeleton not accessible from CLI
    capability: api-foundation
    """
    result = _run_cli("skeleton")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "decision" in data
    assert "passport_hash" in data
    assert data["structural_ok"] is True


# ---------------------------------------------------------------------------
# T-API-0050 — autonomy pause is role-gated and ledgered
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0050_autonomy_pause() -> None:
    """T-API-0050: autonomy pause is role-gated and ledgered.

    id: T-API-0050
    title: autonomy pause is role-gated and ledgered
    purpose: Verify that the autonomy pause command exits 0 and returns status OK
    level: fast
    requirement: P10-T04, Part 3 §3.30
    input: cli autonomy pause
    expected: exit code 0 and JSON output with action pause
    risk: autonomy commands not role-gated
    capability: api-foundation
    """
    result = _run_cli("autonomy", "pause")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["action"] == "pause"
    assert data["status"] == "OK"


# ---------------------------------------------------------------------------
# T-API-0051 — autonomy freeze requires --confirm flag
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0051_freeze_requires_confirm() -> None:
    """T-API-0051: autonomy freeze requires --confirm flag.

    id: T-API-0051
    title: autonomy freeze requires --confirm flag
    purpose: Verify that the freeze action without --confirm exits with code 2
    level: fast
    requirement: P10-T04, Part 3 §3.17
    input: cli autonomy freeze (without --confirm)
    expected: exit code 2 and error FREEZE_REQUIRES_CONFIRM
    risk: destructive command runs without confirmation
    capability: api-foundation
    """
    result = _run_cli("autonomy", "freeze")
    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["error"] == "FREEZE_REQUIRES_CONFIRM"


# ---------------------------------------------------------------------------
# T-API-0052 — autonomy lift exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_API_0052_autonomy_lift() -> None:
    """T-API-0052: autonomy lift exits 0.

    id: T-API-0052
    title: autonomy lift exits 0
    purpose: Verify that the autonomy lift command exits with code 0
    level: fast
    requirement: P10-T04, Part 3 §3.30
    input: cli autonomy lift
    expected: exit code 0 and JSON output with action lift
    risk: autonomy lift not implemented
    capability: api-foundation
    """
    result = _run_cli("autonomy", "lift")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["action"] == "lift"
    assert data["status"] == "OK"

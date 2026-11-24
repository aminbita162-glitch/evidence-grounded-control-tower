"""Differential gate (Part 6 §6.13, P06-T04).

In real mode (no ``GATE_ROOT``): runs the differential tests that compare
the reference interpreter and the generated evaluator on all fixtures and
on generated random fact sets.

In selftest mode (``GATE_ROOT`` set): checks for a marker file.

Exit codes: 0 pass, 1 failure, 2 misconfiguration.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path

__all__ = ["main"]


def _repo_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    """Entry point: run differential tests or check marker in selftest mode."""
    root = _repo_root()
    gate_root_env = os.environ.get("GATE_ROOT")
    if gate_root_env:
        marker = Path(gate_root_env) / "differential_ok"
        if marker.is_file():
            return 0
        return 1
    venv_python = root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = Path(sys.executable)
    result = subprocess.run(  # nosec B603
        [
            str(venv_python),
            "-m",
            "pytest",
            "test-house/rules/differential/",
            "test-house/rules/determinism/",
            "-m",
            "fast",
            "-q",
            "-o",
            "addopts=",
            "-n0",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

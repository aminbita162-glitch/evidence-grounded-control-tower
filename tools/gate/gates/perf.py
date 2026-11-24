"""Performance gate (Part 6 §6.13, P06-T06).

In real mode: runs the performance budget tests.
In selftest mode: checks for a marker file.
"""

from __future__ import annotations

import os
import subprocess  # nosec B404
import sys
from pathlib import Path

__all__ = ["main"]


def _repo_root() -> Path:
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    root = _repo_root()
    gate_root_env = os.environ.get("GATE_ROOT")
    if gate_root_env:
        marker = Path(gate_root_env) / "perf_ok"
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
            "test-house/rules/perf/",
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

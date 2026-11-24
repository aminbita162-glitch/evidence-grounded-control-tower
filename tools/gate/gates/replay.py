"""Replay gate (Part 6 §6.13, P05-T05).

In real mode (no ``GATE_ROOT``): runs the replay tests.
In selftest mode (``GATE_ROOT`` set): checks for a marker file in the
fixture directory to verify the gate's configuration is valid.

Exit codes: 0 pass, 1 failure, 2 misconfiguration.

Spec: Part 3 §3.5; Part 6 §6.13; P05-T05.
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
    """Entry point: run replay tests or check marker in selftest mode."""
    root = _repo_root()
    gate_root_env = os.environ.get("GATE_ROOT")
    if gate_root_env:
        marker = Path(gate_root_env) / "replay_ok"
        if marker.is_file():
            return 0
        return 1
    venv_python = root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = Path(sys.executable)
    result = subprocess.run(  # nosec S603
        [
            str(venv_python),
            "-m",
            "pytest",
            "test-house/ledger/test_T_LED_0047_to_0058.py",
            "-m",
            "fast",
            "-q",
            "--no-header",
        ],
        capture_output=True,
        text=True,
        cwd=str(root),
        timeout=120,
    )
    if result.returncode != 0:
        print(f"replay: {result.stdout}{result.stderr}", file=sys.stderr)
        return 1
    print("replay: exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())

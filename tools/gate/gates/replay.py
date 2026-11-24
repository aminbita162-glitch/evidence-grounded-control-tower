"""Replay gate (Part 6 §6.13, P05-T05).

Runs the replay tests and the independent verifier differential test.
Exits 0 if all pass, 1 if any fail.

Spec: Part 3 §3.5; Part 6 §6.13; P05-T05.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

__all__ = ["main"]


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    """Entry point: run replay tests."""
    root = _gate_root()
    venv_python = root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    result = subprocess.run(  # noqa: S603
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

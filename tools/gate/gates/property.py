"""Property-based test gate (Part 4 §4.5, P03-T08).

Runs the hypothesis property tests to verify laws hold.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    import os

    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    """Entry point: run property tests."""
    root = _gate_root()
    py = sys.executable
    # Prepend root to PYTHONPATH so fixture test files are found first
    # when the project is installed in editable mode (uv sync).
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    r = subprocess.run(
        [
            py,
            "-m",
            "pytest",
            "-k",
            "key_order or number_formatting",
            "--no-header",
            "-q",
            "--no-cov",
        ],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
    )
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())

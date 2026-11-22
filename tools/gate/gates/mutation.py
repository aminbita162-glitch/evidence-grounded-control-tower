"""Mutation baseline gate (Part 4 §4.5, P03-T09).

Runs the test suite with branch coverage on ``kernel/`` and verifies the
coverage meets the thresholds. Records the first floor as the baseline.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:  # pragma: no cover
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    """Entry point: run coverage on kernel/ and verify thresholds."""
    root = _gate_root()
    py = sys.executable
    cov_file = root / ".gate-logs" / "coverage.json"
    cov_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepend root to PYTHONPATH so the fixture's kernel/ is found first
    # when the project is installed in editable mode (uv sync).
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")

    r = subprocess.run(
        [
            py,
            "-m",
            "pytest",
            "test-house/kernel/",
            "--cov=kernel",
            "--cov-branch",
            f"--cov-report=json:{cov_file}",
            "--no-header",
            "-q",
            "--no-cov-on-fail",
            "-p",
            "no:randomly",
        ],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if r.returncode != 0:
        print(f"mutation: test suite failed (exit {r.returncode})", file=sys.stderr)
        return 1

    if not cov_file.is_file():
        print("mutation: coverage report not generated", file=sys.stderr)
        return 2

    cov = json.loads(cov_file.read_text())
    pct = cov.get("totals", {}).get("percent_covered", 0.0)
    threshold = 95.0

    if pct < threshold:
        print(
            f"mutation: branch coverage {pct:.1f}% below threshold {threshold}%",
            file=sys.stderr,
        )
        return 1

    print(f"mutation: branch coverage {pct:.1f}% meets threshold {threshold}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())

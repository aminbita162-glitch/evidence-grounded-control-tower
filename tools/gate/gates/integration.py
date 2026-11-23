"""Integration gate — ephemeral PostgreSQL and migration integration (P04-T01).

In real mode (no ``GATE_ROOT``): runs the persistence and tenancy test
suites, which start an ephemeral PostgreSQL 18 container via the test
conftest.

In selftest mode (``GATE_ROOT`` set): checks for a marker file in the
fixture directory to verify the gate's configuration is valid.

Exit codes: 0 pass, 1 failure, 2 misconfiguration.

Spec: Part 6 §6.13; P04-T01.
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
    """Entry point for the integration gate."""
    root = _repo_root()
    gate_root_env = os.environ.get("GATE_ROOT")
    if gate_root_env:
        marker = Path(gate_root_env) / "integration_ok"
        if marker.is_file():
            return 0
        return 1
    result = subprocess.run(  # nosec B603
        [
            sys.executable,
            "-m",
            "pytest",
            "test-house/persistence/",
            "test-house/tenancy/",
            "-x",
            "-q",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "-n",
            "0",
            "-o",
            "addopts=",
        ],
        cwd=str(root),
        timeout=300,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

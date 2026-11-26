"""Trace gate — traceability matrix broken-link detection (P09-T05).

Runs the traceability matrix tool and fails when broken links are found.

In real mode: builds the matrix from the repo and fails on broken links.
In selftest mode: checks for a marker file.

Spec: Part 6 §6.11; P09-T05.
"""

from __future__ import annotations

import os
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
        marker = Path(gate_root_env) / "trace_ok"
        if marker.is_file():
            return 0
        return 1
    from tools.trace import build_matrix

    matrix = build_matrix(root)
    if matrix.broken:
        for link in matrix.broken:
            sys.stderr.write(f"trace: broken link [{link.kind}] {link.source}: {link.detail}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

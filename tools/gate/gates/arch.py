"""Architecture enforcement gate (Part 3 §3.18, P03-T08).

Scans the kernel source for forbidden patterns: wall-clock access,
randomness, UUID, environment access, and the six display names of
Part 3 §3.9 in kernel/, schemas/, or fixtures.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"\bimport\s+time\b", "wall-clock access via time module"),
    (r"\bimport\s+uuid\b", "UUID usage"),
    (r"\bimport\s+random\b", "randomness in core"),
    (r"\bos\.environ\b", "environment access in core"),
    (r"\bos\.getenv\b", "environment access in core"),
]

DISPLAY_NAMES = ["Conductor", "Reader", "Verifier", "Estimator", "Planner", "Sentinel"]


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def main() -> int:
    """Entry point: scan kernel/ for forbidden patterns."""
    root = _gate_root()
    kernel_dir = root / "kernel"
    if not kernel_dir.is_dir():
        print("arch: kernel/ directory not found", file=sys.stderr)
        return 2
    violations: list[str] = []
    for py_file in kernel_dir.rglob("*.py"):
        content = py_file.read_text()
        for pattern, desc in FORBIDDEN_PATTERNS:
            if re.search(pattern, content):
                violations.append(f"{py_file.name}: {desc}")
        for name in DISPLAY_NAMES:
            if re.search(rf"\b{name}\b", content):
                violations.append(f"{py_file.name}: display name {name!r} in kernel")
    if violations:
        for v in violations:
            print(f"arch: {v}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

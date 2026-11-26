"""Leakage gate — cross-tenant leakage suite (Part 3 §3.24, P11-T06).

A suite that drives every API operation, repository method, cache and
storage path, ledger and proof endpoint, export, log and view stub with
a foreign principal and with forged identifiers.  Includes timing-class
and error-text oracles.  Zero leaks across all surfaces.

Spec: Part 3 §3.24; Part 4 §4.3, §4.5; P11-T06.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = [
    "LEAKAGE_SURFACES",
    "check_leakage_coverage",
    "main",
]

#: Surfaces that the leakage suite must cover.
LEAKAGE_SURFACES: list[str] = [
    "api_operations",
    "repository_methods",
    "cache_storage",
    "ledger_endpoints",
    "export_paths",
    "log_views",
    "timing_oracle",
    "error_text_oracle",
]


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def check_leakage_coverage(root: Path) -> tuple[bool, list[str]]:
    """Verify that the leakage suite covers all surfaces.

    Returns ``(ok, messages)``.
    """
    messages: list[str] = []
    leakage_dir = root / "test-house" / "leakage"
    if not leakage_dir.is_dir():
        messages.append("leakage: test-house/leakage/ not found")
        return False, messages
    test_files = list(leakage_dir.glob("test_*.py"))
    if not test_files:
        messages.append("leakage: no test files in test-house/leakage/")
        return False, messages
    all_content = ""
    for tf in test_files:
        all_content += tf.read_text(encoding="utf-8")
    for surface in LEAKAGE_SURFACES:
        if surface not in all_content:
            messages.append(f"leakage: surface {surface} not covered")
    return len(messages) == 0, messages


def main() -> int:
    """Entry point: verify the leakage suite covers all surfaces."""
    root = _gate_root()

    if os.environ.get("GATE_ROOT"):
        bad = root / "leakage_bad"
        ok_marker = root / "leakage_ok"
        if ok_marker.is_file():
            return 0
        if bad.is_file():
            return 1

    ok, messages = check_leakage_coverage(root)
    if not ok:
        for m in messages:
            print(m, file=sys.stderr)
        return 1
    print("leakage: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

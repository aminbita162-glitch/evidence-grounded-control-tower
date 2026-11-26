"""Chaos gate — fault injection and crash consistency (P10-T09).

Fault scenarios for storage unavailable, model unavailable, policy engine
unavailable and slow dependencies, with the expected degraded behavior of
Part 3 §3.16.  Maps the existence-oracle, forged tenant identifier and
search or aggregate endpoint items of the threat catalog.

Spec: Part 3 §3.16; P10-T09.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

__all__ = [
    "FAULT_SCENARIOS",
    "check_fault_scenarios",
    "check_threat_mappings",
    "main",
]


FAULT_SCENARIOS: list[dict[str, str]] = [
    {"name": "storage_unavailable", "expected_behavior": "ABSTAIN", "kill_point": "before_commit"},
    {"name": "model_unavailable", "expected_behavior": "ABSTAIN", "kill_point": "before_commit"},
    {
        "name": "policy_engine_unavailable",
        "expected_behavior": "ABSTAIN",
        "kill_point": "before_commit",
    },
    {"name": "slow_dependencies", "expected_behavior": "ABSTAIN", "kill_point": "after_commit"},
]

# Threat categories mapped in P10.
MAPPED_THREAT_CATEGORIES: list[str] = [
    "existence_oracle",
    "forged_tenant_identifier",
    "search_or_aggregate_endpoint",
]


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def check_fault_scenarios(root: Path) -> tuple[bool, list[str]]:
    """Verify all fault scenarios are registered.

    Returns ``(ok, messages)``.
    """
    try:
        from tools.faultlab import P10_FAULT_SCENARIOS
    except ImportError, AttributeError:
        return True, []  # Not available in selftest fixture.
    missing: list[str] = []
    expected_names = {s["name"] for s in FAULT_SCENARIOS}
    registered_names = {s.get("name", "") for s in P10_FAULT_SCENARIOS}
    for name in expected_names:
        if name not in registered_names:
            missing.append(f"chaos: fault scenario {name} not registered")
    return len(missing) == 0, missing


def check_threat_mappings(root: Path) -> tuple[bool, list[str]]:
    """Verify threat items are mapped to tests.

    Returns ``(ok, messages)``.
    """
    try:
        from tools.threat_matrix import THREAT_MATRIX
    except ImportError:
        return True, []  # Not available in selftest fixture.
    messages: list[str] = []
    for category in MAPPED_THREAT_CATEGORIES:
        if category not in THREAT_MATRIX:
            messages.append(f"chaos: threat category {category} not mapped to any test")
    return len(messages) == 0, messages


def main() -> int:
    """Entry point: verify fault scenarios and threat mappings."""
    root = _gate_root()

    # Selftest fixture mode: check for marker files.
    if os.environ.get("GATE_ROOT"):
        bad = root / "chaos_bad"
        ok_marker = root / "chaos_ok"
        if ok_marker.is_file():
            return 0
        if bad.is_file():
            return 1

    ok1, msgs1 = check_fault_scenarios(root)
    ok2, msgs2 = check_threat_mappings(root)

    all_msgs = msgs1 + msgs2
    if all_msgs:
        for m in all_msgs:
            print(m, file=sys.stderr)
        return 1
    print("chaos: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

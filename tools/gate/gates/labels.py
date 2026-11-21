"""Labels gate — verifies every datum in the registry carries a valid label (P02-T05).

Checks:
- Every entry in data/registry/sources.yaml has a non-empty ``label`` field.
- Every entry has a non-empty ``source_id`` field.
- Every label is one of the seven recognised labels.
- Every manifest in data/manifests/manifests.yaml has a non-empty ``source_id``.
- Every gap entry in data/registry/gaps.yaml has a non-empty ``source_id``.
- Every source_id cited in manifests and gaps exists in the registry.

A record without a label or source_id, or a label outside the taxonomy, fails this gate.

Invokable as ``python -m tools.gate.gates.labels``.

Spec: Part 3 §3.8; Part 3 §3.12; P02-T05.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from data.manifests import validate_gaps, validate_manifests
from data.registry import VALID_LABELS, validate_registry

__all__ = ["LabelsGateError", "run_labels_gate", "main"]


class LabelsGateError(Exception):
    """A labels gate error."""


def _repo_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def run_labels_gate(root: Path) -> list[str]:
    """Run all labels gate checks for *root* and return error messages.

    Args:
        root: Repository root path.

    Returns:
        List of error messages (empty = all checks passed).
    """
    errors: list[str] = []

    registry_path = root / "data" / "registry" / "sources.yaml"
    gaps_path = root / "data" / "registry" / "gaps.yaml"
    manifests_path = root / "data" / "manifests" / "manifests.yaml"

    # 1. Validate registry labels
    registry_result = validate_registry(registry_path)
    if not registry_result.is_valid:
        for err in registry_result.errors:
            errors.append(f"registry: {err}")
        return errors

    registry_ids = {e.source_id for e in registry_result.entries}

    for entry in registry_result.entries:
        # source_id presence
        if not entry.source_id:
            errors.append("registry: entry missing source_id")
        # label presence and validity
        if not entry.label:
            errors.append(f"registry: {entry.source_id!r} missing label")
        elif entry.label not in VALID_LABELS:
            errors.append(
                f"registry: {entry.source_id!r} label {entry.label!r} not in taxonomy "
                f"{sorted(VALID_LABELS)}"
            )

    # 2. Validate manifest source_ids
    manifests_result = validate_manifests(manifests_path)
    if not manifests_result.is_valid:
        for err in manifests_result.errors:
            errors.append(f"manifest: {err}")
    else:
        for manifest in manifests_result.entries:
            if not manifest.source_id:
                errors.append("manifest: entry missing source_id")
            elif manifest.source_id not in registry_ids:
                errors.append(f"manifest: source_id {manifest.source_id!r} is not in the registry")

    # 3. Validate gap source_ids
    gaps_result = validate_gaps(gaps_path)
    if not gaps_result.is_valid:
        for err in gaps_result.errors:
            errors.append(f"gap: {err}")
    else:
        for gap in gaps_result.entries:
            if not gap.source_id:
                errors.append("gap: entry missing source_id")
            elif gap.source_id not in registry_ids:
                errors.append(f"gap: source_id {gap.source_id!r} is not in the registry")

    return errors


def main() -> int:
    """Entry point for the labels gate."""
    root = _repo_root()
    errors = run_labels_gate(root)
    if errors:
        for err in errors:
            print(f"labels: FAIL {err}")
        return 1
    print("labels: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

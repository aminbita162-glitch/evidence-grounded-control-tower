"""Data gate — validates the Source Registry, manifests and gap register (P02-T05).

Checks:
- Registry (data/registry/sources.yaml) is valid per schemas/source.json.
- BASELINE.json matches the registry (no changed entry without a baseline update).
- Manifests (data/manifests/manifests.yaml) are valid per schemas/license-manifest.json.
- Every source in the registry has a manifest entry.
- Every UNVERIFIED source with a V-item has a gap entry in gaps.yaml.
- Gap entries are valid per schemas/gap.json.
- No tracked file under data/ contains protected copyright content (Part 3 §3.12).

The gate also checks the ``license`` dependency: a dependency missing from the
registry (kind DEPENDENCY) fails this gate.

Invokable as ``python -m tools.gate.gates.data``.

Spec: Part 3 §3.12; P02-T03; P02-T05.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from data.manifests import check_third_party_content, validate_gaps, validate_manifests
from data.registry import check_baseline, validate_registry

__all__ = ["DataGateError", "run_data_gate", "main"]


class DataGateError(Exception):
    """A data gate error."""


def _repo_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def run_data_gate(root: Path) -> list[str]:
    """Run all data gate checks for *root* and return error messages.

    Args:
        root: Repository root path.

    Returns:
        List of error messages (empty = all checks passed).
    """
    errors: list[str] = []

    registry_path = root / "data" / "registry" / "sources.yaml"
    baseline_path = root / "data" / "registry" / "BASELINE.json"
    gaps_path = root / "data" / "registry" / "gaps.yaml"
    manifests_path = root / "data" / "manifests" / "manifests.yaml"

    # 1. Validate the registry
    registry_result = validate_registry(registry_path)
    if not registry_result.is_valid:
        for err in registry_result.errors:
            errors.append(f"registry: {err}")
        return errors  # stop early; other checks need a valid registry

    # 2. Check baseline
    baseline_errors = check_baseline(registry_path, baseline_path)
    for err in baseline_errors:
        errors.append(f"baseline: {err}")

    # 3. Validate manifests
    manifests_result = validate_manifests(manifests_path)
    if not manifests_result.is_valid:
        for err in manifests_result.errors:
            errors.append(f"manifest: {err}")

    # 4. Validate gap register
    gaps_result = validate_gaps(gaps_path)
    if not gaps_result.is_valid:
        for err in gaps_result.errors:
            errors.append(f"gap: {err}")

    # 5. Coverage: every source must have a manifest
    registry_ids = {e.source_id for e in registry_result.entries}
    manifest_ids: set[str] = (
        {m.source_id for m in manifests_result.entries} if manifests_result.is_valid else set()
    )
    uncovered = registry_ids - manifest_ids
    for sid in sorted(uncovered):
        errors.append(f"coverage: source {sid!r} has no manifest entry")

    # 6. Every UNVERIFIED source with a non-none V-item must have a gap entry
    gap_ids: set[str] = (
        {g.source_id for g in gaps_result.entries} if gaps_result.is_valid else set()
    )
    for entry in registry_result.entries:
        needs_gap = entry.status == "UNVERIFIED" and entry.v_item and entry.v_item != "none"
        if needs_gap and entry.source_id not in gap_ids:
            errors.append(
                f"gap-coverage: UNVERIFIED source {entry.source_id!r} with "
                f"v_item={entry.v_item!r} has no gap entry"
            )

    # 7. Third-party copyright content check
    copyright_errors = check_third_party_content(root)
    for err in copyright_errors:
        errors.append(f"copyright: {err}")

    return errors


def main() -> int:
    """Entry point for the data gate."""
    root = _repo_root()
    errors = run_data_gate(root)
    if errors:
        for err in errors:
            print(f"data: FAIL {err}")
        return 1
    print("data: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

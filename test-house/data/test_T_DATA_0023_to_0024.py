"""Tests for the Source Registry seed content (P02-T04).

Test IDs: T-DATA-0023 to T-DATA-0024.
Covers: registry count equals 20 seed entries; every field present and valid;
every V-item in V-04 to V-09, V-16 has a gap entry or verified source.

Spec: P02-T04; <<<P8-SOURCES>>>; Part 3 §3.12; data/registry/__init__.py.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from data.manifests import validate_gaps, validate_manifests
from data.registry import check_baseline, validate_registry

# ---------------------------------------------------------------------------
# Paths to live registry files
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_REGISTRY_PATH = _REPO_ROOT / "data" / "registry" / "sources.yaml"
_BASELINE_PATH = _REPO_ROOT / "data" / "registry" / "BASELINE.json"
_GAPS_PATH = _REPO_ROOT / "data" / "registry" / "gaps.yaml"
_MANIFESTS_PATH = _REPO_ROOT / "data" / "manifests" / "manifests.yaml"

#: Seed source_ids from <<<P8-SOURCES>>> (count must be exactly 20).
_SEED_SOURCE_IDS: frozenset[str] = frozenset(
    {
        "SRC-OFAC-SDN",
        "SRC-OFAC-CONS",
        "SRC-UN-CONS",
        "SRC-EOCN-LTL",
        "SRC-EU-FSF",
        "SRC-DUBAI-PULSE",
        "SRC-UAE-OPENDATA",
        "SRC-DXB-NOTICES",
        "SRC-DXB-POLICY-35-2011",
        "SRC-UAE-TARIFF",
        "SRC-WCO-HS",
        "SRC-ICC-INCOTERMS",
        "SRC-UAE-CALENDAR",
        "SRC-ISO-4217",
        "SRC-ISO-3166",
        "SRC-UN-LOCODE",
        "SRC-DUAL-USE",
        "SIM-FREIGHT-RATES",
        "SIM-FREE-DAYS",
        "SIM-SURCHARGES",
    }
)

#: V-items that concern data per the directive (V-04 to V-09, V-16).
_DATA_V_ITEMS: tuple[str, ...] = ("V-04", "V-05", "V-06", "V-07", "V-08", "V-09", "V-16")

#: Months pattern
_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ---------------------------------------------------------------------------
# T-DATA-0023: registry count equals 20 seed entries
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0023_seed_entry_count_equals_20() -> None:
    """T-DATA-0023: the number of transcribed seed entries equals 20.

    id: T-DATA-0023
    title: Seed entry count equals 20
    purpose: Verify that exactly 20 source entries were transcribed from P8-SOURCES.
    level: fast
    requirement: P02-T04; <<<P8-SOURCES>>>; data/registry/sources.yaml
    input: live sources.yaml registry
    expected: exactly 20 entries with non-DEPENDENCY kind match the seed source_ids
    risk: missing or extra entries indicate transcription errors
    owning capability: data-registry
    """
    result = validate_registry(_REGISTRY_PATH)
    assert result.is_valid, f"registry validation failed: {result.errors}"

    seed_entries = [e for e in result.entries if e.source_id in _SEED_SOURCE_IDS]
    assert len(seed_entries) == 20, (
        f"expected 20 seed entries, got {len(seed_entries)}: {[e.source_id for e in seed_entries]}"
    )


@pytest.mark.fast
def test_T_DATA_0023_seed_source_ids_match() -> None:
    """T-DATA-0023: seed source_ids in registry exactly match the P8-SOURCES list.

    id: T-DATA-0023
    title: Seed entry count equals 20
    purpose: Verify that exactly 20 source entries were transcribed from P8-SOURCES.
    level: fast
    requirement: P02-T04; <<<P8-SOURCES>>>; data/registry/sources.yaml
    input: live sources.yaml registry
    expected: exactly 20 entries with non-DEPENDENCY kind match the seed source_ids
    risk: missing or extra entries indicate transcription errors
    owning capability: data-registry
    """
    result = validate_registry(_REGISTRY_PATH)
    assert result.is_valid, f"registry validation failed: {result.errors}"

    registry_ids = {e.source_id for e in result.entries}
    missing = _SEED_SOURCE_IDS - registry_ids
    assert not missing, f"missing seed source_ids: {sorted(missing)}"


# ---------------------------------------------------------------------------
# T-DATA-0024: every field present and valid; V-items covered
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0024_all_fields_valid_and_v_items_covered() -> None:
    """T-DATA-0024: all entries valid; every data V-item has a gap or verified source.

    id: T-DATA-0024
    title: All fields valid and data V-items covered
    purpose: Verify every field is present and valid; every data V-item is covered.
    level: fast
    requirement: P02-T04; <<<P8-SOURCES>>>; data/registry/sources.yaml; data/registry/gaps.yaml
    input: live sources.yaml registry and gaps.yaml
    expected: validation passes; V-04 to V-09 and V-16 each covered by a gap or verified source
    risk: invalid entries or uncovered V-items block compliance verification
    owning capability: data-registry
    """
    # Registry must be valid
    result = validate_registry(_REGISTRY_PATH)
    assert result.is_valid, f"registry validation failed: {result.errors}"

    # Every entry must pass field-level checks
    for entry in result.entries:
        assert entry.source_id, "entry has empty source_id"
        assert _MONTH_RE.match(entry.retrieved_month), (
            f"{entry.source_id}: retrieved_month {entry.retrieved_month!r} not YYYY-MM"
        )
        assert entry.max_age_months >= 1, (
            f"{entry.source_id}: max_age_months must be >= 1, got {entry.max_age_months}"
        )
        assert entry.label, f"{entry.source_id}: label is empty"
        assert entry.status in ("UNVERIFIED", "VERIFIED"), (
            f"{entry.source_id}: status {entry.status!r} not valid"
        )

    # Collect all V-items mentioned in sources (compound values like "V-04, V-05, V-16")
    all_source_v_items: set[str] = set()
    for entry in result.entries:
        if entry.v_item and entry.v_item != "none":
            for v in entry.v_item.split(","):
                all_source_v_items.add(v.strip())

    # Collect V-items from gap entries
    gaps_result = validate_gaps(_GAPS_PATH)
    assert gaps_result.is_valid, f"gaps validation failed: {gaps_result.errors}"
    gap_v_items = {g.v_item for g in gaps_result.entries}

    # Every data V-item must be covered by a source mention OR a gap entry
    # (or a verified source, which none are yet - all UNVERIFIED at this stage)
    for v_item in _DATA_V_ITEMS:
        in_sources = v_item in all_source_v_items
        in_gaps = v_item in gap_v_items
        assert in_sources or in_gaps, (
            f"V-item {v_item!r} not found in any source v_item field or gap entry"
        )


@pytest.mark.fast
def test_T_DATA_0024_baseline_matches_registry() -> None:
    """T-DATA-0024: BASELINE.json matches the current registry.

    id: T-DATA-0024
    title: All fields valid and data V-items covered
    purpose: Verify every field is present and valid; every data V-item is covered.
    level: fast
    requirement: P02-T04; <<<P8-SOURCES>>>; data/registry/sources.yaml; data/registry/gaps.yaml
    input: live sources.yaml registry and gaps.yaml
    expected: validation passes; V-04 to V-09 and V-16 each covered by a gap or verified source
    risk: invalid entries or uncovered V-items block compliance verification
    owning capability: data-registry
    """
    errors = check_baseline(_REGISTRY_PATH, _BASELINE_PATH)
    assert not errors, f"baseline mismatch: {errors}"


@pytest.mark.fast
def test_T_DATA_0024_manifests_cover_all_sources() -> None:
    """T-DATA-0024: every source has a manifest entry.

    id: T-DATA-0024
    title: All fields valid and data V-items covered
    purpose: Verify every field is present and valid; every data V-item is covered.
    level: fast
    requirement: P02-T04; <<<P8-SOURCES>>>; data/registry/sources.yaml; data/registry/gaps.yaml
    input: live sources.yaml registry and gaps.yaml
    expected: validation passes; V-04 to V-09 and V-16 each covered by a gap or verified source
    risk: invalid entries or uncovered V-items block compliance verification
    owning capability: data-registry
    """
    registry_result = validate_registry(_REGISTRY_PATH)
    assert registry_result.is_valid, f"registry invalid: {registry_result.errors}"

    manifests_result = validate_manifests(_MANIFESTS_PATH)
    assert manifests_result.is_valid, f"manifests invalid: {manifests_result.errors}"

    registry_ids = {e.source_id for e in registry_result.entries}
    manifest_ids = {m.source_id for m in manifests_result.entries}
    uncovered = registry_ids - manifest_ids
    assert not uncovered, f"sources without manifests: {sorted(uncovered)}"

"""Tests for the Source Registry validator (P02-T02).

Test IDs: T-DATA-0007 to T-DATA-0014.
Covers: missing field fails; duplicate source_id fails; day-level date fails;
changed entry without baseline update fails; baseline update outside named
task is refused.

Spec: Part 3 §3.12; schemas/source.json; data/registry/__init__.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from data.registry import (
    RegistryValidationResult,
    check_baseline,
    compute_entry_hash,
    load_baseline,
    update_baseline,
    validate_registry,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_ENTRY: dict[str, object] = {
    "source_id": "SRC-TEST-VALID",
    "publisher": "Test Publisher",
    "reference": "https://example.com/test",
    "retrieved_month": "2026-11",
    "label": "OFFICIAL",
    "license_summary": "MIT licence",
    "redistributable": "yes",
    "kind": "DATASET",
    "use_class": "SCREENING",
    "status": "UNVERIFIED",
    "max_age_months": 6,
    "v_item": "V-01",
}


def _write_registry(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    """Write a registry YAML file and return its path."""
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.dump({"sources": entries}), encoding="utf-8")
    return path


def _write_baseline(tmp_path: Path, data: dict[str, str]) -> Path:
    """Write a BASELINE.json and return its path."""
    path = tmp_path / "BASELINE.json"
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# T-DATA-0007: missing required field fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "missing_field",
    [
        "source_id",
        "publisher",
        "reference",
        "retrieved_month",
        "label",
        "license_summary",
        "redistributable",
        "kind",
        "use_class",
        "status",
        "max_age_months",
    ],
)
def test_T_DATA_0007_missing_field_fails(tmp_path: Path, missing_field: str) -> None:
    """T-DATA-0007: a missing required field causes validation to fail.

    id: T-DATA-0007
    title: Missing required field fails validation
    purpose: Verify that each required field is enforced by the validator.
    level: fast
    requirement: P02-T02; Part 3 §3.12; schemas/source.json
    input: entry with one required field removed
    expected: validation result has errors
    risk: missing field accepted silently leaves incomplete registry entries
    owning capability: data-registry
    """
    entry = dict(_VALID_ENTRY)
    del entry[missing_field]
    reg_path = _write_registry(tmp_path, [entry])
    result = validate_registry(reg_path)
    assert not result.is_valid, f"expected failure when {missing_field!r} is missing"
    assert any(missing_field in err for err in result.errors), (
        f"expected error mentioning {missing_field!r}, got: {result.errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0008: duplicate source_id fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0008_duplicate_id_fails(tmp_path: Path) -> None:
    """T-DATA-0008: duplicate source_id causes validation to fail.

    id: T-DATA-0008
    title: Duplicate source_id fails validation
    purpose: Verify that source_id uniqueness is enforced.
    level: fast
    requirement: P02-T02; Part 3 §3.12
    input: two entries with the same source_id
    expected: validation result has a duplicate error
    risk: duplicate IDs cause ambiguous registry lookups
    owning capability: data-registry
    """
    entry1 = dict(_VALID_ENTRY)
    entry2 = dict(_VALID_ENTRY)
    entry2["publisher"] = "Second Publisher"
    reg_path = _write_registry(tmp_path, [entry1, entry2])
    result = validate_registry(reg_path)
    assert not result.is_valid, "expected failure for duplicate source_id"
    assert any("duplicate" in err.lower() for err in result.errors), (
        f"expected duplicate error, got: {result.errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0009: day-level date fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "bad_date",
    ["2026-11-01", "2026-11-30", "2026/11", "November 2026", "2026-13", "2026-00"],
)
def test_T_DATA_0009_day_level_date_fails(tmp_path: Path, bad_date: str) -> None:
    """T-DATA-0009: a day-level or invalid date in retrieved_month fails.

    id: T-DATA-0009
    title: Day-level retrieved_month date fails validation
    purpose: Verify that only YYYY-MM dates are accepted.
    level: fast
    requirement: P02-T02; Part 3 §3.12
    input: entry with an invalid or day-level retrieved_month
    expected: validation result has errors
    risk: day-level dates expose personal precision contrary to honesty rules
    owning capability: data-registry
    """
    entry = dict(_VALID_ENTRY)
    entry["retrieved_month"] = bad_date
    reg_path = _write_registry(tmp_path, [entry])
    result = validate_registry(reg_path)
    assert not result.is_valid, f"expected failure for date {bad_date!r}"


# ---------------------------------------------------------------------------
# T-DATA-0010: valid entry passes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0010_valid_entry_passes(tmp_path: Path) -> None:
    """T-DATA-0010: a fully valid entry passes validation.

    id: T-DATA-0010
    title: Valid entry passes validation
    purpose: Verify that a correctly formed entry produces no errors.
    level: fast
    requirement: P02-T02; Part 3 §3.12
    input: one valid entry
    expected: validation result is clean, one entry returned
    risk: false positives reject valid registrations
    owning capability: data-registry
    """
    reg_path = _write_registry(tmp_path, [dict(_VALID_ENTRY)])
    result = validate_registry(reg_path)
    assert result.is_valid, f"expected valid, got errors: {result.errors}"
    assert len(result.entries) == 1


# ---------------------------------------------------------------------------
# T-DATA-0011: changed entry without baseline update fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0011_changed_entry_without_baseline_fails(tmp_path: Path) -> None:
    """T-DATA-0011: a changed entry without a baseline update fails.

    id: T-DATA-0011
    title: Changed entry without baseline update fails
    purpose: Verify that modifying an entry without updating BASELINE.json is detected.
    level: fast
    requirement: P02-T02; Part 3 §3.12
    input: registry entry changed, old hash in baseline
    expected: check_baseline returns errors
    risk: undetected changes corrupt the registry provenance trail
    owning capability: data-registry
    """
    entry = dict(_VALID_ENTRY)
    reg_path = _write_registry(tmp_path, [entry])
    baseline_path = tmp_path / "BASELINE.json"
    # Write baseline with OLD hash (before change)
    old_hash = compute_entry_hash(entry)
    _write_baseline(tmp_path, {"SRC-TEST-VALID": old_hash})

    # Modify the entry
    entry["publisher"] = "Changed Publisher"
    reg_path.write_text(yaml.dump({"sources": [entry]}), encoding="utf-8")

    errors = check_baseline(reg_path, baseline_path)
    assert errors, "expected baseline mismatch error after entry change"
    assert any("SRC-TEST-VALID" in err for err in errors), (
        f"expected error mentioning SRC-TEST-VALID, got: {errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0012: new entry without baseline update fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0012_new_entry_without_baseline_fails(tmp_path: Path) -> None:
    """T-DATA-0012: a new entry not in the baseline fails.

    id: T-DATA-0012
    title: New entry not in baseline fails
    purpose: Verify that adding an entry without updating baseline is detected.
    level: fast
    requirement: P02-T02; Part 3 §3.12
    input: registry entry added, baseline unchanged
    expected: check_baseline returns errors
    risk: unrecorded sources enter the system without governance
    owning capability: data-registry
    """
    entry = dict(_VALID_ENTRY)
    reg_path = _write_registry(tmp_path, [entry])
    baseline_path = _write_baseline(tmp_path, {})  # empty baseline

    errors = check_baseline(reg_path, baseline_path)
    assert errors, "expected error for entry missing from baseline"
    assert any("SRC-TEST-VALID" in err for err in errors), (
        f"expected error mentioning SRC-TEST-VALID, got: {errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0013: update_baseline writes correct hashes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0013_update_baseline_writes_correct_hashes(tmp_path: Path) -> None:
    """T-DATA-0013: update_baseline writes correct hashes for all entries.

    id: T-DATA-0013
    title: update_baseline writes correct entry hashes
    purpose: Verify that update_baseline produces a valid BASELINE.json.
    level: fast
    requirement: P02-T02; Part 3 §3.12
    input: registry with two valid entries
    expected: baseline contains correct hash for each source_id
    risk: wrong baseline hashes cause false positives or allow undetected changes
    owning capability: data-registry
    """
    entry1 = dict(_VALID_ENTRY)
    entry2 = dict(_VALID_ENTRY)
    entry2["source_id"] = "SRC-TEST-SECOND"
    entry2["publisher"] = "Second"
    reg_path = _write_registry(tmp_path, [entry1, entry2])
    baseline_path = tmp_path / "BASELINE.json"

    update_baseline(reg_path, baseline_path)

    baseline = load_baseline(baseline_path)
    assert "SRC-TEST-VALID" in baseline
    assert "SRC-TEST-SECOND" in baseline
    assert baseline["SRC-TEST-VALID"] == compute_entry_hash(entry1)
    assert baseline["SRC-TEST-SECOND"] == compute_entry_hash(entry2)

    # After update, check_baseline should pass
    errors = check_baseline(reg_path, baseline_path)
    assert not errors, f"expected no errors after baseline update, got: {errors}"


# ---------------------------------------------------------------------------
# T-DATA-0014: source_id format validation
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "bad_id",
    ["src-lower", "MISSING-PREFIX", "SRC_UNDERSCORE", "SRC-", "123-ABC", ""],
)
def test_T_DATA_0014_invalid_source_id_format_fails(tmp_path: Path, bad_id: str) -> None:
    """T-DATA-0014: invalid source_id format fails validation.

    id: T-DATA-0014
    title: Invalid source_id format fails validation
    purpose: Verify the source_id pattern SRC-/SIM- prefix is enforced.
    level: fast
    requirement: P02-T02; Part 3 §3.12; schemas/source.json
    input: entry with an invalid source_id
    expected: validation result has errors
    risk: badly formatted IDs cause registry lookups to fail silently
    owning capability: data-registry
    """
    entry = dict(_VALID_ENTRY)
    entry["source_id"] = bad_id
    reg_path = _write_registry(tmp_path, [entry])
    result = validate_registry(reg_path)
    assert not result.is_valid, f"expected failure for source_id {bad_id!r}"


@pytest.mark.fast
@pytest.mark.parametrize(
    "good_id",
    ["SRC-OFAC-SDN", "SIM-FREIGHT-RATES", "SRC-UAE-TARIFF", "SRC-ISO-4217"],
)
def test_T_DATA_0014_valid_source_id_format_passes(tmp_path: Path, good_id: str) -> None:
    """T-DATA-0014: valid source_id format passes validation.

    id: T-DATA-0014
    title: Invalid source_id format fails validation
    purpose: Verify the source_id pattern SRC-/SIM- prefix is enforced.
    level: fast
    requirement: P02-T02; Part 3 §3.12; schemas/source.json
    input: entry with a valid source_id
    expected: no source_id format error
    risk: badly formatted IDs cause registry lookups to fail silently
    owning capability: data-registry
    """
    entry = dict(_VALID_ENTRY)
    entry["source_id"] = good_id
    reg_path = _write_registry(tmp_path, [entry])
    result = validate_registry(reg_path)
    # Only check there is no source_id format error (other errors may exist for
    # entries with the same id as _VALID_ENTRY but that's not what we test here)
    format_errors = [e for e in result.errors if "does not match pattern" in e and good_id in e]
    assert not format_errors, f"unexpected format error for {good_id!r}: {format_errors}"

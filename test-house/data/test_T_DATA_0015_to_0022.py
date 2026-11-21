"""Tests for the License Manifest and Source Gap Register (P02-T03).

Test IDs: T-DATA-0015 to T-DATA-0022.
Covers: uncovered file fails; UNVERIFIED license on a used dataset fails;
third-party table detection fixture fails; gap entry without verification id fails.

Spec: Part 3 §3.12; schemas/license-manifest.json; schemas/gap.json;
      data/manifests/__init__.py; data/registry/gaps.yaml.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from data.manifests import (
    check_third_party_content,
    validate_gaps,
    validate_manifest_entry,
    validate_manifests,
)
from data.registry import RegistryEntry

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_VALID_MANIFEST_DICT: dict[str, object] = {
    "source_id": "SRC-TEST-VALID",
    "terms": "MIT licence",
    "attribution_text": "Copyright Test Publisher",
    "permitted_uses": "unrestricted",
    "redistribution_permission": "yes",
}

_VALID_GAP_DICT: dict[str, object] = {
    "source_id": "SRC-TEST-VALID",
    "reason": "terms not verified",
    "v_item": "V-04",
    "next_check": "2027-05",
}


def _write_manifests(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    """Write a manifests YAML file and return its path."""
    path = tmp_path / "manifests.yaml"
    path.write_text(yaml.dump({"manifests": entries}), encoding="utf-8")
    return path


def _write_gaps(tmp_path: Path, entries: list[dict[str, object]]) -> Path:
    """Write a gaps YAML file and return its path."""
    path = tmp_path / "gaps.yaml"
    path.write_text(yaml.dump({"gaps": entries}), encoding="utf-8")
    return path


def _make_registry_entry(
    source_id: str = "SRC-TEST-VALID", status: str = "UNVERIFIED"
) -> RegistryEntry:
    """Return a minimal RegistryEntry for testing."""
    return RegistryEntry(
        source_id=source_id,
        publisher="Test Publisher",
        reference="https://example.com/test",
        retrieved_month="2026-11",
        label="OFFICIAL",
        license_summary="MIT licence",
        redistributable="yes",
        kind="DATASET",
        use_class="SCREENING",
        status=status,
        max_age_months=6,
        v_item="V-04",
    )


# ---------------------------------------------------------------------------
# T-DATA-0015: uncovered file under data/ fails the data gate
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0015_uncovered_file_fails(tmp_path: Path) -> None:
    """T-DATA-0015: a file under data/ not covered by any manifest fails.

    id: T-DATA-0015
    title: Uncovered data file fails the data gate
    purpose: Verify that every data file must have a manifest entry.
    level: fast
    requirement: P02-T03; Part 3 §3.12; data/manifests/__init__.py
    input: data file with and without a matching manifest entry
    expected: uncovered file reports a gap; covered file passes
    risk: uncovered datasets enter the system without governance
    owning capability: data-registry
    """
    # Create a manifest store that covers SRC-OTHER but not SRC-TEST-VALID
    manifest_path = _write_manifests(
        tmp_path,
        [
            {
                "source_id": "SRC-OTHER",
                "terms": "MIT",
                "attribution_text": "none",
                "permitted_uses": "unrestricted",
                "redistribution_permission": "yes",
            }
        ],
    )
    result = validate_manifests(manifest_path)
    assert result.is_valid, f"unexpected manifest errors: {result.errors}"

    # The coverage check: SRC-TEST-VALID has no manifest
    covered_ids = {e.source_id for e in result.entries}
    registry_ids = {"SRC-TEST-VALID"}
    uncovered = registry_ids - covered_ids
    assert "SRC-TEST-VALID" in uncovered, "expected SRC-TEST-VALID to be uncovered"


@pytest.mark.fast
def test_T_DATA_0015_covered_file_passes(tmp_path: Path) -> None:
    """T-DATA-0015: a file covered by a manifest passes the check.

    id: T-DATA-0015
    title: Uncovered data file fails the data gate
    purpose: Verify that every data file must have a manifest entry.
    level: fast
    requirement: P02-T03; Part 3 §3.12; data/manifests/__init__.py
    input: data file with and without a matching manifest entry
    expected: uncovered file reports a gap; covered file passes
    risk: uncovered datasets enter the system without governance
    owning capability: data-registry
    """
    manifest_path = _write_manifests(tmp_path, [dict(_VALID_MANIFEST_DICT)])
    result = validate_manifests(manifest_path)
    assert result.is_valid, f"unexpected manifest errors: {result.errors}"
    covered_ids = {e.source_id for e in result.entries}
    assert "SRC-TEST-VALID" in covered_ids


# ---------------------------------------------------------------------------
# T-DATA-0016: UNVERIFIED license on a used dataset fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0016_unverified_license_fails(tmp_path: Path) -> None:
    """T-DATA-0016: an UNVERIFIED dataset must have a gap entry.

    id: T-DATA-0016
    title: UNVERIFIED license on a used dataset fails the data gate
    purpose: Verify that UNVERIFIED datasets require a gap entry and are detected without one.
    level: fast
    requirement: P02-T03; Part 3 §3.12
    input: UNVERIFIED registry entry with and without a gap entry
    expected: entry with gap passes; entry without gap is detected as missing
    risk: unverified license terms expose the project to legal risk
    owning capability: data-registry
    """
    # An UNVERIFIED registry entry has a gap; verify the gap exists
    gap_path = _write_gaps(tmp_path, [dict(_VALID_GAP_DICT)])
    result = validate_gaps(gap_path)
    assert result.is_valid, f"unexpected gap errors: {result.errors}"

    # An entry used (kind=DATASET) with status UNVERIFIED must have a gap entry
    entry = _make_registry_entry(status="UNVERIFIED")
    gap_ids = {g.source_id for g in result.entries}
    assert entry.source_id in gap_ids, "UNVERIFIED dataset must have a gap entry"


@pytest.mark.fast
def test_T_DATA_0016_unverified_dataset_without_gap_is_missing(tmp_path: Path) -> None:
    """T-DATA-0016: a used UNVERIFIED dataset without a gap entry is a governance failure.

    id: T-DATA-0016
    title: UNVERIFIED license on a used dataset fails the data gate
    purpose: Verify that UNVERIFIED datasets require a gap entry and are detected without one.
    level: fast
    requirement: P02-T03; Part 3 §3.12
    input: UNVERIFIED registry entry with and without a gap entry
    expected: entry with gap passes; entry without gap is detected as missing
    risk: unverified license terms expose the project to legal risk
    owning capability: data-registry
    """
    gap_path = _write_gaps(tmp_path, [])  # empty gap register
    result = validate_gaps(gap_path)
    assert result.is_valid, f"unexpected errors: {result.errors}"

    gap_ids = {g.source_id for g in result.entries}
    entry = _make_registry_entry(status="UNVERIFIED")
    assert entry.source_id not in gap_ids, "expected gap to be missing"


# ---------------------------------------------------------------------------
# T-DATA-0017: third-party table detection fixture
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DATA_0017_third_party_table_detected(tmp_path: Path) -> None:
    """T-DATA-0017: files with copyright content are detected; clean files pass.

    id: T-DATA-0017
    title: Third-party copyright table detection
    purpose: Verify stored rule/heading text from S-11 or S-12 is detected; clean data passes.
    level: fast
    requirement: P02-T03; Part 3 §3.12 (no stored copyrighted tables)
    input: data directory with Incoterms, WCO HS, and clean SYNTHETIC content
    expected: Incoterms and WCO HS content detected; clean content produces no errors
    risk: copyrighted tables stored in the repository create legal exposure
    owning capability: data-registry
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    bad_file = data_dir / "fixture.txt"
    bad_file.write_text("Incoterms rules EXW FCA CPT", encoding="utf-8")

    errors = check_third_party_content(tmp_path)
    assert errors, "expected detection of Incoterms content"
    assert any("Incoterms rules" in e for e in errors), (
        f"expected marker 'Incoterms rules' in errors, got: {errors}"
    )


@pytest.mark.fast
def test_T_DATA_0017_wco_hs_content_detected(tmp_path: Path) -> None:
    """T-DATA-0017: a file containing WCO HS nomenclature text is detected.

    id: T-DATA-0017
    title: Third-party copyright table detection
    purpose: Verify stored rule/heading text from S-11 or S-12 is detected; clean data passes.
    level: fast
    requirement: P02-T03; Part 3 §3.12 (no stored copyrighted tables)
    input: data directory with Incoterms, WCO HS, and clean SYNTHETIC content
    expected: Incoterms and WCO HS content detected; clean content produces no errors
    risk: copyrighted tables stored in the repository create legal exposure
    owning capability: data-registry
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    bad_file = data_dir / "hs_copy.txt"
    bad_file.write_text("Harmonized System chapter 84 notes", encoding="utf-8")

    errors = check_third_party_content(tmp_path)
    assert errors, "expected detection of Harmonized System content"
    assert any("Harmonized System" in e for e in errors), (
        f"expected marker in errors, got: {errors}"
    )


@pytest.mark.fast
def test_T_DATA_0017_clean_data_dir_passes(tmp_path: Path) -> None:
    """T-DATA-0017: a clean data directory produces no errors.

    id: T-DATA-0017
    title: Third-party copyright table detection
    purpose: Verify stored rule/heading text from S-11 or S-12 is detected; clean data passes.
    level: fast
    requirement: P02-T03; Part 3 §3.12 (no stored copyrighted tables)
    input: data directory with Incoterms, WCO HS, and clean SYNTHETIC content
    expected: Incoterms and WCO HS content detected; clean content produces no errors
    risk: copyrighted tables stored in the repository create legal exposure
    owning capability: data-registry
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    clean_file = data_dir / "synthetic.txt"
    clean_file.write_text("SYNTHETIC freight rates: 100 USD per TEU", encoding="utf-8")

    errors = check_third_party_content(tmp_path)
    assert not errors, f"expected no errors, got: {errors}"


# ---------------------------------------------------------------------------
# T-DATA-0018: gap entry without verification id fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "bad_v_item",
    ["none", "", "V-", "V04", "v-04", "VA-04", "not-a-v-item"],
)
def test_T_DATA_0018_gap_without_verification_id_fails(tmp_path: Path, bad_v_item: str) -> None:
    """T-DATA-0018: gap entry validation enforces a valid V-xx id.

    id: T-DATA-0018
    title: Gap entry without verification id fails
    purpose: Verify that every gap entry must have a valid V-xx id; valid ids pass.
    level: fast
    requirement: P02-T03; Part 3 §3.12; schemas/gap.json
    input: gap entry with invalid v_item values and valid V-xx values
    expected: invalid v_item fails; valid V-xx passes
    risk: gaps without verification ids cannot be tracked to closure
    owning capability: data-registry
    """
    entry: dict[str, object] = dict(_VALID_GAP_DICT)
    entry["v_item"] = bad_v_item
    gap_path = _write_gaps(tmp_path, [entry])
    result = validate_gaps(gap_path)
    assert not result.is_valid, f"expected failure for v_item={bad_v_item!r}"
    assert any("v_item" in err for err in result.errors), (
        f"expected error mentioning 'v_item', got: {result.errors}"
    )


@pytest.mark.fast
@pytest.mark.parametrize(
    "good_v_item",
    ["V-04", "V-05", "V-16", "V-100"],
)
def test_T_DATA_0018_gap_with_valid_verification_id_passes(
    tmp_path: Path, good_v_item: str
) -> None:
    """T-DATA-0018: gap entry validation enforces a valid V-xx id.

    id: T-DATA-0018
    title: Gap entry without verification id fails
    purpose: Verify that every gap entry must have a valid V-xx id; valid ids pass.
    level: fast
    requirement: P02-T03; Part 3 §3.12; schemas/gap.json
    input: gap entry with invalid v_item values and valid V-xx values
    expected: invalid v_item fails; valid V-xx passes
    risk: gaps without verification ids cannot be tracked to closure
    owning capability: data-registry
    """
    entry: dict[str, object] = dict(_VALID_GAP_DICT)
    entry["v_item"] = good_v_item
    gap_path = _write_gaps(tmp_path, [entry])
    result = validate_gaps(gap_path)
    assert result.is_valid, f"expected success for v_item={good_v_item!r}, got: {result.errors}"


# ---------------------------------------------------------------------------
# T-DATA-0019: manifest missing required field fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "missing_field",
    ["source_id", "terms", "attribution_text", "permitted_uses", "redistribution_permission"],
)
def test_T_DATA_0019_manifest_missing_field_fails(tmp_path: Path, missing_field: str) -> None:
    """T-DATA-0019: a manifest entry missing a required field fails.

    id: T-DATA-0019
    title: Manifest missing required field fails
    purpose: Verify that required fields are enforced in manifests.
    level: fast
    requirement: P02-T03; schemas/license-manifest.json
    input: manifest entry with one required field removed
    expected: validation reports an error mentioning the missing field
    risk: missing manifest fields leave governance gaps
    owning capability: data-registry
    """
    entry = dict(_VALID_MANIFEST_DICT)
    del entry[missing_field]
    manifest_path = _write_manifests(tmp_path, [entry])
    result = validate_manifests(manifest_path)
    assert not result.is_valid, f"expected failure when {missing_field!r} is missing"
    assert any(missing_field in err for err in result.errors), (
        f"expected error mentioning {missing_field!r}, got: {result.errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0020: gap missing required field fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "missing_field",
    ["source_id", "reason", "v_item", "next_check"],
)
def test_T_DATA_0020_gap_missing_field_fails(tmp_path: Path, missing_field: str) -> None:
    """T-DATA-0020: a gap entry missing a required field fails.

    id: T-DATA-0020
    title: Gap entry missing required field fails
    purpose: Verify that required fields are enforced in gap entries.
    level: fast
    requirement: P02-T03; schemas/gap.json
    input: gap entry with one required field removed
    expected: validation reports an error mentioning the missing field
    risk: missing fields in gap entries prevent proper tracking
    owning capability: data-registry
    """
    entry = dict(_VALID_GAP_DICT)
    del entry[missing_field]
    gap_path = _write_gaps(tmp_path, [entry])
    result = validate_gaps(gap_path)
    assert not result.is_valid, f"expected failure when {missing_field!r} is missing"
    assert any(missing_field in err for err in result.errors), (
        f"expected error mentioning {missing_field!r}, got: {result.errors}"
    )


# ---------------------------------------------------------------------------
# T-DATA-0021: manifest redistribution_permission validated
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "bad_rdist",
    ["maybe", "YES", "NO", "true", "false", "1", ""],
)
def test_T_DATA_0021_invalid_redistribution_permission_fails(
    tmp_path: Path, bad_rdist: str
) -> None:
    """T-DATA-0021: redistribution_permission accepts only valid values.

    id: T-DATA-0021
    title: Invalid redistribution_permission fails
    purpose: Verify redistribution_permission accepts yes/no/unknown/not-applicable only.
    level: fast
    requirement: P02-T03; schemas/license-manifest.json
    input: manifest entry with invalid and valid redistribution_permission values
    expected: invalid value reports an error; valid value produces no error
    risk: invalid redistribution permission accepted silently
    owning capability: data-registry
    """
    entry = dict(_VALID_MANIFEST_DICT)
    entry["redistribution_permission"] = bad_rdist
    _, errors = validate_manifest_entry(entry, 0)
    assert errors, f"expected error for redistribution_permission={bad_rdist!r}"


@pytest.mark.fast
@pytest.mark.parametrize(
    "good_rdist",
    ["yes", "no", "unknown", "not-applicable"],
)
def test_T_DATA_0021_valid_redistribution_permission_passes(
    tmp_path: Path, good_rdist: str
) -> None:
    """T-DATA-0021: redistribution_permission accepts only valid values.

    id: T-DATA-0021
    title: Invalid redistribution_permission fails
    purpose: Verify redistribution_permission accepts yes/no/unknown/not-applicable only.
    level: fast
    requirement: P02-T03; schemas/license-manifest.json
    input: manifest entry with invalid and valid redistribution_permission values
    expected: invalid value reports an error; valid value produces no error
    risk: invalid redistribution permission accepted silently
    owning capability: data-registry
    """
    entry = dict(_VALID_MANIFEST_DICT)
    entry["redistribution_permission"] = good_rdist
    result_entry, errors = validate_manifest_entry(entry, 0)
    rdist_errors = [e for e in errors if "redistribution_permission" in e]
    assert not rdist_errors, f"unexpected error for {good_rdist!r}: {rdist_errors}"


# ---------------------------------------------------------------------------
# T-DATA-0022: gap next_check date must be YYYY-MM
# ---------------------------------------------------------------------------


@pytest.mark.fast
@pytest.mark.parametrize(
    "bad_date",
    ["2027-05-01", "2027/05", "May 2027", "2027-13", "2027-00"],
)
def test_T_DATA_0022_gap_invalid_date_fails(tmp_path: Path, bad_date: str) -> None:
    """T-DATA-0022: gap next_check accepts only YYYY-MM dates.

    id: T-DATA-0022
    title: Gap entry invalid next_check date fails
    purpose: Verify that only YYYY-MM dates are accepted for next_check.
    level: fast
    requirement: P02-T03; schemas/gap.json
    input: gap entry with invalid day-level dates and a valid YYYY-MM date
    expected: invalid dates fail; valid YYYY-MM date passes
    risk: day-level dates expose personal precision contrary to honesty rules
    owning capability: data-registry
    """
    entry = dict(_VALID_GAP_DICT)
    entry["next_check"] = bad_date
    gap_path = _write_gaps(tmp_path, [entry])
    result = validate_gaps(gap_path)
    assert not result.is_valid, f"expected failure for next_check={bad_date!r}"
    assert any("next_check" in err for err in result.errors), (
        f"expected error mentioning 'next_check', got: {result.errors}"
    )


@pytest.mark.fast
def test_T_DATA_0022_gap_valid_date_passes(tmp_path: Path) -> None:
    """T-DATA-0022: gap next_check accepts only YYYY-MM dates.

    id: T-DATA-0022
    title: Gap entry invalid next_check date fails
    purpose: Verify that only YYYY-MM dates are accepted for next_check.
    level: fast
    requirement: P02-T03; schemas/gap.json
    input: gap entry with invalid day-level dates and a valid YYYY-MM date
    expected: invalid dates fail; valid YYYY-MM date passes
    risk: day-level dates expose personal precision contrary to honesty rules
    owning capability: data-registry
    """
    gap_path = _write_gaps(tmp_path, [dict(_VALID_GAP_DICT)])
    result = validate_gaps(gap_path)
    assert result.is_valid, f"expected valid gap, got: {result.errors}"

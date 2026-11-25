"""Tests for pack validation and loading (P06-T02).

Test IDs: T-RUL-0015 to T-RUL-0026.
Covers: each invalidity class is rejected; overlapping windows without
precedence are rejected; a rule without citation or label is rejected;
a pack whose declared label is stronger than the weakest label among its
registered sources is rejected; a valid pack loads and its hash is stable.

Spec: Part 3 §3.6, §3.8; kernel/rules/validator.py; kernel/rules/loader.py.
"""

from __future__ import annotations

import pytest

from kernel.rules.loader import LoadedPack, load_pack
from kernel.rules.validator import ValidationError, validate_pack


def _valid_pack() -> dict[str, object]:
    """Return a minimal valid pack for testing."""
    return {
        "tenant_id": "tenant-a",
        "schema_version": 1,
        "pack_id": "test-pack",
        "version": "1.0.0",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-12-31T23:59:59Z",
        "jurisdiction": "AE",
        "languages": ["en"],
        "sources": ["src-1"],
        "declared_label": "DERIVED",
        "rules": [
            {
                "id": "rule-1",
                "version": "1.0.0",
                "condition": {
                    "type": "eq",
                    "left": {"type": "field", "name": "hs_code"},
                    "right": {"type": "string", "value": "0101.21"},
                },
                "outcome": "ALLOW",
                "reason_code": "RULE.001.MATCH",
                "citation_source_id": "src-1",
                "citation_locator": "page 42",
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_to": "2026-12-31T23:59:59Z",
                "label": "DERIVED",
            },
        ],
    }


# ---------------------------------------------------------------------------
# T-RUL-0015 — A pack missing a required manifest field is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0015
# title: Missing manifest field is rejected
# purpose: Verify that a pack missing a required manifest field fails.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack dict without 'jurisdiction'
# expected: validate_pack raises ValidationError with code PACK_MISSING_FIELD
# risk: invalid pack accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0015_missing_manifest_field() -> None:
    """A pack missing a required manifest field is rejected."""
    pack = _valid_pack()
    del pack["jurisdiction"]
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_MISSING_FIELD"


# ---------------------------------------------------------------------------
# T-RUL-0016 — An invalid window (valid_from > valid_to) is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0016
# title: Invalid window is rejected
# purpose: Verify that a pack with valid_from > valid_to is rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with valid_from after valid_to
# expected: validate_pack raises ValidationError with code PACK_INVALID_WINDOW
# risk: rules active outside their validity window
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0016_invalid_window() -> None:
    """An invalid window (valid_from > valid_to) is rejected."""
    pack = _valid_pack()
    pack["valid_from"] = "2026-12-31T23:59:59Z"
    pack["valid_to"] = "2026-01-01T00:00:00Z"
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_INVALID_WINDOW"


# ---------------------------------------------------------------------------
# T-RUL-0017 — A rule without a citation is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0017
# title: Rule without citation is rejected
# purpose: Verify that a rule missing citation_source_id is rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with a rule that has no citation_source_id
# expected: validate_pack raises ValidationError with code PACK_MISSING_FIELD
# risk: uncited rule accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0017_rule_without_citation() -> None:
    """A rule without a citation is rejected."""
    pack = _valid_pack()
    rules: list[object] = pack["rules"]  # type: ignore[assignment]
    rule0: dict[str, object] = rules[0]  # type: ignore[assignment]
    del rule0["citation_source_id"]
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_MISSING_FIELD"


# ---------------------------------------------------------------------------
# T-RUL-0018 — A rule without a label is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0018
# title: Rule without label is rejected
# purpose: Verify that a rule missing a label is rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.8
# input: a pack with a rule that has no label
# expected: validate_pack raises ValidationError with code PACK_MISSING_FIELD
# risk: unlabelled rule accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0018_rule_without_label() -> None:
    """A rule without a label is rejected."""
    pack = _valid_pack()
    rules: list[object] = pack["rules"]  # type: ignore[assignment]
    rule0: dict[str, object] = rules[0]  # type: ignore[assignment]
    del rule0["label"]
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_MISSING_FIELD"


# ---------------------------------------------------------------------------
# T-RUL-0019 — A declared label stronger than the weakest source is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0019
# title: Declared label ceiling violation is rejected
# purpose: Verify that a pack whose declared label is stronger than the
#          weakest source label is rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.8
# input: a pack with declared_label OFFICIAL but a source labelled SECONDARY
# expected: validate_pack raises ValidationError with code PACK_LABEL_CEILING
# risk: label inflation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0019_label_ceiling_violation() -> None:
    """A declared label stronger than the weakest source label is rejected."""
    pack = _valid_pack()
    pack["declared_label"] = "OFFICIAL"
    pack["sources"] = ["src-1", "src-2"]
    source_labels = {"src-1": "DERIVED", "src-2": "SECONDARY"}
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack, source_labels=source_labels)
    assert exc_info.value.code == "PACK_LABEL_CEILING"


# ---------------------------------------------------------------------------
# T-RUL-0020 — Overlapping rule windows without precedence are rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0020
# title: Overlapping windows without precedence rejected
# purpose: Verify that two rules with overlapping windows and no precedence
#          are rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with two rules that overlap in time without precedence
# expected: validate_pack raises ValidationError with code PACK_OVERLAP_NO_PRECEDENCE
# risk: ambiguous rule evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0020_overlapping_no_precedence() -> None:
    """Overlapping rule windows without precedence are rejected."""
    pack = _valid_pack()
    pack["rules"] = [
        {
            "id": "rule-1",
            "version": "1.0.0",
            "condition": {"type": "bool", "value": True},
            "outcome": "ALLOW",
            "reason_code": "R1",
            "citation_source_id": "src-1",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_to": "2026-06-30T23:59:59Z",
            "label": "DERIVED",
        },
        {
            "id": "rule-2",
            "version": "1.0.0",
            "condition": {"type": "bool", "value": True},
            "outcome": "HOLD",
            "reason_code": "R2",
            "citation_source_id": "src-1",
            "valid_from": "2026-06-01T00:00:00Z",
            "valid_to": "2026-12-31T23:59:59Z",
            "label": "DERIVED",
        },
    ]
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_OVERLAP_NO_PRECEDENCE"


# ---------------------------------------------------------------------------
# T-RUL-0021 — An invalid expression in a rule condition is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0021
# title: Invalid condition expression rejected
# purpose: Verify that a rule with a forbidden construct in its condition
#          is rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with a rule condition using a forbidden construct
# expected: validate_pack raises ValidationError with code PACK_INVALID_CONDITION
# risk: non-deterministic rule evaluation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0021_invalid_condition() -> None:
    """A rule with an invalid expression in its condition is rejected."""
    pack = _valid_pack()
    rules: list[object] = pack["rules"]  # type: ignore[assignment]
    rule0: dict[str, object] = rules[0]  # type: ignore[assignment]
    rule0["condition"] = {"type": "while"}
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_INVALID_CONDITION"


# ---------------------------------------------------------------------------
# T-RUL-0022 — An invalid outcome is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0022
# title: Invalid outcome is rejected
# purpose: Verify that a rule with an outcome not in the allowed set is
#          rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with a rule outcome of 'MAYBE'
# expected: validate_pack raises ValidationError with code PACK_INVALID_OUTCOME
# risk: unexpected decision value
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0022_invalid_outcome() -> None:
    """A rule with an invalid outcome is rejected."""
    pack = _valid_pack()
    pack["rules"][0]["outcome"] = "MAYBE"  # type: ignore[index]
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_INVALID_OUTCOME"


# ---------------------------------------------------------------------------
# T-RUL-0023 — A valid pack loads and its hash is stable
# ---------------------------------------------------------------------------
# id: T-RUL-0023
# title: Valid pack loads with stable hash
# purpose: Verify that a valid pack loads and produces a stable hash.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a valid pack dict
# expected: load_pack returns a LoadedPack with a deterministic hash
# risk: non-deterministic pack hash
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0023_valid_pack_loads_stable_hash() -> None:
    """A valid pack loads and its hash is stable across loads."""
    pack = _valid_pack()
    loaded1 = load_pack(pack)
    loaded2 = load_pack(pack)
    assert isinstance(loaded1, LoadedPack)
    assert loaded1.hash == loaded2.hash
    # Hash should be a 64-char hex string
    assert len(loaded1.hash) == 64
    int(loaded1.hash, 16)  # must be valid hex


# ---------------------------------------------------------------------------
# T-RUL-0024 — A rule with an unknown citation source is rejected
# ---------------------------------------------------------------------------
# id: T-RUL-0024
# title: Unknown citation source is rejected
# purpose: Verify that a rule citing a source not in the pack sources is
#          rejected.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with a rule citing 'src-99' not in the sources list
# expected: validate_pack raises ValidationError with code PACK_UNKNOWN_SOURCE
# risk: uncited or mis-cited rule accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0024_unknown_citation_source() -> None:
    """A rule citing a source not in the pack is rejected."""
    pack = _valid_pack()
    pack["rules"][0]["citation_source_id"] = "src-99"  # type: ignore[index]
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack)
    assert exc_info.value.code == "PACK_UNKNOWN_SOURCE"


# ---------------------------------------------------------------------------
# T-RUL-0025 — Overlapping windows with precedence are accepted
# ---------------------------------------------------------------------------
# id: T-RUL-0025
# title: Overlapping windows with precedence are accepted
# purpose: Verify that two rules with overlapping windows and declared
#          precedence are accepted.
# level: fast
# requirement: P06-T02, Part 3 §3.6
# input: a pack with two overlapping rules, one with precedence
# expected: validate_pack does not raise
# risk: valid pack rejected
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0025_overlapping_with_precedence() -> None:
    """Overlapping windows with precedence declared are accepted."""
    pack = _valid_pack()
    pack["rules"] = [
        {
            "id": "rule-1",
            "version": "1.0.0",
            "condition": {"type": "bool", "value": True},
            "outcome": "ALLOW",
            "reason_code": "R1",
            "citation_source_id": "src-1",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_to": "2026-06-30T23:59:59Z",
            "label": "DERIVED",
            "precedence": 1,
        },
        {
            "id": "rule-2",
            "version": "1.0.0",
            "condition": {"type": "bool", "value": True},
            "outcome": "HOLD",
            "reason_code": "R2",
            "citation_source_id": "src-1",
            "valid_from": "2026-06-01T00:00:00Z",
            "valid_to": "2026-12-31T23:59:59Z",
            "label": "DERIVED",
            "precedence": 2,
        },
    ]
    validate_pack(pack)  # should not raise


# ---------------------------------------------------------------------------
# T-RUL-0026 — A pack with a label at the ceiling is accepted
# ---------------------------------------------------------------------------
# id: T-RUL-0026
# title: Label at ceiling is accepted
# purpose: Verify that a pack whose declared label equals the weakest
#          source label is accepted.
# level: fast
# requirement: P06-T02, Part 3 §3.8
# input: a pack with declared_label DERIVED and all sources DERIVED
# expected: validate_pack does not raise
# risk: valid pack rejected
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0026_label_at_ceiling() -> None:
    """A declared label at the ceiling (equal to weakest) is accepted."""
    pack = _valid_pack()
    pack["declared_label"] = "DERIVED"
    pack["sources"] = ["src-1", "src-2"]
    source_labels = {"src-1": "DERIVED", "src-2": "DERIVED"}
    validate_pack(pack, source_labels=source_labels)  # should not raise

"""Tests for the synthetic data factory (P09-T01).

Test IDs: T-BCH-0001 to T-BCH-0012.
Covers: determinism for fixed seed; every record carries SYNTHETIC label,
seed and factory version; no deny-list name appears; Arabic-Indic and Persian
digits present; tariff rows have HS codes; tenant feeds have entries; labels
gate passes on factory output.

Spec: Part 3 §3.12; Part 4 §4.5; P09-T01.
"""

from __future__ import annotations

import json

import pytest

from data.synthetic import (
    DENYLIST,
    FACTORY_VERSION,
    SYNTHETIC_LABEL,
    SyntheticFactory,
    generate,
    to_canonical,
)

# --------------------------------------------------------------------------- #
# T-BCH-0001 — Same seed gives byte-identical output                          #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0001_same_seed_byte_identical() -> None:
    """T-BCH-0001: Same seed gives byte-identical output.

    id: T-BCH-0001
    title: Same seed gives byte-identical output
    purpose: Verify that two batches from the same seed are byte-identical.
    level: fast
    requirement: P09-T01, Part 3 §3.12
    input: seed 42, generate_batch twice
    expected: identical JSON
    risk: synthetic data passing as real
    capability: none
    """
    a = generate(42)
    b = generate(42)
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


# --------------------------------------------------------------------------- #
# T-BCH-0002 — Different seed gives different output                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0002_different_seed_different_output() -> None:
    """T-BCH-0002: Different seed gives different output.

    id: T-BCH-0002
    title: Different seed gives different output
    purpose: Verify that different seeds produce different data.
    level: fast
    requirement: P09-T01, Part 3 §3.12
    input: seeds 42 and 100
    expected: different JSON
    risk: synthetic data passing as real
    capability: none
    """
    a = generate(42)
    b = generate(100)
    assert json.dumps(a, sort_keys=True, default=str) != json.dumps(b, sort_keys=True, default=str)


# --------------------------------------------------------------------------- #
# T-BCH-0003 — Every record carries the SYNTHETIC label                       #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0003_every_record_labelled() -> None:
    """T-BCH-0003: Every record carries the SYNTHETIC label.

    id: T-BCH-0003
    title: Every record carries the SYNTHETIC label
    purpose: Verify that every synthetic record is labelled SYNTHETIC.
    level: fast
    requirement: P09-T01, Part 3 §3.12, PR-09
    input: seed 42, full batch
    expected: all records have label == SYNTHETIC
    risk: synthetic data passing as real
    capability: none
    """
    batch = generate(42)
    for cat in ("documents", "facts", "tariff_rows", "tenant_feeds"):
        for rec in batch[cat]:
            assert rec.label == SYNTHETIC_LABEL, f"{cat} record missing label"


# --------------------------------------------------------------------------- #
# T-BCH-0004 — Every record carries the seed                                  #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0004_every_record_carries_seed() -> None:
    """T-BCH-0004: Every record carries the seed.

    id: T-BCH-0004
    title: Every record carries the seed
    purpose: Verify that every record carries the producing seed.
    level: fast
    requirement: P09-T01, Part 3 §3.12
    input: seed 42, full batch
    expected: all records have seed == 42
    risk: broken traceability
    capability: none
    """
    batch = generate(42)
    for cat in ("documents", "facts", "tariff_rows", "tenant_feeds"):
        for rec in batch[cat]:
            assert rec.seed == 42, f"{cat} record missing seed"


# --------------------------------------------------------------------------- #
# T-BCH-0005 — Every record carries the factory version                       #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0005_every_record_carries_factory_version() -> None:
    """T-BCH-0005: Every record carries the factory version.

    id: T-BCH-0005
    title: Every record carries the factory version
    purpose: Verify that every record carries the factory version.
    level: fast
    requirement: P09-T01, Part 3 §3.12
    input: seed 42, full batch
    expected: all records have factory_version == FACTORY_VERSION
    risk: broken traceability
    capability: none
    """
    batch = generate(42)
    for cat in ("documents", "facts", "tariff_rows", "tenant_feeds"):
        for rec in batch[cat]:
            assert rec.factory_version == FACTORY_VERSION


# --------------------------------------------------------------------------- #
# T-BCH-0006 — No deny-list name appears in output                            #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0006_no_denylist_in_output() -> None:
    """T-BCH-0006: No deny-list name appears in output.

    id: T-BCH-0006
    title: No deny-list name appears in output
    purpose: Verify that no real name, company or identifier from the deny
        list appears in any synthetic record's text or values.
    level: fast
    requirement: P09-T01, Part 3 §3.12, PR-09
    input: seed 42, full batch
    expected: no deny-list substring in any record
    risk: synthetic data passing as real
    capability: none
    """
    batch = generate(42)
    for cat in ("documents", "facts", "tariff_rows", "tenant_feeds"):
        for rec in batch[cat]:
            blob = json.dumps(to_canonical(rec), ensure_ascii=False)
            for denied in DENYLIST:
                assert denied not in blob, f"deny-list entry '{denied}' found in {cat}"


# --------------------------------------------------------------------------- #
# T-BCH-0007 — Arabic-Indic digits present in Arabic documents                #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0007_arabic_indic_digits() -> None:
    """T-BCH-0007: Arabic-Indic digits present in Arabic documents.

    id: T-BCH-0007
    title: Arabic-Indic digits present in Arabic documents
    purpose: Verify that Arabic documents contain Arabic-Indic digits.
    level: fast
    requirement: P09-T01, PR-11
    input: seed 42, Arabic document
    expected: arabic_indic_digits field is non-empty and contains U+0660-range
    risk: scenario gaps
    capability: none
    """
    f = SyntheticFactory(42)
    doc = f.generate_document("invoice", "ar")
    assert doc.arabic_indic_digits, "Arabic-Indic digits empty"
    assert all("\u0660" <= ch <= "\u0669" for ch in doc.arabic_indic_digits)


# --------------------------------------------------------------------------- #
# T-BCH-0008 — Persian digits present in Persian documents                     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0008_persian_digits() -> None:
    """T-BCH-0008: Persian digits present in Persian documents.

    id: T-BCH-0008
    title: Persian digits present in Persian documents
    purpose: Verify that Persian documents contain Persian digits.
    level: fast
    requirement: P09-T01, PR-11
    input: seed 42, Persian document
    expected: persian_digits field is non-empty and contains U+06F0-range
    risk: scenario gaps
    capability: none
    """
    f = SyntheticFactory(42)
    doc = f.generate_document("invoice", "fa")
    assert doc.persian_digits, "Persian digits empty"
    assert all("\u06f0" <= ch <= "\u06f9" for ch in doc.persian_digits)


# --------------------------------------------------------------------------- #
# T-BCH-0009 — Factory is deterministic on regenerate                          #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0009_deterministic_regenerate() -> None:
    """T-BCH-0009: Factory is deterministic on regenerate.

    id: T-BCH-0009
    title: Factory is deterministic on regenerate
    purpose: Verify that regenerating a single document from the same seed
        and factory instance is byte-identical.
    level: fast
    requirement: P09-T01, Part 3 §3.12
    input: two factory instances seed 42
    expected: identical first document
    risk: broken traceability
    capability: none
    """
    f1 = SyntheticFactory(42)
    f2 = SyntheticFactory(42)
    d1 = f1.generate_document("invoice", "en")
    d2 = f2.generate_document("invoice", "en")
    assert to_canonical(d1) == to_canonical(d2)


# --------------------------------------------------------------------------- #
# T-BCH-0010 — Tariff rows have HS codes                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0010_tariff_rows_have_hs_codes() -> None:
    """T-BCH-0010: Tariff rows have HS codes.

    id: T-BCH-0010
    title: Tariff rows have HS codes
    purpose: Verify that every tariff row has a non-empty HS code.
    level: fast
    requirement: P09-T01, Part 3 §3.6
    input: seed 42, full batch
    expected: all tariff rows have non-empty hs_code
    risk: scenario gaps
    capability: none
    """
    batch = generate(42)
    for row in batch["tariff_rows"]:
        assert row.hs_code, "tariff row missing HS code"
        assert "." in row.hs_code


# --------------------------------------------------------------------------- #
# T-BCH-0011 — Tenant feeds have entries                                      #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0011_tenant_feeds_have_entries() -> None:
    """T-BCH-0011: Tenant feeds have entries.

    id: T-BCH-0011
    title: Tenant feeds have entries
    purpose: Verify that every tenant feed has at least one entry.
    level: fast
    requirement: P09-T01, Part 3 §3.24
    input: seed 42, full batch
    expected: all tenant feeds have non-empty entries
    risk: scenario gaps
    capability: none
    """
    batch = generate(42)
    for feed in batch["tenant_feeds"]:
        assert feed.entries, "tenant feed has no entries"
        assert feed.tenant_id, "tenant feed missing tenant_id"


# --------------------------------------------------------------------------- #
# T-BCH-0012 — Labels gate passes on factory output                           #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0012_labels_gate_factory_output() -> None:
    """T-BCH-0012: Labels gate passes on factory output.

    id: T-BCH-0012
    title: Labels gate passes on factory output
    purpose: Verify that every synthetic record carries the SYNTHETIC label
        in its label field and that the label is correct.
    level: fast
    requirement: P09-T01, Part 3 §3.8, PR-09
    input: seed 42, full batch
    expected: all records have label == 'SYNTHETIC'
    risk: synthetic data passing as real
    capability: none
    """
    batch = generate(42)
    for cat in ("documents", "facts", "tariff_rows", "tenant_feeds"):
        for rec in batch[cat]:
            assert rec.label == "SYNTHETIC"

"""Tests for canonical serialization and domain-separated hashing (P03-T02).

Test IDs: T-KRN-0009 to T-KRN-0018.
Covers: RFC 8785 known-answer vectors; SHA-256 known-answer; cross-purpose
hash separation; decimal serialization without ambiguity; key order and
number formatting stability (property tests); unknown tag rejection;
algorithm identifier; tag registry validation; differential test (rfc8785 vs
jcs).

Spec: Part 3 §3.5; kernel/canonical/; kernel/hashing/; schemas/hash-tags.json.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# T-KRN-0009 — Known-answer vector for RFC 8785 canonical JSON
# ---------------------------------------------------------------------------
# id: T-KRN-0009
# title: Known-answer vector for RFC 8785 canonical JSON
# purpose: Verify canonical JSON produces sorted keys and minimal whitespace.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: a dict with out-of-order keys
# expected: keys are sorted, no whitespace
# risk: canonicalization is not deterministic
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0009_rfc8785_known_answer() -> None:
    """RFC 8785 canonical JSON sorts keys and removes whitespace."""
    from kernel.canonical import canonical_dumps

    assert canonical_dumps({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert canonical_dumps({}) == "{}"
    assert canonical_dumps([3, 1, 2]) == "[3,1,2]"


# ---------------------------------------------------------------------------
# T-KRN-0010 — Known-answer vector for SHA-256 domain hash
# ---------------------------------------------------------------------------
# id: T-KRN-0010
# title: Known-answer vector for SHA-256 domain hash
# purpose: Verify domain_hash produces the correct SHA-256 of tag||canonical.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: a known tag and payload
# expected: digest matches independently computed SHA-256
# risk: the hash function is wrong
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0010_sha256_known_answer() -> None:
    """domain_hash matches an independently computed SHA-256."""
    from kernel.canonical import canonical_bytes
    from kernel.hashing import ALGORITHM, domain_hash

    tag = "ctc/commit/v1"
    payload = {"a": 1}
    expected = hashlib.sha256(tag.encode("utf-8") + canonical_bytes(payload)).hexdigest()
    assert domain_hash(tag, payload) == expected
    assert ALGORITHM == "sha256"


# ---------------------------------------------------------------------------
# T-KRN-0011 — Cross-purpose hash separation
# ---------------------------------------------------------------------------
# id: T-KRN-0011
# title: Cross-purpose hash separation
# purpose: Verify the same payload under different tags never produces the same hash.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: the same payload with two different tags
# expected: hashes are different
# risk: cross-purpose hash replay is possible
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0011_cross_purpose_hash_separation() -> None:
    """The same payload under different tags produces different hashes."""
    from kernel.hashing import domain_hash

    payload = {"case_id": "c-001", "value": 42}
    tags = ["ctc/record/v1", "ctc/leaf/v1", "ctc/node/v1", "ctc/commit/v1", "ctc/payload/v1"]
    hashes = {domain_hash(tag, payload) for tag in tags}
    assert len(hashes) == len(tags), "different tags produced identical hashes"


# ---------------------------------------------------------------------------
# T-KRN-0012 — Decimals serialize without exponent or trailing zeros ambiguity
# ---------------------------------------------------------------------------
# id: T-KRN-0012
# title: Decimals serialize without exponent or trailing zeros ambiguity
# purpose: Verify float values serialize without trailing zeros or exponents.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: floats with trailing zeros
# expected: no trailing zeros or exponent notation in canonical output
# risk: number formatting is ambiguous
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0012_decimal_serialization() -> None:
    """Floats serialize without trailing zeros or exponent notation."""
    from kernel.canonical import canonical_dumps

    assert canonical_dumps({"x": 3.0}) == '{"x":3}'
    assert "e" not in canonical_dumps({"x": 0.1}).lower()
    assert canonical_dumps({"x": 100.0}) == '{"x":100}'


# ---------------------------------------------------------------------------
# T-KRN-0013 — Key order stability under random input order (property)
# ---------------------------------------------------------------------------
# id: T-KRN-0013
# title: Key order stability under random input order
# purpose: Verify that key insertion order does not affect canonical output.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: dicts with the same content but different key order
# expected: canonical output is identical
# risk: canonicalization depends on insertion order
# capability: kernel-contracts


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=5),
        st.integers(min_value=-(2**53) + 1, max_value=2**53 - 1),
    )
)
@settings(max_examples=100, derandomize=True)
def test_T_KRN_0013_key_order_stability(d: dict[str, int]) -> None:
    """Key order does not affect canonical JSON output."""
    from kernel.canonical import canonical_dumps

    reversed_d = dict(reversed(list(d.items())))
    assert canonical_dumps(d) == canonical_dumps(reversed_d)


# ---------------------------------------------------------------------------
# T-KRN-0014 — Number formatting stability under random input (property)
# ---------------------------------------------------------------------------
# id: T-KRN-0014
# title: Number formatting stability under random input
# purpose: Verify that the same number always produces the same canonical form.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: an integer value
# expected: canonical form is deterministic
# risk: number formatting is non-deterministic
# capability: kernel-contracts


@given(st.integers(min_value=-(2**53) + 1, max_value=2**53 - 1))
@settings(max_examples=100, derandomize=True)
def test_T_KRN_0014_number_formatting_stability(n: int) -> None:
    """The same integer always produces the same canonical form."""
    from kernel.canonical import canonical_dumps

    assert canonical_dumps({"n": n}) == canonical_dumps({"n": n})


# ---------------------------------------------------------------------------
# T-KRN-0015 — Unknown tag rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0015
# title: Unknown tag rejected
# purpose: Verify that using an unregistered hash tag raises an error.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: an unregistered tag string
# expected: UnknownTagError is raised
# risk: an unregistered tag is used for hashing
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0015_unknown_tag_rejected() -> None:
    """An unknown hash tag raises UnknownTagError."""
    from kernel.hashing import UnknownTagError, domain_hash

    with pytest.raises(UnknownTagError):
        domain_hash("ctc/unknown/v1", {"a": 1})


# ---------------------------------------------------------------------------
# T-KRN-0016 — Algorithm identifier present
# ---------------------------------------------------------------------------
# id: T-KRN-0016
# title: Algorithm identifier present
# purpose: Verify that the hashing module exposes an algorithm identifier.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: the hashing module
# expected: ALGORITHM is 'sha256'
# risk: the algorithm is not recorded for hash agility
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0016_algorithm_identifier() -> None:
    """The hashing module exposes the algorithm identifier 'sha256'."""
    from kernel.hashing import ALGORITHM

    assert ALGORITHM == "sha256"


# ---------------------------------------------------------------------------
# T-KRN-0017 — Tag registry validates and all tags are unique
# ---------------------------------------------------------------------------
# id: T-KRN-0017
# title: Tag registry validates and all tags are unique
# purpose: Verify that the hash tag registry has unique, versioned entries.
# level: fast
# requirement: P03-T02, Part 3 §3.5
# input: schemas/hash-tags.json
# expected: all tags are unique and have a version field
# risk: duplicate tags allow cross-purpose hash replay
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0017_tag_registry_validates() -> None:
    """The hash tag registry has unique, versioned entries."""
    from kernel.hashing import KNOWN_TAGS, load_tags

    tags_path = _REPO_ROOT / "schemas" / "hash-tags.json"
    loaded = load_tags(tags_path)
    assert loaded == KNOWN_TAGS
    tag_list = list(loaded)
    assert len(tag_list) == len(set(tag_list)), "duplicate tags found"
    assert len(tag_list) >= 5


# ---------------------------------------------------------------------------
# T-KRN-0018 — Differential test: rfc8785 vs jcs produce identical output
# ---------------------------------------------------------------------------
# id: T-KRN-0018
# title: Differential test: rfc8785 vs jcs produce identical output
# purpose: Verify two independent RFC 8785 implementations agree.
# level: fast
# requirement: P03-T02, Part 3 §3.5, Part 4 §4.5
# input: a set of varied JSON-serializable values
# expected: both implementations produce the same canonical bytes
# risk: the primary canonicalization library has a bug
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0018_differential_rfc8785_vs_jcs() -> None:
    """rfc8785 and jcs produce identical canonical JSON for the same input."""
    import jcs
    import rfc8785

    inputs: list[object] = [
        {"b": 1, "a": 2},
        {"z": [1, 2, 3], "a": {"c": True, "b": False}},
        {},
        [],
        {"nested": {"deep": {"value": 42}}},
        {"unicode": "héllo"},
    ]
    for obj in inputs:
        rfc_out = rfc8785.dumps(obj)  # type: ignore[arg-type]
        jcs_out = jcs.canonicalize(obj)
        jcs_bytes = jcs_out.encode("utf-8") if isinstance(jcs_out, str) else jcs_out
        assert rfc_out == jcs_bytes, f"mismatch for {obj!r}"

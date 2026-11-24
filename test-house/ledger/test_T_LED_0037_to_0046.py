"""Tests for cryptographic commitments (P05-T04).

Test IDs: T-LED-0037 to T-LED-0046.
Covers: equal inputs give equal commitments; input changes give different
values; revealed value and salt verify; salt destroyed prevents confirmation;
cross-purpose reuse fails.

Spec: Part 3 §3.5, §3.7; Part 4 §4.4; P05-T04.
"""

from __future__ import annotations

import hashlib

import pytest

from kernel.ledger.commitments import (
    evaluation_commitment,
    field_commitment,
    generate_field_salt,
    proposal_commitment,
    verify_field_commitment,
)

# ---------------------------------------------------------------------------
# T-LED-0037 — Equal inputs give equal evaluation commitments
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0037_eval_commitment_equal_inputs() -> None:
    """T-LED-0037: Equal inputs give equal evaluation commitments.

    id: T-LED-0037
    title: Equal inputs give equal evaluation commitments
    purpose: Verify that the same inputs produce the same evaluation commitment.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: two calls with identical arguments
    expected: identical commitments
    risk: non-deterministic commitment
    capability: evidence-ledger
    """
    c1 = evaluation_commitment("fsh", "psh", "2026-11-01T00:00:00Z", "ch")
    c2 = evaluation_commitment("fsh", "psh", "2026-11-01T00:00:00Z", "ch")
    assert c1 == c2


# ---------------------------------------------------------------------------
# T-LED-0038 — Any input change gives a different evaluation commitment
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0038_eval_commitment_input_change() -> None:
    """T-LED-0038: Any input change gives a different evaluation commitment.

    id: T-LED-0038
    title: Any input change gives a different evaluation commitment
    purpose: Verify that changing any input to the evaluation commitment
        produces a different value.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: base commitment and four modified variants
    expected: all four differ from the base
    risk: input change not detected
    capability: evidence-ledger
    """
    base = evaluation_commitment("fsh", "psh", "2026-11-01T00:00:00Z", "ch")
    assert evaluation_commitment("x", "psh", "2026-11-01T00:00:00Z", "ch") != base
    assert evaluation_commitment("fsh", "x", "2026-11-01T00:00:00Z", "ch") != base
    assert evaluation_commitment("fsh", "psh", "x", "ch") != base
    assert evaluation_commitment("fsh", "psh", "2026-11-01T00:00:00Z", "x") != base


# ---------------------------------------------------------------------------
# T-LED-0039 — Proposal commitment is deterministic
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0039_proposal_commitment_deterministic() -> None:
    """T-LED-0039: Proposal commitment is deterministic.

    id: T-LED-0039
    title: Proposal commitment is deterministic
    purpose: Verify that the same proposal produces the same commitment.
    level: fast
    requirement: P05-T04, Part 3 §3.7
    input: two calls with the same proposal dict
    expected: identical commitments
    risk: non-deterministic proposal commitment
    capability: evidence-ledger
    """
    p: dict[str, object] = {"id": "p1", "value": "test"}
    c1 = proposal_commitment(p)
    c2 = proposal_commitment(p)
    assert c1 == c2


# ---------------------------------------------------------------------------
# T-LED-0040 — Proposal commitment changes on proposal change
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0040_proposal_commitment_changes() -> None:
    """T-LED-0040: Proposal commitment changes on proposal change.

    id: T-LED-0040
    title: Proposal commitment changes on proposal change
    purpose: Verify that a changed proposal produces a different commitment.
    level: fast
    requirement: P05-T04, Part 3 §3.7
    input: two proposals that differ in one field
    expected: different commitments
    risk: proposal change not detected
    capability: evidence-ledger
    """
    p1: dict[str, object] = {"id": "p1", "value": "test"}
    p2: dict[str, object] = {"id": "p1", "value": "changed"}
    assert proposal_commitment(p1) != proposal_commitment(p2)


# ---------------------------------------------------------------------------
# T-LED-0041 — Field commitment with revealed value and salt verifies
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0041_field_commitment_verifies() -> None:
    """T-LED-0041: Field commitment with revealed value and salt verifies.

    id: T-LED-0041
    title: Field commitment with revealed value and salt verifies
    purpose: Verify that revealing the value and salt allows verification.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: a field commitment and the correct value and salt
    expected: verify returns True
    risk: verification fails with correct inputs
    capability: evidence-ledger
    """
    salt_id, salt = generate_field_salt()
    value: object = {"name": "Alice", "amount": 1000}
    ch = field_commitment(salt_id, salt, value)
    assert verify_field_commitment(salt_id, salt, value, ch)


# ---------------------------------------------------------------------------
# T-LED-0042 — Field commitment with wrong value fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0042_field_commitment_wrong_value() -> None:
    """T-LED-0042: Field commitment with wrong value fails.

    id: T-LED-0042
    title: Field commitment with wrong value fails
    purpose: Verify that a wrong value does not verify.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: a field commitment and a wrong value
    expected: verify returns False
    risk: wrong value accepted
    capability: evidence-ledger
    """
    salt_id, salt = generate_field_salt()
    ch = field_commitment(salt_id, salt, {"name": "Alice"})
    assert not verify_field_commitment(salt_id, salt, {"name": "Bob"}, ch)


# ---------------------------------------------------------------------------
# T-LED-0043 — Field commitment with wrong salt fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0043_field_commitment_wrong_salt() -> None:
    """T-LED-0043: Field commitment with wrong salt fails.

    id: T-LED-0043
    title: Field commitment with wrong salt fails
    purpose: Verify that a wrong salt does not verify.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: a field commitment and a wrong salt
    expected: verify returns False
    risk: wrong salt accepted
    capability: evidence-ledger
    """
    salt_id, salt = generate_field_salt()
    value: object = {"name": "Alice"}
    ch = field_commitment(salt_id, salt, value)
    wrong_salt = hashlib.sha256(b"wrong").digest()
    assert not verify_field_commitment(salt_id, wrong_salt, value, ch)


# ---------------------------------------------------------------------------
# T-LED-0044 — Salt destroyed prevents confirmation
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0044_salt_destroyed_prevents_confirmation() -> None:
    """T-LED-0044: With salt destroyed, value cannot be confirmed.

    id: T-LED-0044
    title: With salt destroyed, value cannot be confirmed
    purpose: Verify that destroying the salt makes the commitment unverifiable.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: a field commitment where the salt is lost (empty bytes)
    expected: verify returns False
    risk: salt loss allows confirmation
    capability: evidence-ledger
    """
    salt_id, salt = generate_field_salt()
    value: object = {"name": "Alice"}
    ch = field_commitment(salt_id, salt, value)
    # Salt is destroyed — replaced with empty bytes.
    assert not verify_field_commitment(salt_id, b"", value, ch)


# ---------------------------------------------------------------------------
# T-LED-0045 — Different salts produce different field commitments
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0045_different_salts_different_commitments() -> None:
    """T-LED-0045: Different salts produce different field commitments.

    id: T-LED-0045
    title: Different salts produce different field commitments
    purpose: Verify that different salts produce different commitments for
        the same value.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: same value with two different salts
    expected: different commitments
    risk: salt not incorporated
    capability: evidence-ledger
    """
    sid1, s1 = generate_field_salt()
    sid2, s2 = generate_field_salt()
    value: object = "test"
    assert field_commitment(sid1, s1, value) != field_commitment(sid2, s2, value)


# ---------------------------------------------------------------------------
# T-LED-0046 — Cross-purpose reuse fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0046_cross_purpose_reuse_fails() -> None:
    """T-LED-0046: A commitment hash cannot be used as a record hash.

    id: T-LED-0046
    title: Cross-purpose hash reuse fails
    purpose: Verify that a commitment hash differs from a record hash for
        the same data due to domain separation.
    level: fast
    requirement: P05-T04, Part 3 §3.5
    input: the same payload under ctc/commit/v1 and ctc/record/v1
    expected: the two hashes differ
    risk: cross-purpose hash replay
    capability: evidence-ledger
    """
    from kernel.ledger.records import ZERO_HASH, compute_record_hash

    payload: dict[str, object] = {"k": "v"}
    commit = proposal_commitment(payload)
    record = compute_record_hash(payload, ZERO_HASH)
    assert commit != record

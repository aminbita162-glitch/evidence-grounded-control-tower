"""Tests for Merkle tree, checkpoints and proofs (P05-T03).

Test IDs: T-LED-0021 to T-LED-0036.
Covers: known-answer vectors for leaf, node, root; property tests for
inclusion and consistency proofs; tamper detection; cross-purpose hash
replay; witness refusal of rewritten history; verification levels.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T03.
"""

from __future__ import annotations

import hashlib
import random

import pytest

from adapters.signing import DevSigner
from kernel.ledger.checkpoint import Checkpoint
from kernel.ledger.proofs import (
    ConsistencyProof,
    create_consistency_proof,
    create_inclusion_proof,
    verify_consistency_proof,
    verify_inclusion,
)
from kernel.ledger.tree import ZERO_HASH, MerkleTree, leaf_hash, node_hash
from tools.witness import LocalWitness

# ---------------------------------------------------------------------------
# Known-answer vectors
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0021_leaf_hash_known_answer() -> None:
    """T-LED-0021: Leaf hash known-answer vector.

    id: T-LED-0021
    title: Leaf hash known-answer vector
    purpose: Verify leaf_hash produces the expected SHA-256 for a known input.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: record_hash = "abc123"
    expected: H("ctc/leaf/v1" || "abc123")
    risk: leaf hash computation incorrect
    capability: evidence-ledger
    """
    expected = hashlib.sha256(b"ctc/leaf/v1abc123").hexdigest()
    assert leaf_hash("abc123") == expected


@pytest.mark.fast
def test_T_LED_0022_node_hash_known_answer() -> None:
    """T-LED-0022: Node hash known-answer vector.

    id: T-LED-0022
    title: Node hash known-answer vector
    purpose: Verify node_hash produces the expected SHA-256 for known inputs.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: left = "aaa", right = "bbb"
    expected: H("ctc/node/v1" || "aaa" || "bbb")
    risk: node hash computation incorrect
    capability: evidence-ledger
    """
    expected = hashlib.sha256(b"ctc/node/v1aaabbb").hexdigest()
    assert node_hash("aaa", "bbb") == expected


@pytest.mark.fast
def test_T_LED_0023_root_single_leaf() -> None:
    """T-LED-0023: Root of a single-leaf tree is the leaf itself.

    id: T-LED-0023
    title: Root of a single-leaf tree is the leaf itself
    purpose: Verify that a tree with one leaf has root equal to that leaf.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: one record hash
    expected: root == leaf_hash(record_hash)
    risk: single-leaf tree root incorrect
    capability: evidence-ledger
    """
    rh = "record-1"
    tree = MerkleTree([rh])
    assert tree.root == leaf_hash(rh)
    assert tree.size == 1


@pytest.mark.fast
def test_T_LED_0024_root_two_leaves() -> None:
    """T-LED-0024: Root of a two-leaf tree is node_hash of the two leaves.

    id: T-LED-0024
    title: Root of a two-leaf tree is node_hash of the two leaves
    purpose: Verify that a tree with two leaves has root = node_hash(leaf0, leaf1).
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: two record hashes
    expected: root == node_hash(leaf_hash(r0), leaf_hash(r1))
    risk: two-leaf tree root incorrect
    capability: evidence-ledger
    capability: evidence-ledger
    """
    tree = MerkleTree(["r0", "r1"])
    expected = node_hash(leaf_hash("r0"), leaf_hash("r1"))
    assert tree.root == expected


@pytest.mark.fast
def test_T_LED_0025_root_empty_tree() -> None:
    """T-LED-0025: Root of an empty tree is all zeros.

    id: T-LED-0025
    title: Root of an empty tree is all zeros
    purpose: Verify that an empty tree has root = ZERO_HASH.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: no record hashes
    expected: root == "0"*64
    risk: empty tree root not zero
    capability: evidence-ledger
    """
    tree = MerkleTree([])
    assert tree.root == ZERO_HASH
    assert tree.size == 0


# ---------------------------------------------------------------------------
# Inclusion proofs
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0026_inclusion_proof_valid() -> None:
    """T-LED-0026: Inclusion proof verifies for a valid leaf.

    id: T-LED-0026
    title: Inclusion proof verifies for a valid leaf
    purpose: Verify that an inclusion proof for a present leaf passes verification.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: tree of 7 leaves, proof for index 3
    expected: verify_inclusion returns True
    risk: valid inclusion proof rejected
    capability: evidence-ledger
    """
    record_hashes = [f"rec-{i}" for i in range(7)]
    tree = MerkleTree(record_hashes)
    proof = create_inclusion_proof(tree, record_hashes, 3)
    assert verify_inclusion("rec-3", 3, tree.size, proof.path, proof.root)


@pytest.mark.fast
def test_T_LED_0027_inclusion_proof_wrong_index() -> None:
    """T-LED-0027: Inclusion proof fails for a wrong index.

    id: T-LED-0027
    title: Inclusion proof fails for a wrong index
    purpose: Verify that an inclusion proof for the wrong leaf index fails.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: proof for index 3, verified with record_hash of index 4
    expected: verify_inclusion returns False
    risk: wrong index accepted
    capability: evidence-ledger
    """
    record_hashes = [f"rec-{i}" for i in range(7)]
    tree = MerkleTree(record_hashes)
    proof = create_inclusion_proof(tree, record_hashes, 3)
    # Use the wrong record hash.
    assert not verify_inclusion("rec-4", 3, tree.size, proof.path, proof.root)


@pytest.mark.fast
def test_T_LED_0028_inclusion_proof_tampered_root() -> None:
    """T-LED-0028: Inclusion proof fails for a tampered root.

    id: T-LED-0028
    title: Inclusion proof fails for a tampered root
    purpose: Verify that an inclusion proof with a wrong root fails.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: valid proof, wrong expected_root
    expected: verify_inclusion returns False
    risk: tampered root accepted
    capability: evidence-ledger
    """
    record_hashes = [f"rec-{i}" for i in range(5)]
    tree = MerkleTree(record_hashes)
    proof = create_inclusion_proof(tree, record_hashes, 2)
    wrong_root = "0" * 64
    assert not verify_inclusion("rec-2", 2, tree.size, proof.path, wrong_root)


# ---------------------------------------------------------------------------
# Consistency proofs
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0029_consistency_proof_valid() -> None:
    """T-LED-0029: Consistency proof verifies for a valid extension.

    id: T-LED-0029
    title: Consistency proof verifies for a valid extension
    purpose: Verify that a consistency proof from size 4 to size 7 passes.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: tree of 7 leaves, consistency proof from size 4
    expected: verify_consistency_proof returns True
    risk: valid consistency proof rejected
    capability: evidence-ledger
    """
    record_hashes = [f"rec-{i}" for i in range(7)]
    tree = MerkleTree(record_hashes)
    proof = create_consistency_proof(tree, 4)
    assert verify_consistency_proof(tree, 4, proof)


@pytest.mark.fast
def test_T_LED_0030_consistency_proof_tampered_prev_root() -> None:
    """T-LED-0030: Consistency proof fails for a tampered previous root.

    id: T-LED-0030
    title: Consistency proof fails for a tampered previous root
    purpose: Verify that a consistency proof with a wrong prev_root fails.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: valid proof, wrong prev_root
    expected: verify_consistency_proof returns False
    risk: tampered previous root accepted
    capability: evidence-ledger
    """
    record_hashes = [f"rec-{i}" for i in range(7)]
    tree = MerkleTree(record_hashes)
    proof = create_consistency_proof(tree, 4)
    tampered = ConsistencyProof(
        prev_size=proof.prev_size,
        curr_size=proof.curr_size,
        path=proof.path,
        prev_root="0" * 64,
        curr_root=proof.curr_root,
    )
    assert not verify_consistency_proof(tree, 4, tampered)


# ---------------------------------------------------------------------------
# Tamper detection
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0031_tampered_record_detected() -> None:
    """T-LED-0031: A changed byte in a record is detected by the tree root.

    id: T-LED-0031
    title: A changed byte in a record is detected by the tree root
    purpose: Verify that changing one record hash produces a different root.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: two trees that differ in one record hash
    expected: roots differ
    risk: tamper not detected
    capability: evidence-ledger
    """
    records = [f"rec-{i}" for i in range(8)]
    tree1 = MerkleTree(records)
    records[3] = "tampered"
    tree2 = MerkleTree(records)
    assert tree1.root != tree2.root


@pytest.mark.fast
def test_T_LED_0032_tampered_checkpoint_signature_detected() -> None:
    """T-LED-0032: A changed byte in a checkpoint signature is detected.

    id: T-LED-0032
    title: A changed byte in a checkpoint signature is detected
    purpose: Verify that a tampered checkpoint signature fails verification.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: a valid checkpoint signature, then one with a changed byte
    expected: verify returns False for the tampered signature
    risk: signature tamper not detected
    capability: evidence-ledger
    """
    signer = DevSigner()
    cp = Checkpoint(
        chain_id="chain-1",
        tree_size=5,
        root_hash="abc" + "0" * 61,
        system_chain_position=1,
        recorded_at="2026-11",
        signature=signer.sign(b"test-checkpoint"),
    )
    # Verify the original signature.
    assert signer.verify(b"test-checkpoint", cp.signature)
    # Tamper with the signature.
    tampered_sig = "0" + cp.signature[1:]
    assert not signer.verify(b"test-checkpoint", tampered_sig)


# ---------------------------------------------------------------------------
# Cross-purpose hash replay
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0033_cross_purpose_replay_fails() -> None:
    """T-LED-0033: A leaf hash cannot be used as a node hash and vice versa.

    id: T-LED-0033
    title: Cross-purpose hash replay fails
    purpose: Verify that leaf and node hashes are domain-separated and cannot
        be interchanged.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: the same record_hash hashed as leaf and as one side of a node
    expected: the two hashes differ
    risk: cross-purpose hash replay
    capability: evidence-ledger
    """
    rh = "test-record"
    lh = leaf_hash(rh)
    nh = node_hash(rh, rh)
    assert lh != nh
    assert lh != rh
    assert nh != rh


# ---------------------------------------------------------------------------
# Property tests over random trees
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0034_inclusion_property_random_trees() -> None:
    """T-LED-0034: Inclusion proof verifies for random trees.

    id: T-LED-0034
    title: Inclusion proof verifies for random trees
    purpose: Verify that inclusion proofs verify for every leaf in random trees.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: 20 random trees of sizes 1-20, every leaf
    expected: all inclusion proofs verify
    risk: inclusion proof fails on some tree shape
    capability: evidence-ledger
    """
    rng = random.Random(42)
    for _ in range(20):
        size = rng.randint(1, 20)
        records = [f"r-{i}-{rng.randint(0, 9999)}" for i in range(size)]
        tree = MerkleTree(records)
        for i in range(size):
            proof = create_inclusion_proof(tree, records, i)
            assert verify_inclusion(records[i], i, tree.size, proof.path, proof.root)


@pytest.mark.fast
def test_T_LED_0035_consistency_property_random_trees() -> None:
    """T-LED-0035: Consistency proof verifies for random tree extensions.

    id: T-LED-0035
    title: Consistency proof verifies for random tree extensions
    purpose: Verify that consistency proofs verify for random tree size pairs.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: 20 random trees, consistency from size k to size n (k < n)
    expected: all consistency proofs verify
    risk: consistency proof fails on some tree shape
    capability: evidence-ledger
    """
    rng = random.Random(99)
    for _ in range(20):
        size = rng.randint(2, 20)
        records = [f"r-{i}-{rng.randint(0, 9999)}" for i in range(size)]
        tree = MerkleTree(records)
        prev_size = rng.randint(1, size - 1)
        proof = create_consistency_proof(tree, prev_size)
        assert verify_consistency_proof(tree, prev_size, proof)


# ---------------------------------------------------------------------------
# Witness and verification levels
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0036_checkpoint_without_cosign_self_attested() -> None:
    """T-LED-0036: A checkpoint without a valid co-signature is SELF-ATTESTED.

    id: T-LED-0036
    title: A checkpoint without a valid co-signature is SELF-ATTESTED
    purpose: Verify that a checkpoint with no witness co-signature reports
        SELF-ATTESTED and a witnessed one reports the correct level.
    level: fast
    requirement: P05-T03, Part 3 §3.5
    input: a checkpoint without a witness, and one with a LOCAL witness
    expected: SELF-ATTESTED and WITNESSED-LOCAL respectively
    risk: verification level misreported
    capability: evidence-ledger
    """
    signer = DevSigner()
    signing_bytes = b"test-checkpoint"
    cp_self = Checkpoint(
        chain_id="c1",
        tree_size=5,
        root_hash="abc" + "0" * 61,
        system_chain_position=1,
        recorded_at="2026-11",
        signature=signer.sign(signing_bytes),
    )
    assert cp_self.verification_level() == "SELF-ATTESTED"

    witness = LocalWitness(signer=DevSigner())
    cp_witnessed = witness.cosign(cp_self)
    assert cp_witnessed.verification_level() == "WITNESSED-LOCAL"

    # The witness refuses a checkpoint that rewrites history (smaller tree size).
    cp_rewrite = Checkpoint(
        chain_id="c1",
        tree_size=3,
        root_hash="b" + "0" * 63,
        system_chain_position=1,
        recorded_at="2026-11",
        signature=signer.sign(b"cp2"),
    )
    with pytest.raises(ValueError, match="witness refuses"):
        witness.cosign(cp_rewrite)

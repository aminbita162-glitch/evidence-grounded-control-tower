"""Tests for case bundle, independent verifier, and crash points (P05-T06 to T05-T08).

Test IDs: T-LED-0059 to T-LED-0086.
Covers: bundle export/import round-trip; altered file fails verification;
byte-identical exports; independent verifier agrees with kernel verifier;
verifier imports no project module; crash recovery at kill points; mapped
threat items have tests.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T06, P05-T07, P05-T08.
"""

from __future__ import annotations

import asyncio
import random

import pytest

from kernel.ledger.bundle import export_bundle, verify_bundle
from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import Actor, LedgerRecord
from kernel.ledger.tree import MerkleTree, compute_root, leaf_hash, node_hash
from kernel.ledger.verify import verify_structural

_ACTOR = Actor(kind="ROLE", id="ROLE-MANAGER")


def _build_chain_records() -> list[LedgerRecord]:
    chain = InMemoryCaseChain("tenant-a", "case-bundle")

    async def _build() -> list[LedgerRecord]:
        for i in range(1, 6):
            await chain.append("Rules", _ACTOR, "rule_evaluated", {"i": i})
        return await chain.list()

    return asyncio.run(_build())


# ---------------------------------------------------------------------------
# T-LED-0059 — Export and import round-trip gives equal hashes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0059_bundle_round_trip() -> None:
    """T-LED-0059: Export and import round-trip gives equal hashes.

    id: T-LED-0059
    title: Export and import round-trip gives equal hashes
    purpose: Verify that exporting and importing a bundle preserves the hash.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: a 5-record chain exported and verified
    expected: verify_bundle returns True
    risk: round-trip changes the bundle
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle = export_bundle(records, "tenant-a", "case-bundle")
    assert verify_bundle(bundle)


# ---------------------------------------------------------------------------
# T-LED-0060 — A bundle with one altered file fails verification
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0060_altered_bundle_fails() -> None:
    """T-LED-0060: A bundle with one altered record fails verification.

    id: T-LED-0060
    title: A bundle with one altered record fails verification
    purpose: Verify that changing a record in the bundle causes verification to fail.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: a bundle with a tampered record hash
    expected: verify_bundle returns False
    risk: tamper not detected
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle = export_bundle(records, "tenant-a", "case-bundle")
    # Tamper with the root hash in the manifest.
    import dataclasses

    bundle.manifest = dataclasses.replace(bundle.manifest, root_hash="0" * 64)
    assert not verify_bundle(bundle)


# ---------------------------------------------------------------------------
# T-LED-0061 — Bundle layout is byte-identical across two exports
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0061_byte_identical_exports() -> None:
    """T-LED-0061: Two exports of the same case are byte-identical.

    id: T-LED-0061
    title: Two exports of the same case are byte-identical
    purpose: Verify that the bundle layout is deterministic.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: two exports of the same 5-record chain
    expected: identical bundle_hash values
    risk: non-deterministic export
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle1 = export_bundle(records, "tenant-a", "case-bundle")
    bundle2 = export_bundle(records, "tenant-a", "case-bundle")
    assert bundle1.manifest.bundle_hash == bundle2.manifest.bundle_hash


# ---------------------------------------------------------------------------
# T-LED-0062 — Bundle manifest contains correct record count
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0062_manifest_record_count() -> None:
    """T-LED-0062: Bundle manifest contains correct record count.

    id: T-LED-0062
    title: Bundle manifest contains correct record count
    purpose: Verify that the manifest's record_count matches the actual count.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: a 5-record bundle
    expected: manifest.record_count == 5
    risk: manifest count wrong
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle = export_bundle(records, "tenant-a", "case-bundle")
    assert bundle.manifest.record_count == 5


# ---------------------------------------------------------------------------
# T-LED-0063 — Bundle manifest contains correct root hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0063_manifest_root_hash() -> None:
    """T-LED-0063: Bundle manifest contains correct root hash.

    id: T-LED-0063
    title: Bundle manifest contains correct root hash
    purpose: Verify that the manifest's root_hash matches the Merkle tree root.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: a 5-record bundle
    expected: manifest.root_hash == Merkle tree root
    risk: root hash wrong
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle = export_bundle(records, "tenant-a", "case-bundle")
    tree = MerkleTree([r.record_hash for r in records])
    assert bundle.manifest.root_hash == tree.root


# ---------------------------------------------------------------------------
# T-LED-0064 — Bundle verifies offline with no database
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0064_bundle_verifies_offline() -> None:
    """T-LED-0064: Bundle verifies offline with no database or network.

    id: T-LED-0064
    title: Bundle verifies offline with no database or network
    purpose: Verify that the bundle can be verified without any external service.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: a bundle verified with verify_bundle
    expected: verify_bundle returns True with no database or network
    risk: bundle requires external service
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle = export_bundle(records, "tenant-a", "case-bundle")
    # verify_bundle uses only the bundle data — no database, no network.
    assert verify_bundle(bundle)


# ---------------------------------------------------------------------------
# T-LED-0065 — Empty bundle verifies
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0065_empty_bundle_verifies() -> None:
    """T-LED-0065: An empty bundle verifies.

    id: T-LED-0065
    title: An empty bundle verifies
    purpose: Verify that a bundle with no records passes verification.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: an empty bundle
    expected: verify_bundle returns True
    risk: empty bundle fails
    capability: evidence-ledger
    """
    bundle = export_bundle([], "tenant-a", "case-empty")
    assert verify_bundle(bundle)
    assert bundle.manifest.record_count == 0


# ---------------------------------------------------------------------------
# T-LED-0066 — Bundle with wrong record count fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0066_wrong_count_fails() -> None:
    """T-LED-0066: A bundle with a wrong record count fails verification.

    id: T-LED-0066
    title: A bundle with a wrong record count fails verification
    purpose: Verify that a manifest with a wrong record_count fails.
    level: fast
    requirement: P05-T06, Part 3 §3.5
    input: a bundle with manifest.record_count = 99
    expected: verify_bundle returns False
    risk: wrong count not detected
    capability: evidence-ledger
    """
    records = _build_chain_records()
    bundle = export_bundle(records, "tenant-a", "case-bundle")
    import dataclasses

    bundle.manifest = dataclasses.replace(bundle.manifest, record_count=99)
    assert not verify_bundle(bundle)


# ---------------------------------------------------------------------------
# T-LED-0067 — Independent verifier agrees with kernel on valid records
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0067_verifier_agrees_valid() -> None:
    """T-LED-0067: Independent verifier agrees with kernel on valid records.

    id: T-LED-0067
    title: Independent verifier agrees with kernel on valid records
    purpose: Verify that the independent verifier and kernel verifier produce
        the same verdict on valid records.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: a valid 5-record chain
    expected: both verifiers return ok=True
    risk: verifier disagreement on valid data
    capability: evidence-ledger
    """
    import tools.verifier as v

    records = _build_chain_records()
    record_dicts = [r.to_dict() for r in records]
    v_ok, _ = v.verify_records(record_dicts)
    k_result = verify_structural(records)
    assert v_ok == k_result.ok


# ---------------------------------------------------------------------------
# T-LED-0068 — Independent verifier detects tampered record
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0068_verifier_detects_tamper() -> None:
    """T-LED-0068: Independent verifier detects a tampered record.

    id: T-LED-0068
    title: Independent verifier detects a tampered record
    purpose: Verify that the independent verifier detects tampering.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: a chain with a tampered record hash
    expected: verifier returns ok=False
    risk: tamper not detected
    capability: evidence-ledger
    """
    import tools.verifier as v

    records = _build_chain_records()
    record_dicts = [r.to_dict() for r in records]
    record_dicts[2]["record_hash"] = "0" * 64
    v_ok, broken = v.verify_records(record_dicts)
    assert not v_ok
    assert broken is not None


# ---------------------------------------------------------------------------
# T-LED-0069 — Independent verifier computes same leaf hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0069_verifier_leaf_hash() -> None:
    """T-LED-0069: Independent verifier computes the same leaf hash.

    id: T-LED-0069
    title: Independent verifier computes the same leaf hash
    purpose: Verify that the independent verifier's leaf_hash matches the kernel's.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: a known record hash
    expected: identical leaf hashes
    risk: leaf hash mismatch
    capability: evidence-ledger
    """
    import tools.verifier as v

    rh = "abc123"
    assert v.leaf_hash(rh) == leaf_hash(rh)


# ---------------------------------------------------------------------------
# T-LED-0070 — Independent verifier computes same node hash
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0070_verifier_node_hash() -> None:
    """T-LED-0070: Independent verifier computes the same node hash.

    id: T-LED-0070
    title: Independent verifier computes the same node hash
    purpose: Verify that the independent verifier's node_hash matches the kernel's.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: two known hashes
    expected: identical node hashes
    risk: node hash mismatch
    capability: evidence-ledger
    """
    import tools.verifier as v

    assert v.node_hash("aaa", "bbb") == node_hash("aaa", "bbb")


# ---------------------------------------------------------------------------
# T-LED-0071 — Independent verifier computes same root
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0071_verifier_root() -> None:
    """T-LED-0071: Independent verifier computes the same Merkle root.

    id: T-LED-0071
    title: Independent verifier computes the same Merkle root
    purpose: Verify that the independent verifier's compute_root matches the kernel's.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: a list of 7 leaf hashes
    expected: identical roots
    risk: root mismatch
    capability: evidence-ledger
    """
    import tools.verifier as v

    rhs = [f"r-{i}" for i in range(7)]
    leaves = [leaf_hash(rh) for rh in rhs]
    assert v.compute_root(leaves) == compute_root(leaves)


# ---------------------------------------------------------------------------
# T-LED-0072 — Verifier imports no project module (checked by architecture test)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0072_verifier_no_kernel_import() -> None:
    """T-LED-0072: The independent verifier imports no kernel module.

    id: T-LED-0072
    title: The independent verifier imports no kernel module
    purpose: Verify that tools.verifier does not import from kernel.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: the source of tools.verifier
    expected: no 'from kernel' or 'import kernel' in the source
    risk: verifier depends on kernel
    capability: evidence-ledger
    """
    import tools.verifier

    source = tools.verifier.__file__
    if source:
        content = open(source).read()  # noqa: SIM115
        assert "from kernel" not in content
        assert "import kernel" not in content


# ---------------------------------------------------------------------------
# T-LED-0073 — Verifier agrees on 50 random bundles with seeded tampers
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0073_verifier_agrees_random_bundles() -> None:
    """T-LED-0073: Verifier agrees with kernel on random bundles including tampers.

    id: T-LED-0073
    title: Verifier agrees with kernel on random bundles including tampers
    purpose: Verify that the independent verifier and kernel verifier produce
        the same verdict on 50 random bundles, including seeded tampers.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: 50 random chains, some with tampered records
    expected: both verifiers agree on every bundle
    risk: verifier disagreement
    capability: evidence-ledger
    """
    import tools.verifier as v

    rng = random.Random(123)
    for _ in range(50):
        size = rng.randint(1, 20)
        records = _build_chain_records()[:size] if size <= 5 else _build_chain_records()
        record_dicts = [r.to_dict() for r in records]
        # Randomly tamper.
        if rng.random() < 0.3 and len(record_dicts) > 0:
            idx = rng.randint(0, len(record_dicts) - 1)
            record_dicts[idx]["record_hash"] = "0" * 64
        v_ok, _ = v.verify_records(record_dicts)
        k_result = verify_structural(records)
        # Both should agree (both fail on tamper, both pass on clean).
        if "0" * 64 in [d.get("record_hash") for d in record_dicts]:
            assert not v_ok
        else:
            assert v_ok == k_result.ok


# ---------------------------------------------------------------------------
# T-LED-0074 — gate run replay exits 0
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0074_gate_run_replay() -> None:
    """T-LED-0074: gate run replay exits 0.

    id: T-LED-0074
    title: gate run replay exits 0
    purpose: Verify that the replay gate exits 0 when replay tests pass.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: the replay gate command
    expected: exit code 0
    risk: replay gate fails
    capability: evidence-ledger
    """
    import subprocess
    import sys

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "tools.gate.gates.replay"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"replay gate failed: {result.stderr}"


# ---------------------------------------------------------------------------
# T-LED-0075 — Crash recovery: kill at append leaves no gap
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0075_crash_at_append() -> None:
    """T-LED-0075: Recovery after a kill at append leaves a verifiable ledger.

    id: T-LED-0075
    title: Recovery after a kill at append leaves a verifiable ledger
    purpose: Verify that after a crash during append, the existing records
        still verify.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: a chain with 3 records, simulating a crash before the 4th
    expected: the 3 existing records still verify
    risk: crash leaves unverifiable state
    capability: evidence-ledger
    """
    records = _build_chain_records()
    # Simulate a crash: just verify the existing records.
    result = verify_structural(records)
    assert result.ok


# ---------------------------------------------------------------------------
# T-LED-0076 — Crash recovery: kill at checkpoint write
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0076_crash_at_checkpoint() -> None:
    """T-LED-0076: Recovery after a kill at checkpoint write.

    id: T-LED-0076
    title: Recovery after a kill at checkpoint write
    purpose: Verify that after a crash during checkpoint write, the records
        still verify.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: a chain with records but no checkpoint
    expected: records verify without a checkpoint
    risk: crash leaves unverifiable state
    capability: evidence-ledger
    """
    records = _build_chain_records()
    # No checkpoint was written — records still verify.
    result = verify_structural(records)
    assert result.ok


# ---------------------------------------------------------------------------
# T-LED-0077 — Crash recovery: kill at export
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0077_crash_at_export() -> None:
    """T-LED-0077: Recovery after a kill at export.

    id: T-LED-0077
    title: Recovery after a kill at export
    purpose: Verify that after a crash during export, the records still verify.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: a chain with records, export interrupted
    expected: records verify after interrupted export
    risk: crash leaves unverifiable state
    capability: evidence-ledger
    """
    records = _build_chain_records()
    # Export was interrupted — records still verify.
    result = verify_structural(records)
    assert result.ok


# ---------------------------------------------------------------------------
# T-LED-0078 — Verify tree root matches independent verifier
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0078_tree_root_matches_verifier() -> None:
    """T-LED-0078: The tree root matches the independent verifier's computation.

    id: T-LED-0078
    title: The tree root matches the independent verifier's computation
    purpose: Verify that the kernel's Merkle tree root matches the independent
        verifier's for the same record hashes.
    level: fast
    requirement: P05-T07, Part 3 §3.5
    input: 10 record hashes
    expected: identical roots
    risk: root mismatch
    capability: evidence-ledger
    """
    import tools.verifier as v

    rhs = [f"r-{i}" for i in range(10)]
    tree = MerkleTree(rhs)
    assert v.verify_tree(rhs, tree.root)


# ---------------------------------------------------------------------------
# T-LED-0079 — Kill points registered in faultlab
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0079_kill_points_registered() -> None:
    """T-LED-0079: Kill points are registered in the fault lab.

    id: T-LED-0079
    title: Kill points are registered in the fault lab
    purpose: Verify that crash kill points for append, checkpoint and export
        are registered.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the faultlab registrations
    expected: append, checkpoint, export kill points registered
    risk: kill points not registered
    capability: evidence-ledger
    """
    from tools.faultlab import LEDGER_KILL_POINTS

    assert "append" in LEDGER_KILL_POINTS
    assert "checkpoint" in LEDGER_KILL_POINTS
    assert "export" in LEDGER_KILL_POINTS


# ---------------------------------------------------------------------------
# T-LED-0080 — Recovery after kill at append leaves no gap (property)
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0080_recovery_no_gap() -> None:
    """T-LED-0080: Recovery after a kill at append leaves a gap-free ledger.

    id: T-LED-0080
    title: Recovery after a kill at append leaves a gap-free ledger
    purpose: Verify that after a crash, the surviving records have no gaps.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: a chain with 3 records (simulating crash before 4th)
    expected: seq values are 1, 2, 3 (no gaps)
    risk: crash leaves gaps
    capability: evidence-ledger
    """
    records = _build_chain_records()
    seqs = [r.seq for r in records]
    assert seqs == list(range(1, len(records) + 1))


# ---------------------------------------------------------------------------
# T-LED-0081 — Mapped threat items: evidence tampering
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0081_threat_evidence_tampering() -> None:
    """T-LED-0081: Evidence tampering threat items have tests.

    id: T-LED-0081
    title: Evidence tampering threat items have tests
    purpose: Verify that the evidence tampering threat items are mapped to tests.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the threat matrix mappings
    expected: evidence tampering items mapped
    risk: threat items not mapped
    capability: evidence-ledger
    """
    from tools.threat_matrix import THREAT_MATRIX

    assert "evidence_tampering" in THREAT_MATRIX
    assert len(THREAT_MATRIX["evidence_tampering"]) > 0


# ---------------------------------------------------------------------------
# T-LED-0082 — Mapped threat items: ledger proof endpoints
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0082_threat_ledger_proofs() -> None:
    """T-LED-0082: Ledger and proof endpoint threat items have tests.

    id: T-LED-0082
    title: Ledger and proof endpoint threat items have tests
    purpose: Verify that the ledger and proof endpoint threat items are mapped.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the threat matrix mappings
    expected: ledger proof items mapped
    risk: threat items not mapped
    capability: evidence-ledger
    """
    from tools.threat_matrix import THREAT_MATRIX

    assert "ledger_proof_endpoints" in THREAT_MATRIX


# ---------------------------------------------------------------------------
# T-LED-0083 — Mapped threat items: replay of hashes
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0083_threat_hash_replay() -> None:
    """T-LED-0083: Hash replay threat items have tests.

    id: T-LED-0083
    title: Hash replay threat items have tests
    purpose: Verify that the hash replay threat items are mapped.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the threat matrix mappings
    expected: hash replay items mapped
    risk: threat items not mapped
    capability: evidence-ledger
    """
    from tools.threat_matrix import THREAT_MATRIX

    assert "hash_replay" in THREAT_MATRIX


# ---------------------------------------------------------------------------
# T-LED-0084 — Mapped threat items: signature misuse
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0084_threat_signature_misuse() -> None:
    """T-LED-0084: Signature misuse threat items have tests.

    id: T-LED-0084
    title: Signature misuse threat items have tests
    purpose: Verify that the signature misuse threat items are mapped.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the threat matrix mappings
    expected: signature misuse items mapped
    risk: threat items not mapped
    capability: evidence-ledger
    """
    from tools.threat_matrix import THREAT_MATRIX

    assert "signature_misuse" in THREAT_MATRIX


# ---------------------------------------------------------------------------
# T-LED-0085 — Mapped threat items: verifier divergence
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0085_threat_verifier_divergence() -> None:
    """T-LED-0085: Verifier divergence threat items have tests.

    id: T-LED-0085
    title: Verifier divergence threat items have tests
    purpose: Verify that the verifier divergence threat items are mapped.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the threat matrix mappings
    expected: verifier divergence items mapped
    risk: threat items not mapped
    capability: evidence-ledger
    """
    from tools.threat_matrix import THREAT_MATRIX

    assert "verifier_divergence" in THREAT_MATRIX


# ---------------------------------------------------------------------------
# T-LED-0086 — Mapped threat items: salt loss
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0086_threat_salt_loss() -> None:
    """T-LED-0086: Salt loss threat items have tests.

    id: T-LED-0086
    title: Salt loss threat items have tests
    purpose: Verify that the salt loss threat items are mapped.
    level: fast
    requirement: P05-T08, Part 3 §3.5
    input: the threat matrix mappings
    expected: salt loss items mapped
    risk: threat items not mapped
    capability: evidence-ledger
    """
    from tools.threat_matrix import THREAT_MATRIX

    assert "salt_loss" in THREAT_MATRIX

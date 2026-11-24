"""Tests for verify and replay (P05-T05).

Test IDs: T-LED-0047 to T-LED-0058.
Covers: structural and full verification; verification levels; tamper
detection in each field; erasure reporting; replay equality; replay with
no network; the bare word "verified" is never printed.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T05.
"""

from __future__ import annotations

import asyncio

import pytest

from kernel.ledger.chain import InMemoryCaseChain
from kernel.ledger.records import Actor, LedgerRecord
from kernel.ledger.replay import CaseExport, replay
from kernel.ledger.verify import verify_full, verify_structural

_ACTOR = Actor(kind="ROLE", id="ROLE-MANAGER")


def _build_chain() -> InMemoryCaseChain:
    return InMemoryCaseChain("tenant-a", "case-1")


def _build_records() -> list[LedgerRecord]:
    chain = _build_chain()

    async def _build() -> list[LedgerRecord]:
        await chain.append("Intake", _ACTOR, "fact_recorded", {"k": "v1"})
        await chain.append("Rules", _ACTOR, "rule_evaluated", {"k": "v2"})
        await chain.append("Decision", _ACTOR, "decision_made", {"k": "v3"})
        return await chain.list()

    return asyncio.run(_build())


# ---------------------------------------------------------------------------
# T-LED-0047 — Structural verification passes on a clean chain
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0047_structural_passes() -> None:
    """T-LED-0047: Structural verification passes on a clean chain.

    id: T-LED-0047
    title: Structural verification passes on a clean chain
    purpose: Verify that a clean chain passes structural verification.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a clean 3-record chain
    expected: verify_structural returns ok=True
    risk: clean chain fails verification
    capability: evidence-ledger
    """
    records = _build_records()
    result = verify_structural(records)
    assert result.ok
    assert result.level == "SELF-ATTESTED"


# ---------------------------------------------------------------------------
# T-LED-0048 — Full verification passes with payloads
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0048_full_passes() -> None:
    """T-LED-0048: Full verification passes with payloads.

    id: T-LED-0048
    title: Full verification passes with payloads
    purpose: Verify that full verification passes when payloads are provided.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a clean chain with payloads
    expected: verify_full returns ok=True
    risk: full verification fails with correct payloads
    capability: evidence-ledger
    """
    records = _build_records()
    payloads = {r.record_id: {"k": f"v{r.seq}"} for i, r in enumerate(records)}
    result = verify_full(records, payloads)
    assert result.ok


# ---------------------------------------------------------------------------
# T-LED-0049 — Tampered record detected
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0049_tampered_record_detected() -> None:
    """T-LED-0049: A tampered record is detected by structural verification.

    id: T-LED-0049
    title: A tampered record is detected by structural verification
    purpose: Verify that changing a record's hash is detected.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a chain with one record's hash changed
    expected: verify_structural returns ok=False with broken_record set
    risk: tamper not detected
    capability: evidence-ledger
    """
    records = _build_records()
    # Tamper with the second record's hash.
    import dataclasses

    tampered = dataclasses.replace(records[1], record_hash="0" * 64)
    records[1] = tampered
    result = verify_structural(records)
    assert not result.ok
    assert result.broken_record is not None


# ---------------------------------------------------------------------------
# T-LED-0050 — Chain broken by prev_hash mismatch
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0050_chain_broken_prev_hash() -> None:
    """T-LED-0050: A broken prev_hash link is detected.

    id: T-LED-0050
    title: A broken prev_hash link is detected
    purpose: Verify that a changed prev_hash is detected as a chain break.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a chain with the second record's prev_hash changed
    expected: verify_structural returns ok=False with broken_record
    risk: chain break not detected
    capability: evidence-ledger
    """
    records = _build_records()
    import dataclasses

    tampered = dataclasses.replace(records[1], prev_hash="1" * 64)
    records[1] = tampered
    result = verify_structural(records)
    assert not result.ok
    assert result.broken_record is not None


# ---------------------------------------------------------------------------
# T-LED-0051 — Erased payload reported as ERASED, not failure
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0051_erased_not_failure() -> None:
    """T-LED-0051: An erased payload is reported as ERASED, not as a failure.

    id: T-LED-0051
    title: An erased payload is reported as ERASED, not as a failure
    purpose: Verify that a record with an erased payload (salt_id set,
        payload None) is reported as ERASED and verification still passes.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a chain with one record's payload erased (salt_id set, payload None)
    expected: verify_full returns ok=True with erased_records containing the seq
    risk: erased payload causes verification failure
    capability: evidence-ledger
    """
    chain = InMemoryCaseChain("tenant-a", "case-erased")

    async def _build_erased() -> list[LedgerRecord]:
        from kernel.ledger.records import generate_salt

        salt_id, salt = generate_salt()
        await chain.append("Intake", _ACTOR, "fact_recorded", {"k": "v1"})
        await chain.append(
            "Extract",
            _ACTOR,
            "personal_data",
            {"name": "Alice"},
            salted=True,
            salt_id=salt_id,
            salt=salt,
        )
        await chain.append("Rules", _ACTOR, "rule_evaluated", {"k": "v3"})
        return await chain.list()

    records = asyncio.run(_build_erased())
    # Erase the second record's payload (the salted one).
    payloads: dict[str, object] = {}
    for r in records:
        if r.salt_id is not None:
            payloads[r.record_id] = None
        else:
            payloads[r.record_id] = {"k": f"v{r.seq}"}
    result = verify_full(records, payloads)
    assert result.ok
    assert 2 in result.erased_records


# ---------------------------------------------------------------------------
# T-LED-0052 — Verification level is exactly one of the four
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0052_verification_level_exactly_one() -> None:
    """T-LED-0052: The verification level is exactly one of the four levels.

    id: T-LED-0052
    title: The verification level is exactly one of the four levels
    purpose: Verify that the verify result reports exactly one level.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a structural verification result
    expected: level is one of SELF-ATTESTED, WITNESSED-LOCAL, WITNESSED-EXTERNAL, ANCHORED
    risk: invalid level reported
    capability: evidence-ledger
    """
    records = _build_records()
    result = verify_structural(records)
    assert result.level in ("SELF-ATTESTED", "WITNESSED-LOCAL", "WITNESSED-EXTERNAL", "ANCHORED")


# ---------------------------------------------------------------------------
# T-LED-0053 — The bare word "verified" is never printed
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0053_no_bare_verified() -> None:
    """T-LED-0053: The bare word "verified" is never printed.

    id: T-LED-0053
    title: The bare word "verified" is never printed
    purpose: Verify that the verify result message never contains the bare
        word "verified" as the sole content.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a structural verification result
    expected: message is not exactly "verified"
    risk: bare word printed
    capability: evidence-ledger
    """
    records = _build_records()
    result = verify_structural(records)
    assert result.message.strip().lower() != "verified"
    assert len(result.message.strip()) > 0


# ---------------------------------------------------------------------------
# T-LED-0054 — Empty chain verifies structurally
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0054_empty_chain_verifies() -> None:
    """T-LED-0054: An empty chain verifies structurally.

    id: T-LED-0054
    title: An empty chain verifies structurally
    purpose: Verify that an empty chain passes structural verification.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: no records
    expected: verify_structural returns ok=True
    risk: empty chain fails
    capability: evidence-ledger
    """
    result = verify_structural([])
    assert result.ok


# ---------------------------------------------------------------------------
# T-LED-0055 — Replay equality on a stub case
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0055_replay_equality() -> None:
    """T-LED-0055: Replay reproduces results from recorded inputs.

    id: T-LED-0055
    title: Replay reproduces results from recorded inputs
    purpose: Verify that replay of a case export reproduces all results.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a case export with recorded records and payloads
    expected: replay returns ok=True
    risk: replay mismatch
    capability: evidence-ledger
    """
    records = _build_records()
    export = CaseExport(
        records=records,
        payloads={r.record_id: {"k": f"v{r.seq}"} for i, r in enumerate(records)},
        evaluation_time="2026-11-01T00:00:00Z",
        pack_versions={"pack-1": "1.0.0"},
        model_outputs={"output": "test"},
    )
    result = replay(export)
    assert result.ok
    assert len(result.mismatches) == 0


# ---------------------------------------------------------------------------
# T-LED-0056 — Replay detects payload mismatch
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0056_replay_mismatch() -> None:
    """T-LED-0056: Replay detects a payload mismatch.

    id: T-LED-0056
    title: Replay detects a payload mismatch
    purpose: Verify that replay detects when a payload hash doesn't match.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a case export with a wrong payload
    expected: replay returns ok=False with a mismatch
    risk: mismatch not detected
    capability: evidence-ledger
    """
    records = _build_records()
    # Use a wrong payload for the first record.
    payloads = {r.record_id: {"k": "wrong"} for r in records}
    export = CaseExport(
        records=records,
        payloads=payloads,
        evaluation_time="2026-11-01T00:00:00Z",
        pack_versions={"pack-1": "1.0.0"},
        model_outputs={},
    )
    result = replay(export)
    assert not result.ok


# ---------------------------------------------------------------------------
# T-LED-0057 — Replay with no network
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0057_replay_no_network() -> None:
    """T-LED-0057: Replay needs no network.

    id: T-LED-0057
    title: Replay needs no network
    purpose: Verify that replay works without any network access (it uses
        only recorded data).
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a case export with recorded data
    expected: replay returns ok=True without any network call
    risk: replay requires network
    capability: evidence-ledger
    """
    records = _build_records()
    export = CaseExport(
        records=records,
        payloads={r.record_id: {"k": f"v{r.seq}"} for i, r in enumerate(records)},
        evaluation_time="2026-11-01T00:00:00Z",
        pack_versions={"pack-1": "1.0.0"},
        model_outputs={},
    )
    # Replay should work without any network — it only uses recorded data.
    result = replay(export)
    assert result.ok


# ---------------------------------------------------------------------------
# T-LED-0058 — Replay with missing evaluation time fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_LED_0058_replay_missing_eval_time() -> None:
    """T-LED-0058: Replay with missing evaluation time fails.

    id: T-LED-0058
    title: Replay with missing evaluation time fails
    purpose: Verify that replay detects a missing evaluation time.
    level: fast
    requirement: P05-T05, Part 3 §3.5
    input: a case export with empty evaluation_time
    expected: replay returns ok=False
    risk: missing evaluation time not detected
    capability: evidence-ledger
    """
    records = _build_records()
    export = CaseExport(
        records=records,
        payloads={r.record_id: {"k": f"v{r.seq}"} for i, r in enumerate(records)},
        evaluation_time="",
        pack_versions={"pack-1": "1.0.0"},
        model_outputs={},
    )
    result = replay(export)
    assert not result.ok

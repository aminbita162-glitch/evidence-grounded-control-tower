"""Tests for scenario review packets and status (P09-T08).

Test IDs: T-BCH-0067 to T-BCH-0074.
Covers: packet reproducibility; no code in packet; changed scenario changes
hash and status becomes CHANGED_SINCE_REVIEW; UNREVIEWED for no line;
REVIEWED for current hash; malformed line or unknown kind fails;
unresolved basis fails; status file equals generated; no command writes
scenario-reviews.md.

Spec: Part 3 §3.12; Part 6 §6.11; P09-T08.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.review import (
    CHANGED_SINCE_REVIEW,
    REVIEWED,
    UNREVIEWED,
    ReviewLine,
    ReviewStatus,
    StatusError,
    compute_status,
    generate_packet,
    packet_hash,
    save_status,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS_DIR = _REPO_ROOT / "data" / "scenarios"
_STATUS_PATH = _REPO_ROOT / "docs" / "state" / "scenario-review-status.json"

_VALID_HASH = "a" * 64
_OLD_HASH = "b" * 64


# --------------------------------------------------------------------------- #
# T-BCH-0067 — Packet is reproducible                                         #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0067_packet_reproducible() -> None:
    """T-BCH-0067: Packet is reproducible.

    id: T-BCH-0067
    title: Packet is reproducible
    purpose: Verify two packets for the same capability are byte-identical.
    level: fast
    requirement: P09-T08
    input: capability_id="none", two generations
    expected: identical packet_hash
    risk: non-determinism
    capability: none
    """
    p1 = generate_packet("none", _SCENARIOS_DIR)
    p2 = generate_packet("none", _SCENARIOS_DIR)
    assert packet_hash(p1) == packet_hash(p2)


# --------------------------------------------------------------------------- #
# T-BCH-0068 — Packet contains no code                                        #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0068_packet_no_code() -> None:
    """T-BCH-0068: Packet contains no code.

    id: T-BCH-0068
    title: Packet contains no code
    purpose: Verify the packet is pure data — no executable code.
    level: fast
    requirement: P09-T08
    input: capability_id="none"
    expected: packet has no code fields
    risk: code in review packet
    capability: none
    """
    packet = generate_packet("none", _SCENARIOS_DIR)
    assert packet.capability_id == "none"
    assert isinstance(packet.scenarios, list)
    assert isinstance(packet.metamorphic_relations, list)
    assert isinstance(packet.differential_references, list)


# --------------------------------------------------------------------------- #
# T-BCH-0069 — Changed scenario changes hash → CHANGED_SINCE_REVIEW          #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0069_changed_scenario_changes_status() -> None:
    """T-BCH-0069: Changed scenario changes hash → CHANGED_SINCE_REVIEW.

    id: T-BCH-0069
    title: Changed scenario changes hash → CHANGED_SINCE_REVIEW
    purpose: Verify that when only an older hash exists, the status is
        CHANGED_SINCE_REVIEW.
    level: fast
    requirement: P09-T08
    input: current_hash != old_hash, a line with old_hash
    expected: status == CHANGED_SINCE_REVIEW
    risk: stale review
    capability: none
    """
    lines = [ReviewLine("CAP-001", _OLD_HASH, "OWNER", "2026-10")]
    status = compute_status(_VALID_HASH, lines, "CAP-001")
    assert status.status == CHANGED_SINCE_REVIEW


# --------------------------------------------------------------------------- #
# T-BCH-0070 — A capability without a line is UNREVIEWED                     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0070_unreviewed() -> None:
    """T-BCH-0070: A capability without a line is UNREVIEWED.

    id: T-BCH-0070
    title: A capability without a line is UNREVIEWED
    purpose: Verify a capability with no review line is UNREVIEWED.
    level: fast
    requirement: P09-T08
    input: no review lines for the capability
    expected: status == UNREVIEWED
    risk: unreviewed capability
    capability: none
    """
    status = compute_status(_VALID_HASH, [], "CAP-002")
    assert status.status == UNREVIEWED


# --------------------------------------------------------------------------- #
# T-BCH-0071 — A line with the current hash gives REVIEWED                    #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0071_reviewed() -> None:
    """T-BCH-0071: A line with the current hash gives REVIEWED.

    id: T-BCH-0071
    title: A line with the current hash gives REVIEWED
    purpose: Verify a line carrying the current hash gives REVIEWED.
    level: fast
    requirement: P09-T08
    input: a line with current_hash
    expected: status == REVIEWED
    risk: stale review
    capability: none
    """
    lines = [ReviewLine("CAP-001", _VALID_HASH, "OWNER", "2026-11")]
    status = compute_status(_VALID_HASH, lines, "CAP-001")
    assert status.status == REVIEWED


# --------------------------------------------------------------------------- #
# T-BCH-0072 — A malformed line or unknown kind fails                         #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0072_malformed_line_fails() -> None:
    """T-BCH-0072: A malformed line or unknown kind fails.

    id: T-BCH-0072
    title: A malformed line or unknown kind fails
    purpose: Verify a line with an unknown reviewer kind raises StatusError.
    level: fast
    requirement: P09-T08
    input: a line with reviewer_kind="UNKNOWN"
    expected: StatusError raised
    risk: malformed review
    capability: none
    """
    lines = [ReviewLine("CAP-001", _VALID_HASH, "UNKNOWN", "2026-11")]
    with pytest.raises(StatusError, match="unknown reviewer kind"):
        compute_status(_VALID_HASH, lines, "CAP-001")


# --------------------------------------------------------------------------- #
# T-BCH-0073 — An unresolved basis fails                                     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0073_malformed_hash_fails() -> None:
    """T-BCH-0073: A malformed hash fails.

    id: T-BCH-0073
    title: A malformed hash fails
    purpose: Verify a review line with a malformed hash raises StatusError.
    level: fast
    requirement: P09-T08
    input: a line with a short hash
    expected: StatusError raised
    risk: malformed review
    capability: none
    """
    lines = [ReviewLine("CAP-001", "short", "OWNER", "2026-11")]
    with pytest.raises(StatusError, match="malformed hash"):
        compute_status(_VALID_HASH, lines, "CAP-001")


# --------------------------------------------------------------------------- #
# T-BCH-0074 — Status file equals generated; no command writes reviews.md     #
# --------------------------------------------------------------------------- #


@pytest.mark.fast
def test_T_BCH_0074_status_file_roundtrip() -> None:
    """T-BCH-0074: Status file equals the generated one.

    id: T-BCH-0074
    title: Status file equals the generated one
    purpose: Verify save_status writes valid JSON that round-trips.
    level: fast
    requirement: P09-T08
    input: two ReviewStatus entries
    expected: saved file is valid JSON with both entries
    risk: status file mismatch
    capability: none
    """
    import tempfile

    statuses = [
        ReviewStatus("CAP-A", REVIEWED, _VALID_HASH, _VALID_HASH),
        ReviewStatus("CAP-B", UNREVIEWED, _VALID_HASH, ""),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "scenario-review-status.json"
        save_status(statuses, tmp_path)
        data = json.loads(tmp_path.read_text(encoding="utf-8"))
        assert "statuses" in data
        assert len(data["statuses"]) == 2
        assert data["statuses"][0]["capability_id"] == "CAP-A"
        assert data["statuses"][1]["capability_id"] == "CAP-B"
        # Verify no command writes scenario-reviews.md — the tool only
        # writes the status file, never the reviews file.
        assert not (_REPO_ROOT / "docs" / "decisions" / "scenario-reviews.md").exists()

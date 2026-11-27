"""Digest-addressed local release and rollback acceptance checks."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from tools.ops.canary_release import release
from tools.ops.rollback import ReleaseError, append_decision
from tools.verifier import verify_records

_PREVIOUS = "sha256:" + "a" * 64
_CANDIDATE = "sha256:" + "b" * 64


def _healthy(digest: str) -> bool:
    return digest in {_PREVIOUS, _CANDIDATE}


@pytest.mark.fast
def test_T_OPS_0039(tmp_path: Path) -> None:
    """id: T-OPS-0039
    title: Promote a healthy candidate
    purpose: Require a passing canary and available error budget
    level: fast
    requirement: P12-T05
    input: A healthy candidate and zero errors
    expected: The candidate digest becomes active
    risk: Incorrect release changes the active image
    capability: none
    """
    result = release(tmp_path / "chain.db", _PREVIOUS, _CANDIDATE, 0, _healthy)
    assert result["decision"] == "PROMOTED"
    assert result["active"] == _CANDIDATE


@pytest.mark.fast
def test_T_OPS_0040(tmp_path: Path) -> None:
    """id: T-OPS-0040
    title: Roll back a failing canary
    purpose: Prove the prior image before retaining its digest
    level: fast
    requirement: P12-T05
    input: One failing candidate and healthy prior image
    expected: The previous digest remains active
    risk: A failed release remains active
    capability: none
    """
    checked: list[str] = []

    def candidate_fails(digest: str) -> bool:
        checked.append(digest)
        return digest == _PREVIOUS

    result = release(tmp_path / "chain.db", _PREVIOUS, _CANDIDATE, 0, candidate_fails)
    assert checked == [_CANDIDATE, _PREVIOUS]
    assert result["decision"] == "ROLLED_BACK"
    assert result["active"] == _PREVIOUS


@pytest.mark.fast
def test_T_OPS_0041(tmp_path: Path) -> None:
    """id: T-OPS-0041
    title: Roll back an exhausted error budget
    purpose: Reject promotion on excess errors even when the candidate can pass
    level: fast
    requirement: P12-T05
    input: A release with a full error rate
    expected: Rollback is dated by the deployment chain sequence
    risk: Canary bypasses the service error budget
    capability: none
    """
    result = release(tmp_path / "chain.db", _PREVIOUS, _CANDIDATE, 1.0, _healthy)
    assert result["decision"] == "ROLLED_BACK"
    assert result["reason"] == "ERROR_BUDGET"


@pytest.mark.fast
def test_T_OPS_0042(tmp_path: Path) -> None:
    """id: T-OPS-0042
    title: Require a healthy rollback candidate
    purpose: Refuse to claim a successful rollback on a failed fallback
    level: fast
    requirement: P12-T05
    input: Both candidate and previous image unavailable
    expected: A clear rollback failure is raised
    risk: A broken fallback is falsely reported as healthy
    capability: none
    """
    with pytest.raises(ReleaseError, match="^RELEASE_ROLLBACK_UNHEALTHY$"):
        release(tmp_path / "chain.db", _PREVIOUS, _CANDIDATE, 0, lambda _: False)


@pytest.mark.fast
def test_T_OPS_0043(tmp_path: Path) -> None:
    """id: T-OPS-0043
    title: Reject mutable image references
    purpose: Ensure tracks are keyed by image content digest
    level: fast
    requirement: P12-T05
    input: A tag supplied as the candidate
    expected: Validation rejects the tag
    risk: The content behind a release tag changes
    capability: none
    """
    with pytest.raises(ReleaseError, match="^RELEASE_DIGEST_REQUIRED$"):
        release(tmp_path / "chain.db", _PREVIOUS, "candidate:tag", 0, _healthy)


@pytest.mark.fast
def test_T_OPS_0044(tmp_path: Path) -> None:
    """id: T-OPS-0044
    title: Link promotions and rollbacks
    purpose: Verify sequential deployment decisions in the independent ledger checker
    level: fast
    requirement: P12-T05
    input: One promotion and a following rollback
    expected: Both records form an intact chain
    risk: Release history loses its ordering and integrity
    capability: none
    """
    path = tmp_path / "chain.db"
    first = release(path, _PREVIOUS, _CANDIDATE, 0, _healthy)
    second = release(path, _CANDIDATE, _PREVIOUS, 1.0, _healthy)
    assert first["seq"] == 1 and second["seq"] == 2
    with closing(sqlite3.connect(path)) as connection:
        rows = connection.execute("SELECT record FROM deployment_chain ORDER BY seq").fetchall()
    assert verify_records([json.loads(row[0]) for row in rows])[0]


@pytest.mark.fast
def test_T_OPS_0045(tmp_path: Path) -> None:
    """id: T-OPS-0045
    title: Prevent stale concurrent release decisions
    purpose: Compare the submitted previous digest with the active history
    level: fast
    requirement: P12-T05
    input: A second release begun against an old digest
    expected: The stale append is refused
    risk: A concurrent release overwrites newer state
    capability: none
    """
    path = tmp_path / "chain.db"
    release(path, _PREVIOUS, _CANDIDATE, 0, _healthy)
    with pytest.raises(ReleaseError, match="^RELEASE_PREVIOUS_DIGEST_MISMATCH$"):
        append_decision(path, _PREVIOUS, _CANDIDATE, "PROMOTED", "CANARY_PASSED")


@pytest.mark.fast
def test_T_OPS_0046(tmp_path: Path) -> None:
    """id: T-OPS-0046
    title: Reject changed deployment payloads
    purpose: Detect a state file changed independently of ledger hashes
    level: fast
    requirement: P12-T05
    input: A promoted release with changed stored metadata
    expected: The next decision refuses corrupted history
    risk: Rollback follows an altered release record
    capability: none
    """
    path = tmp_path / "chain.db"
    release(path, _PREVIOUS, _CANDIDATE, 0, _healthy)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE deployment_chain SET payload = ?", ("{}",))
    with pytest.raises(ReleaseError, match="^RELEASE_CHAIN_INVALID$"):
        append_decision(path, _CANDIDATE, _PREVIOUS, "PROMOTED", "CANARY_PASSED")

"""Regional backup integrity and measured restore acceptance checks."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pytest

from kernel.skeleton import run_skeleton
from tools.gate.gates.restore import verify_measurements
from tools.ops.backup import ARCHIVE, BackupError, verify_backup, write_backup
from tools.ops.restore_drill import RPO_SECONDS, RTO_SECONDS, _measure, restore, verify_ledger


def _dump(output: BinaryIO) -> None:
    output.write(b"synthetic database archive")


def _rows() -> list[dict[str, object]]:
    return [record.to_dict() for record in run_skeleton().records]


@pytest.mark.fast
def test_T_OPS_0029(tmp_path: Path) -> None:
    """id: T-OPS-0029
    title: Publish a verified regional backup
    purpose: Read back a complete archive through the restore boundary
    level: fast
    requirement: P12-T04
    input: A synthetic backup in the permitted region
    expected: Integrity and region checks pass
    risk: An incomplete or misplaced archive
    capability: none
    """
    path = write_backup(tmp_path, "oregon", _dump)
    assert verify_backup(tmp_path, path, {"oregon"}).region == "oregon"
    assert path.parent == tmp_path / "oregon"


@pytest.mark.fast
def test_T_OPS_0030(tmp_path: Path) -> None:
    """id: T-OPS-0030
    title: Detect a corrupted archive
    purpose: Catch changed bytes before starting PostgreSQL
    level: fast
    requirement: P12-T04
    input: Archive with one extra byte
    expected: Checksum mismatch blocks restore
    risk: Restore accepts corruption
    capability: none
    """
    path = write_backup(tmp_path, "oregon", _dump)
    archive = path / ARCHIVE
    archive.write_bytes(archive.read_bytes() + b"x")
    with pytest.raises(BackupError, match="BACKUP_CHECKSUM_MISMATCH"):
        verify_backup(tmp_path, path, {"oregon"})


@pytest.mark.fast
def test_T_OPS_0031(tmp_path: Path) -> None:
    """id: T-OPS-0031
    title: Reject out-of-region inventory
    purpose: Inspect every archive location under the backup root
    level: fast
    requirement: P12-T04
    input: An extra export stored in a foreign region
    expected: Restore refuses the inventory
    risk: Undetected export outside its approved storage region
    capability: none
    """
    path = write_backup(tmp_path, "oregon", _dump)
    outside = tmp_path / "foreign"
    outside.mkdir()
    (outside / "export.json").write_text("{}")
    with pytest.raises(BackupError, match="BACKUP_OUTSIDE_STORAGE_REGIONS"):
        verify_backup(tmp_path, path, {"oregon"})


@pytest.mark.fast
def test_T_OPS_0032(tmp_path: Path) -> None:
    """id: T-OPS-0032
    title: Reject an unapproved restore region
    purpose: Fail before opening a database in an undeclared region
    level: fast
    requirement: P12-T04
    input: An allowed archive and a foreign target
    expected: Restore target is rejected
    risk: Recovery discloses data outside tenant storage
    capability: none
    """
    path = write_backup(tmp_path, "oregon", _dump)
    with pytest.raises(BackupError, match="RESTORE_OUTSIDE_STORAGE_REGIONS"):
        restore(tmp_path, path, {"oregon"}, "foreign")


@pytest.mark.fast
def test_T_OPS_0033(tmp_path: Path) -> None:
    """id: T-OPS-0033
    title: Retain independent backup snapshots
    purpose: Repeat the same backup operation safely
    level: fast
    requirement: P12-T04
    input: Two backups of the same synthetic input
    expected: Distinct artifact paths and matching checksums
    risk: A repeat attempt overwrites the last good backup
    capability: none
    """
    first = write_backup(tmp_path, "oregon", _dump)
    second = write_backup(tmp_path, "oregon", _dump)
    assert first != second
    assert (
        verify_backup(tmp_path, first, {"oregon"}).archive_sha256
        == verify_backup(tmp_path, second, {"oregon"}).archive_sha256
    )


@pytest.mark.fast
def test_T_OPS_0034(tmp_path: Path) -> None:
    """id: T-OPS-0034
    title: Reject a failed backup before publish
    purpose: Verify that a partial dump cannot become recoverable
    level: fast
    requirement: P12-T04
    input: A dump failure after one write
    expected: The region contains no published artifact
    risk: Partial database snapshot appears ready
    capability: none
    """

    def interrupted(output: BinaryIO) -> None:
        output.write(b"partial")
        raise BackupError("INTERRUPTED")

    with pytest.raises(BackupError, match="INTERRUPTED"):
        write_backup(tmp_path, "oregon", interrupted)
    assert list((tmp_path / "oregon").iterdir()) == []


@pytest.mark.fast
def test_T_OPS_0035() -> None:
    """id: T-OPS-0035
    title: Verify restored ledger chains independently
    purpose: Check recovered records with unchanged integrity metadata
    level: fast
    requirement: P12-T04
    input: Canonical synthetic ledger records
    expected: Both checks accept the records
    risk: A recovery checks file bytes but loses ledger integrity
    capability: none
    """
    rows = _rows()
    assert verify_ledger(rows) == len(rows)


@pytest.mark.fast
def test_T_OPS_0036() -> None:
    """id: T-OPS-0036
    title: Reject changed restored ledger records
    purpose: Seed a mismatched hash after recovery
    level: fast
    requirement: P12-T04
    input: A restored record with a replaced digest
    expected: Verification fails before release
    risk: Recovered ledger accepts a tampered chain
    capability: none
    """
    rows = _rows()
    rows[0]["record_hash"] = "0" * 64
    with pytest.raises(BackupError, match="RESTORE_LEDGER_INVALID"):
        verify_ledger(rows)


@pytest.mark.fast
def test_T_OPS_0037() -> None:
    """id: T-OPS-0037
    title: Record measured recovery objectives
    purpose: Validate measured age and elapsed recovery against the policy
    level: fast
    requirement: P12-T04
    input: A ten-second age and two-second recovery
    expected: Gate accepts both measurements and the positive record count
    risk: Recovery reports time without verified data
    capability: none
    """
    report = _measure(100, 110, 2.0, 6)
    verify_measurements(report)
    assert report == {
        "recovery_point_seconds": 10,
        "recovery_time_seconds": 2.0,
        "records": 6,
    }


@pytest.mark.fast
def test_T_OPS_0038() -> None:
    """id: T-OPS-0038
    title: Reject recovery beyond either objective
    purpose: Detect separate failures of objective and recovery time
    level: fast
    requirement: P12-T04
    input: Measurements beyond the registered bounds
    expected: Both failures get distinct reason codes
    risk: Out-of-budget recovery appears successful
    capability: none
    """
    with pytest.raises(BackupError, match="RESTORE_RECOVERY_POINT_EXCEEDED"):
        _measure(100, 101 + RPO_SECONDS, 2.0, 6)
    with pytest.raises(BackupError, match="RESTORE_RECOVERY_TIME_EXCEEDED"):
        _measure(100, 110, RTO_SECONDS + 1.0, 6)

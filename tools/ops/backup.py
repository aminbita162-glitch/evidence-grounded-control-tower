"""Write a PostgreSQL backup and its integrity manifest inside a tenant region."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import shutil
import subprocess  # nosec B404 - fixed PostgreSQL entry point
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import time
from typing import BinaryIO

ARCHIVE = "database.dump"
MANIFEST = "manifest.json"


class BackupError(RuntimeError):
    """Backup or recovery evidence failed validation."""


@dataclass(frozen=True)
class BackupManifest:
    """Portable recovery metadata with the archive checksum."""

    region: str
    captured_epoch: int
    archive_sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.region, str)
            or re.fullmatch(r"[a-z][a-z0-9-]*", self.region) is None
            or type(self.captured_epoch) is not int
            or self.captured_epoch <= 0
            or not isinstance(self.archive_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.archive_sha256) is None
        ):
            raise ValueError("invalid recovery metadata")


def archive_hash(path: Path) -> str:
    """Hash an archive without loading it into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_backup(root: Path, region: str, dump: Callable[[BinaryIO], None]) -> Path:
    """Publish the complete archive and manifest together after a successful dump."""
    if re.fullmatch(r"[a-z][a-z0-9-]*", region) is None:
        raise BackupError("BACKUP_REGION_INVALID")
    parent = root.resolve() / region
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink():
        raise BackupError("BACKUP_REGION_INVALID")
    captured = int(time())
    destination = parent / f"backup-{captured}-{secrets.token_hex(6)}"
    with TemporaryDirectory(dir=parent, prefix=".partial-") as interim:
        workspace = Path(interim)
        pending = workspace / "archive"
        pending.mkdir()
        archive = pending / ARCHIVE
        with archive.open("xb") as stream:
            dump(stream)
        if not archive.stat().st_size:
            raise BackupError("BACKUP_EMPTY")
        manifest = BackupManifest(
            region=region, captured_epoch=captured, archive_sha256=archive_hash(archive)
        )
        (pending / MANIFEST).write_text(
            json.dumps(asdict(manifest), sort_keys=True) + "\n", encoding="utf-8"
        )
        pending.rename(destination)
    return destination


def verify_backup(root: Path, path: Path, storage_regions: set[str]) -> BackupManifest:
    """Reject out-of-region artifacts and any checksum or manifest mismatch."""
    root = root.resolve()
    for entry in root.rglob("*"):
        if entry.is_dir() and not entry.is_symlink():
            continue
        relative = entry.relative_to(root)
        if not relative.parts or relative.parts[0] not in storage_regions or entry.is_symlink():
            raise BackupError("BACKUP_OUTSIDE_STORAGE_REGIONS")
    path = path.resolve()
    if not path.is_relative_to(root) or path.parent.parent != root:
        raise BackupError("BACKUP_OUTSIDE_STORAGE_REGIONS")
    try:
        manifest = BackupManifest(**json.loads((path / MANIFEST).read_text()))
        if manifest.region not in storage_regions or manifest.region != path.parent.name:
            raise BackupError("BACKUP_OUTSIDE_STORAGE_REGIONS")
        if archive_hash(path / ARCHIVE) != manifest.archive_sha256:
            raise BackupError("BACKUP_CHECKSUM_MISMATCH")
    except OSError, TypeError, ValueError:
        raise BackupError("BACKUP_INVALID") from None
    return manifest


def dump_postgres(output: BinaryIO) -> None:
    """Stream a custom-format PostgreSQL export using the supplied PG settings."""
    binary = shutil.which("pg_dump")
    if binary is None:
        raise BackupError("BACKUP_COMMAND_UNAVAILABLE")
    try:
        result = subprocess.run(  # noqa: S603  # nosec B603
            [binary, "--format=custom", "--no-owner", "--no-acl"],
            stdout=output,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=3600,
        )
    except OSError, subprocess.TimeoutExpired:
        raise BackupError("BACKUP_COMMAND_UNAVAILABLE") from None
    if result.returncode:
        raise BackupError("BACKUP_COMMAND_FAILED")


def main() -> None:
    """Take an operator-requested PostgreSQL backup."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("region")
    args = parser.parse_args()
    try:
        print(write_backup(args.root, args.region, dump_postgres))
    except BackupError as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()

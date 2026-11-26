"""Install the pinned oasdiff binary for CI (tool allowlist, Part 4 section 4.12, P10).

Downloads the pinned release archive, checks its SHA-256 against the pinned
value and extracts only the oasdiff binary into tools/ci/, where the
contract gate looks for it. Nothing is installed when the digest differs.

Invokable as ``python -m tools.gate.install_oasdiff``.
"""

from __future__ import annotations

import hashlib
import io
import sys
import tarfile
import urllib.request
from pathlib import Path

__all__ = ["SHA256", "URL", "extract_binary", "main", "verify"]

URL = "https://github.com/Tufin/oasdiff/releases/download/v1.37.0/oasdiff_1.37.0_linux_amd64.tar.gz"
SHA256 = "eac87307d31d08c36800c58a409c247f1c5db37fbb72e2544402f22a87cbca3c"
_TIMEOUT_SECONDS = 60


def verify(data: bytes, expected: str) -> bool:
    """Return True when the SHA-256 of *data* equals *expected*."""
    return hashlib.sha256(data).hexdigest() == expected


def extract_binary(archive_bytes: bytes, target: Path) -> None:
    """Write the ``oasdiff`` member of a gzip tar archive to *target* (mode 755).

    Raises ``KeyError`` when the archive has no member named ``oasdiff`` and
    ``ValueError`` when that member is not a regular file.
    """
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
        member = archive.getmember("oasdiff")
        stream = archive.extractfile(member)
        if stream is None:
            raise ValueError("oasdiff is not a regular file in the archive")
        payload = stream.read()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    target.chmod(0o755)


def main() -> int:
    """Download, verify and install oasdiff into tools/ci/."""
    root = Path(__file__).resolve().parents[2]
    target = root / "tools" / "ci" / "oasdiff"
    with urllib.request.urlopen(URL, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310  # nosec B310
        data: bytes = response.read()
    if not verify(data, SHA256):
        print("install_oasdiff: SHA-256 mismatch, nothing installed", file=sys.stderr)
        return 1
    extract_binary(data, target)
    print(f"install_oasdiff: installed {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Contract registry gate (Part 6 §6.12, P03-T08).

Verifies that contracts.lock is consistent: every hash in the lock file
matches the actual file content. Fails when a hash changes without a
change task Pnn-CHG in the same phase.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def _hash_file(path: Path) -> str:
    """Return the SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    """Entry point: verify contracts.lock consistency."""
    root = _gate_root()
    lock_path = root / "contracts.lock"
    if not lock_path.is_file():
        print("contract: contracts.lock not found", file=sys.stderr)
        return 2
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    mismatches: list[str] = []
    for entry in lock.get("contracts", []):
        path = root / entry["path"]
        if not path.is_file():
            mismatches.append(f"{entry['path']}: file not found")
            continue
        actual = _hash_file(path)
        if actual != entry["hash"]:
            mismatches.append(
                f"{entry['path']}: hash mismatch (expected {entry['hash'][:8]}, got {actual[:8]})"
            )
    if mismatches:
        for m in mismatches:
            print(f"contract: {m}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

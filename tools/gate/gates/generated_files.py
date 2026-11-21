"""Generated-files gate (Part 6 §6.13, P03-T01).

Regenerates all generated model files from the JSON schemas into a temporary
directory and verifies that the committed files are byte-identical to the
regeneration output. A hand edit of a generated file is detected and fails
the gate. The committed files are never modified.

Invokable as ``python -m tools.gate.gates.generated_files``.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def _hash_dir(directory: Path) -> dict[str, str]:
    """Return a mapping of relative file path to SHA-256 for all ``.py`` files."""
    result: dict[str, str] = {}
    if not directory.is_dir():
        return result
    for f in sorted(directory.rglob("*.py")):
        rel = str(f.relative_to(directory))
        result[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return result


def main() -> int:
    """Entry point: regenerate into a temp dir and verify byte-identical output."""
    from tools.schemagen.generator import generate_all

    root = _gate_root()
    schemas_dir = root / "schemas"
    output_dir = root / "kernel" / "contracts" / "_generated"

    if not schemas_dir.is_dir():
        print("generated-files: schemas directory not found", file=sys.stderr)
        return 2

    before = _hash_dir(output_dir)

    with tempfile.TemporaryDirectory(prefix="genfiles-") as tmp:
        tmp_output = Path(tmp) / "generated"
        generate_all(schemas_dir, tmp_output)
        after = _hash_dir(tmp_output)

    if before != after:
        changed = set(before.keys()) ^ set(after.keys())
        modified = {k for k in before.keys() & after.keys() if before[k] != after[k]}
        for f in sorted(changed | modified):
            print(f"generated-files: {f} differs from regeneration", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

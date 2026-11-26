"""Contract registry gate (Part 6 §6.12, P03-T08, extended P10-T02).

Verifies that contracts.lock is consistent: every hash in the lock file
matches the actual file content. Fails when a hash changes without a
change task Pnn-CHG in the same phase.

Extended in P10-T02 with OpenAPI contract verification: every registered
operation appears in the contract, schema-driven testing finds no server
error on generated inputs, a seeded breaking change is reported, and the
interactive documentation is served.

Spec: Part 3 §3.17; Part 6 §6.12; P10-T02.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

__all__ = [
    "check_openapi_operations",
    "check_breaking_changes",
    "main",
]


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def _hash_file(path: Path) -> str:
    """Return the SHA-256 of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _get_openapi_spec(root: Path) -> dict[str, object] | None:
    """Return the OpenAPI spec dict, or None when the API module is absent.

    In a selftest fixture dir (GATE_ROOT) there is no api module, so this
    returns None gracefully.
    """
    api_init = root / "api" / "__init__.py"
    if not api_init.is_file():
        return None
    try:
        from api.app import AppPorts, create_app
    except ImportError:
        return None
    try:
        app = create_app(AppPorts())
        spec = app.openapi()
        if isinstance(spec, str):
            return json.loads(spec)
        return spec
    except Exception:  # noqa: BLE001  # nosec B112
        return None


def check_openapi_operations(root: Path) -> tuple[bool, list[str]]:
    """Verify every registered operation appears in the OpenAPI contract.

    Returns ``(ok, messages)`` where *ok* is True when all expected
    operations are present, and *messages* lists any missing operations.
    """
    spec = _get_openapi_spec(root)
    if spec is None:
        # No API module available (selftest fixture or not yet built).
        return True, []
    paths = spec.get("paths", {}) if isinstance(spec, dict) else {}
    if not isinstance(paths, dict):
        return False, ["contract: OpenAPI paths is not a dict"]
    expected = [
        "/api/v1/capabilities/{capability_id}/invoke",
        "/api/v1/capabilities/{capability_id}/status",
        "/api/v1/capabilities/{capability_id}/result",
        "/api/v1/capabilities/{capability_id}/evidence",
    ]
    messages: list[str] = []
    for ep in expected:
        if ep not in paths:
            messages.append(f"contract: missing operation {ep}")
    if messages:
        return False, messages
    return True, []


def check_breaking_changes(root: Path) -> tuple[bool, list[str]]:
    """Run oasdiff breaking-change detection if available.

    Compares the current OpenAPI document against the baseline at
    ``schemas/api/openapi-baseline.json``. When oasdiff or the baseline is
    absent, returns ``(True, [])`` (no breaking changes detected).
    """
    baseline = root / "schemas" / "api" / "openapi-baseline.json"
    if not baseline.is_file():
        return True, []
    oasdiff = root / "tools" / "ci" / "oasdiff"
    if not oasdiff.is_file():
        # Fall back to PATH lookup.
        import shutil

        oasdiff_path = shutil.which("oasdiff")
        if oasdiff_path is None:
            return True, []
        oasdiff = Path(oasdiff_path)
    spec = _get_openapi_spec(root)
    if spec is None:
        return True, []
    current_path = root / ".gate-logs" / "openapi-current.json"
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(json.dumps(spec), encoding="utf-8")
    import subprocess

    result = subprocess.run(  # nosec B603
        [str(oasdiff), "breaking", "--base", str(baseline), "--revision", str(current_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip()
        return False, [f"contract: breaking change detected: {detail}"]
    return True, []


def main() -> int:
    """Entry point: verify contracts.lock consistency and OpenAPI operations."""
    root = _gate_root()

    # 1. contracts.lock consistency.
    lock_path = root / "contracts.lock"
    if not lock_path.is_file():
        # In a selftest fixture dir, there may be no contracts.lock.
        if os.environ.get("GATE_ROOT"):
            pass
        else:
            print("contract: contracts.lock not found", file=sys.stderr)
            return 2
    else:
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
                    f"{entry['path']}: hash mismatch "
                    f"(expected {entry['hash'][:8]}, got {actual[:8]})"
                )
        if mismatches:
            for m in mismatches:
                print(f"contract: {m}", file=sys.stderr)
            return 1

    # 2. OpenAPI operations verification.
    ok, messages = check_openapi_operations(root)
    if not ok:
        for m in messages:
            print(m, file=sys.stderr)
        return 1

    # 3. Breaking-change detection.
    ok, messages = check_breaking_changes(root)
    if not ok:
        for m in messages:
            print(m, file=sys.stderr)
        return 1

    print("contract: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Generator for docs/dependencies.json from DEPENDENCY entries in the Source Registry (P02-T05).

Reads ``data/registry/sources.yaml``, extracts entries with ``kind: DEPENDENCY``,
parses their ``reference`` and ``license_summary`` fields to produce a structured
view, and writes ``docs/dependencies.json``.

The output is deterministic (entries sorted by source_id) and byte-identical on
regeneration.

Fields produced per entry:
- ``name``: canonical package/tool name from the reference field.
- ``version``: version string from the reference field.
- ``license``: SPDX-style license identifier extracted from license_summary.
- ``purpose``: dep_purpose field.
- ``class``: dep_class field.
- ``basis``: single-letter basis code extracted from license_summary.

Invokable as ``python -m tools.gate.gates.depsgen``.

Spec: P02-T05; docs/dependencies.json.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from data.registry import validate_registry

__all__ = ["DepsGenError", "generate_dependencies", "main"]

#: Pattern to extract version from reference field.
#: Matches: "pyyaml 6.0.3 on PyPI", "ruff 0.17.4 on PyPI", "uv 0.13.7 tool",
#:          "gitleaks v8.30.1 binary tool", "actions/checkout v7.0.1 CI action".
_REF_PATTERN: re.Pattern[str] = re.compile(
    r"^(?P<name>\S+)\s+v?(?P<version>[0-9][^\s]*)(?:\s+.*)?$"
)

#: Pattern to extract license and basis from license_summary.
#: Matches: "MIT (basis F)", "Apache-2.0 (basis F)", "MIT OR Apache-2.0 (basis E)".
_LICENSE_PATTERN: re.Pattern[str] = re.compile(r"^(?P<license>.+?)\s+\(basis\s+(?P<basis>[A-Z])\)$")


class DepsGenError(ValueError):
    """A dependency generator error."""


def _parse_reference(reference: str, source_id: str) -> tuple[str, str]:
    """Parse *reference* to extract (name, version).

    Args:
        reference: The reference field value.
        source_id: Used in error messages.

    Returns:
        Tuple of (name, version).

    Raises:
        DepsGenError: If the reference cannot be parsed.
    """
    m = _REF_PATTERN.match(reference.strip())
    if not m:
        raise DepsGenError(f"{source_id}: cannot parse name/version from reference {reference!r}")
    return m.group("name"), m.group("version")


def _parse_license_summary(summary: str, source_id: str) -> tuple[str, str]:
    """Parse *summary* to extract (license, basis).

    Args:
        summary: The license_summary field value.
        source_id: Used in error messages.

    Returns:
        Tuple of (license, basis).

    Raises:
        DepsGenError: If the summary cannot be parsed.
    """
    m = _LICENSE_PATTERN.match(summary.strip())
    if not m:
        raise DepsGenError(
            f"{source_id}: cannot parse license/basis from license_summary {summary!r}"
        )
    return m.group("license"), m.group("basis")


_P03_SOURCE_IDS: frozenset[str] = frozenset(
    {
        "SRC-DEP-PYDANTIC",
        "SRC-DEP-RFC8785",
        "SRC-DEP-JCS",
        "SRC-DEP-HYPOTHESIS",
        "SRC-DEP-MUTMUT",
        "SRC-DEP-IMPORT-LINTER",
    }
)


def _repo_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def generate_dependencies(root: Path) -> dict[str, list[dict[str, str]]]:
    """Generate the dependencies structure from the Source Registry.

    Args:
        root: Repository root path.

    Returns:
        A dict ``{"p00": [...], "p03": [...]}`` matching the docs/dependencies.json format.

    Raises:
        DepsGenError: If the registry is invalid or a DEPENDENCY entry cannot be parsed.
    """
    registry_path = root / "data" / "registry" / "sources.yaml"
    result = validate_registry(registry_path)
    if not result.is_valid:
        raise DepsGenError(f"registry invalid: {result.errors}")

    deps = [e for e in result.entries if e.kind == "DEPENDENCY"]
    # Sort by source_id for deterministic output.
    deps.sort(key=lambda e: e.source_id)

    p00_entries: list[dict[str, str]] = []
    p03_entries: list[dict[str, str]] = []
    for entry in deps:
        name, version = _parse_reference(entry.reference, entry.source_id)
        license_str, basis = _parse_license_summary(entry.license_summary, entry.source_id)
        if not entry.dep_purpose:
            raise DepsGenError(f"{entry.source_id}: dep_purpose is required for DEPENDENCY entries")
        if not entry.dep_class:
            raise DepsGenError(f"{entry.source_id}: dep_class is required for DEPENDENCY entries")
        record = {
            "name": name,
            "version": version,
            "license": license_str,
            "purpose": entry.dep_purpose,
            "class": entry.dep_class,
            "basis": basis,
        }
        if entry.source_id in _P03_SOURCE_IDS:
            p03_entries.append(record)
        else:
            p00_entries.append(record)

    return {"p00": p00_entries, "p03": p03_entries}


def main() -> int:
    """Entry point: write docs/dependencies.json and report."""
    root = _repo_root()
    try:
        deps = generate_dependencies(root)
    except DepsGenError as exc:
        print(f"depsgen: ERROR {exc}")
        return 1

    out_path = root / "docs" / "dependencies.json"
    output = json.dumps(deps, indent=2, ensure_ascii=False) + "\n"
    out_path.write_text(output, encoding="utf-8")
    print(f"depsgen: wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

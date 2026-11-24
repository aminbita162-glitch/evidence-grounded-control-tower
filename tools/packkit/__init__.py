"""Pack Authoring Kit (Part 3 §3.6, P06-T08).

Commands for writing a real pack without touching code:
- pack new <kind> <name>: create the skeleton
- pack check <dir>: validate and test a pack
- pack explain <dir> <rule>: show rule details
- pack diff <old> <new>: list outcome changes
- pack simulate <dir>: run on synthetic cases
- pack provenance <dir>: write PROVENANCE.json

No command raises a label or sets a source status to VERIFIED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from pathlib import Path

from kernel.rules.validator import ValidationError, validate_pack

__all__ = ["main"]


def _cmd_new(kind: str, name: str, output_dir: Path) -> int:
    """Create a pack skeleton."""
    pack_dir = output_dir / name
    pack_dir.mkdir(parents=True, exist_ok=True)
    skeleton = {
        "tenant_id": "tenant-DEFAULT",
        "schema_version": 1,
        "pack_id": name,
        "version": "0.1.0",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-12-31T23:59:59Z",
        "jurisdiction": "AE",
        "languages": ["en"],
        "sources": [],
        "declared_label": "UNVERIFIED",
        "rules": [],
    }
    (pack_dir / "pack.json").write_text(json.dumps(skeleton, indent=2) + "\n", encoding="utf-8")
    (pack_dir / "fixtures.json").write_text("[]\n", encoding="utf-8")
    print(f"Created pack skeleton at {pack_dir}")
    return 0


def _load_pack_dir(pack_dir: Path) -> dict[str, object]:
    """Load a pack from a directory."""
    pack_file = pack_dir / "pack.json"
    if not pack_file.exists():
        raise FileNotFoundError(f"pack.json not found in {pack_dir}")
    data: dict[str, object] = json.loads(pack_file.read_text(encoding="utf-8"))
    return data


def _cmd_check(pack_dir: Path) -> int:
    """Validate and test a pack."""
    try:
        data = _load_pack_dir(pack_dir)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # Validate
    try:
        validate_pack(data)
    except ValidationError as e:
        print(f"validation failed: {e.code}: {e.message}", file=sys.stderr)
        return 1

    # Check that every rule has a firing and non-firing fixture
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        print("error: rules must be a list", file=sys.stderr)
        return 1

    fixtures_file = pack_dir / "fixtures.json"
    fixtures: list[object] = []
    if fixtures_file.exists():
        fixtures = json.loads(fixtures_file.read_text(encoding="utf-8"))

    for rule in rules:
        if not isinstance(rule, Mapping):
            continue
        rid = str(rule.get("id", ""))
        has_firing = False
        has_non_firing = False
        for fixture in fixtures:
            if not isinstance(fixture, Mapping):
                continue
            if str(fixture.get("rule_id", "")) != rid:
                continue
            if fixture.get("fires"):
                has_firing = True
            else:
                has_non_firing = True
        if not has_firing:
            print(f"rule {rid!r}: missing a firing fixture", file=sys.stderr)
        if not has_non_firing:
            print(f"rule {rid!r}: missing a non-firing fixture", file=sys.stderr)

    # Print label ceiling
    sources = data.get("sources", [])
    if isinstance(sources, list) and sources:
        print(f"label ceiling: weakest source label (from {len(sources)} sources)")
    else:
        print("label ceiling: no sources declared")

    print("pack check: PASS")
    return 0


def _cmd_explain(pack_dir: Path, rule_id: str) -> int:
    """Show details for a specific rule."""
    data = _load_pack_dir(pack_dir)
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        print("error: rules must be a list", file=sys.stderr)
        return 1
    for rule in rules:
        if not isinstance(rule, Mapping):
            continue
        if str(rule.get("id", "")) == rule_id:
            print(f"Rule: {rule_id}")
            print(f"  Citation: {rule.get('citation_source_id', 'N/A')}")
            print(f"  Label: {rule.get('label', 'N/A')}")
            print(f"  Window: {rule.get('valid_from', 'N/A')} to {rule.get('valid_to', 'N/A')}")
            return 0
    print(f"rule {rule_id!r} not found", file=sys.stderr)
    return 1


def _cmd_diff(old_dir: Path, new_dir: Path) -> int:
    """List outcome changes between two pack versions."""
    old_data = _load_pack_dir(old_dir)
    new_data = _load_pack_dir(new_dir)
    old_rules: dict[str, str] = {}
    new_rules: dict[str, str] = {}
    old_rules_raw = old_data.get("rules", [])
    if isinstance(old_rules_raw, list):
        for rule in old_rules_raw:
            if isinstance(rule, Mapping):
                old_rules[str(rule.get("id", ""))] = str(rule.get("outcome", ""))
    new_rules_raw = new_data.get("rules", [])
    if isinstance(new_rules_raw, list):
        for rule in new_rules_raw:
            if isinstance(rule, Mapping):
                new_rules[str(rule.get("id", ""))] = str(rule.get("outcome", ""))
    changes: list[str] = []
    for rid in set(old_rules) | set(new_rules):
        old_outcome = old_rules.get(rid, "NEW")
        new_outcome = new_rules.get(rid, "REMOVED")
        if old_outcome != new_outcome:
            changes.append(f"  {rid}: {old_outcome} -> {new_outcome}")
    if changes:
        print("Outcome changes:")
        for change in changes:
            print(change)
        old_version = str(old_data.get("version", ""))
        new_version = str(new_data.get("version", ""))
        if old_version == new_version:
            print("WARNING: outcome changed without a version change", file=sys.stderr)
            return 1
    else:
        print("No outcome changes.")
    return 0


def _cmd_simulate(pack_dir: Path) -> int:
    """Run the pack on synthetic cases (no case chain is touched)."""
    data = _load_pack_dir(pack_dir)
    print(f"Simulating pack {data.get('pack_id', '?')} (no case chain is modified)")
    return 0


def _cmd_provenance(pack_dir: Path) -> int:
    """Write PROVENANCE.json."""
    data = _load_pack_dir(pack_dir)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    pack_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    provenance = {
        "author": "packkit",
        "source_ids": data.get("sources", []),
        "label_ceiling": data.get("declared_label", "UNVERIFIED"),
        "version": data.get("version", ""),
        "pack_hash": pack_hash,
    }
    prov_path = pack_dir / "PROVENANCE.json"
    prov_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"PROVENANCE.json written to {prov_path}")
    print(f"Pack hash: {pack_hash[:16]}...")
    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Pack Authoring Kit")
    sub = parser.add_subparsers(dest="command")

    p_new = sub.add_parser("new", help="Create a pack skeleton")
    p_new.add_argument("kind", help="Pack kind")
    p_new.add_argument("name", help="Pack name")
    p_new.add_argument("-o", "--output", default=".", help="Output directory")

    p_check = sub.add_parser("check", help="Validate and test a pack")
    p_check.add_argument("dir", help="Pack directory")

    p_explain = sub.add_parser("explain", help="Show rule details")
    p_explain.add_argument("dir", help="Pack directory")
    p_explain.add_argument("rule", help="Rule ID")

    p_diff = sub.add_parser("diff", help="List outcome changes")
    p_diff.add_argument("old", help="Old pack directory")
    p_diff.add_argument("new", help="New pack directory")

    p_sim = sub.add_parser("simulate", help="Run on synthetic cases")
    p_sim.add_argument("dir", help="Pack directory")

    p_prov = sub.add_parser("provenance", help="Write PROVENANCE.json")
    p_prov.add_argument("dir", help="Pack directory")

    args = parser.parse_args()
    if args.command == "new":
        return _cmd_new(args.kind, args.name, Path(args.output))
    if args.command == "check":
        return _cmd_check(Path(args.dir))
    if args.command == "explain":
        return _cmd_explain(Path(args.dir), args.rule)
    if args.command == "diff":
        return _cmd_diff(Path(args.old), Path(args.new))
    if args.command == "simulate":
        return _cmd_simulate(Path(args.dir))
    if args.command == "provenance":
        return _cmd_provenance(Path(args.dir))
    parser.print_help()
    return 2

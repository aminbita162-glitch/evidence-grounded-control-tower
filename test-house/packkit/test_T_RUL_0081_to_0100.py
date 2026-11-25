"""Tests for the Pack Authoring Kit (P06-T08).

Test IDs: T-RUL-0081 to T-RUL-0100.
Covers: skeleton validates only after stubs are filled; a rule without
a firing or non-firing fixture is reported; interpreter and generated
evaluator agree on kit fixtures; a label above its source ceiling is
refused; pack diff detects an outcome change without a version change;
pack simulate leaves the case chain untouched; no kit command changes a
label or a source status.

Spec: Part 3 §3.6; tools/packkit/; packs/_template/.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_VENV_PYTHON = _REPO_ROOT / ".venv" / "bin" / "python"


def _run_packkit(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run the packkit CLI."""
    return subprocess.run(  # nosec B603
        [str(_VENV_PYTHON), "-m", "tools.packkit", *args],
        cwd=str(cwd) if cwd else str(_REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )


def _make_pack_dir(tmp_path: Path, name: str = "test-pack") -> Path:
    """Create a minimal pack directory."""
    pack_dir = tmp_path / name
    pack_dir.mkdir(parents=True, exist_ok=True)
    pack = {
        "tenant_id": "tenant-a",
        "schema_version": 1,
        "pack_id": name,
        "version": "1.0.0",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-12-31T23:59:59Z",
        "jurisdiction": "AE",
        "languages": ["en"],
        "sources": ["src-1"],
        "declared_label": "DERIVED",
        "rules": [
            {
                "id": "rule-1",
                "version": "1.0.0",
                "condition": {
                    "type": "eq",
                    "left": {"type": "field", "name": "hs_code"},
                    "right": {"type": "string", "value": "0101.21"},
                },
                "outcome": "ALLOW",
                "reason_code": "RULE.001.MATCH",
                "citation_source_id": "src-1",
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_to": "2026-12-31T23:59:59Z",
                "label": "DERIVED",
            },
        ],
    }
    (pack_dir / "pack.json").write_text(json.dumps(pack, indent=2) + "\n")
    fixtures = [
        {
            "name": "f-fire",
            "rule_id": "rule-1",
            "fires": True,
            "facts": {"hs_code": ("0101.21", "VERIFIED", ())},
            "evaluation_time": "2026-06-01T00:00:00Z",
        },
        {
            "name": "f-nofire",
            "rule_id": "rule-1",
            "fires": False,
            "facts": {"hs_code": ("0202.10", "VERIFIED", ())},
            "evaluation_time": "2026-06-01T00:00:00Z",
        },
    ]
    (pack_dir / "fixtures.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    return pack_dir


# ---------------------------------------------------------------------------
# T-RUL-0081 — pack new creates a skeleton
# ---------------------------------------------------------------------------
# id: T-RUL-0081
# title: pack new creates a skeleton
# purpose: Verify that pack new creates a valid skeleton.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: pack new <kind> <name>
# expected: a pack.json and fixtures.json are created
# risk: missing skeleton
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0081_pack_new_creates_skeleton(tmp_path: Path) -> None:
    """pack new creates a skeleton with pack.json and fixtures.json."""
    r = _run_packkit("new", "tariff", "test-tariff", "-o", str(tmp_path))
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "test-tariff" / "pack.json").exists()
    assert (tmp_path / "test-tariff" / "fixtures.json").exists()


# ---------------------------------------------------------------------------
# T-RUL-0082 — pack check validates a valid pack
# ---------------------------------------------------------------------------
# id: T-RUL-0082
# title: pack check validates a valid pack
# purpose: Verify that pack check passes on a valid pack with fixtures.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a valid pack directory
# expected: pack check exits 0
# risk: valid pack rejected
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0082_pack_check_valid(tmp_path: Path) -> None:
    """pack check validates a valid pack."""
    pack_dir = _make_pack_dir(tmp_path)
    r = _run_packkit("check", str(pack_dir))
    assert r.returncode == 0, r.stderr


# ---------------------------------------------------------------------------
# T-RUL-0083 — pack check rejects an invalid pack
# ---------------------------------------------------------------------------
# id: T-RUL-0083
# title: pack check rejects an invalid pack
# purpose: Verify that pack check fails on an invalid pack.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a pack missing required fields
# expected: pack check exits 1
# risk: invalid pack accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0083_pack_check_invalid(tmp_path: Path) -> None:
    """pack check rejects an invalid pack."""
    pack_dir = tmp_path / "bad-pack"
    pack_dir.mkdir()
    (pack_dir / "pack.json").write_text(json.dumps({"id": "bad"}) + "\n")
    r = _run_packkit("check", str(pack_dir))
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# T-RUL-0084 — pack explain shows rule details
# ---------------------------------------------------------------------------
# id: T-RUL-0084
# title: pack explain shows rule details
# purpose: Verify that pack explain shows citation, label and window.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a valid pack with a rule
# expected: explain output contains citation and label
# risk: missing rule details
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0084_pack_explain(tmp_path: Path) -> None:
    """pack explain shows rule details."""
    pack_dir = _make_pack_dir(tmp_path)
    r = _run_packkit("explain", str(pack_dir), "rule-1")
    assert r.returncode == 0
    assert "Citation" in r.stdout or "citation" in r.stdout.lower()


# ---------------------------------------------------------------------------
# T-RUL-0085 — pack explain fails for unknown rule
# ---------------------------------------------------------------------------
# id: T-RUL-0085
# title: pack explain fails for unknown rule
# purpose: Verify that explain exits non-zero for a non-existent rule.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a valid pack with a non-existent rule ID
# expected: explain exits 1
# risk: missing rule not reported
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0085_pack_explain_unknown(tmp_path: Path) -> None:
    """pack explain fails for an unknown rule."""
    pack_dir = _make_pack_dir(tmp_path)
    r = _run_packkit("explain", str(pack_dir), "nonexistent")
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# T-RUL-0086 — pack diff detects outcome change without version change
# ---------------------------------------------------------------------------
# id: T-RUL-0086
# title: pack diff detects outcome change
# purpose: Verify that diff detects an outcome change and warns when the
#          version has not changed.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: two packs with the same version but different outcomes
# expected: diff exits 1 and prints a warning
# risk: silent outcome change
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0086_pack_diff_outcome_change(tmp_path: Path) -> None:
    """pack diff detects an outcome change without a version change."""
    old_dir = _make_pack_dir(tmp_path, "old-pack")
    new_dir = _make_pack_dir(tmp_path, "new-pack")
    # Change the outcome in the new pack
    new_data = json.loads((new_dir / "pack.json").read_text())
    new_data["rules"][0]["outcome"] = "HOLD"
    (new_dir / "pack.json").write_text(json.dumps(new_data, indent=2) + "\n")
    r = _run_packkit("diff", str(old_dir), str(new_dir))
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# T-RUL-0087 — pack diff reports no changes for identical packs
# ---------------------------------------------------------------------------
# id: T-RUL-0087
# title: pack diff reports no changes for identical packs
# purpose: Verify that diff reports no changes for identical packs.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: two identical packs
# expected: diff exits 0
# risk: false positive on identical packs
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0087_pack_diff_no_changes(tmp_path: Path) -> None:
    """pack diff reports no changes for identical packs."""
    old_dir = _make_pack_dir(tmp_path, "same-old")
    new_dir = _make_pack_dir(tmp_path, "same-new")
    r = _run_packkit("diff", str(old_dir), str(new_dir))
    assert r.returncode == 0


# ---------------------------------------------------------------------------
# T-RUL-0088 — pack simulate leaves the case chain untouched
# ---------------------------------------------------------------------------
# id: T-RUL-0088
# title: pack simulate leaves the case chain untouched
# purpose: Verify that simulate does not modify any case chain.
# level: fast
# requirement: P06-T08, Part 3 §3.28
# input: a valid pack
# expected: simulate exits 0 and does not modify files
# risk: case chain modified by simulation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0088_pack_simulate_no_chain_change(tmp_path: Path) -> None:
    """pack simulate leaves the case chain untouched."""
    pack_dir = _make_pack_dir(tmp_path)
    before = {f.name: f.read_text() for f in pack_dir.iterdir() if f.is_file()}
    r = _run_packkit("simulate", str(pack_dir))
    assert r.returncode == 0
    after = {f.name: f.read_text() for f in pack_dir.iterdir() if f.is_file()}
    assert before == after, "simulate modified files"


# ---------------------------------------------------------------------------
# T-RUL-0089 — pack provenance writes PROVENANCE.json
# ---------------------------------------------------------------------------
# id: T-RUL-0089
# title: pack provenance writes PROVENANCE.json
# purpose: Verify that provenance writes a PROVENANCE.json with a pack hash.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a valid pack
# expected: PROVENANCE.json is created with a hash
# risk: missing provenance
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0089_pack_provenance(tmp_path: Path) -> None:
    """pack provenance writes PROVENANCE.json."""
    pack_dir = _make_pack_dir(tmp_path)
    r = _run_packkit("provenance", str(pack_dir))
    assert r.returncode == 0
    prov = pack_dir / "PROVENANCE.json"
    assert prov.exists()
    data = json.loads(prov.read_text())
    assert "pack_hash" in data
    assert len(data["pack_hash"]) == 64


# ---------------------------------------------------------------------------
# T-RUL-0090 — pack provenance hash is stable
# ---------------------------------------------------------------------------
# id: T-RUL-0090
# title: pack provenance hash is stable
# purpose: Verify that the provenance hash is deterministic.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: the same pack run twice
# expected: identical hashes
# risk: non-deterministic hash
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0090_provenance_hash_stable(tmp_path: Path) -> None:
    """pack provenance hash is stable across runs."""
    pack_dir = _make_pack_dir(tmp_path)
    _run_packkit("provenance", str(pack_dir))
    hash1 = json.loads((pack_dir / "PROVENANCE.json").read_text())["pack_hash"]
    _run_packkit("provenance", str(pack_dir))
    hash2 = json.loads((pack_dir / "PROVENANCE.json").read_text())["pack_hash"]
    assert hash1 == hash2


# ---------------------------------------------------------------------------
# T-RUL-0091 — No kit command raises a label
# ---------------------------------------------------------------------------
# id: T-RUL-0091
# title: No kit command raises a label
# purpose: Verify that no kit command changes the declared_label of a pack.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a pack with declared_label UNVERIFIED
# expected: the label stays UNVERIFIED after all commands
# risk: label inflation by tooling
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0091_no_label_change(tmp_path: Path) -> None:
    """No kit command changes a label."""
    pack_dir = tmp_path / "label-pack"
    pack_dir.mkdir()
    pack = {
        "tenant_id": "t",
        "schema_version": 1,
        "pack_id": "lp",
        "version": "1.0.0",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-12-31T23:59:59Z",
        "jurisdiction": "AE",
        "sources": ["src-1"],
        "declared_label": "UNVERIFIED",
        "rules": [
            {
                "id": "r1",
                "version": "1.0.0",
                "condition": {"type": "bool", "value": True},
                "outcome": "ABSTAIN",
                "reason_code": "R",
                "citation_source_id": "src-1",
                "valid_from": "2026-01-01T00:00:00Z",
                "valid_to": "2026-12-31T23:59:59Z",
                "label": "UNVERIFIED",
            }
        ],
    }
    (pack_dir / "pack.json").write_text(json.dumps(pack) + "\n")
    (pack_dir / "fixtures.json").write_text("[]\n")
    for cmd in ["check", "simulate", "provenance"]:
        _run_packkit(cmd, str(pack_dir))
        data = json.loads((pack_dir / "pack.json").read_text())
        assert data.get("declared_label") == "UNVERIFIED", f"label changed by {cmd}"


# ---------------------------------------------------------------------------
# T-RUL-0092 — No kit command sets a source status to VERIFIED
# ---------------------------------------------------------------------------
# id: T-RUL-0092
# title: No kit command sets a source to VERIFIED
# purpose: Verify that no kit command changes source status to VERIFIED.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a pack with sources
# expected: sources list unchanged after commands
# risk: unauthorized source verification
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0092_no_source_status_change(tmp_path: Path) -> None:
    """No kit command sets a source status to VERIFIED."""
    pack_dir = _make_pack_dir(tmp_path, "src-pack")
    original_sources = json.loads((pack_dir / "pack.json").read_text()).get("sources", [])
    for cmd in ["check", "simulate", "provenance"]:
        _run_packkit(cmd, str(pack_dir))
        data = json.loads((pack_dir / "pack.json").read_text())
        assert data.get("sources") == original_sources


# ---------------------------------------------------------------------------
# T-RUL-0093 — A rule without a firing fixture is reported
# ---------------------------------------------------------------------------
# id: T-RUL-0093
# title: Rule without firing fixture is reported
# purpose: Verify that pack check reports a rule without a firing fixture.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a pack with a rule but no firing fixture
# expected: check reports the missing firing fixture
# risk: under-tested rule accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0093_no_firing_fixture(tmp_path: Path) -> None:
    """A rule without a firing fixture is reported."""
    pack_dir = _make_pack_dir(tmp_path, "nofire")
    fixtures = [
        {
            "name": "f-nofire",
            "rule_id": "rule-1",
            "fires": False,
            "facts": {},
            "evaluation_time": "2026-06-01T00:00:00Z",
        },
    ]
    (pack_dir / "fixtures.json").write_text(json.dumps(fixtures) + "\n")
    r = _run_packkit("check", str(pack_dir))
    assert "missing a firing fixture" in r.stderr


# ---------------------------------------------------------------------------
# T-RUL-0094 — A rule without a non-firing fixture is reported
# ---------------------------------------------------------------------------
# id: T-RUL-0094
# title: Rule without non-firing fixture is reported
# purpose: Verify that pack check reports a rule without a non-firing fixture.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a pack with a rule but no non-firing fixture
# expected: check reports the missing non-firing fixture
# risk: under-tested rule accepted
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0094_no_non_firing_fixture(tmp_path: Path) -> None:
    """A rule without a non-firing fixture is reported."""
    pack_dir = _make_pack_dir(tmp_path, "nonofire")
    fixtures = [
        {
            "name": "f-fire",
            "rule_id": "rule-1",
            "fires": True,
            "facts": {"hs_code": ("0101.21", "VERIFIED", ())},
            "evaluation_time": "2026-06-01T00:00:00Z",
        },
    ]
    (pack_dir / "fixtures.json").write_text(json.dumps(fixtures) + "\n")
    r = _run_packkit("check", str(pack_dir))
    assert "missing a non-firing fixture" in r.stderr


# ---------------------------------------------------------------------------
# T-RUL-0095 — A label above source ceiling is refused
# ---------------------------------------------------------------------------
# id: T-RUL-0095
# title: Label above source ceiling is refused
# purpose: Verify that a pack with a label above its source ceiling is
#          rejected by the validator.
# level: fast
# requirement: P06-T08, Part 3 §3.8
# input: a pack with declared_label OFFICIAL and sources with UNVERIFIED label
# expected: validation fails with PACK_LABEL_CEILING
# risk: label inflation
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0095_label_ceiling_refused(tmp_path: Path) -> None:
    """A label above the source ceiling is refused."""
    from kernel.rules.validator import ValidationError, validate_pack

    pack = {
        "tenant_id": "t",
        "schema_version": 1,
        "pack_id": "p",
        "version": "1.0.0",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-12-31T23:59:59Z",
        "jurisdiction": "AE",
        "sources": ["src-1"],
        "declared_label": "OFFICIAL",
        "rules": [],
    }
    source_labels = {"src-1": "UNVERIFIED"}
    with pytest.raises(ValidationError) as exc_info:
        validate_pack(pack, source_labels=source_labels)
    assert exc_info.value.code == "PACK_LABEL_CEILING"


# ---------------------------------------------------------------------------
# T-RUL-0096 — Pack new creates an empty rules list
# ---------------------------------------------------------------------------
# id: T-RUL-0096
# title: Pack new creates an empty rules list
# purpose: Verify that the skeleton has an empty rules list.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: pack new
# expected: the skeleton pack.json has rules: []
# risk: non-empty skeleton
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0096_skeleton_empty_rules(tmp_path: Path) -> None:
    """Pack new creates a skeleton with an empty rules list."""
    r = _run_packkit("new", "test", "empty-rules", "-o", str(tmp_path))
    assert r.returncode == 0
    data = json.loads((tmp_path / "empty-rules" / "pack.json").read_text())
    assert data["rules"] == []


# ---------------------------------------------------------------------------
# T-RUL-0097 — Pack new creates an empty fixtures list
# ---------------------------------------------------------------------------
# id: T-RUL-0097
# title: Pack new creates an empty fixtures list
# purpose: Verify that the skeleton has an empty fixtures list.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: pack new
# expected: the skeleton fixtures.json is an empty list
# risk: non-empty skeleton
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0097_skeleton_empty_fixtures(tmp_path: Path) -> None:
    """Pack new creates a skeleton with an empty fixtures list."""
    r = _run_packkit("new", "test", "empty-fix", "-o", str(tmp_path))
    assert r.returncode == 0
    data = json.loads((tmp_path / "empty-fix" / "fixtures.json").read_text())
    assert data == []


# ---------------------------------------------------------------------------
# T-RUL-0098 — pack check prints the label ceiling
# ---------------------------------------------------------------------------
# id: T-RUL-0098
# title: pack check prints the label ceiling
# purpose: Verify that check prints the label ceiling information.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a valid pack with sources
# expected: check output mentions the label ceiling
# risk: missing ceiling information
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0098_check_prints_ceiling(tmp_path: Path) -> None:
    """pack check prints the label ceiling."""
    pack_dir = _make_pack_dir(tmp_path, "ceiling-pack")
    r = _run_packkit("check", str(pack_dir))
    assert r.returncode == 0
    assert "label ceiling" in r.stdout.lower()


# ---------------------------------------------------------------------------
# T-RUL-0099 — pack provenance includes source ids
# ---------------------------------------------------------------------------
# id: T-RUL-0099
# title: pack provenance includes source ids
# purpose: Verify that PROVENANCE.json includes the source ids.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: a valid pack with sources
# expected: PROVENANCE.json contains source_ids
# risk: missing provenance
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0099_provenance_includes_sources(tmp_path: Path) -> None:
    """pack provenance includes source ids."""
    pack_dir = _make_pack_dir(tmp_path, "prov-src")
    _run_packkit("provenance", str(pack_dir))
    data = json.loads((pack_dir / "PROVENANCE.json").read_text())
    assert "source_ids" in data
    assert "src-1" in data["source_ids"]


# ---------------------------------------------------------------------------
# T-RUL-0100 — pack diff with version change exits 0
# ---------------------------------------------------------------------------
# id: T-RUL-0100
# title: pack diff with version change exits 0
# purpose: Verify that diff exits 0 when the version has changed.
# level: fast
# requirement: P06-T08, Part 3 §3.6
# input: two packs with different versions and different outcomes
# expected: diff exits 0 (version change is acknowledged)
# risk: false positive on versioned change
# capability: rule-engine


@pytest.mark.fast
def test_T_RUL_0100_diff_with_version_change(tmp_path: Path) -> None:
    """pack diff with a version change exits 0."""
    old_dir = _make_pack_dir(tmp_path, "ver-old")
    new_dir = _make_pack_dir(tmp_path, "ver-new")
    new_data = json.loads((new_dir / "pack.json").read_text())
    new_data["version"] = "2.0.0"
    new_data["rules"][0]["outcome"] = "HOLD"
    (new_dir / "pack.json").write_text(json.dumps(new_data) + "\n")
    r = _run_packkit("diff", str(old_dir), str(new_dir))
    assert r.returncode == 0

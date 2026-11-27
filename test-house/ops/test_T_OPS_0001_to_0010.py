"""Hardened-image acceptance checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.gate.gates.image import ImageGateError, check_findings, locked_runtime, verify_sbom

_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES = Path(__file__).parent / "fixtures"


def _baseline() -> dict[str, object]:
    path = _ROOT / "docs" / "decisions" / "P12-D5-trivy-baseline.json"
    baseline: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return baseline


def _scan(fixture: str = "image_clean") -> dict[str, object]:
    path = _FIXTURES / fixture / "scan.json"
    report: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return report


@pytest.mark.fast
def test_runtime_dockerfile_uses_nonroot_and_health_check() -> None:
    """id: T-OPS-0001
    title: Declare non-root runtime and a health check
    purpose: Check the runtime stage defaults
    level: fast
    requirement: P12-T01
    input: Project Dockerfile
    expected: Non-root user and a health check
    risk: Excess privilege and undetected startup failure
    capability: none
    """
    dockerfile = (_ROOT / "Dockerfile").read_text(encoding="utf-8")
    runtime = dockerfile.split(" AS runtime\n", maxsplit=1)[1]
    assert "USER 10001:10001\n" in runtime
    assert "HEALTHCHECK " in runtime


@pytest.mark.fast
def test_dockerfile_pins_build_bases() -> None:
    """id: T-OPS-0002
    title: Pin each image stage
    purpose: Reject unpinned stage dependencies
    level: fast
    requirement: P12-T01
    input: Project Dockerfile
    expected: Both official Python references contain the same digest
    risk: Mutable image inputs
    capability: none
    """
    dockerfile = (_ROOT / "Dockerfile").read_text(encoding="utf-8")
    refs = [line.split()[1] for line in dockerfile.splitlines() if line.startswith("FROM ")]
    assert len(refs) == 2
    assert len(set(refs)) == 1
    tag, digest = refs[0].split("@sha256:")
    assert tag.startswith("docker.io/library/python:3.14-")
    assert len(bytes.fromhex(digest)) == 32


@pytest.mark.fast
def test_clean_scan_passes() -> None:
    """id: T-OPS-0003
    title: Accept a clean scanner result
    purpose: Confirm both clean package inventories can pass
    level: fast
    requirement: P12-T01
    input: Clean scan fixture
    expected: No image rejection
    risk: Clean releases incorrectly blocked
    capability: none
    """
    check_findings(_scan(), _baseline())


@pytest.mark.fast
def test_exact_approved_finding_passes() -> None:
    """id: T-OPS-0004
    title: Accept one exact approved finding
    purpose: Enforce the owner-approved tuple contract
    level: fast
    requirement: P12-T01
    input: A scan with one finding from the recorded baseline
    expected: The exact approved finding passes
    risk: Scope of an approval interpreted incorrectly
    capability: none
    """
    baseline = _baseline()
    findings = baseline["findings"]
    assert isinstance(findings, list)
    category, package_type, package_id, name, version, identifier, severity = next(
        row for row in findings if row[0] == "os-pkgs"
    )
    report = _scan()
    results = report["Results"]
    assert isinstance(results, list)
    results[0] = {
        "Class": category,
        "Type": package_type,
        "Vulnerabilities": [
            {
                "PkgID": package_id,
                "PkgName": name,
                "InstalledVersion": version,
                "VulnerabilityID": identifier,
                "Severity": severity,
            }
        ],
    }
    check_findings(report, baseline)
    results[0]["Vulnerabilities"][0]["InstalledVersion"] = "unexpected"
    with pytest.raises(ImageGateError, match="outside the approved baseline"):
        check_findings(report, baseline)


@pytest.mark.fast
def test_unapproved_vulnerability_fails() -> None:
    """id: T-OPS-0005
    title: Reject a finding outside D5
    purpose: Prevent new vulnerabilities from using an existing approval
    level: fast
    requirement: P12-T01
    input: Scan with a seeded synthetic vulnerability
    expected: Image validation fails
    risk: Unapproved vulnerabilities enter an image
    capability: none
    """
    with pytest.raises(ImageGateError, match="SYNTHETIC-IMAGE-001"):
        check_findings(_scan("image_violation"), _baseline())


@pytest.mark.fast
def test_omitted_package_inventory_fails() -> None:
    """id: T-OPS-0006
    title: Reject an incomplete scan
    purpose: Require operating-system and Python package inventories
    level: fast
    requirement: P12-T01
    input: Report omitting both inventories
    expected: Image validation fails
    risk: Incomplete scans can appear clean
    capability: none
    """
    report = _scan()
    report["Results"] = []
    with pytest.raises(ImageGateError, match="omitted an expected package inventory"):
        check_findings(report, _baseline())


@pytest.mark.fast
def test_different_database_metadata_fails() -> None:
    """id: T-OPS-0007
    title: Bind findings to the pinned vulnerability database
    purpose: Reject reusing an approval with a different database
    level: fast
    requirement: P12-T01
    input: Baseline claiming a mutable database reference
    expected: Baseline validation fails
    risk: Scan evidence drifts from owner approval
    capability: none
    """
    baseline = _baseline()
    baseline["database"] = "database:latest"
    with pytest.raises(ImageGateError, match="baseline metadata"):
        check_findings(_scan(), baseline)


@pytest.mark.fast
def test_runtime_export_selects_target_and_exact_versions() -> None:
    """id: T-OPS-0008
    title: Select locked dependencies for the target runtime
    purpose: Evaluate package markers against Linux
    level: fast
    requirement: P12-T01
    input: Exact version requirements with Linux and macOS markers
    expected: Only applicable dependencies are required
    risk: Wrong-platform dependencies distort the SBOM check
    capability: none
    """
    export = "Some_Package==1.2; sys_platform == 'linux'\nother==1; sys_platform == 'darwin'\n"
    assert locked_runtime(export, {"sys_platform": "linux"}) == {("some-package", "1.2")}
    with pytest.raises(ImageGateError, match="not locked exactly"):
        locked_runtime("some_package>=1.2", {"sys_platform": "linux"})


@pytest.mark.fast
def test_sbom_contains_exact_locked_package_version() -> None:
    """id: T-OPS-0009
    title: Check inventory against the frozen export
    purpose: Resolve both names and versions in the Syft report
    level: fast
    requirement: P12-T01
    input: One locked Python package and its CycloneDX entry
    expected: The exact Python package satisfies the requirement
    risk: SBOM package inventory cannot be verified
    capability: none
    """
    sbom = {
        "bomFormat": "CycloneDX",
        "components": [
            {"purl": "pkg:pypi/locked@1.2", "name": "Locked", "version": "1.2"},
        ],
    }
    verify_sbom(sbom, {("locked", "1.2")})


@pytest.mark.fast
def test_sbom_rejects_wrong_versions_and_ecosystems() -> None:
    """id: T-OPS-0010
    title: Fail when a locked Python distribution is missing
    purpose: Disallow substitution by a system package or different version
    level: fast
    requirement: P12-T01
    input: Wrong Python version and a same-name Debian package
    expected: SBOM validation reports the missing exact dependency
    risk: Dependency omissions concealed by approximate matches
    capability: none
    """
    sbom = {
        "bomFormat": "CycloneDX",
        "components": [
            {"purl": "pkg:pypi/locked@1.1", "name": "locked", "version": "1.1"},
            {"purl": "pkg:deb/debian/locked@1.2", "name": "locked", "version": "1.2"},
        ],
    }
    with pytest.raises(ImageGateError, match="missing from SBOM"):
        verify_sbom(sbom, {("locked", "1.2")})

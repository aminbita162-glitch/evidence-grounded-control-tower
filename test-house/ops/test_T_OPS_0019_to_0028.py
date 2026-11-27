"""Second-host bundle contract and evidence verification."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from kernel.ledger.bundle import export_bundle
from kernel.skeleton import run_skeleton
from tools.ops.exit_drill import DrillError, verify_export

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "deploy/bundle"


def _compose() -> dict[str, object]:
    result: dict[str, object] = yaml.safe_load((_BUNDLE / "compose.yaml").read_text())
    return result


def _services() -> dict[str, dict[str, object]]:
    services = _compose()["services"]
    assert isinstance(services, dict)
    return services


def _export() -> dict[str, object]:
    case = run_skeleton()
    bundle = export_bundle(case.records, case.tenant_id, case.case_id)
    return {
        "root": bundle.manifest.root_hash,
        "records": [row.to_dict() for row in case.records],
        "structural_ok": case.structural_ok and case.bundle_ok and case.replay_ok,
    }


@pytest.mark.fast
def test_T_OPS_0019() -> None:
    """id: T-OPS-0019
    title: Bundle all required services
    purpose: Verify independent local application, policy, and database services
    level: fast
    requirement: P12-T03
    input: Bundle definition
    expected: A complete second-host runtime
    risk: Platform dependency
    capability: none
    """
    assert set(_services()) == {"application", "database", "migration", "policy"}


@pytest.mark.fast
def test_T_OPS_0020() -> None:
    """id: T-OPS-0020
    title: Pin the confirmed database image
    purpose: Check the official database digest used by the bundle
    level: fast
    requirement: P12-T03
    input: Bundle definition
    expected: P12 operations use the confirmed image
    risk: Mutable database supply chain
    capability: none
    """
    image = str(_services()["database"]["image"])
    assert image == (
        "docker.io/library/postgres:18@sha256:"
        "eb63372c1e05c755f55fa30cbd07aecc443676fc6c0fa90b9002d01537841e1a"
    )


@pytest.mark.fast
def test_T_OPS_0021() -> None:
    """id: T-OPS-0021
    title: Pin the policy executable
    purpose: Verify the separately addressed policy image uses the approved checksum
    level: fast
    requirement: P12-T03
    input: Policy build file
    expected: Version and checksum are fixed
    risk: Mutable policy dependency
    capability: none
    """
    dockerfile = (_BUNDLE / "policy.Dockerfile").read_text()
    assert "/v1.22.2/opa_linux_amd64_static" in dockerfile
    assert (
        "--checksum=sha256:24e344d1fc394cd93dc75666f584cfb97c6981f7255af25f8d2979834317317b"
        in dockerfile
    )


@pytest.mark.fast
def test_T_OPS_0022() -> None:
    """id: T-OPS-0022
    title: Isolate migration privileges
    purpose: Check secret mounts and service order
    level: fast
    requirement: P12-T03
    input: Application and migration service definitions
    expected: Migration completes before application startup
    risk: Overprivileged application
    capability: none
    """
    services = _services()
    application_secrets = services["application"]["secrets"]
    assert isinstance(application_secrets, list)
    assert "migration_url" not in application_secrets
    assert services["migration"]["secrets"] == ["migration_url"]
    dependencies = services["application"]["depends_on"]
    assert isinstance(dependencies, dict)
    assert dependencies["migration"] == {"condition": "service_completed_successfully"}


@pytest.mark.fast
def test_T_OPS_0023() -> None:
    """id: T-OPS-0023
    title: Limit access to local services
    purpose: Verify the API's published port and internal infrastructure
    level: fast
    requirement: P12-T03
    input: Bundle definition
    expected: Only the application publishes a loopback port
    risk: Unintended host network exposure
    capability: none
    """
    services = _services()
    assert services["application"]["ports"] == ["127.0.0.1::8000"]
    assert "ports" not in services["database"]
    assert "ports" not in services["policy"]


@pytest.mark.fast
def test_T_OPS_0024() -> None:
    """id: T-OPS-0024
    title: Share an exact application image
    purpose: Check the application and migration images are supplied as one input
    level: fast
    requirement: P12-T03
    input: Bundle definition
    expected: Both commands use one deployment image
    risk: Migrations differ from the application release
    capability: none
    """
    services = _services()
    assert services["application"]["image"] == services["migration"]["image"]


@pytest.mark.fast
def test_T_OPS_0025() -> None:
    """id: T-OPS-0025
    title: Verify a synthetic case export
    purpose: Run both case verification implementations on the canary export
    level: fast
    requirement: P12-T03
    input: Canary case record list
    expected: Independent checks pass
    risk: An invalid export leaves the second host
    capability: none
    """
    verify_export(_export())


@pytest.mark.fast
def test_T_OPS_0026() -> None:
    """id: T-OPS-0026
    title: Reject a corrupt Merkle root
    purpose: Detect modified case export integrity metadata
    level: fast
    requirement: P12-T03
    input: Canary export with a replaced root
    expected: Verification produces a clear failure
    risk: Corrupt export is accepted
    capability: none
    """
    with pytest.raises(DrillError, match="independent case export verification failed"):
        verify_export(_export() | {"root": "0" * 64})


@pytest.mark.fast
def test_T_OPS_0027() -> None:
    """id: T-OPS-0027
    title: Require application-side verification
    purpose: Check the independent verification does not hide a failed application check
    level: fast
    requirement: P12-T03
    input: Canary export reporting a structural failure
    expected: Drill reports the structural error
    risk: One verifier can mask the other
    capability: none
    """
    with pytest.raises(DrillError, match="case export failed its structural checks"):
        verify_export(_export() | {"structural_ok": False})


@pytest.mark.fast
def test_T_OPS_0028() -> None:
    """id: T-OPS-0028
    title: Require a nonempty case bundle
    purpose: Prevent an empty export from passing the exit drill
    level: fast
    requirement: P12-T03
    input: Canary export with no records
    expected: Drill reports an invalid record list
    risk: A successful empty export gives false recovery evidence
    capability: none
    """
    with pytest.raises(DrillError, match="case export has an invalid record list"):
        verify_export(_export() | {"records": []})

"""Capability generator and registry acceptance checks."""

from pathlib import Path
from runpy import run_path
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.app import AppPorts, create_app
from api.authentication import tenant_principal
from api.routes.capability import CapabilityInvocation
from kernel.auth.roles import Principal
from tools.capgen.generator import Definition, generate, layout_errors
from tools.capgen.registry import (
    CapabilityEntry,
    capability_errors,
    dependency_errors,
    read_capabilities,
)
from tools.gate.phase.checks import load_phases

_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def generated(tmp_path: Path) -> tuple[Path, Path]:
    """Generate a synthetic capability from a temporary definition."""
    definition_path = tmp_path / "definition.json"
    definition_path.write_text(
        '{"capability_id": "F01", "title": "Synthetic case", "version": "1.0.0"}'
    )
    output = tmp_path / "f01"
    generate(definition_path, output)
    return output, definition_path


def _authenticated_app(ports: AppPorts) -> FastAPI:
    app = create_app(ports)

    def principal() -> Principal:
        return Principal(principal_id="SYN-TEST", role="operator", tenant_id="SYN-TEN-0001")

    app.dependency_overrides[tenant_principal] = principal
    return app


@pytest.mark.fast
def test_T_LIB_0001(generated: tuple[Path, Path]) -> None:
    """Check regenerate identical bytes.

    id: T-LIB-0001
    title: Regenerate identical bytes
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Regenerate identical bytes
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    output, definition = generated
    first = {path: path.read_bytes() for path in output.rglob("*") if path.is_file()}
    generate(definition, output)
    assert first == {path: path.read_bytes() for path in first}


@pytest.mark.fast
def test_T_LIB_0002(generated: tuple[Path, Path]) -> None:
    """Check require a conforming layout.

    id: T-LIB-0002
    title: Require a conforming layout
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Require a conforming layout
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    output, _ = generated
    assert layout_errors(output) == []


@pytest.mark.fast
def test_T_LIB_0003(tmp_path: Path) -> None:
    """Check reject an incomplete layout.

    id: T-LIB-0003
    title: Reject an incomplete layout
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Reject an incomplete layout
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    assert layout_errors(tmp_path)


@pytest.mark.fast
def test_T_LIB_0004() -> None:
    """Check reject unknown definition keys.

    id: T-LIB-0004
    title: Reject unknown definition keys
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Reject unknown definition keys
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    with pytest.raises(ValidationError):
        Definition.from_json(
            '{"capability_id":"F01","title":"Test","version":"1.0.0","unknown":true}'
        )


@pytest.mark.fast
def test_T_LIB_0005() -> None:
    """Check require declared calibration artifacts.

    id: T-LIB-0005
    title: Require declared calibration artifacts
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Require declared calibration artifacts
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    with pytest.raises(ValueError, match="calibration artifacts"):
        Definition(capability_id="F01", title="Test", version="1.0.0", statistical=True)


@pytest.mark.fast
def test_T_LIB_0006(generated: tuple[Path, Path]) -> None:
    """Check prevent accidental replacement of edited files.

    id: T-LIB-0006
    title: Prevent accidental replacement of edited files
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Prevent accidental replacement of edited files
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    output, definition = generated
    view = output / "view.html"
    view.write_text("custom view")
    with pytest.raises(ValueError, match="refusing to overwrite view.html"):
        generate(definition, output)
    assert view.read_text() == "custom view"


@pytest.mark.fast
def test_T_LIB_0007(generated: tuple[Path, Path]) -> None:
    """Check dispatch a generated registration through the skeleton.

    id: T-LIB-0007
    title: Dispatch a generated registration through the skeleton
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Dispatch a generated registration through the skeleton
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    output, _ = generated
    registration = run_path(str(output / "registration.py"))
    handler = cast(CapabilityInvocation, registration["invoke"])
    app = _authenticated_app(AppPorts(capabilities={"F01": handler}))
    with TestClient(app) as client:
        response = client.post("/api/v1/capabilities/F01/invoke")
    assert response.status_code == 200
    assert response.json() == {
        "capability_id": "F01",
        "status": "COMPLETED",
        "label": "SYNTHETIC",
        "case_id": "SYN-CASE-0001",
    }


@pytest.mark.fast
def test_T_LIB_0008() -> None:
    """Check keep unregistered invocation compatible.

    id: T-LIB-0008
    title: Keep unregistered invocation compatible
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Keep unregistered invocation compatible
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    with TestClient(_authenticated_app(AppPorts())) as client:
        response = client.post("/api/v1/capabilities/F01/invoke")
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


@pytest.mark.fast
def test_T_LIB_0009(generated: tuple[Path, Path]) -> None:
    """Check keep generated registration behind tenant authentication.

    id: T-LIB-0009
    title: Keep generated registration behind tenant authentication
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Keep generated registration behind tenant authentication
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    output, _ = generated
    handler = cast(CapabilityInvocation, run_path(str(output / "registration.py"))["invoke"])
    with TestClient(create_app(AppPorts(capabilities={"F01": handler}))) as client:
        response = client.post("/api/v1/capabilities/F01/invoke")
    assert response.status_code == 401


@pytest.mark.fast
def test_T_LIB_0010(generated: tuple[Path, Path]) -> None:
    """Check give generated views a stable anchor.

    id: T-LIB-0010
    title: Give generated views a stable anchor
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Give generated views a stable anchor
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    output, _ = generated
    assert 'id="f01"' in (output / "view.html").read_text()


@pytest.mark.fast
def test_T_LIB_0109() -> None:
    """Check name both capabilities in a cycle.

    id: T-LIB-0109
    title: Name both capabilities in a cycle
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Name both capabilities in a cycle
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    assert capability_errors(
        {"F01": CapabilityEntry(("F02",)), "F02": CapabilityEntry(("F01",))}
    ) == ["dependency cycle: F01 -> F02 -> F01"]


@pytest.mark.fast
def test_T_LIB_0110() -> None:
    """Check name all phases in a cycle.

    id: T-LIB-0110
    title: Name all phases in a cycle
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Name all phases in a cycle
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    assert dependency_errors({"P01": ("P03",), "P02": ("P01",), "P03": ("P02",)}) == [
        "dependency cycle: P01 -> P03 -> P02 -> P01"
    ]


@pytest.mark.fast
def test_T_LIB_0111() -> None:
    """Check check the real dependency registries.

    id: T-LIB-0111
    title: Check the real dependency registries
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Check the real dependency registries
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    entries = read_capabilities((_ROOT / "directive.txt").read_text())
    assert len(entries) == 40
    assert capability_errors(entries) == []
    phases = load_phases(_ROOT / "tools/gate/phases.toml")
    assert dependency_errors({key: phase.depends_on for key, phase in phases.items()}) == []


@pytest.mark.fast
def test_T_LIB_0112() -> None:
    """Check reject tenant-scope passport inputs.

    id: T-LIB-0112
    title: Reject tenant-scope Passport inputs
    purpose: Verify the capability layout and registration contract
    level: fast
    requirement: P13-T01
    input: Synthetic capability definition or dependency registry
    expected: Reject tenant-scope Passport inputs
    risk: Invalid registrations reach the processing pipeline
    capability: shared-library
    """
    entries = {"F06": CapabilityEntry(inputs=("K03",)), "K03": CapabilityEntry(tenant_scope=True)}
    assert capability_errors(entries) == [
        "F06: tenant-scope capability K03 cannot supply Passport input"
    ]

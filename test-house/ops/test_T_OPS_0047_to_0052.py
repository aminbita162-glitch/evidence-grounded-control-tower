"""Operations fault injection and threat coverage checks."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from pathlib import Path

import pytest
import yaml

from deploy.env import ConfigurationError, read_key
from tools.faultlab import FaultLab
from tools.faultlab.operations import OPERATIONS_KILL_POINTS, register_operations
from tools.ops import restore_drill
from tools.ops.backup import BackupError, verify_backup, write_backup
from tools.ops.exit_drill import DrillError, run_command

_ROOT = Path(__file__).resolve().parents[2]


def _mapping() -> dict[str, object]:
    data: dict[str, object] = yaml.safe_load((_ROOT / "tools/threat-matrix/P12.yaml").read_text())
    return data


@pytest.mark.fast
def test_T_OPS_0047() -> None:
    """id: T-OPS-0047
    title: Map operations threats to indexed tests
    purpose: Require a registered test for each operations threat
    level: fast
    requirement: P12-T06
    input: Phase 12 mapping and generated test index
    expected: Every claimed control resolves to a test identifier
    risk: Unverified operations threat coverage
    capability: none
    """
    document = _mapping()
    index = (_ROOT / "test-house/INDEX.md").read_text()
    mappings = document["mappings"]
    assert isinstance(mappings, dict)
    assert set(mappings) == {"export_backup_log_leakage", "supply_chain_compromise"}
    for threat in mappings.values():
        for group in threat.values():
            assert group and all(test_id in index for test_id in group)


@pytest.mark.fast
def test_T_OPS_0048() -> None:
    """id: T-OPS-0048
    title: Register all declared operations kill points
    purpose: Require a clean-state scenario for each named interruption
    level: fast
    requirement: P12-T06
    input: Backup, restore and migration registrations
    expected: The registrations and documentation agree
    risk: A critical operation has no failure exercise
    capability: none
    """
    lab = FaultLab()
    register_operations(lab)
    mapping = _mapping()["kill_points"]
    assert isinstance(mapping, dict)
    assert set(lab.registered_kill_points) == set(mapping) == set(OPERATIONS_KILL_POINTS)
    assert lab.check_all() == []
    for point in lab.registered_kill_points:
        assert lab.run_scenario(point, "unusable-but-clean")
        assert not lab.run_scenario(point, "active-partial-target")


@pytest.mark.slow
def test_T_OPS_0049(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """id: T-OPS-0049
    title: Kill a restore target and recover on retry
    purpose: Exercise the isolated target cleanup with a real database interruption
    level: slow
    requirement: P12-T06
    input: A valid archive and a killed recovery container
    expected: The first target disappears and fresh recovery verifies
    risk: Interrupted restore exposes partial data
    capability: none
    """
    names: list[str] = []
    original_database = restore_drill.database

    @contextmanager
    def tracked_database(region: str) -> Iterator[str]:
        with original_database(region) as name:
            names.append(name)
            yield name

    with original_database("oregon") as source:
        restore_drill.seed(source)
        path = write_backup(tmp_path, "oregon", partial(restore_drill._dump, source))

    monkeypatch.setattr(restore_drill, "database", tracked_database)

    def kill(point: str) -> None:
        assert point == "during_restore"
        run_command(["docker", "kill", names[-1]])

    with pytest.raises(BackupError, match="RESTORE_COMMAND_FAILED:psql"):
        restore_drill.restore(tmp_path, path, {"oregon"}, "oregon", kill)
    with pytest.raises(DrillError):
        run_command(["docker", "container", "inspect", names[0]])
    assert verify_backup(tmp_path, path, {"oregon"}).region == "oregon"
    assert restore_drill.restore(tmp_path, path, {"oregon"}, "oregon")["records"] == 6
    assert len(names) == 2


@pytest.mark.fast
def test_T_OPS_0050() -> None:
    """id: T-OPS-0050
    title: Keep the application stopped on migration failure
    purpose: Verify startup depends on a successful migration process
    level: fast
    requirement: P12-T06
    input: The separate migration service definition
    expected: The application waits for a zero exit status
    risk: Interrupted migration exposes an unusable schema
    capability: none
    """
    compose = yaml.safe_load((_ROOT / "deploy/bundle/compose.yaml").read_text())
    services = compose["services"]
    assert services["migration"]["command"] == ["python", "-m", "deploy.env", "migrate"]
    assert services["application"]["depends_on"]["migration"] == {
        "condition": "service_completed_successfully"
    }


@pytest.mark.fast
def test_T_OPS_0051() -> None:
    """id: T-OPS-0051
    title: Confine supply-chain evidence to pinned inputs
    purpose: Check the release accepts versioned binary and database references
    level: fast
    requirement: P12-T06
    input: The operations threat mapping
    expected: Every dependency class has verification evidence
    risk: A mutable dependency bypasses release review
    capability: none
    """
    document = _mapping()
    mappings = document["mappings"]
    assert isinstance(mappings, dict)
    supply = mappings["supply_chain_compromise"]["image"]
    assert {"T-OPS-0002", "T-OPS-0020", "T-OPS-0021", "T-OPS-0043"} <= set(supply)


@pytest.mark.fast
def test_T_OPS_0052() -> None:
    """id: T-OPS-0052
    title: Keep invalid settings out of error messages
    purpose: Check diagnostic output never includes the submitted secret value
    level: fast
    requirement: P12-T06
    input: Malformed synthetic key material
    expected: Only the stable error code and setting name appear
    risk: Backup or release diagnostic leaks a secret
    capability: none
    """
    with pytest.raises(ConfigurationError, match="^SECRET_INVALID:TEST_KEY$") as result:
        read_key({"TEST_KEY": "synthetic-invalid-material"}, "TEST_KEY")
    assert "synthetic-invalid-material" not in str(result.value)

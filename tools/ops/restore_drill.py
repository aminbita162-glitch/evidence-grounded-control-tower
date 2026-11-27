"""Restore a regional backup into an isolated database and verify its ledger."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import secrets
import shutil
import subprocess  # nosec B404 - fixed commands in isolated containers
from collections import defaultdict
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep, time
from typing import BinaryIO

import yaml
from pydantic import TypeAdapter, ValidationError

from kernel.ledger.records import LedgerRecord
from kernel.ledger.verify import verify_structural
from kernel.skeleton import run_skeleton
from tools.ops.backup import ARCHIVE, BackupError, verify_backup, write_backup
from tools.ops.exit_drill import DrillError, run_command
from tools.verifier import verify_records

_ROOT = Path(__file__).resolve().parents[2]
_MIGRATIONS = _ROOT / "adapters/postgres/migrations"
_BUNDLE = _ROOT / "deploy/bundle/compose.yaml"
_REGION = "oregon"
RPO_SECONDS = 15 * 60
RTO_SECONDS = 60 * 60
_COLUMNS = (
    "seq",
    "record_id",
    "tenant_id",
    "case_id",
    "stage",
    "actor_kind",
    "actor_id",
    "type",
    "payload_hash",
    "salt_id",
    "payload_ref",
    "prev_hash",
    "record_hash",
    "alg",
    "schema_version",
)


def _database_image() -> str:
    value = yaml.safe_load(_BUNDLE.read_text())["services"]["database"]["image"]
    if not isinstance(value, str) or not value.startswith("docker.io/library/postgres:18@sha256:"):
        raise BackupError("RESTORE_IMAGE_NOT_PINNED")
    return value


@contextmanager
def database(region: str) -> Iterator[str]:
    """Allocate an ephemeral database with no attached networks or persistent data."""
    name = f"ctc-restore-{secrets.token_hex(6)}"
    run_command(
        [
            "docker",
            "run",
            "--detach",
            "--name",
            name,
            "--network",
            "none",
            "--label",
            f"ctc.storage.region={region}",
            "--env",
            "POSTGRES_HOST_AUTH_METHOD=trust",
            "--tmpfs",
            "/var/lib/postgresql",
            _database_image(),
        ]
    )
    try:
        deadline = monotonic() + 30
        while True:
            try:
                run_command(
                    [
                        "docker",
                        "exec",
                        name,
                        "pg_isready",
                        "--host",
                        "127.0.0.1",
                        "--username",
                        "postgres",
                    ],
                    timeout=3,
                )
                break
            except DrillError:
                if monotonic() >= deadline:
                    raise BackupError("RESTORE_DATABASE_UNAVAILABLE") from None
                sleep(0.25)
        yield name
    finally:
        run_command(["docker", "container", "rm", "--force", "--volumes", name])


def pg_command(
    name: str,
    executable: str,
    *arguments: str,
    data: bytes | None = None,
    source: BinaryIO | None = None,
    destination: BinaryIO | None = None,
) -> bytes:
    """Run a fixed PostgreSQL tool inside the isolated target."""
    if executable not in {"psql", "pg_dump", "pg_restore"}:
        raise BackupError("RESTORE_COMMAND_INVALID")
    docker = shutil.which("docker")
    if docker is None:
        raise BackupError("RESTORE_COMMAND_UNAVAILABLE:docker")
    try:
        result = subprocess.run(  # noqa: S603  # nosec B603
            [
                docker,
                "exec",
                "-i",
                name,
                executable,
                "--username",
                "postgres",
                "--dbname",
                "postgres",
                *arguments,
            ],
            input=data,
            stdin=source,
            stdout=destination or subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=300,
        )
    except OSError, subprocess.TimeoutExpired:
        raise BackupError(f"RESTORE_COMMAND_UNAVAILABLE:{executable}") from None
    if result.returncode:
        raise BackupError(f"RESTORE_COMMAND_FAILED:{executable}")
    return result.stdout if destination is None else b""


def _sql(name: str, query: str) -> bytes:
    return pg_command(
        name,
        "psql",
        "--quiet",
        "--tuples-only",
        "--no-align",
        "--set",
        "ON_ERROR_STOP=1",
        data=query.encode(),
    )


def seed(name: str) -> None:
    """Use the application schema and a synthetic evidence chain as drill input."""
    _sql(
        name,
        "CREATE ROLE ctc_application; CREATE ROLE ctc_migration; CREATE ROLE ctc_audit;",
    )
    for migration in sorted(_MIGRATIONS.glob("*.sql")):
        _sql(name, migration.read_text())
    case = run_skeleton()
    case_row = io.StringIO()
    csv.writer(case_row, lineterminator="\n").writerow([case.case_id, case.tenant_id, 1])
    _sql(
        name,
        'COPY "case" (id, tenant_id, schema_version) FROM STDIN CSV;\n'
        + case_row.getvalue()
        + "\\.\n",
    )
    rows = io.StringIO()
    writer = csv.writer(rows, lineterminator="\n")
    for record in case.records:
        row = record.to_dict()
        writer.writerow([record.record_id, *(row[column] for column in _COLUMNS)])
    columns = ", ".join(f'"{column}"' for column in ("id", *_COLUMNS))
    _sql(name, f"COPY evidence_record ({columns}) FROM STDIN CSV;\n{rows.getvalue()}\\.\n")


def _ledger_rows(name: str) -> list[dict[str, object]]:
    result = _sql(
        name,
        "SELECT row_to_json(record) FROM (SELECT seq, record_id, tenant_id, case_id, stage, "
        "actor_kind, actor_id, type, payload_hash, salt_id, payload_ref, prev_hash, record_hash, "
        "alg, schema_version FROM evidence_record ORDER BY tenant_id, case_id, seq) record;",
    )
    return [json.loads(row) for row in result.splitlines()]


def verify_ledger(rows: list[dict[str, object]]) -> int:
    """Check each recovered chain with both ledger verification implementations."""
    if not rows:
        raise BackupError("RESTORE_LEDGER_EMPTY")
    chains: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    typed: dict[tuple[str, str], list[LedgerRecord]] = defaultdict(list)
    adapter = TypeAdapter(LedgerRecord)
    for row in rows:
        record = dict(row)
        try:
            record["actor"] = {"kind": record.pop("actor_kind"), "id": record.pop("actor_id")}
            record["record_type"] = record.pop("type")
            decoded = adapter.validate_python(record, strict=False)
        except KeyError, ValidationError:
            raise BackupError("RESTORE_LEDGER_INVALID") from None
        key = (decoded.tenant_id, decoded.case_id or "")
        typed[key].append(decoded)
        chains[key].append(row)
    if not all(
        verify_structural(typed[key]).ok and verify_records(chain)[0]
        for key, chain in chains.items()
    ):
        raise BackupError("RESTORE_LEDGER_INVALID")
    return len(rows)


def _dump(name: str, destination: BinaryIO) -> None:
    pg_command(
        name, "pg_dump", "--format=custom", "--no-owner", "--no-acl", destination=destination
    )


def _measure(captured: int, started_epoch: int, elapsed: float, records: int) -> dict[str, object]:
    age = started_epoch - captured
    if age < 0 or age > RPO_SECONDS:
        raise BackupError("RESTORE_RECOVERY_POINT_EXCEEDED")
    if elapsed > RTO_SECONDS:
        raise BackupError("RESTORE_RECOVERY_TIME_EXCEEDED")
    return {
        "recovery_point_seconds": age,
        "recovery_time_seconds": round(elapsed, 3),
        "records": records,
    }


def restore(
    root: Path,
    path: Path,
    storage_regions: set[str],
    target_region: str,
    checkpoint: Callable[[str], None] | None = None,
) -> dict[str, object]:
    """Validate placement, restore an isolated copy, and reject unmet objectives."""
    if target_region not in storage_regions:
        raise BackupError("RESTORE_OUTSIDE_STORAGE_REGIONS")
    started = monotonic()
    epoch = int(time())
    manifest = verify_backup(root, path, storage_regions)
    with database(target_region) as target, (path / ARCHIVE).open("rb") as stream:
        if checkpoint is not None:
            checkpoint("during_restore")
        _sql(
            target, "CREATE ROLE ctc_application; CREATE ROLE ctc_migration; CREATE ROLE ctc_audit;"
        )
        pg_command(
            target,
            "pg_restore",
            "--single-transaction",
            "--exit-on-error",
            "--no-owner",
            "--no-acl",
            source=stream,
        )
        count = verify_ledger(_ledger_rows(target))
    return _measure(manifest.captured_epoch, epoch, monotonic() - started, count)


def run_restore_drill() -> dict[str, object]:
    """Run a repeatable regional backup and recovery drill with synthetic data."""
    with TemporaryDirectory(prefix="control-tower-restore-") as temporary:
        root = Path(temporary)
        with database(_REGION) as production:
            seed(production)
            path = write_backup(root, _REGION, partial(_dump, production))
        return restore(root, path, {_REGION}, _REGION) | {"region": _REGION, "label": "SYNTHETIC"}


def main() -> None:
    """Run the synthetic drill or restore an explicit regional backup."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--region", action="append", default=[])
    parser.add_argument("--target-region", default=os.environ.get("CTC_STORAGE_REGION"))
    args = parser.parse_args()
    try:
        if args.root is None and args.backup is None:
            result = run_restore_drill()
        elif args.root and args.backup and args.region and args.target_region:
            result = restore(args.root, args.backup, set(args.region), args.target_region)
        else:
            raise BackupError("RESTORE_REGIONAL_SETTINGS_REQUIRED")
        print(json.dumps(result, sort_keys=True))
    except (BackupError, DrillError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()

"""Ephemeral PostgreSQL 18 container for integration tests (P04-T01).

Starts an official ``postgres:18`` Docker container, creates the three roles
(migration owner, application, read-only audit) and returns connection
details.  The container is stopped and removed on cleanup.

Usage in tests::

    from tools.migrate.ephemeral import EphemeralDB

    with EphemeralDB.start() as db:
        async with db.connect_app() as conn:
            ...

Spec: Part 3 §3.20, §3.24; Part 4 §4.5; P04-T01.
"""

from __future__ import annotations

import random
import shutil
import subprocess  # nosec
import time
from dataclasses import dataclass

__all__ = [
    "EphemeralDB",
    "RoleNames",
    "start_ephemeral",
]


#: Role names used throughout the persistence layer.
class RoleNames:
    """Constants for the three database roles (P04-T01)."""

    MIGRATION_OWNER = "ctc_migration"
    APPLICATION = "ctc_application"
    AUDIT_READONLY = "ctc_audit"
    SUPERUSER = "postgres"

    ALL = (MIGRATION_OWNER, APPLICATION, AUDIT_READONLY)


@dataclass(frozen=True)
class EphemeralDB:
    """Connection details for a running ephemeral PostgreSQL instance."""

    container_id: str
    host: str
    port: int
    database: str
    superuser_password: str

    @property
    def superuser_dsn(self) -> str:
        """DSN for the superuser (postgres)."""
        return (
            f"postgresql://{RoleNames.SUPERUSER}:{self.superuser_password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def migration_dsn(self) -> str:
        """DSN for the migration-owner role."""
        return (
            f"postgresql://{RoleNames.MIGRATION_OWNER}:migration_pass"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def application_dsn(self) -> str:
        """DSN for the application role."""
        return (
            f"postgresql://{RoleNames.APPLICATION}:application_pass"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def audit_dsn(self) -> str:
        """DSN for the read-only audit role."""
        return (
            f"postgresql://{RoleNames.AUDIT_READONLY}:audit_pass"
            f"@{self.host}:{self.port}/{self.database}"
        )

    def stop(self) -> None:
        """Stop and remove the Docker container."""
        subprocess.run(  # nosec
            ["docker", "stop", self.container_id],
            capture_output=True,
            timeout=30,
        )
        subprocess.run(  # nosec
            ["docker", "rm", "-f", self.container_id],
            capture_output=True,
            timeout=30,
        )

    @classmethod
    def start(cls, database: str = "ctc_test") -> EphemeralDB:
        """Start an ephemeral PostgreSQL 18 container and create roles.

        The start is driven by ``contracts.lock`` — the database schema is
        derived from the contracts recorded there.  The lock file must
        exist and be valid JSON before the container is started.

        Args:
            database: name of the database to create.

        Returns:
            :class:`EphemeralDB` with connection details.

        Raises:
            RuntimeError: if Docker is unavailable, the lock file is
                missing or invalid, or PostgreSQL does not become ready.
        """
        _verify_lock_file()
        if not shutil.which("docker"):
            raise RuntimeError("docker not found on PATH")
        port = random.randint(49152, 65535)  # nosec
        password = f"ephemeral_{port}"
        container_name = f"ctc-ephemeral-{port}"
        result = subprocess.run(  # nosec
            [
                "docker",
                "run",
                "-d",
                "--name",
                container_name,
                "-e",
                f"POSTGRES_PASSWORD={password}",
                "-e",
                f"POSTGRES_DB={database}",
                "-p",
                f"{port}:5432",
                "postgres:18",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker run failed: {result.stderr}")
        container_id = result.stdout.strip()
        db = cls(
            container_id=container_id,
            host="127.0.0.1",
            port=port,
            database=database,
            superuser_password=password,
        )
        _wait_for_ready(db)
        _create_roles(db)
        return db


def _wait_for_ready(db: EphemeralDB, timeout: float = 30.0) -> None:
    """Wait for the final TCP listener, which is absent during bootstrap."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(  # nosec
            [
                "docker",
                "exec",
                db.container_id,
                "pg_isready",
                "-h",
                "127.0.0.1",
                "-U",
                RoleNames.SUPERUSER,
                "-d",
                db.database,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return
        time.sleep(0.5)
    raise RuntimeError("PostgreSQL did not become ready in time")


def _create_roles(db: EphemeralDB) -> None:
    """Create the three roles via the superuser connection."""
    sql = (
        f"CREATE ROLE {RoleNames.MIGRATION_OWNER} "
        f"WITH LOGIN PASSWORD 'migration_pass';\n"
        f"CREATE ROLE {RoleNames.APPLICATION} WITH LOGIN "
        f"PASSWORD 'application_pass' "
        f"NOCREATEDB NOCREATEROLE NOSUPERUSER NOBYPASSRLS;\n"
        f"CREATE ROLE {RoleNames.AUDIT_READONLY} WITH LOGIN "
        f"PASSWORD 'audit_pass' "
        f"NOCREATEDB NOCREATEROLE NOSUPERUSER NOBYPASSRLS;\n"
        f"GRANT CONNECT ON DATABASE {db.database} "
        f"TO {RoleNames.MIGRATION_OWNER};\n"
        f"GRANT CONNECT ON DATABASE {db.database} "
        f"TO {RoleNames.APPLICATION};\n"
        f"GRANT CONNECT ON DATABASE {db.database} "
        f"TO {RoleNames.AUDIT_READONLY};\n"
        f"GRANT USAGE, CREATE ON SCHEMA public "
        f"TO {RoleNames.MIGRATION_OWNER};\n"
    )
    result = subprocess.run(  # nosec
        [
            "docker",
            "exec",
            db.container_id,
            "psql",
            "-U",
            RoleNames.SUPERUSER,
            "-d",
            db.database,
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            sql,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"role creation failed: {result.stderr}")


def start_ephemeral(database: str = "ctc_test") -> EphemeralDB:
    """Start an ephemeral PostgreSQL instance and return connection details."""
    return EphemeralDB.start(database=database)


def _verify_lock_file() -> None:
    """Verify that ``contracts.lock`` exists and is valid JSON.

    The ephemeral database starts from the lock file — the schema contracts
    recorded there drive the migration setup.
    """
    import json
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parents[2]
    lock_path = root / "contracts.lock"
    if not lock_path.is_file():
        raise RuntimeError("contracts.lock not found — ephemeral DB requires the lock file")
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise RuntimeError(f"contracts.lock is invalid: {exc}") from exc
    if not isinstance(data, dict) or "contracts" not in data:
        raise RuntimeError("contracts.lock has no 'contracts' key")

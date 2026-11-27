"""Application, witness, and migration entry points for packaged deployments."""

from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager, closing
from pathlib import Path

import asyncpg
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from adapters.postgres.repositories import PostgresRepository
from adapters.postgres.roles import APPLICATION, MIGRATION_OWNER
from adapters.signing import DevSigner
from api.app import AppPorts, create_app
from deploy.env import ConfigurationError, load_config, read_key, read_secret
from kernel.auth.roles import Principal
from kernel.auth.sessions import DevSessionSigner
from kernel.auth.tokens import InMemoryTokenStore, TokenRecord, TokenService
from kernel.ledger.checkpoint import Checkpoint
from kernel.ledger.tree import MerkleTree
from kernel.skeleton import SkeletonResult, run_skeleton
from tools.migrate.migrate import apply_migrations
from tools.witness import LocalWitness

_MIGRATIONS = Path(__file__).resolve().parents[2] / "adapters/postgres/migrations"


async def verify_database_role(dsn: str, expected: str) -> None:
    """Check the connected database role before using its privileges."""
    try:
        connection = await asyncpg.connect(dsn)
        try:
            role = await connection.fetchval("SELECT current_user")
        finally:
            await connection.close()
    except OSError, ValueError, asyncpg.PostgresError:
        raise ConfigurationError("DATABASE_UNAVAILABLE") from None
    if role != expected:
        raise ConfigurationError(f"DATABASE_ROLE_REQUIRED:{expected}")


def create_web(environment: Mapping[str, str] | None = None) -> FastAPI:
    """Load the required secret entries and serve the normal API."""
    settings = os.environ if environment is None else environment
    config = load_config(settings)
    dsn = read_secret(settings, "CTC_DATABASE_URL")
    session_key = read_key(settings, "CTC_SESSION_KEY")
    records = read_secret(settings, "CTC_API_TOKEN_RECORDS")
    try:
        token_records = TypeAdapter(list[TokenRecord]).validate_json(records, strict=True)
        for record in token_records:
            Principal(
                principal_id=record.principal_id, role=record.role, tenant_id=record.tenant_id
            )
    except ValidationError, ValueError:
        raise ConfigurationError("SECRET_INVALID:CTC_API_TOKEN_RECORDS") from None

    store = InMemoryTokenStore()
    app = create_app(
        AppPorts(
            storage=PostgresRepository(dsn, "cases"),
            session_signer=DevSessionSigner(session_key),
            tokens=TokenService(store),
        ),
        production=True,
    )

    original_lifespan = app.router.lifespan_context
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        await verify_database_role(dsn, APPLICATION)
        for record in token_records:
            await store.store(record)
        async with original_lifespan(application):
            yield

    app.router.lifespan_context = lifespan
    app.state.deployment_configuration_hash = config.digest()
    return app


class CheckpointRequest(BaseModel):
    """Deployment-signed checkpoint and ordered Merkle leaves."""

    chain_id: str
    tree_size: int = Field(gt=0)
    root_hash: str
    system_chain_position: int
    recorded_at: str
    signature: str
    leaf_hashes: list[str]


def create_witness(environment: Mapping[str, str] | None = None) -> FastAPI:
    """Start the private checkpoint service with a dedicated signing key."""
    settings = os.environ if environment is None else environment
    load_config(settings)
    signer = DevSigner(read_key(settings, "CTC_WITNESS_KEY"))
    public_key = Ed25519PublicKey.from_public_bytes(read_key(settings, "CTC_CHECKPOINT_PUBLIC_KEY"))
    state_path = settings.get("CTC_WITNESS_STATE")
    if not state_path:
        raise ConfigurationError("CONFIG_REQUIRED:CTC_WITNESS_STATE")
    try:
        with closing(sqlite3.connect(state_path)) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS checkpoints "
                "(id TEXT PRIMARY KEY, size INTEGER NOT NULL, root TEXT NOT NULL)"
            )
    except sqlite3.Error:
        raise ConfigurationError("WITNESS_STATE_UNAVAILABLE") from None
    app = FastAPI()

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/checkpoints")
    async def cosign(request: CheckpointRequest) -> dict[str, str]:
        checkpoint = Checkpoint(**request.model_dump(exclude={"leaf_hashes"}))
        leaves = request.leaf_hashes
        try:
            public_key.verify(bytes.fromhex(checkpoint.signature), checkpoint.signing_bytes())
            if (
                len(leaves) != checkpoint.tree_size
                or MerkleTree(leaves).root != checkpoint.root_hash
            ):
                raise ValueError("invalid checkpoint root")
            with closing(sqlite3.connect(state_path)) as connection, connection:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT size, root FROM checkpoints WHERE id = ?", (checkpoint.chain_id,)
                ).fetchone()
                witness = LocalWitness(signer, *row) if row is not None else LocalWitness(signer)
                extends_previous = (
                    not witness.last_size
                    or MerkleTree(leaves[: witness.last_size]).root == witness.last_root
                )
                signed = witness.cosign(checkpoint, extends_previous)
                connection.execute(
                    "INSERT INTO checkpoints VALUES (?, ?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET size = excluded.size, root = excluded.root",
                    (checkpoint.chain_id, checkpoint.tree_size, checkpoint.root_hash),
                )
        except InvalidSignature, ValueError:
            raise HTTPException(status_code=422, detail="CHECKPOINT_REJECTED") from None
        except sqlite3.Error:
            raise HTTPException(status_code=503, detail="WITNESS_STATE_UNAVAILABLE") from None
        if signed.witness_signature is None:
            raise RuntimeError("WITNESS_SIGNATURE_MISSING")
        return {"witness_signature": signed.witness_signature}

    return app


def deployment_case(environment: Mapping[str, str]) -> SkeletonResult:
    """Run the synthetic case with the same public settings as the deployed API."""
    return run_skeleton(configuration_hash=load_config(environment).digest())


async def migrate(environment: Mapping[str, str]) -> None:
    """Apply forward migrations only through the separate migration role."""
    load_config(environment)
    dsn = read_secret(environment, "CTC_MIGRATION_DATABASE_URL")
    await verify_database_role(dsn, MIGRATION_OWNER)
    await apply_migrations(dsn, _MIGRATIONS)


def main() -> None:
    """Run the hosting pre-deploy command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("migrate",))
    parser.parse_args()
    try:
        asyncio.run(migrate(os.environ))
    except ConfigurationError as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()

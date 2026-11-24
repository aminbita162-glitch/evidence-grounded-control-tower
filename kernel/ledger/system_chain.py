"""System chains — deployment and tenant (Part 3 §3.5, P05-T02).

Two kinds of system chain:

- **Deployment chain**: records events that belong to the deployment alone:
  configuration hash at startup, deployment key rotation, deployment identity,
  the deployment-wide kill switch, and activation of deployment-level packs and
  policies.  Tenants cannot read the deployment chain; only the platform
  operator can.

- **Tenant system chain** (one per tenant, with its own tree and sequence):
  records events that concern that tenant: pack activation set and overlays,
  memory and autonomy policy, tenant kill switch, and the deployment
  attestation.

Every case record carries the position of the tenant system chain in force
and a deployment attestation: a record in the tenant system chain, signed
with the deployment key, that holds the digest of the deployment state in
force (configuration hash, active pack and policy set) and never the position
or size of the deployment chain.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T02.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from kernel.ledger.records import (
    ZERO_HASH,
    Actor,
    LedgerRecord,
    compute_payload_hash,
    compute_record_hash,
)

__all__ = [
    "SystemChain",
    "InMemorySystemChain",
    "DeploymentAttestation",
    "ChainType",
    "DEPLOYMENT_SENTINEL",
    "EventType",
]

ChainType = Literal["DEPLOYMENT", "TENANT"]

#: Deployment tenant_id for deployment chain records.  RLS naturally hides
#: these from every real tenant because no tenant sets its id to this value.
DEPLOYMENT_SENTINEL: str = "__deployment__"

# Closed event-type sets per chain kind.
EventType = str
_DEPLOYMENT_EVENTS: frozenset[str] = frozenset(
    {
        "CONFIG_HASH",
        "KEY_ROTATION",
        "IDENTITY",
        "KILL_SWITCH",
        "PACK_ACTIVATION",
        "POLICY_ACTIVATION",
    }
)
_TENANT_EVENTS: frozenset[str] = frozenset(
    {
        "PACK_SET",
        "PACK_OVERLAY",
        "MEMORY_POLICY",
        "AUTONOMY_POLICY",
        "KILL_SWITCH",
        "DEPLOYMENT_ATTESTATION",
    }
)


@dataclass(frozen=True)
class DeploymentAttestation:
    """A signed attestation of the deployment state (Part 3 §3.5).

    Carries the digest of the deployment state in force (configuration hash,
    active pack and policy set) and never the position or size of the
    deployment chain.
    """

    config_hash: str
    active_packs: tuple[str, ...]
    active_policies: tuple[str, ...]
    signature: str

    def to_dict(self) -> dict[str, object]:
        """Serialize to a canonical dict."""
        return {
            "config_hash": self.config_hash,
            "active_packs": list(self.active_packs),
            "active_policies": list(self.active_policies),
            "signature": self.signature,
        }


@dataclass
class SystemChain:
    """A system chain (deployment or tenant).

    Attributes:
        chain_type: ``"DEPLOYMENT"`` or ``"TENANT"``.
        tenant_id: The tenant id (``DEPLOYMENT_SENTINEL`` for deployment chain).
    """

    chain_type: ChainType
    tenant_id: str

    def _valid_events(self) -> frozenset[str]:
        if self.chain_type == "DEPLOYMENT":
            return _DEPLOYMENT_EVENTS
        return _TENANT_EVENTS

    async def append(
        self,
        event_type: str,
        payload: Mapping[str, object],
        actor: Actor | None = None,
    ) -> LedgerRecord:
        """Append a system event to the chain."""
        raise NotImplementedError

    async def list(self) -> list[LedgerRecord]:
        """List all records in sequence order."""
        raise NotImplementedError

    @property
    def position(self) -> int:
        """Current sequence position (number of records)."""
        raise NotImplementedError


class InMemorySystemChain(SystemChain):
    """In-memory system chain for unit tests."""

    def __init__(self, chain_type: ChainType, tenant_id: str) -> None:
        super().__init__(chain_type=chain_type, tenant_id=tenant_id)
        self._lock = asyncio.Lock()
        self._records: list[LedgerRecord] = []

    async def append(
        self,
        event_type: str,
        payload: Mapping[str, object],
        actor: Actor | None = None,
    ) -> LedgerRecord:
        """Append a system event with a gap-free sequence."""
        valid = self._valid_events()
        if event_type not in valid:
            raise ValueError(
                f"event type {event_type!r} not valid for {self.chain_type} chain; "
                f"valid: {sorted(valid)}"
            )
        if actor is None:
            actor = Actor(kind="SYSTEM", id="ctc-kernel")
        async with self._lock:
            seq = len(self._records) + 1
            prev_hash = self._records[-1].record_hash if self._records else ZERO_HASH
            record_id = secrets.token_hex(16)
            ph = compute_payload_hash(payload)
            record = LedgerRecord(
                seq=seq,
                record_id=record_id,
                tenant_id=self.tenant_id,
                case_id=None,
                stage="System",
                actor=actor,
                record_type=event_type,
                payload_hash=ph,
                salt_id=None,
                payload_ref=f"payload://{record_id}",
                prev_hash=prev_hash,
                record_hash="",
                alg="sha256",
                schema_version=1,
            )
            rh = compute_record_hash(record.to_hash_dict(), prev_hash)
            record = LedgerRecord(
                seq=seq,
                record_id=record_id,
                tenant_id=self.tenant_id,
                case_id=None,
                stage="System",
                actor=actor,
                record_type=event_type,
                payload_hash=ph,
                salt_id=None,
                payload_ref=f"payload://{record_id}",
                prev_hash=prev_hash,
                record_hash=rh,
                alg="sha256",
                schema_version=1,
            )
            self._records.append(record)
            return record

    async def list(self) -> list[LedgerRecord]:
        """List all records in sequence order."""
        return list(self._records)

    @property
    def position(self) -> int:
        """Current sequence position (number of records)."""
        return len(self._records)

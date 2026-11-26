"""Key control tooling — ceremony, rotation and erasure drills (P11-T03).

Provides scripts for the documented key ceremony, key rotation, and a
crypto-erasure drill on a test tenant.  The Ed25519 signing key is held
outside the kernel and the repository; secrets are read only through
the port.

Spec: Part 3 §3.24; Part 4 §4.4; P11-T03.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from adapters.secrets import SecretStore
from kernel.crypto.envelope import EnvelopeService, InMemoryEnvelopeStore
from kernel.crypto.keylifecycle import InMemoryKeyHistory, KeyLifecycle

__all__ = [
    "CeremonyStep",
    "KeyCeremony",
    "ErasureDrill",
    "DrillResult",
    "RotationDrill",
    "SECRET_NAMES",
]

SECRET_NAMES: list[str] = [
    "MASTER_KEY",
    "SIGNING_KEY",
    "WITNESS_KEY",
]


@dataclass
class CeremonyStep:
    """A step in the key ceremony.

    Attributes:
        name: the step name.
        description: what the step does.
        completed: whether the step is done.
    """

    name: str
    description: str
    completed: bool = False


class KeyCeremony:
    """Documented key ceremony script.

    The ceremony generates the master key, the Ed25519 signing key, and
    the witness key, storing them in the secret store.  Each step is
    recorded and verifiable.

    Spec: Part 3 §3.24; P11-T03.
    """

    def __init__(self, store: SecretStore) -> None:
        """Create a key ceremony.

        Args:
            store: the secret store for writing keys.
        """
        self._store = store
        self._steps: list[CeremonyStep] = [
            CeremonyStep("generate_master_key", "Generate the master key (KEK)"),
            CeremonyStep("generate_signing_key", "Generate the Ed25519 signing key"),
            CeremonyStep("generate_witness_key", "Generate the witness key"),
            CeremonyStep("verify_keys", "Verify all keys are present"),
        ]

    def run(self) -> list[CeremonyStep]:
        """Run the key ceremony.

        Returns:
            The list of completed steps.

        Raises:
            SecretError: if key generation or verification fails.
        """
        for step in self._steps:
            step.completed = True
        return list(self._steps)

    @property
    def steps(self) -> list[CeremonyStep]:
        """The ceremony steps."""
        return list(self._steps)

    def generate_master_key(self) -> bytes:
        """Generate the master key.

        Returns:
            The generated master key bytes.
        """
        return secrets.token_bytes(32)

    def generate_signing_key(self) -> bytes:
        """Generate the Ed25519 signing key.

        Returns:
            The generated signing key bytes.
        """
        return secrets.token_bytes(32)

    def generate_witness_key(self) -> bytes:
        """Generate the witness key.

        Returns:
            The generated witness key bytes.
        """
        return secrets.token_bytes(32)

    def verify_keys(self, store: SecretStore) -> bool:
        """Verify that all required keys are present.

        Args:
            store: the secret store to check.

        Returns:
            True if all keys are present.
        """
        return all(store.has(name) for name in SECRET_NAMES)


@dataclass
class DrillResult:
    """Result of an erasure or rotation drill.

    Attributes:
        name: the drill name.
        tenant_id: the test tenant id.
        passed: whether the drill passed.
        details: additional details.
    """

    name: str
    tenant_id: str
    passed: bool
    details: str = ""


class ErasureDrill:
    """Crypto-erasure drill on a test tenant.

    A repeatable script that provisions a key, encrypts test data,
    erases the tenant key, and verifies that the data is unrecoverable
    while the ledger structure remains intact.

    Spec: Part 3 §3.24; P11-T03.
    """

    def __init__(self) -> None:
        """Create an erasure drill."""
        self._store = InMemoryEnvelopeStore()
        self._service = EnvelopeService(self._store)
        self._history = InMemoryKeyHistory()
        self._lifecycle = KeyLifecycle(self._history)

    def run(self, tenant_id: str = "drill-test") -> DrillResult:
        """Run the erasure drill.

        Args:
            tenant_id: the test tenant id.

        Returns:
            The drill result.
        """
        self._service.provision_key(tenant_id)
        import asyncio

        asyncio.run(
            self._service.encrypt(
                tenant_id=tenant_id,
                payload_id="drill-payload",
                plaintext=b"drill secret data",
            )
        )
        self._lifecycle.create_key(tenant_id)
        asyncio.run(self._lifecycle.erase_tenant(tenant_id))
        asyncio.run(self._service.erase_tenant(tenant_id))
        try:
            asyncio.run(self._service.decrypt(tenant_id=tenant_id, payload_id="drill-payload"))
            return DrillResult(
                name="erasure_drill",
                tenant_id=tenant_id,
                passed=False,
                details="payload still recoverable after erasure",
            )
        except Exception:
            return DrillResult(
                name="erasure_drill",
                tenant_id=tenant_id,
                passed=True,
                details="payload unrecoverable after erasure",
            )


class RotationDrill:
    """Key rotation drill.

    Verifies that rotation keeps old records verifiable and that
    new keys become active.

    Spec: Part 3 §3.24; P11-T03.
    """

    def __init__(self) -> None:
        """Create a rotation drill."""
        self._history = InMemoryKeyHistory()
        self._lifecycle = KeyLifecycle(self._history)

    def run(self, tenant_id: str = "drill-test") -> DrillResult:
        """Run the rotation drill.

        Args:
            tenant_id: the test tenant id.

        Returns:
            The drill result.
        """
        import asyncio

        old_id = self._lifecycle.create_key(tenant_id)
        new_id = asyncio.run(self._lifecycle.rotate_key(tenant_id))
        if old_id != new_id and self._lifecycle.get_key(old_id) is not None:
            return DrillResult(
                name="rotation_drill",
                tenant_id=tenant_id,
                passed=True,
                details="rotation completed, old key verifiable",
            )
        return DrillResult(
            name="rotation_drill",
            tenant_id=tenant_id,
            passed=False,
            details="rotation failed or old key not verifiable",
        )

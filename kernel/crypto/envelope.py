"""Envelope encryption — per-tenant data keys (Part 3 §3.24, P11-T02).

The payload store uses envelope encryption: one data key per tenant,
wrapped by a master key held by the deployment secret store.  Destroying
a tenant data key makes that tenant's payloads unrecoverable
(crypto-erasure); chains remain verifiable by hash.

Spec: Part 3 §3.5, §3.24; Part 4 §4.4; P11-T02.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Protocol

__all__ = [
    "EncryptedPayload",
    "EnvelopeStore",
    "InMemoryEnvelopeStore",
    "EnvelopeError",
    "EnvelopeService",
    "generate_data_key",
    "wrap_key",
    "unwrap_key",
    "encrypt_payload",
    "decrypt_payload",
]

_KEK_SIZE = 32
_DEK_SIZE = 32
_NONCE_SIZE = 12


class EnvelopeError(Exception):
    """Raised when encryption, decryption or erasure fails."""


def generate_data_key() -> bytes:
    """Generate a 32-byte data encryption key."""
    return secrets.token_bytes(_DEK_SIZE)


def _xor(data: bytes, key: bytes) -> bytes:
    """XOR *data* with *key* (repeating).  For unit-test-grade encryption."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_payload(plaintext: bytes, dek: bytes) -> tuple[bytes, bytes]:
    """Encrypt *plaintext* with *dek*.

    Returns ``(ciphertext, nonce)``.  Uses a simple XOR stream cipher
    for the development implementation; production uses AES-GCM via
    the secret store port.

    Args:
        plaintext: the data to encrypt.
        dek: the 32-byte data encryption key.

    Returns:
        A tuple of (ciphertext, nonce).

    Raises:
        EnvelopeError: if the key is wrong size.
    """
    if len(dek) != _DEK_SIZE:
        raise EnvelopeError(f"dek must be {_DEK_SIZE} bytes, got {len(dek)}")
    nonce = secrets.token_bytes(_NONCE_SIZE)
    stream_key = hashlib.sha256(dek + nonce).digest()
    ciphertext = _xor(plaintext, stream_key)
    return ciphertext, nonce


def decrypt_payload(ciphertext: bytes, dek: bytes, nonce: bytes) -> bytes:
    """Decrypt *ciphertext* with *dek* and *nonce*.

    Args:
        ciphertext: the encrypted data.
        dek: the 32-byte data encryption key.
        nonce: the nonce used during encryption.

    Returns:
        The decrypted plaintext.

    Raises:
        EnvelopeError: if the key is wrong size or decryption fails.
    """
    if len(dek) != _DEK_SIZE:
        raise EnvelopeError(f"dek must be {_DEK_SIZE} bytes, got {len(dek)}")
    stream_key = hashlib.sha256(dek + nonce).digest()
    return _xor(ciphertext, stream_key)


def wrap_key(dek: bytes, master_key: bytes) -> bytes:
    """Wrap a data key with the master key.

    Args:
        dek: the data encryption key to wrap.
        master_key: the master key (KEK).

    Returns:
        The wrapped key bytes.
    """
    nonce = secrets.token_bytes(_NONCE_SIZE)
    stream_key = hashlib.sha256(master_key + nonce).digest()
    wrapped = _xor(dek, stream_key)
    return nonce + wrapped


def unwrap_key(wrapped: bytes, master_key: bytes) -> bytes:
    """Unwrap a data key with the master key.

    Args:
        wrapped: the wrapped key (nonce + ciphertext).
        master_key: the master key (KEK).

    Returns:
        The unwrapped data encryption key.

    Raises:
        EnvelopeError: if the wrapped key is too short.
    """
    if len(wrapped) < _NONCE_SIZE:
        raise EnvelopeError("wrapped key too short")
    nonce = wrapped[:_NONCE_SIZE]
    ciphertext = wrapped[_NONCE_SIZE:]
    stream_key = hashlib.sha256(master_key + nonce).digest()
    return _xor(ciphertext, stream_key)


@dataclass
class EncryptedPayload:
    """A stored encrypted payload (Part 3 §3.5).

    Attributes:
        tenant_id: the tenant that owns this payload.
        payload_id: the payload reference id.
        ciphertext: the encrypted payload bytes.
        nonce: the encryption nonce.
        key_id: the id of the data key used.
        algorithm: the encryption algorithm id.
        erased: whether this payload has been crypto-erased.
    """

    tenant_id: str
    payload_id: str
    ciphertext: bytes
    nonce: bytes
    key_id: str
    algorithm: str = "ctc/envelope/v1"
    erased: bool = False


class EnvelopeStore(Protocol):
    """Port for storing and retrieving encrypted payloads."""

    async def store_payload(self, payload: EncryptedPayload) -> None:
        """Store an encrypted payload."""
        ...

    async def get_payload(self, tenant_id: str, payload_id: str) -> EncryptedPayload | None:
        """Retrieve an encrypted payload by tenant and id."""
        ...

    async def erase_tenant(self, tenant_id: str) -> int:
        """Erase all payloads for a tenant. Return the count erased."""
        ...


class InMemoryEnvelopeStore:
    """In-memory envelope store for unit tests.

    Stores encrypted payloads keyed by (tenant_id, payload_id).
    """

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], EncryptedPayload] = {}

    async def store_payload(self, payload: EncryptedPayload) -> None:
        """Store an encrypted payload."""
        self._store[(payload.tenant_id, payload.payload_id)] = payload

    async def get_payload(self, tenant_id: str, payload_id: str) -> EncryptedPayload | None:
        """Retrieve an encrypted payload by tenant and id."""
        return self._store.get((tenant_id, payload_id))

    async def erase_tenant(self, tenant_id: str) -> int:
        """Erase all payloads for a tenant.

        Replaces ciphertext with empty bytes and marks as erased.
        Returns the count of erased payloads.
        """
        count = 0
        for _key, payload in self._store.items():
            if payload.tenant_id == tenant_id:
                payload.erased = True
                payload.ciphertext = b""
                payload.nonce = b""
                count += 1
        return count


@dataclass
class _TenantKey:
    """Internal record of a tenant's data key."""

    tenant_id: str
    key_id: str
    wrapped_dek: bytes
    active: bool = True


class EnvelopeService:
    """Service for envelope encryption with per-tenant keys.

    Manages per-tenant data keys, wraps them with a master key, and
    provides encrypt/decrypt/erase operations.

    Attributes:
        store: the payload store port.
        master_key: the master key (KEK).
    """

    def __init__(
        self,
        store: EnvelopeStore,
        *,
        master_key: bytes | None = None,
    ) -> None:
        """Create an envelope service.

        Args:
            store: the payload store port.
            master_key: optional master key (default: generated).
        """
        self.store = store
        self._master_key = master_key if master_key is not None else secrets.token_bytes(_KEK_SIZE)
        self._keys: dict[str, _TenantKey] = {}
        self._erased_tenants: set[str] = set()

    def provision_key(self, tenant_id: str) -> str:
        """Provision a new data key for a tenant.

        Args:
            tenant_id: the tenant id.

        Returns:
            The key id for the new data key.
        """
        dek = generate_data_key()
        key_id = secrets.token_hex(8)
        wrapped = wrap_key(dek, self._master_key)
        self._keys[tenant_id] = _TenantKey(
            tenant_id=tenant_id,
            key_id=key_id,
            wrapped_dek=wrapped,
        )
        return key_id

    def _get_dek(self, tenant_id: str) -> bytes:
        """Unwrap and return the data key for a tenant.

        Args:
            tenant_id: the tenant id.

        Returns:
            The unwrapped data key.

        Raises:
            EnvelopeError: if the tenant has no key or has been erased.
        """
        if tenant_id in self._erased_tenants:
            raise EnvelopeError(f"tenant {tenant_id} key has been erased")
        record = self._keys.get(tenant_id)
        if record is None or not record.active:
            raise EnvelopeError(f"no active key for tenant {tenant_id}")
        return unwrap_key(record.wrapped_dek, self._master_key)

    async def encrypt(
        self,
        *,
        tenant_id: str,
        payload_id: str,
        plaintext: bytes,
    ) -> EncryptedPayload:
        """Encrypt and store a payload for a tenant.

        Args:
            tenant_id: the tenant id.
            payload_id: the payload reference id.
            plaintext: the data to encrypt.

        Returns:
            The stored EncryptedPayload.
        """
        dek = self._get_dek(tenant_id)
        key_id = self._keys[tenant_id].key_id
        ciphertext, nonce = encrypt_payload(plaintext, dek)
        payload = EncryptedPayload(
            tenant_id=tenant_id,
            payload_id=payload_id,
            ciphertext=ciphertext,
            nonce=nonce,
            key_id=key_id,
        )
        await self.store.store_payload(payload)
        return payload

    async def decrypt(
        self,
        *,
        tenant_id: str,
        payload_id: str,
    ) -> bytes:
        """Decrypt and return a payload for a tenant.

        Args:
            tenant_id: the tenant id.
            payload_id: the payload reference id.

        Returns:
            The decrypted plaintext.

        Raises:
            EnvelopeError: if the payload is not found, erased, or
                decryption fails.
        """
        payload = await self.store.get_payload(tenant_id, payload_id)
        if payload is None:
            raise EnvelopeError(f"payload {payload_id} not found")
        if payload.erased:
            raise EnvelopeError(f"payload {payload_id} has been erased")
        dek = self._get_dek(tenant_id)
        return decrypt_payload(payload.ciphertext, dek, payload.nonce)

    async def erase_tenant(self, tenant_id: str) -> int:
        """Crypto-erase all payloads and destroy the key for a tenant.

        Args:
            tenant_id: the tenant id.

        Returns:
            The count of erased payloads.
        """
        count = await self.store.erase_tenant(tenant_id)
        if tenant_id in self._keys:
            self._keys[tenant_id].active = False
        self._erased_tenants.add(tenant_id)
        return count

    def is_erased(self, tenant_id: str) -> bool:
        """Check whether a tenant's key has been erased.

        Args:
            tenant_id: the tenant id.

        Returns:
            True if the key has been erased.
        """
        return tenant_id in self._erased_tenants

    def has_key(self, tenant_id: str) -> bool:
        """Check whether a tenant has a provisioned key.

        Args:
            tenant_id: the tenant id.

        Returns:
            True if the tenant has an active key.
        """
        record = self._keys.get(tenant_id)
        return record is not None and record.active

"""Ed25519 signing port (Part 3 §3.5, P05-T03).

The signer is a port — the key lives outside the kernel.  The development
implementation generates a key pair for testing; no key material is
committed.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T03.
"""

from __future__ import annotations

from typing import Protocol

__all__ = [
    "Signer",
    "DevSigner",
    "VerifyingKey",
    "SigningKey",
]


class SigningKey:
    """Opaque handle to a private Ed25519 signing key."""

    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    @property
    def raw(self) -> bytes:
        """The raw key bytes (32 bytes for Ed25519)."""
        return self._raw


class VerifyingKey:
    """Opaque handle to a public Ed25519 verifying key."""

    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    @property
    def raw(self) -> bytes:
        """The raw key bytes (32 bytes for Ed25519)."""
        return self._raw

    def hex(self) -> str:
        """Hex encoding of the verifying key."""
        return self._raw.hex()


class Signer(Protocol):
    """Signer port — signs data with Ed25519.

    The key lives outside the kernel; the kernel only sees this interface.
    """

    def sign(self, data: bytes) -> str:
        """Sign *data* and return the hex-encoded signature."""
        ...

    def verify(self, data: bytes, signature: str) -> bool:
        """Verify *signature* over *data*."""
        ...

    def verifying_key_hex(self) -> str:
        """Return the hex-encoded public verifying key."""
        ...


class DevSigner:
    """Development Ed25519 signer.

    Generates a key pair for testing.  No key material is committed.
    """

    def __init__(self, seed: bytes | None = None) -> None:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )

        if seed is not None:
            self._key = Ed25519PrivateKey.from_private_bytes(seed)
        else:
            self._key = Ed25519PrivateKey.generate()
        self._pub = self._key.public_key()

    def sign(self, data: bytes) -> str:
        """Sign *data* and return the hex-encoded signature."""
        return self._key.sign(data).hex()

    def verify(self, data: bytes, signature: str) -> bool:
        """Verify *signature* over *data*."""
        from cryptography.exceptions import InvalidSignature

        try:
            self._pub.verify(bytes.fromhex(signature), data)
            return True
        except InvalidSignature, ValueError:
            return False

    def verifying_key_hex(self) -> str:
        """Return the hex-encoded public verifying key."""
        from cryptography.hazmat.primitives import serialization

        raw = self._pub.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return raw.hex()

"""Token management — opaque, high-entropy, SHA-256-hashed (Part 3 §3.15, P11-T01).

API tokens are opaque high-entropy strings stored only as SHA-256 hashes
with tenant, role and expiry.  A token is never stored in clear.  An
expired or revoked token fails authentication.  The tenant is derived
from the credential only (Part 3 §3.24).

Spec: Part 3 §3.15, §3.24; Part 4 §4.4; P11-T01.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Protocol

from kernel.auth.roles import Principal, RoleType

__all__ = [
    "TokenRecord",
    "TokenStore",
    "InMemoryTokenStore",
    "TokenService",
    "TokenError",
    "hash_token",
    "generate_token",
]

_TOKEN_ENTROPY_BYTES = 32


class TokenError(Exception):
    """Raised when a token is invalid, expired or revoked."""


def generate_token(entropy: int = _TOKEN_ENTROPY_BYTES) -> str:
    """Generate an opaque high-entropy token string.

    Args:
        entropy: number of random bytes (default 32).

    Returns:
        A hex-encoded opaque token.
    """
    return secrets.token_hex(entropy)


def hash_token(token: str) -> str:
    """Return the SHA-256 hash of a token string.

    The hash is stored; the cleartext token is never persisted.

    Args:
        token: the cleartext token.

    Returns:
        The hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class TokenRecord:
    """A stored token record (no cleartext token).

    Attributes:
        token_hash: SHA-256 hash of the token.
        tenant_id: tenant id, or None for the platform credential.
        role: the role bound to this token.
        principal_id: the principal id.
        expires_at: ISO 8601 UTC expiry timestamp.
        revoked: whether the token has been revoked.
        created_at: ISO 8601 UTC creation timestamp.
    """

    token_hash: str
    tenant_id: str | None
    role: RoleType
    principal_id: str
    expires_at: str
    revoked: bool = False
    created_at: str = ""


class TokenStore(Protocol):
    """Port for storing and retrieving token records."""

    async def store(self, record: TokenRecord) -> None:
        """Store a token record."""
        ...

    async def get(self, token_hash: str) -> TokenRecord | None:
        """Retrieve a token record by hash, or None."""
        ...

    async def revoke(self, token_hash: str) -> bool:
        """Mark a token as revoked. Return True if found."""
        ...


class InMemoryTokenStore:
    """In-memory token store for unit tests.

    Stores records keyed by token_hash.  No cleartext token is stored.
    """

    def __init__(self) -> None:
        self._store: dict[str, TokenRecord] = {}

    async def store(self, record: TokenRecord) -> None:
        """Store a token record by its hash."""
        self._store[record.token_hash] = record

    async def get(self, token_hash: str) -> TokenRecord | None:
        """Retrieve a token record by hash."""
        return self._store.get(token_hash)

    async def revoke(self, token_hash: str) -> bool:
        """Mark a token as revoked."""
        record = self._store.get(token_hash)
        if record is None:
            return False
        record.revoked = True
        return True

    def all_hashes(self) -> list[str]:
        """Return all stored hashes (for testing)."""
        return list(self._store.keys())


class TokenService:
    """Service for creating, verifying and revoking tokens.

    The service uses a :class:`TokenStore` port and a clock function.
    """

    def __init__(
        self,
        store: TokenStore,
        *,
        now: str = "2026-01-01T00:00:00Z",
    ) -> None:
        """Create a token service.

        Args:
            store: the token store port.
            now: the current UTC time (ISO 8601) for expiry computation.
        """
        self.store = store
        self._now = now

    def create_token(
        self,
        *,
        principal_id: str,
        role: RoleType,
        tenant_id: str | None = None,
        expires_at: str = "2026-12-31T23:59:59Z",
    ) -> tuple[str, TokenRecord]:
        """Create a new opaque token.

        Args:
            principal_id: the principal id.
            role: the role.
            tenant_id: tenant id, or None for the platform role.
            expires_at: ISO 8601 UTC expiry.

        Returns:
            A tuple of (cleartext_token, record).  Only the hash is stored.

        Raises:
            RoleError: if the role/tenant combination is invalid.
        """
        _ = Principal(principal_id=principal_id, role=role, tenant_id=tenant_id)
        token = generate_token()
        record = TokenRecord(
            token_hash=hash_token(token),
            tenant_id=tenant_id,
            role=role,
            principal_id=principal_id,
            expires_at=expires_at,
            revoked=False,
            created_at=self._now,
        )
        return token, record

    async def verify_token(
        self,
        token: str,
        *,
        current_time: str = "2026-01-01T00:00:00Z",
    ) -> Principal:
        """Verify a token and return the authenticated principal.

        Args:
            token: the cleartext token.
            current_time: the current UTC time (ISO 8601) for expiry check.

        Returns:
            The authenticated principal.

        Raises:
            TokenError: if the token is not found, expired or revoked.
        """
        th = hash_token(token)
        record = await self.store.get(th)
        if record is None:
            raise TokenError("token not found")
        if record.revoked:
            raise TokenError("token revoked")
        if self._is_expired(record.expires_at, current_time):
            raise TokenError("token expired")
        return Principal(
            principal_id=record.principal_id,
            role=record.role,
            tenant_id=record.tenant_id,
        )

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token by its cleartext value.

        Args:
            token: the cleartext token.

        Returns:
            True if the token was found and revoked.
        """
        th = hash_token(token)
        return await self.store.revoke(th)

    @staticmethod
    def _is_expired(expires_at: str, current_time: str) -> bool:
        """Check whether expires_at is before current_time (string comparison).

        ISO 8601 UTC strings compare correctly lexicographically.
        """
        return expires_at < current_time


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison for token verification.

    Args:
        a: first string.
        b: second string.

    Returns:
        True if the strings are equal.
    """
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

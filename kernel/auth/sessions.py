"""Session cookies — signed, HTTP-only, same-site (Part 3 §3.15, P11-T01).

Web sessions use signed, HTTP-only, same-site cookies.  The session is
bound to a tenant and role derived from the credential only.  Reviewer
approvals are separate from operator actions.

Spec: Part 3 §3.15, §3.24; P11-T01.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Protocol

from kernel.auth.roles import Principal, RoleType

__all__ = [
    "SessionPayload",
    "SessionSigner",
    "DevSessionSigner",
    "SessionError",
    "create_session_cookie",
    "verify_session_cookie",
    "COOKIE_NAME",
    "COOKIE_ATTRIBUTES",
]

COOKIE_NAME = "ctc_session"

COOKIE_ATTRIBUTES: dict[str, str] = {
    "HttpOnly": "",
    "SameSite": "Strict",
    "Secure": "",
}

_DEFAULT_SIGNING_KEY = secrets.token_bytes(32)


class SessionError(Exception):
    """Raised when a session cookie is invalid or tampered."""


class SessionPayload:
    """The signed payload of a session cookie.

    Attributes:
        principal_id: the principal id.
        role: the role.
        tenant_id: tenant id, or None for the platform credential.
        issued_at: ISO 8601 UTC timestamp.
        expires_at: ISO 8601 UTC timestamp.
    """

    __slots__ = ("principal_id", "role", "tenant_id", "issued_at", "expires_at")

    def __init__(
        self,
        *,
        principal_id: str,
        role: RoleType,
        tenant_id: str | None,
        issued_at: str,
        expires_at: str,
    ) -> None:
        """Create a session payload.

        Args:
            principal_id: the principal id.
            role: the role.
            tenant_id: tenant id, or None for the platform credential.
            issued_at: ISO 8601 UTC timestamp.
            expires_at: ISO 8601 UTC timestamp.
        """
        self.principal_id = principal_id
        self.role: RoleType = role
        self.tenant_id = tenant_id
        self.issued_at = issued_at
        self.expires_at = expires_at

    def to_dict(self) -> dict[str, str | None]:
        """Serialize to a dict for JSON encoding."""
        return {
            "principal_id": self.principal_id,
            "role": self.role,
            "tenant_id": self.tenant_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> SessionPayload:
        """Deserialize from a dict.

        Args:
            data: the parsed JSON dict.

        Returns:
            A SessionPayload instance.

        Raises:
            SessionError: if required fields are missing.
        """
        required = ("principal_id", "role", "issued_at", "expires_at")
        for key in required:
            if key not in data:
                raise SessionError(f"missing field: {key}")
        role_val: str = str(data["role"])
        if role_val not in ("viewer", "operator", "reviewer", "administrator", "platform"):
            raise SessionError(f"invalid role: {role_val}")
        return cls(
            principal_id=str(data["principal_id"]),
            role=role_val,  # type: ignore[arg-type]
            tenant_id=str(data["tenant_id"]) if data.get("tenant_id") else None,
            issued_at=str(data["issued_at"]),
            expires_at=str(data["expires_at"]),
        )


class SessionSigner(Protocol):
    """Port for signing and verifying session cookies."""

    def sign(self, payload: str) -> str:
        """Return the HMAC-SHA256 signature of *payload*."""
        ...

    def verify(self, payload: str, signature: str) -> bool:
        """Verify that *signature* matches *payload*."""
        ...


class DevSessionSigner:
    """Development session signer using a generated key.

    The key is generated per instance; no key material is committed.
    """

    def __init__(self, key: bytes | None = None) -> None:
        """Create a dev signer.

        Args:
            key: optional signing key (default: generated).
        """
        self._key = key if key is not None else _DEFAULT_SIGNING_KEY

    def sign(self, payload: str) -> str:
        """Sign the payload with HMAC-SHA256.

        Args:
            payload: the JSON-encoded payload string.

        Returns:
            Hex-encoded HMAC signature.
        """
        return hmac.new(self._key, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify(self, payload: str, signature: str) -> bool:
        """Verify the signature in constant time.

        Args:
            payload: the JSON-encoded payload string.
            signature: the hex-encoded signature to verify.

        Returns:
            True if the signature matches.
        """
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)


def create_session_cookie(
    *,
    principal: Principal,
    issued_at: str = "2026-01-01T00:00:00Z",
    expires_at: str = "2026-12-31T23:59:59Z",
    signer: SessionSigner | None = None,
) -> str:
    """Create a signed session cookie value.

    The cookie value is ``base64(json(payload)).signature``.

    Args:
        principal: the authenticated principal.
        issued_at: ISO 8601 UTC timestamp.
        expires_at: ISO 8601 UTC timestamp.
        signer: the session signer (default: DevSessionSigner).

    Returns:
        The signed cookie value string.
    """
    sig: SessionSigner = signer if signer is not None else DevSessionSigner()
    payload = SessionPayload(
        principal_id=principal.principal_id,
        role=principal.role,
        tenant_id=principal.tenant_id,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    payload_json = json.dumps(payload.to_dict(), sort_keys=True, separators=(",", ":"))
    signature = sig.sign(payload_json)
    return f"{payload_json}.{signature}"


def verify_session_cookie(
    cookie_value: str,
    *,
    signer: SessionSigner | None = None,
    current_time: str = "2026-01-01T00:00:00Z",
) -> Principal:
    """Verify a signed session cookie and return the principal.

    Args:
        cookie_value: the cookie value string.
        signer: the session signer (default: DevSessionSigner).
        current_time: the current UTC time for expiry check.

    Returns:
        The authenticated principal.

    Raises:
        SessionError: if the signature is invalid, the payload is
            malformed, or the session has expired.
    """
    sig: SessionSigner = signer if signer is not None else DevSessionSigner()
    if "." not in cookie_value:
        raise SessionError("invalid cookie format")
    payload_json, signature = cookie_value.rsplit(".", 1)
    if not sig.verify(payload_json, signature):
        raise SessionError("invalid signature")
    try:
        data: dict[str, object] = json.loads(payload_json)
    except json.JSONDecodeError:
        raise SessionError("invalid payload JSON") from None
    payload = SessionPayload.from_dict(data)
    if payload.expires_at < current_time:
        raise SessionError("session expired")
    return Principal(
        principal_id=payload.principal_id,
        role=payload.role,
        tenant_id=payload.tenant_id,
    )

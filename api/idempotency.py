"""Idempotency middleware for mutating commands (P10-T03).

Idempotency keys on every mutating call.  The first call with a given key
stores the response; a repeated call with the same key returns the original
response without re-executing the operation.  The P04 store interface is
used; an in-memory implementation is provided for the synthetic-data stage.

Spec: Part 3 §3.4; P10-T03.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, cast

__all__ = [
    "IdempotencyRecord",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "IdempotencyMiddleware",
    "ConflictError",
]


class ConflictError(Exception):
    """Raised when a stale version or idempotency conflict occurs."""

    def __init__(self, code: str = "IDEMPOTENCY_CONFLICT", detail: str = "") -> None:
        """Initialize with a stable error code and detail."""
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass
class IdempotencyRecord:
    """A stored idempotency record."""

    key: str
    tenant_id: str
    response_body: str
    status_code: int
    created_at: str
    request_hash: str


class IdempotencyStore:
    """Protocol for the P04 idempotency store."""

    def get(self, key: str, tenant_id: str) -> IdempotencyRecord | None:
        """Return the stored record for *key* or None."""
        raise NotImplementedError

    def store(self, record: IdempotencyRecord) -> None:
        """Store a new idempotency record."""
        raise NotImplementedError

    def exists(self, key: str, tenant_id: str) -> bool:
        """Return True when *key* already exists for *tenant_id*."""
        return self.get(key, tenant_id) is not None


class InMemoryIdempotencyStore(IdempotencyStore):
    """In-memory idempotency store for the synthetic-data stage."""

    def __init__(self) -> None:
        """Initialize an empty store."""
        self._records: dict[tuple[str, str], IdempotencyRecord] = {}

    def get(self, key: str, tenant_id: str) -> IdempotencyRecord | None:
        """Return the stored record for *key* or None."""
        return self._records.get((key, tenant_id))

    def store(self, record: IdempotencyRecord) -> None:
        """Store a new idempotency record.  Raises on duplicate."""
        if (record.key, record.tenant_id) in self._records:
            existing = self._records[(record.key, record.tenant_id)]
            if existing.request_hash != record.request_hash:
                raise ConflictError(
                    "IDEMPOTENCY_CONFLICT",
                    "idempotency key already used with a different request",
                )
        self._records[(record.key, record.tenant_id)] = record


def _hash_request(body: Any) -> str:
    """Return a SHA-256 hash of a request body."""
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


@dataclass
class IdempotencyMiddleware:
    """Middleware that enforces idempotency on mutating calls.

    Args:
        store: The idempotency store (P04 interface).
        tenant_id: The current tenant identifier.
    """

    store: IdempotencyStore
    tenant_id: str = "SYN-TEN-0001"

    def execute(
        self,
        key: str,
        request_body: dict[str, Any],
        handler: Any,
    ) -> dict[str, Any]:
        """Execute *handler* with idempotency.

        If *key* already exists, return the stored response.
        Otherwise, execute *handler*, store the result, and return it.

        Raises:
            ConflictError: When a stale version or idempotency conflict occurs.
        """
        if not key:
            raise ConflictError(
                "IDEMPOTENCY_CONFLICT", "idempotency key required for mutating call"
            )
        existing = self.store.get(key, self.tenant_id)
        if existing is not None:
            if existing.request_hash != _hash_request(request_body):
                raise ConflictError(
                    "IDEMPOTENCY_CONFLICT", "idempotency key used with different request"
                )
            return cast("dict[str, Any]", json.loads(existing.response_body))
        result = handler(request_body)
        record = IdempotencyRecord(
            key=key,
            tenant_id=self.tenant_id,
            response_body=json.dumps(result, sort_keys=True, default=str),
            status_code=200,
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            request_hash=_hash_request(request_body),
        )
        self.store.store(record)
        return cast("dict[str, Any]", result)

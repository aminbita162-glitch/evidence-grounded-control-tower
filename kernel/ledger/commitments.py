"""Cryptographic commitments (Part 3 §3.5, P05-T04).

Three kinds of commitment, all using the domain tag ``ctc/commit/v1``:

- **Evaluation commitment**:
  ``H("ctc/commit/v1" || facts_set_hash || pack_set_hash || evaluation_time || config_hash)``.
  Recorded before Rules run; replay must reproduce this value.

- **Proposal commitment**: a Proposal is committed by its hash before any
  human sees it; an Approval is valid only for that hash.

- **Field commitment**: ``H("ctc/commit/v1" || salt_id || per_field_salt || canonical_value)``.
  Salts are referenced from the encrypted payload store; destroying a salt
  makes the commitment unlinkable.

Spec: Part 3 §3.5, §3.7; Part 4 §4.4; P05-T04.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Mapping

from kernel.canonical import canonical_bytes

__all__ = [
    "evaluation_commitment",
    "proposal_commitment",
    "field_commitment",
    "verify_field_commitment",
    "generate_field_salt",
]

_COMMIT_TAG = "ctc/commit/v1"


def evaluation_commitment(
    facts_set_hash: str,
    pack_set_hash: str,
    evaluation_time: str,
    config_hash: str,
) -> str:
    """Compute the evaluation commitment (Part 3 §3.5).

    ``H("ctc/commit/v1" || facts_set_hash || pack_set_hash || evaluation_time || config_hash)``
    """
    data = (
        _COMMIT_TAG.encode("utf-8")
        + facts_set_hash.encode("utf-8")
        + pack_set_hash.encode("utf-8")
        + evaluation_time.encode("utf-8")
        + config_hash.encode("utf-8")
    )
    return hashlib.sha256(data).hexdigest()


def proposal_commitment(proposal: Mapping[str, object]) -> str:
    """Commit a proposal by its hash before any human sees it.

    ``H("ctc/commit/v1" || canonical(proposal))``
    """
    data = _COMMIT_TAG.encode("utf-8") + canonical_bytes(proposal)
    return hashlib.sha256(data).hexdigest()


def field_commitment(
    salt_id: str,
    field_salt: bytes,
    value: object,
) -> str:
    """Compute a salted field commitment (Part 3 §3.5).

    ``H("ctc/commit/v1" || salt_id || field_salt || canonical(value))``

    Args:
        salt_id: Identifier for the salt in the encrypted payload store.
        field_salt: Per-field random salt bytes.
        value: The value to commit.

    Returns:
        Lowercase hex SHA-256 digest.
    """
    data = (
        _COMMIT_TAG.encode("utf-8") + salt_id.encode("utf-8") + field_salt + canonical_bytes(value)
    )
    return hashlib.sha256(data).hexdigest()


def verify_field_commitment(
    salt_id: str,
    field_salt: bytes,
    value: object,
    expected_hash: str,
) -> bool:
    """Verify a field commitment by recomputing it.

    Returns ``True`` if the recomputed commitment matches *expected_hash*.
    """
    return field_commitment(salt_id, field_salt, value) == expected_hash


def generate_field_salt() -> tuple[str, bytes]:
    """Generate a per-field salt and its identifier.

    Returns:
        ``(salt_id, salt_bytes)`` — 32 random bytes with a hex id.
    """
    salt = secrets.token_bytes(32)
    salt_id = hashlib.sha256(salt).hexdigest()
    return salt_id, salt

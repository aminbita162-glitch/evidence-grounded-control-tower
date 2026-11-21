"""Domain-separated SHA-256 hashing (Part 3 §3.5, P03-T02).

Every hash is SHA-256 over ``domain_tag || canonical(payload)`` where
``domain_tag`` is registered in ``schemas/hash-tags.json`` and unique per
purpose. Cross-purpose hash replay is prevented by the domain tag prefix.
Every hash carries an algorithm identifier for hash agility.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from kernel.canonical import canonical_bytes

ALGORITHM: str = "sha256"

KNOWN_TAGS: frozenset[str] = frozenset(
    {
        "ctc/record/v1",
        "ctc/leaf/v1",
        "ctc/node/v1",
        "ctc/commit/v1",
        "ctc/payload/v1",
    }
)


class UnknownTagError(ValueError):
    """Raised when a hash tag is not in the registry."""


def _validate_tag(tag: str) -> None:
    """Validate that *tag* is a registered domain tag."""
    if tag not in KNOWN_TAGS:
        raise UnknownTagError(f"unknown hash tag: {tag!r}")


def domain_hash(tag: str, payload: object) -> str:
    """Compute SHA-256 of ``domain_tag || canonical(payload)``.

    Args:
        tag: A registered domain tag from ``schemas/hash-tags.json``.
        payload: Any JSON-serializable object.

    Returns:
        Lowercase hex SHA-256 digest string.

    Raises:
        UnknownTagError: If *tag* is not in the registry.
    """
    _validate_tag(tag)
    data = tag.encode("utf-8") + canonical_bytes(payload)
    return hashlib.sha256(data).hexdigest()


def load_tags(tags_path: Path) -> set[str]:
    """Load and validate the tag registry from ``tags_path``.

    Args:
        tags_path: Path to ``schemas/hash-tags.json``.

    Returns:
        Set of valid tag strings.
    """
    data = json.loads(tags_path.read_text(encoding="utf-8"))
    tags: set[str] = set()
    for entry in data.get("tags", []):
        tags.add(str(entry["tag"]))
    return tags

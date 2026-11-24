"""Pack loader (Part 3 §3.6, P06-T02).

Loads a validated pack and computes a stable hash over its canonical
JSON serialization.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from kernel.rules.validator import validate_pack

__all__ = ["LoadedPack", "load_pack"]


@dataclass(frozen=True)
class LoadedPack:
    """A validated and loaded pack with a stable hash."""

    data: dict[str, object]
    hash: str


def load_pack(
    data: Mapping[str, object],
    source_labels: Mapping[str, str] | None = None,
) -> LoadedPack:
    """Validate and load a pack, returning it with a stable hash.

    Args:
        data: The pack data (manifest + rules).
        source_labels: Mapping from source_id to label for label ceiling
            check.  If None, the label ceiling check is skipped.

    Returns:
        A :class:`LoadedPack` with the pack data and its SHA-256 hash.

    Raises:
        ValidationError: If the pack is invalid.
    """
    validate_pack(data, source_labels)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    pack_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return LoadedPack(data=dict(data), hash=pack_hash)

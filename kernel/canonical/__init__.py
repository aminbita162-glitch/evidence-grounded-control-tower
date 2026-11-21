"""Canonical JSON serialization per RFC 8785 (Part 3 §3.5, P03-T02).

Provides ``canonical_dumps`` for deterministic JSON serialization used
by every hashed or signed byte sequence.
"""

from __future__ import annotations

from typing import Any

import rfc8785

_JSONValue = Any


def canonical_dumps(obj: _JSONValue) -> str:
    """Serialize *obj* as canonical JSON per RFC 8785.

    Args:
        obj: Any JSON-serializable object.

    Returns:
        Canonical JSON string (sorted keys, minimal whitespace).
    """
    return rfc8785.dumps(obj).decode("utf-8")


def canonical_bytes(obj: _JSONValue) -> bytes:
    """Serialize *obj* as canonical JSON bytes per RFC 8785.

    Args:
        obj: Any JSON-serializable object.

    Returns:
        Canonical JSON bytes.
    """
    return rfc8785.dumps(obj)

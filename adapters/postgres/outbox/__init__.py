"""PostgreSQL outbox adapter (P04-T05).

Provides the outbox and idempotency table schema via migration 0005.

Spec: Part 3 §3.27; P04-T05.
"""

from __future__ import annotations

__all__ = ["OUTBOX_TABLE", "IDEMPOTENCY_TABLE", "DEAD_LETTER_TABLE"]

OUTBOX_TABLE = "_outbox"
IDEMPOTENCY_TABLE = "_idempotency"
DEAD_LETTER_TABLE = "_dead_letter"

"""Check tenant feed envelopes, provenance, effective periods and batches."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import ConfigDict, TypeAdapter

from kernel.hashing import domain_hash
from kernel.types.label import Label, label_rank

__all__ = [
    "FeedAcceptance",
    "FeedEnvelope",
    "FeedPolicy",
    "FeedRejection",
    "FeedStatus",
    "content_hash",
    "validate_feed",
]

type Row = Mapping[str, object]


class FeedStatus(StrEnum):
    """Stable feed validation outcomes."""

    ACCEPTED = "ACCEPTED"
    REPLAY = "REPLAY"
    NOT_VISIBLE = "NOT_VISIBLE"
    BAD_ENVELOPE = "BAD_ENVELOPE"
    WRONG_SOURCE = "WRONG_SOURCE"
    BAD_LABEL = "BAD_LABEL"
    STALE = "STALE"
    BAD_ROW = "BAD_ROW"
    HASH_MISMATCH = "HASH_MISMATCH"
    BATCH_CONFLICT = "BATCH_CONFLICT"


@dataclass(frozen=True, slots=True)
class FeedEnvelope:
    """Immutable metadata for one tenant-provided table batch."""

    __pydantic_config__ = ConfigDict(extra="forbid", strict=True)

    tenant_id: str
    source_id: str
    label: Label
    feed_type: str
    schema_version: int
    batch_id: str
    as_of: datetime
    effective_from: datetime
    effective_until: datetime
    record_count: int
    content_hash: str
    origin: Literal["TENANT_SUPPLIED"]

    @classmethod
    def from_json(cls, data: str | bytes) -> FeedEnvelope:
        """Parse a serialized envelope without coercing its fields."""
        return TypeAdapter(cls).validate_json(data)


@dataclass(frozen=True, slots=True)
class FeedPolicy:
    """Trusted, tenant-specific metadata and a row schema validator."""

    tenant_id: str
    source_id: str
    label: Label
    feed_type: str
    schema_version: int
    max_age: timedelta
    validate_row: Callable[[Row], bool]

    def __post_init__(self) -> None:
        """Prevent official provenance from being conferred by a feed policy."""
        if label_rank(self.label) >= label_rank("OFFICIAL") or self.label == "SIMULATED_RULE":
            raise ValueError("invalid tenant feed policy label")
        if self.max_age < timedelta(0) or self.schema_version < 1:
            raise ValueError("invalid tenant feed policy age or version")


@dataclass(frozen=True, slots=True)
class FeedAcceptance:
    """Receipt to persist before an accepted batch becomes visible."""

    status: Literal[FeedStatus.ACCEPTED, FeedStatus.REPLAY]
    envelope: FeedEnvelope


@dataclass(frozen=True, slots=True)
class FeedRejection:
    """Failure without any data from the referenced batch."""

    status: FeedStatus


def content_hash(rows: Sequence[Row]) -> str:
    """Hash the exact ordered tenant payload in the record-payload domain."""
    return domain_hash(
        "ctc/payload/v1", {"type": "TENANT_FEED", "rows": [dict(row) for row in rows]}
    )


def _is_utc(instant: datetime) -> bool:
    return instant.utcoffset() == timedelta(0)


def _valid_envelope(envelope: FeedEnvelope, at: datetime, rows: Sequence[Row]) -> bool:
    instants = (envelope.as_of, envelope.effective_from, envelope.effective_until, at)
    return (
        all(_is_utc(instant) for instant in instants)
        and bool(envelope.batch_id and envelope.source_id and envelope.feed_type)
        and envelope.origin == "TENANT_SUPPLIED"
        and type(envelope.record_count) is int
        and envelope.record_count == len(rows)
        and envelope.effective_from < envelope.effective_until
        and re.fullmatch(r"[0-9a-f]{64}", envelope.content_hash) is not None
    )


def validate_feed(
    envelope: FeedEnvelope,
    rows: Sequence[Row],
    *,
    tenant_id: str,
    at: datetime,
    policy: FeedPolicy,
    saved: FeedAcceptance | None = None,
) -> FeedAcceptance | FeedRejection:
    """Accept only the authenticated tenant's current batch for a known source.

    The storage adapter used by consumers supplies the prior receipt for the
    exact batch key and atomically records any new acceptance.
    """
    if envelope.tenant_id != tenant_id or policy.tenant_id != tenant_id:
        return FeedRejection(FeedStatus.NOT_VISIBLE)
    if not _valid_envelope(envelope, at, rows):
        return FeedRejection(FeedStatus.BAD_ENVELOPE)
    if (
        envelope.source_id != policy.source_id
        or envelope.feed_type != policy.feed_type
        or envelope.schema_version != policy.schema_version
    ):
        return FeedRejection(FeedStatus.WRONG_SOURCE)
    if envelope.label != policy.label:
        return FeedRejection(FeedStatus.BAD_LABEL)
    if not all(policy.validate_row(row) for row in rows):
        return FeedRejection(FeedStatus.BAD_ROW)
    try:
        digest = content_hash(rows)
    except ValueError, TypeError:
        return FeedRejection(FeedStatus.BAD_ROW)
    if digest != envelope.content_hash:
        return FeedRejection(FeedStatus.HASH_MISMATCH)
    if (
        not envelope.effective_from <= at < envelope.effective_until
        or not timedelta(0) <= at - envelope.as_of <= policy.max_age
    ):
        return FeedRejection(FeedStatus.STALE)
    if saved is not None and (
        saved.envelope.tenant_id,
        saved.envelope.feed_type,
        saved.envelope.batch_id,
    ) == (tenant_id, envelope.feed_type, envelope.batch_id):
        if saved.envelope != envelope:
            return FeedRejection(FeedStatus.BATCH_CONFLICT)
        return FeedAcceptance(FeedStatus.REPLAY, envelope)
    return FeedAcceptance(FeedStatus.ACCEPTED, envelope)

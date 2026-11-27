"""Tenant isolation, feed provenance and frozen-envelope checks."""

import json
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from kernel.lib.feeds import (
    FeedAcceptance,
    FeedEnvelope,
    FeedPolicy,
    FeedRejection,
    FeedStatus,
    content_hash,
    validate_feed,
)

_NOW = datetime.fromtimestamp(100_000, tz=UTC)
_ROWS = ({"amount": "2.00"},)


def _row_is_valid(row: Mapping[str, object]) -> bool:
    return set(row) == {"amount"} and isinstance(row["amount"], str)


_POLICY = FeedPolicy(
    "SYN-TEN", "SYN-SRC", "SYNTHETIC", "SYNTHETIC_COST", 1, timedelta(days=1), _row_is_valid
)


def _envelope(rows: Sequence[Mapping[str, object]] = _ROWS) -> FeedEnvelope:
    return FeedEnvelope(
        tenant_id=_POLICY.tenant_id,
        source_id=_POLICY.source_id,
        label=_POLICY.label,
        feed_type=_POLICY.feed_type,
        schema_version=_POLICY.schema_version,
        batch_id="SYN-BATCH",
        as_of=_NOW - timedelta(hours=1),
        effective_from=_NOW - timedelta(days=1),
        effective_until=_NOW + timedelta(days=1),
        record_count=len(rows),
        content_hash=content_hash(rows),
        origin="TENANT_SUPPLIED",
    )


def _validate(
    envelope: FeedEnvelope,
    rows: Sequence[Mapping[str, object]] = _ROWS,
    *,
    policy: FeedPolicy = _POLICY,
    saved: FeedAcceptance | None = None,
) -> FeedAcceptance | FeedRejection:
    return validate_feed(envelope, rows, tenant_id="SYN-TEN", at=_NOW, policy=policy, saved=saved)


@pytest.mark.fast
def test_T_LIB_0053() -> None:
    """Check accept a current feed with registered provenance.

    id: T-LIB-0053
    title: Accept a current feed with registered provenance
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Accept a current feed with registered provenance
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    assert _validate(_envelope()) == FeedAcceptance(FeedStatus.ACCEPTED, _envelope())


@pytest.mark.fast
def test_T_LIB_0054() -> None:
    """Check allow only the case tenant to see its feed.

    id: T-LIB-0054
    title: Allow only the case tenant to see its feed
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Allow only the case tenant to see its feed
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    foreign = replace(_envelope(), tenant_id="SYN-OTHER", record_count=-1)
    assert _validate(foreign) == FeedRejection(FeedStatus.NOT_VISIBLE)


@pytest.mark.fast
def test_T_LIB_0055() -> None:
    """Check reject a batch labelled official by assertion.

    id: T-LIB-0055
    title: Reject a batch labelled official by assertion
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Reject a batch labelled official by assertion
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    assert _validate(replace(_envelope(), label="OFFICIAL")) == FeedRejection(FeedStatus.BAD_LABEL)


@pytest.mark.fast
def test_T_LIB_0056() -> None:
    """Check reject a stale or future feed.

    id: T-LIB-0056
    title: Reject a stale or future feed
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Reject a stale or future feed
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    policy = replace(_POLICY, max_age=timedelta(seconds=1))
    assert _validate(_envelope(), policy=policy) == FeedRejection(FeedStatus.STALE)
    assert _validate(replace(_envelope(), as_of=_NOW + timedelta(seconds=1))) == FeedRejection(
        FeedStatus.STALE
    )


@pytest.mark.fast
def test_T_LIB_0057() -> None:
    """Check reject at the exclusive effective period endpoint.

    id: T-LIB-0057
    title: Reject at the exclusive effective period endpoint
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Reject at the exclusive effective period endpoint
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    assert _validate(replace(_envelope(), effective_until=_NOW)) == FeedRejection(FeedStatus.STALE)


@pytest.mark.fast
def test_T_LIB_0058() -> None:
    """Check reject the whole batch if one record fails schema validation.

    id: T-LIB-0058
    title: Reject the whole batch if one record fails schema validation
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Reject the whole batch if one record fails schema validation
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    rows = ({"amount": "2.00"}, {"amount": 5})
    assert _validate(_envelope(rows), rows) == FeedRejection(FeedStatus.BAD_ROW)


@pytest.mark.fast
def test_T_LIB_0059() -> None:
    """Check reject content that fails its recorded hash.

    id: T-LIB-0059
    title: Reject content that fails its recorded hash
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Reject content that fails its recorded hash
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    bad_hash = replace(_envelope(), content_hash="0" * 64)
    assert _validate(bad_hash) == FeedRejection(FeedStatus.HASH_MISMATCH)


@pytest.mark.fast
def test_T_LIB_0060() -> None:
    """Check replay identical batch keys and reject replacements.

    id: T-LIB-0060
    title: Replay identical batch keys and reject replacements
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Replay identical batch keys and reject replacements
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    original = _envelope()
    saved = FeedAcceptance(FeedStatus.ACCEPTED, original)
    assert _validate(original, saved=saved) == FeedAcceptance(FeedStatus.REPLAY, original)
    replacement = ({"amount": "7.00"},)
    assert _validate(_envelope(replacement), replacement, saved=saved) == FeedRejection(
        FeedStatus.BATCH_CONFLICT
    )


@pytest.mark.fast
def test_T_LIB_0061() -> None:
    """Check reject malformed envelopes and mismatched sources.

    id: T-LIB-0061
    title: Reject malformed envelopes and mismatched sources
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Reject malformed envelopes and mismatched sources
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    assert _validate(replace(_envelope(), record_count=2)) == FeedRejection(FeedStatus.BAD_ENVELOPE)
    assert _validate(replace(_envelope(), source_id="SYN-FORGED")) == FeedRejection(
        FeedStatus.WRONG_SOURCE
    )


@pytest.mark.fast
def test_T_LIB_0062() -> None:
    """Check validate the serialized envelope against the frozen contract.

    id: T-LIB-0062
    title: Validate the serialized envelope against the frozen contract
    purpose: Verify the tenant feed contract and its failure handling
    level: fast
    requirement: P13-T05
    input: Synthetic feed envelope and table batch
    expected: Validate the serialized envelope against the frozen contract
    risk: A forged or stale feed contributes to a case
    capability: shared-library
    """
    schema_path = Path(__file__).resolve().parents[2] / "schemas/lib/feed_envelope.json"
    contract = json.loads(schema_path.read_text())
    payload = TypeAdapter(FeedEnvelope).dump_json(_envelope())
    serialized = json.loads(payload)
    assert sorted(serialized) == sorted(contract["required"])
    assert serialized["label"] in contract["properties"]["label"]["enum"]
    assert serialized["origin"] == contract["properties"]["origin"]["const"]
    assert FeedEnvelope.from_json(payload) == _envelope()

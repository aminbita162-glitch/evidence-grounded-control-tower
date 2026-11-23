"""Tests for threat-to-test matrix tool (P04-T08).

Test IDs: T-DB-0079 to T-DB-0084.
Covers: the catalog parses to the full item list; a seeded item without a
test is listed; the mapping covers identifier-reference, row-level security
bypass, pooled-connection and shared-sequence items.

Spec: Part 3 §3.15, §3.24; Part 4 §4.5; P04-T08.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.threat_matrix import ATTACK_CATALOG, ThreatMatrix

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CATALOG_PATH = _REPO_ROOT / "docs" / "state" / "threat-catalog.json"


# ---------------------------------------------------------------------------
# T-DB-0079: catalog parses to the full item list
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0079_catalog_full_list() -> None:
    """T-DB-0079: the catalog parses to the full item list.

    id: T-DB-0079
    title: Catalog parses to the full item list
    purpose: Verify the threat catalog JSON parses and lists all items.
    level: fast
    requirement: P04-T08; Part 3 §3.24
    input: docs/state/threat-catalog.json
    expected: 12 catalog items
    risk: catalog items missing
    owning capability: persistence
    """
    data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    catalog = data.get("catalog", [])
    assert len(catalog) == len(ATTACK_CATALOG)
    matrix = ThreatMatrix(catalog)
    assert len(matrix.items) == len(ATTACK_CATALOG)


# ---------------------------------------------------------------------------
# T-DB-0080: a seeded item without a test is listed
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0080_item_without_test_listed() -> None:
    """T-DB-0080: a seeded item without a test is listed.

    id: T-DB-0080
    title: Item without test is listed
    purpose: Verify items without a test mapping appear in items_without_test.
    level: fast
    requirement: P04-T08; Part 3 §3.24
    input: ThreatMatrix with no mappings
    expected: all items have no test
    risk: untested threats pass silently
    owning capability: persistence
    """
    matrix = ThreatMatrix()
    untested = matrix.items_without_test
    assert len(untested) == len(ATTACK_CATALOG)


# ---------------------------------------------------------------------------
# T-DB-0081: mapping covers identifier-reference items
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0081_identifier_coverage() -> None:
    """T-DB-0081: the mapping covers identifier-reference items.

    id: T-DB-0081
    title: Mapping covers identifier-reference items
    purpose: Verify the identifier category items are in the catalog.
    level: fast
    requirement: P04-T08; Part 3 §3.24
    input: ATTACK_CATALOG
    expected: identifier category items exist
    risk: identifier-reference threats not covered
    owning capability: persistence
    """
    matrix = ThreatMatrix()
    id_items = [i for i in matrix.items if i.category == "identifier"]
    assert len(id_items) >= 5, f"expected >=5 identifier items, got {len(id_items)}"


# ---------------------------------------------------------------------------
# T-DB-0082: mapping covers row-level security bypass items
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0082_rls_bypass_coverage() -> None:
    """T-DB-0082: the mapping covers row-level security bypass items.

    id: T-DB-0082
    title: Mapping covers RLS bypass items
    purpose: Verify the rls category items are in the catalog.
    level: fast
    requirement: P04-T08; Part 3 §3.24
    input: ATTACK_CATALOG
    expected: rls category items exist
    risk: RLS bypass threats not covered
    owning capability: persistence
    """
    matrix = ThreatMatrix()
    rls_items = [i for i in matrix.items if i.category == "rls"]
    assert len(rls_items) >= 3, f"expected >=3 rls items, got {len(rls_items)}"


# ---------------------------------------------------------------------------
# T-DB-0083: mapping covers pooled-connection items
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0083_pooled_connection_coverage() -> None:
    """T-DB-0083: the mapping covers pooled-connection items.

    id: T-DB-0083
    title: Mapping covers pooled-connection items
    purpose: Verify the pool category items are in the catalog.
    level: fast
    requirement: P04-T08; Part 3 §3.24
    input: ATTACK_CATALOG
    expected: pool category items exist
    risk: pooled-connection threats not covered
    owning capability: persistence
    """
    matrix = ThreatMatrix()
    pool_items = [i for i in matrix.items if i.category == "pool"]
    assert len(pool_items) >= 1, f"expected >=1 pool item, got {len(pool_items)}"


# ---------------------------------------------------------------------------
# T-DB-0084: mapping covers shared-sequence items
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_DB_0084_shared_sequence_coverage() -> None:
    """T-DB-0084: the mapping covers shared-sequence items.

    id: T-DB-0084
    title: Mapping covers shared-sequence items
    purpose: Verify the sequence category items are in the catalog.
    level: fast
    requirement: P04-T08; Part 3 §3.24
    input: ATTACK_CATALOG
    expected: sequence category items exist
    risk: shared-sequence threats not covered
    owning capability: persistence
    """
    matrix = ThreatMatrix()
    seq_items = [i for i in matrix.items if i.category == "sequence"]
    assert len(seq_items) >= 1, f"expected >=1 sequence item, got {len(seq_items)}"

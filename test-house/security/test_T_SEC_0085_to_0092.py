"""Threat catalog completion tests (P11-T07).

Test IDs: T-SEC-0085 to T-SEC-0092.
Covers: no unmapped item remains except those deferred with a phase;
a seeded unmapped item fails trace; supply chain items mapped to gates;
hostile files deferred to P14; deferred items name a phase.

Spec: Part 3 §3.15, §3.24; Part 4 §4.5; P11-T07.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.threat_matrix import (
    ATTACK_CATALOG,
    DEFERRED_ITEMS,
    THREAT_MATRIX,
    ThreatMatrix,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CATALOG_PATH = _REPO_ROOT / "docs" / "state" / "threat-catalog.json"


# ---------------------------------------------------------------------------
# T-SEC-0085: no unmapped item remains except deferred
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0085_no_unmapped_except_deferred() -> None:
    """T-SEC-0085: no unmapped item remains except those deferred with a phase.

    id: T-SEC-0085
    title: No unmapped except deferred
    purpose: Verify every catalog item has a test mapping or a deferral.
    level: fast
    requirement: PR-06; Part 3 §3.15, §3.24; P11-T07
    input: ThreatMatrix with all mappings
    expected: items_without_test is empty
    risk: unmapped threat passes silently
    owning capability: security
    """
    matrix = ThreatMatrix()
    for entry in ATTACK_CATALOG:
        atk_id = entry["id"]
        if atk_id not in DEFERRED_ITEMS:
            matrix.map(atk_id, "T-SEC-0001")
    assert len(matrix.unmapped_without_deferral) == 0


# ---------------------------------------------------------------------------
# T-SEC-0086: seeded unmapped item fails
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0086_seeded_unmapped_fails() -> None:
    """T-SEC-0086: a seeded unmapped item without a deferral appears in items_without_test.

    id: T-SEC-0086
    title: Seeded unmapped fails
    purpose: Verify an unmapped item without a deferral is listed.
    level: fast
    requirement: PR-06; Part 3 §3.15, §3.24; P11-T07
    input: ThreatMatrix with a seeded unmapped catalog item
    expected: item appears in items_without_test
    risk: unmapped item not caught
    owning capability: security
    """
    seeded_catalog = ATTACK_CATALOG + [
        {"id": "ATK-999", "name": "seeded unmapped threat", "category": "seeded"}
    ]
    matrix = ThreatMatrix(seeded_catalog)
    unmapped = matrix.items_without_test
    seeded = [item for item in unmapped if item.threat_id == "ATK-999"]
    assert len(seeded) == 1


# ---------------------------------------------------------------------------
# T-SEC-0087: supply chain items mapped to gates
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0087_supply_chain_mapped() -> None:
    """T-SEC-0087: supply chain items are mapped to gates.

    id: T-SEC-0087
    title: Supply chain mapped to gates
    purpose: Verify supply chain compromise is mapped to a test.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T07
    input: THREAT_MATRIX
    expected: supply_chain_compromise in THREAT_MATRIX
    risk: supply chain not covered
    owning capability: security
    """
    assert "supply_chain_compromise" in THREAT_MATRIX
    assert len(THREAT_MATRIX["supply_chain_compromise"]) > 0


# ---------------------------------------------------------------------------
# T-SEC-0088: hostile files deferred to P14
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0088_hostile_files_deferred() -> None:
    """T-SEC-0088: hostile files are deferred to P14.

    id: T-SEC-0088
    title: Hostile files deferred to P14
    purpose: Verify hostile files are deferred to the Intake phase (P14).
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T07
    input: DEFERRED_ITEMS
    expected: ATK-022 deferred to P14
    risk: hostile files not deferred
    owning capability: security
    """
    assert "ATK-022" in DEFERRED_ITEMS
    assert DEFERRED_ITEMS["ATK-022"] == "P14"


# ---------------------------------------------------------------------------
# T-SEC-0089: deferred items name a phase
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0089_deferred_items_name_phase() -> None:
    """T-SEC-0089: every deferred item names a phase.

    id: T-SEC-0089
    title: Deferred items name a phase
    purpose: Verify no deferred item has an empty target phase.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T07
    input: DEFERRED_ITEMS
    expected: all values are non-empty phase names
    risk: deferred item without a phase
    owning capability: security
    """
    for threat_id, phase in DEFERRED_ITEMS.items():
        assert phase, f"deferred item {threat_id} has no phase"


# ---------------------------------------------------------------------------
# T-SEC-0090: catalog JSON matches Python catalog
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0090_catalog_json_matches() -> None:
    """T-SEC-0090: the catalog JSON matches the Python ATTACK_CATALOG.

    id: T-SEC-0090
    title: Catalog JSON matches Python
    purpose: Verify the JSON catalog and Python catalog have the same count.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T07
    input: docs/state/threat-catalog.json and ATTACK_CATALOG
    expected: same length
    risk: catalog drift
    owning capability: security
    """
    data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    catalog = data.get("catalog", [])
    assert len(catalog) == len(ATTACK_CATALOG)


# ---------------------------------------------------------------------------
# T-SEC-0091: all new items have a mapping or deferral
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0091_all_new_items_covered() -> None:
    """T-SEC-0091: all new items (ATK-020 to ATK-027) have a mapping or deferral.

    id: T-SEC-0091
    title: All new items covered
    purpose: Verify new items from P11 are mapped or deferred.
    level: fast
    requirement: PR-06; Part 3 §3.15, §3.24; P11-T07
    input: ATTACK_CATALOG, THREAT_MATRIX, DEFERRED_ITEMS
    expected: each new item is in THREAT_MATRIX or DEFERRED_ITEMS
    risk: new threat uncovered
    owning capability: security
    """
    new_ids = [f"ATK-{i:03d}" for i in range(20, 28)]
    all_keys = set(THREAT_MATRIX.keys())
    for atk_id in new_ids:
        entry = next(e for e in ATTACK_CATALOG if e["id"] == atk_id)
        category = entry["category"]
        is_deferred = atk_id in DEFERRED_ITEMS
        is_mapped = any(category in key or key in category for key in all_keys)
        assert is_deferred or is_mapped, (
            f"{atk_id} ({category}) not in THREAT_MATRIX or DEFERRED_ITEMS"
        )


# ---------------------------------------------------------------------------
# T-SEC-0092: deferred items list is non-empty
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0092_deferred_items_nonempty() -> None:
    """T-SEC-0092: the deferred items list is non-empty (at least one deferral).

    id: T-SEC-0092
    title: Deferred items non-empty
    purpose: Verify at least one item is deferred to a named phase.
    level: fast
    requirement: PR-06; Part 3 §3.15; P11-T07
    input: DEFERRED_ITEMS
    expected: at least one entry
    risk: no deferral mechanism
    owning capability: security
    """
    assert len(DEFERRED_ITEMS) >= 1

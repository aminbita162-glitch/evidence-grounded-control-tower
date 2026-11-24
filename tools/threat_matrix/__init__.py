"""Threat-to-test matrix tool (P04-T08).

Reads the attack catalog of Part 3 §3.24 and the threat list of Part 3 §3.15,
assigns every item an identifier, and reads the threat ids named in test
headers.  Prints items without a test.

Spec: Part 3 §3.15, §3.24; Part 4 §4.5; P04-T08.
"""

from __future__ import annotations

__all__ = [
    "ThreatItem",
    "ThreatMatrix",
    "ATTACK_CATALOG",
    "THREAT_MATRIX",
]

ATTACK_CATALOG: list[dict[str, str]] = [
    {"id": "ATK-001", "name": "insecure direct object reference", "category": "identifier"},
    {"id": "ATK-002", "name": "tenant identifier forged in body", "category": "identifier"},
    {"id": "ATK-003", "name": "tenant identifier forged in header", "category": "identifier"},
    {"id": "ATK-004", "name": "tenant identifier forged in path", "category": "identifier"},
    {"id": "ATK-005", "name": "tenant identifier forged in token", "category": "identifier"},
    {"id": "ATK-006", "name": "row-level security bypass by table ownership", "category": "rls"},
    {"id": "ATK-007", "name": "row-level security bypass by privileged roles", "category": "rls"},
    {"id": "ATK-008", "name": "row-level security bypass by functions", "category": "rls"},
    {
        "id": "ATK-009",
        "name": "session setting leaking through pooled connections",
        "category": "pool",
    },
    {
        "id": "ATK-010",
        "name": "shared sequences revealing other tenants activity",
        "category": "sequence",
    },
    {"id": "ATK-011", "name": "existence oracle through status codes", "category": "oracle"},
    {"id": "ATK-012", "name": "cache key collision and cache poisoning", "category": "cache"},
]

#: P05 threat-to-test mappings for the evidence ledger.
THREAT_MATRIX: dict[str, list[str]] = {
    "evidence_tampering": [
        "T-LED-0003",
        "T-LED-0005",
        "T-LED-0006",
        "T-LED-0031",
        "T-LED-0049",
        "T-LED-0050",
        "T-LED-0060",
    ],
    "ledger_proof_endpoints": [
        "T-LED-0026",
        "T-LED-0027",
        "T-LED-0028",
        "T-LED-0029",
        "T-LED-0030",
    ],
    "hash_replay": [
        "T-LED-0004",
        "T-LED-0033",
        "T-LED-0046",
    ],
    "signature_misuse": [
        "T-LED-0032",
        "T-LED-0036",
    ],
    "verifier_divergence": [
        "T-LED-0067",
        "T-LED-0068",
        "T-LED-0073",
    ],
    "salt_loss": [
        "T-LED-0009",
        "T-LED-0044",
    ],
}


class ThreatItem:
    """A threat-to-test mapping entry."""

    def __init__(
        self, threat_id: str, name: str, category: str, test_id: str | None = None
    ) -> None:
        self.threat_id = threat_id
        self.name = name
        self.category = category
        self.test_id = test_id

    @property
    def has_test(self) -> bool:
        return self.test_id is not None


class ThreatMatrix:
    """Threat-to-test matrix.

    Maps attack catalog items to test IDs.  Items without a test are listed.
    """

    def __init__(self, catalog: list[dict[str, str]] | None = None) -> None:
        self._catalog = catalog if catalog is not None else ATTACK_CATALOG
        self._mappings: dict[str, str] = {}

    def map(self, threat_id: str, test_id: str) -> None:
        """Map a threat to a test ID."""
        self._mappings[threat_id] = test_id

    @property
    def items(self) -> list[ThreatItem]:
        """All catalog items with their test mappings."""
        result: list[ThreatItem] = []
        for entry in self._catalog:
            tid = entry["id"]
            result.append(
                ThreatItem(
                    threat_id=tid,
                    name=entry["name"],
                    category=entry["category"],
                    test_id=self._mappings.get(tid),
                )
            )
        return result

    @property
    def items_without_test(self) -> list[ThreatItem]:
        """Catalog items that have no test mapping."""
        return [item for item in self.items if not item.has_test]

    @property
    def coverage(self) -> dict[str, bool]:
        """Coverage report: category -> covered."""
        covered: dict[str, bool] = {}
        for item in self.items:
            if item.category not in covered:
                covered[item.category] = item.has_test
            else:
                covered[item.category] = covered[item.category] or item.has_test
        return covered

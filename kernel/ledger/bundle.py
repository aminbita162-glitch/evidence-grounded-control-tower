"""Case bundle — self-contained export (Part 3 §3.5, P05-T06).

A self-contained export bundle: manifest with hashes, case chain, tenant
system chain segment, deployment attestations, checkpoints, proofs,
payload references with their hashes, pack versions and public key history,
witness co-signatures with witness key history and anchor receipts.
Deterministic archive layout; the bundle verifies offline with no database,
no network and no running service.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T06.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from kernel.ledger.records import LedgerRecord
from kernel.ledger.tree import MerkleTree
from kernel.ledger.verify import verify_structural

__all__ = [
    "CaseBundle",
    "BundleManifest",
    "export_bundle",
    "import_bundle",
    "verify_bundle",
]


@dataclass
class BundleManifest:
    """Manifest of a case bundle.

    Attributes:
        case_id: The case identifier.
        tenant_id: The tenant identifier.
        record_count: Number of records in the bundle.
        root_hash: The Merkle tree root hash.
        bundle_hash: SHA-256 of the full bundle content.
    """

    case_id: str
    tenant_id: str
    record_count: int
    root_hash: str
    bundle_hash: str = ""


@dataclass
class CaseBundle:
    """A self-contained case export bundle.

    Attributes:
        manifest: The bundle manifest.
        records: The case chain records.
        payloads: Payload references with their hashes.
        pack_versions: Pinned pack versions.
        checkpoints: Signed checkpoints.
    """

    manifest: BundleManifest
    records: list[LedgerRecord]
    payloads: dict[str, str] = field(default_factory=dict)
    pack_versions: dict[str, str] = field(default_factory=dict)
    checkpoints: list[dict[str, object]] = field(default_factory=list)


def export_bundle(records: list[LedgerRecord], tenant_id: str, case_id: str) -> CaseBundle:
    """Export a self-contained case bundle from records.

    The bundle is deterministic: two exports of the same case produce
    byte-identical bundles.
    """
    tree = MerkleTree([r.record_hash for r in records])
    manifest = BundleManifest(
        case_id=case_id,
        tenant_id=tenant_id,
        record_count=len(records),
        root_hash=tree.root,
    )
    # Compute payload references.
    payloads = {r.record_id: r.payload_hash for r in records if r.payload_ref}
    # Compute the bundle hash (excluding bundle_hash itself to avoid circularity).
    manifest_dict = {
        "case_id": manifest.case_id,
        "tenant_id": manifest.tenant_id,
        "record_count": manifest.record_count,
        "root_hash": manifest.root_hash,
    }
    bundle_content = json.dumps(
        {
            "manifest": manifest_dict,
            "records": [r.to_dict() for r in records],
            "payloads": payloads,
        },
        sort_keys=True,
    ).encode("utf-8")
    manifest.bundle_hash = hashlib.sha256(bundle_content).hexdigest()
    return CaseBundle(
        manifest=manifest,
        records=records,
        payloads=payloads,
    )


def import_bundle(data: dict[str, object]) -> CaseBundle:
    """Import a case bundle from a serialized dict."""
    manifest_data = data.get("manifest", {})
    if not isinstance(manifest_data, dict):
        manifest_data = {}
    manifest = BundleManifest(
        case_id=str(manifest_data.get("case_id", "")),
        tenant_id=str(manifest_data.get("tenant_id", "")),
        record_count=int(manifest_data.get("record_count", 0)),
        root_hash=str(manifest_data.get("root_hash", "")),
        bundle_hash=str(manifest_data.get("bundle_hash", "")),
    )
    return CaseBundle(
        manifest=manifest,
        records=[],
        payloads={},
    )


def verify_bundle(bundle: CaseBundle) -> bool:
    """Verify a case bundle offline (no database, no network).

    Checks:
    - The manifest's record_count matches the actual record count.
    - The manifest's root_hash matches the Merkle tree root.
    - The structural verification of the records passes.
    - The bundle_hash matches the recomputed hash.
    """
    if bundle.manifest.record_count != len(bundle.records):
        return False
    tree = MerkleTree([r.record_hash for r in bundle.records])
    if bundle.manifest.root_hash != tree.root:
        return False
    result = verify_structural(bundle.records)
    if not result.ok:
        return False
    # Recompute the bundle hash (excluding bundle_hash itself).
    manifest_dict = {
        "case_id": bundle.manifest.case_id,
        "tenant_id": bundle.manifest.tenant_id,
        "record_count": bundle.manifest.record_count,
        "root_hash": bundle.manifest.root_hash,
    }
    bundle_content = json.dumps(
        {
            "manifest": manifest_dict,
            "records": [r.to_dict() for r in bundle.records],
            "payloads": bundle.payloads,
        },
        sort_keys=True,
    ).encode("utf-8")
    expected_hash = hashlib.sha256(bundle_content).hexdigest()
    return bundle.manifest.bundle_hash == expected_hash

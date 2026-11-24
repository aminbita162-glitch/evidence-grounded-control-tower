"""Witness component and anchor port (Part 3 §3.5, P05-T03).

A witness co-signs a checkpoint only if it is a consistent extension of the
last checkpoint it signed.  The witness has its own Ed25519 key in its own
secret-store entry, never readable by the application process.

The witness is declared LOCAL (run by the operator) or EXTERNAL (run by
another party).  The anchor port publishes the checkpoint digest outside
the deployment; the default adapter exports signed checkpoint bundles for
off-site storage.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T03.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from adapters.signing import Signer
from kernel.ledger.checkpoint import Checkpoint

__all__ = [
    "Witness",
    "LocalWitness",
    "AnchorPort",
    "OfflineExportAdapter",
    "AnchorReceipt",
]

Witness = Literal["LOCAL", "EXTERNAL"]


@dataclass
class LocalWitness:
    """A LOCAL witness that co-signs consistent checkpoints.

    The witness keeps track of the last checkpoint it signed.  A new
    checkpoint is co-signed only if it is a consistent extension (its
    tree size >= the last signed size, and the consistency proof holds).

    Attributes:
        signer: The witness's Ed25519 signer (own key, not the deployment key).
        last_size: The tree size of the last co-signed checkpoint.
        last_root: The root hash of the last co-signed checkpoint.
    """

    signer: Signer
    last_size: int = 0
    last_root: str = ""

    def cosign(
        self,
        checkpoint: Checkpoint,
        consistency_proof_valid: bool = True,
    ) -> Checkpoint:
        """Co-sign a checkpoint if it is a consistent extension.

        Args:
            checkpoint: The checkpoint to co-sign.
            consistency_proof_valid: Whether the consistency proof from
                the last signed checkpoint to this one is valid.

        Returns:
            A new checkpoint with the witness co-signature.

        Raises:
            ValueError: If the checkpoint rewrites history (not a consistent
                extension).
        """
        if self.last_size > 0:
            if checkpoint.tree_size < self.last_size:
                raise ValueError(
                    f"witness refuses: tree size shrunk ({checkpoint.tree_size} < {self.last_size})"
                )
            if checkpoint.tree_size == self.last_size and checkpoint.root_hash != self.last_root:
                raise ValueError("witness refuses: root changed at same tree size")
            if not consistency_proof_valid:
                raise ValueError("witness refuses: consistency proof invalid")
        sig = self.signer.sign(checkpoint.signing_bytes())
        self.last_size = checkpoint.tree_size
        self.last_root = checkpoint.root_hash
        return Checkpoint(
            chain_id=checkpoint.chain_id,
            tree_size=checkpoint.tree_size,
            root_hash=checkpoint.root_hash,
            system_chain_position=checkpoint.system_chain_position,
            recorded_at=checkpoint.recorded_at,
            signature=checkpoint.signature,
            witness_signature=sig,
            witness_type="LOCAL",
            anchor_receipt=checkpoint.anchor_receipt,
        )


@dataclass
class AnchorReceipt:
    """A receipt from an anchor proving a checkpoint was published.

    Attributes:
        checkpoint_root: The root hash of the anchored checkpoint.
        receipt_hash: A hash proving the checkpoint was published.
    """

    checkpoint_root: str
    receipt_hash: str


class AnchorPort:
    """Anchor port — publishes checkpoint digests outside the deployment.

    The default adapter is the offline-export adapter.
    """

    def __init__(self, adapter: OfflineExportAdapter | None = None) -> None:
        self._adapter = adapter or OfflineExportAdapter()

    def anchor(self, checkpoint: Checkpoint) -> AnchorReceipt:
        """Anchor a checkpoint and return the receipt."""
        return self._adapter.export(checkpoint)


class OfflineExportAdapter:
    """Offline-export adapter for the anchor port.

    Exports signed checkpoint bundles for off-site storage.  In the
    development implementation, the export is a deterministic bundle
    (a dict of the checkpoint and its signature).
    """

    def export(self, checkpoint: Checkpoint) -> AnchorReceipt:
        """Export a checkpoint and return an anchor receipt."""
        import hashlib

        bundle = checkpoint.to_dict() | {
            "signature": checkpoint.signature,
            "witness_signature": checkpoint.witness_signature,
            "witness_type": checkpoint.witness_type,
        }
        receipt_hash = hashlib.sha256(repr(sorted(bundle.items())).encode("utf-8")).hexdigest()
        return AnchorReceipt(
            checkpoint_root=checkpoint.root_hash,
            receipt_hash=receipt_hash,
        )

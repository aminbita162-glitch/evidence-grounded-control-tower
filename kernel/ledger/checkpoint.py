"""Signed checkpoints (Part 3 §3.5, P05-T03).

A checkpoint is ``{chain_id, tree_size, root_hash, system_chain_position,
recorded_at}`` signed with Ed25519.  A checkpoint is written every 100
records and at case close, and included in the Passport.

Verification levels:
- ``SELF-ATTESTED``: no valid witness co-signature.
- ``WITNESSED-LOCAL``: co-signed by a LOCAL witness.
- ``WITNESSED-EXTERNAL``: co-signed by an EXTERNAL witness.
- ``ANCHORED``: witnessed, with a verified anchor receipt.

Only ``WITNESSED-EXTERNAL`` and ``ANCHORED`` support the claim that the
operator cannot rewrite history unnoticed.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T03.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from kernel.canonical import canonical_bytes

__all__ = [
    "Checkpoint",
    "VerificationLevel",
    "WitnessType",
]

VerificationLevel = Literal["SELF-ATTESTED", "WITNESSED-LOCAL", "WITNESSED-EXTERNAL", "ANCHORED"]
WitnessType = Literal["LOCAL", "EXTERNAL"]


@dataclass(frozen=True)
class Checkpoint:
    """A signed checkpoint over a Merkle tree root.

    Attributes:
        chain_id: Identifier of the chain this checkpoint covers.
        tree_size: Number of leaves in the tree at this checkpoint.
        root_hash: The Merkle root hash.
        system_chain_position: Position of the system chain in force.
        recorded_at: ISO 8601 timestamp (month-level only, D-14).
        signature: Detached Ed25519 signature over the canonical checkpoint.
        witness_signature: Optional witness co-signature.
        witness_type: ``LOCAL``, ``EXTERNAL``, or ``None`` (no witness).
        anchor_receipt: Optional anchor receipt hash.
    """

    chain_id: str
    tree_size: int
    root_hash: str
    system_chain_position: int
    recorded_at: str
    signature: str
    witness_signature: str | None = None
    witness_type: WitnessType | None = None
    anchor_receipt: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize to a canonical dict (without witness/anchor fields)."""
        return {
            "chain_id": self.chain_id,
            "tree_size": self.tree_size,
            "root_hash": self.root_hash,
            "system_chain_position": self.system_chain_position,
            "recorded_at": self.recorded_at,
        }

    def signing_bytes(self) -> bytes:
        """Return the canonical bytes to sign/verify."""
        return canonical_bytes(self.to_dict())

    def verification_level(self) -> VerificationLevel:
        """Return the verification level of this checkpoint.

        - ``SELF-ATTESTED`` if no valid witness co-signature.
        - ``WITNESSED-LOCAL`` if co-signed by a LOCAL witness.
        - ``WITNESSED-EXTERNAL`` if co-signed by an EXTERNAL witness.
        - ``ANCHORED`` if witnessed with a verified anchor receipt.
        """
        if self.witness_signature is None or self.witness_type is None:
            return "SELF-ATTESTED"
        if self.anchor_receipt is not None:
            return "ANCHORED"
        if self.witness_type == "EXTERNAL":
            return "WITNESSED-EXTERNAL"
        return "WITNESSED-LOCAL"

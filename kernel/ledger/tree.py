"""Merkle tree — RFC 9162 style (Part 3 §3.5, P05-T03).

Binary Merkle tree over the ordered records of a chain.  Built in the style
of RFC 9162 with domain-separated leaf and node hashes:

- leaf = H("ctc/leaf/v1" || record_hash)
- node = H("ctc/node/v1" || left || right)

An unbalanced tree follows the RFC's split rule: for ``n`` leaves where
``n`` is not a power of two, let ``k`` be the largest power of two less
than ``n``; the root is ``H(node_tag, root(left[0:k]), root(right[k:n]))``.

Spec: Part 3 §3.5; Part 4 §4.4; P05-T03.
"""

from __future__ import annotations

import hashlib

__all__ = [
    "MerkleTree",
    "leaf_hash",
    "node_hash",
    "compute_root",
    "ZERO_HASH",
]

_LEAF_TAG = "ctc/leaf/v1"
_NODE_TAG = "ctc/node/v1"
ZERO_HASH: str = "0" * 64


def leaf_hash(record_hash: str) -> str:
    """Compute leaf hash: H("ctc/leaf/v1" || record_hash)."""
    data = _LEAF_TAG.encode("utf-8") + record_hash.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def node_hash(left: str, right: str) -> str:
    """Compute internal node hash: H("ctc/node/v1" || left || right)."""
    data = _NODE_TAG.encode("utf-8") + left.encode("utf-8") + right.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _largest_power_of_2_below(n: int) -> int:
    """Return the largest power of two strictly less than n (n > 1)."""
    k = 1
    while k * 2 < n:
        k *= 2
    return k


def compute_root(leaf_hashes: list[str]) -> str:
    """Compute the Merkle root from a list of leaf hashes.

    Uses the RFC 9162 split rule for unbalanced trees.
    """
    if not leaf_hashes:
        return ZERO_HASH
    if len(leaf_hashes) == 1:
        return leaf_hashes[0]
    k = _largest_power_of_2_below(len(leaf_hashes))
    left_root = compute_root(leaf_hashes[:k])
    right_root = compute_root(leaf_hashes[k:])
    return node_hash(left_root, right_root)


class MerkleTree:
    """A Merkle tree over a list of record hashes.

    Attributes:
        record_hashes: The ordered list of record hashes.
        leaves: The computed leaf hashes.
        root: The Merkle root.
        size: The number of leaves.
    """

    def __init__(self, record_hashes: list[str]) -> None:
        self.record_hashes = list(record_hashes)
        self.leaves = [leaf_hash(rh) for rh in self.record_hashes]
        self.root = compute_root(self.leaves)
        self.size = len(self.leaves)

"""Evidence ledger — tamper-evident record chain (Part 3 §3.5, P05).

The ledger is the append-only, hash-chained record of everything the
system does.  Case chains and system chains share the same record format,
hashing rules and algorithm identifier.
"""

from __future__ import annotations

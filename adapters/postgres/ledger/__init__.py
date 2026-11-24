"""PostgreSQL ledger adapter (P05-T01).

Provides the :class:`PostgresCaseChain` that stores case chain records
in the ``evidence_record`` table with the append-only guard and RLS.
"""

from __future__ import annotations

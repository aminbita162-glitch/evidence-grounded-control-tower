"""Synthetic data factory (Part 3 §3.12, P09-T01).

A seeded, reproducible factory producing documents (including Arabic and
English text, Arabic-Indic and Persian digits), facts, tariff-like tables
and tenant feeds. Every record is labelled SYNTHETIC with the seed and
factory version. The factory is never mixed into reference data (Part 3
§3.12). Output is deterministic for a fixed seed.

Spec: Part 3 §3.12, §3.2; P09-T01.
"""

from __future__ import annotations

from data.synthetic.factory import (
    DENYLIST,
    FACTORY_VERSION,
    SYNTHETIC_LABEL,
    SyntheticDocument,
    SyntheticFact,
    SyntheticFactory,
    SyntheticRecord,
    SyntheticTariffRow,
    SyntheticTenantFeed,
    generate,
    to_canonical,
)

__all__ = [
    "DENYLIST",
    "FACTORY_VERSION",
    "SYNTHETIC_LABEL",
    "SyntheticDocument",
    "SyntheticFact",
    "SyntheticRecord",
    "SyntheticTariffRow",
    "SyntheticTenantFeed",
    "SyntheticFactory",
    "generate",
    "to_canonical",
]

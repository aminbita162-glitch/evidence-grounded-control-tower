"""Project-owned synthetic reference inputs for local valuation and diagnostics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from capabilities.k05 import ReferencePack, calibrate_reference
from capabilities.k05.reference import ReferenceGroup, Unit
from capabilities.k05.registration import ValuationJudge
from kernel.hashing import domain_hash
from kernel.lib.money import CurrencyTable
from kernel.lib.valuation import FxPack, ValuationRule

SOURCE_ID = "SRC-SYNTHETIC-K05"
LABEL = "SYNTHETIC"
START = datetime(2026, 11, 1, tzinfo=UTC)


def create_judge() -> ValuationJudge:
    """Build a closed synthetic fixture with no external rates or legal rules."""
    version = domain_hash("ctc/payload/v1", [SOURCE_ID, "1.0.0", "reference"])
    reference = ReferencePack(
        version,
        LABEL,
        SOURCE_ID,
        START,
        START + timedelta(days=30),
        {"1101": ReferenceGroup("1101", "kg", "AED", (Decimal(1),) * 30)},
        {},
        {"kg": Unit("mass", Decimal(1)), "t": Unit("mass", Decimal(1000))},
    )
    fx = FxPack(
        domain_hash("ctc/payload/v1", [SOURCE_ID, "1.0.0", "fx"]),
        CurrencyTable({"AED": 2}, SOURCE_ID),
        {},
        LABEL,
    )
    rules = {"CIF": ValuationRule("SYN-RULE-K05-CIF", (), LABEL)}
    scores = tuple(Decimal(number) / 250 for number in range(500))
    held_out = tuple(Decimal(number) / 20 for number in range(40))
    shifted = tuple(score + Decimal("0.7") for score in held_out)
    calibration = calibrate_reference(
        scores,
        held_out,
        shifted,
        pack_hash=version,
        source_id=SOURCE_ID,
    )
    return ValuationJudge(fx, rules, reference, calibration)

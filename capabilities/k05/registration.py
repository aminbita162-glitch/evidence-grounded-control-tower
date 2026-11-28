"""Bind K05 to the verified facts of a case and the selected valuation packs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, DecimalException

from pydantic_core import to_jsonable_python

from capabilities.f01 import CanonicalFact
from capabilities.k05 import (
    ALPHA,
    Calibration,
    Line,
    Reason,
    ReferencePack,
    ValuationInputs,
    ValuationReport,
    evaluate,
)
from kernel.hashing import domain_hash
from kernel.lib.money import Money
from kernel.lib.valuation import Adjustment, FxPack, ValuationRule
from kernel.types.decision import DecisionValue
from kernel.types.label import weakest_of

CAPABILITY_ID = "K05"


def canonical_inputs(facts: Sequence[CanonicalFact]) -> ValuationInputs | None:
    """Read only verified shipment facts published by F01."""
    keyed = {
        fact.key.removeprefix("shipment."): fact
        for fact in facts
        if fact.key.startswith("shipment.") and fact.status == "VERIFIED"
    }
    lines: dict[str, dict[str, CanonicalFact]] = {}
    for key, fact in keyed.items():
        parts = key.split(".")
        if len(parts) == 3 and parts[0] == "line_items":
            lines.setdefault(parts[1], {})[parts[2]] = fact
    if not lines:
        return None

    def scalar(fact: CanonicalFact) -> str:
        if not isinstance(fact.value, str) or not fact.value:
            raise ValueError("canonical scalar required")
        return fact.value

    def price(fact: CanonicalFact, default_currency: str) -> Money:
        return Money(Decimal(scalar(fact)), fact.unit or default_currency)

    try:
        currency = scalar(keyed["currency"]).upper()
        invoice = price(keyed["invoice_total"], currency)
        declared = price(keyed["declared_customs_value"], currency)
        declared_date = date.fromisoformat(scalar(keyed["declared_date"]))
        incoterm = scalar(keyed["incoterm"]).upper()
        adjusted = {}
        for name, fact in keyed.items():
            if name in {"freight", "insurance"} or name.startswith("adjustment."):
                adjusted[name.removeprefix("adjustment.")] = Adjustment(
                    price(fact, currency),
                    domain_hash("ctc/payload/v1", fact.source_fact_ids),
                    fact.label,
                )
        parsed = []
        for line_id, line in sorted(lines.items()):
            quantity = line["quantity"]
            code = line["declared_classification_code"]
            amount = line["line_amount"]
            parsed.append(
                Line(
                    line_id,
                    scalar(code),
                    price(amount, currency),
                    Decimal(scalar(quantity)),
                    quantity.unit or "",
                    weakest_of(amount.label, weakest_of(quantity.label, code.label)),
                )
            )
        label = keyed["invoice_total"].label
        for key in ("currency", "declared_customs_value", "declared_date", "incoterm"):
            label = weakest_of(label, keyed[key].label)
    except KeyError, ValueError, DecimalException:
        return None
    return ValuationInputs(
        invoice, declared, incoterm, declared_date, adjusted, tuple(parsed), label
    )


@dataclass(frozen=True, slots=True)
class ValuationJudge:
    fx: FxPack
    rules: Mapping[str, ValuationRule]
    reference: ReferencePack
    calibration: Calibration

    def run(
        self, facts: Sequence[CanonicalFact], at: datetime, origin: str
    ) -> tuple[ValuationReport, dict[str, object]]:
        report = evaluate(
            canonical_inputs(facts),
            at=at,
            fx=self.fx,
            rules=self.rules,
            reference=self.reference,
            calibration=self.calibration,
            data_origin=origin,
        )
        record = evidence_record(
            facts,
            at,
            report,
            fx_hash=self.fx.version_hash,
            reference_hash=self.reference.version_hash,
        )
        record["configuration_hash"] = domain_hash(
            "ctc/payload/v1",
            {"rules": {key: asdict(value) for key, value in self.rules.items()}, "alpha": ALPHA},
        )
        return report, record


def evidence_record(
    facts: Sequence[CanonicalFact],
    at: datetime,
    report: ValuationReport,
    *,
    fx_hash: str | None = None,
    reference_hash: str | None = None,
) -> dict[str, object]:
    """Record input and output commitments without exposing the private interval."""
    inputs = [asdict(fact) for fact in sorted(facts, key=lambda fact: fact.key)]
    full = to_jsonable_python(report.view("reviewer"))
    return {
        "capability_id": CAPABILITY_ID,
        "evaluated_at": at.isoformat(),
        "input_hash": domain_hash("ctc/payload/v1", inputs),
        "output_hash": domain_hash("ctc/payload/v1", full),
        "fx_pack_hash": fx_hash,
        "reference_pack_hash": reference_hash,
        "calibration_hash": report.calibration.digest if report.calibration else None,
    }


def register(
    judge: ValuationJudge | None, facts: Sequence[CanonicalFact], at: datetime, origin: str
) -> tuple[ValuationReport, dict[str, object]]:
    """Evaluate a case through the registered configuration and emit its evidence."""
    if judge is not None:
        return judge.run(facts, at, origin)
    reason = (
        Reason.UPSTREAM if canonical_inputs(facts) is None else Reason.VALUATION_RULE_UNAVAILABLE
    )
    report = ValuationReport(DecisionValue.ABSTAIN, (reason,), synthetic=origin == "SYNTHETIC")
    return report, evidence_record(facts, at, report)

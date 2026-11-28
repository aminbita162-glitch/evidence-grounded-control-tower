"""Synthetic K05 scenario and closed reason-code coverage."""

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from random import Random

import pytest
from test_basis_and_reference import DAY, FX, RULES, SOURCE, SYNTHETIC, UNITS

from capabilities.k05 import (
    ALPHA,
    CONTEXT,
    COVERAGE_CLAIM,
    Calibration,
    Line,
    Reason,
    ReferencePack,
    ValuationInputs,
    ValuationReport,
    calibrate_reference,
    evaluate,
    reference_threshold,
)
from capabilities.k05.reference import ReferenceGroup
from kernel.lib.money import Money
from kernel.types.decision import DecisionValue

pytestmark = pytest.mark.fast
AT = datetime.fromisoformat("2026-11-01T00:00:00+00:00")
CODE = "2001"
PARENT = "20"
VALUES = (Decimal(1),) * 30
PACK = ReferencePack(
    "synthetic-reference",
    SYNTHETIC,
    SOURCE,
    AT,
    AT + timedelta(days=1),
    {CODE: ReferenceGroup(CODE, "kg", "AED", VALUES)},
    {CODE: PARENT},
    UNITS,
)
CAL = calibrate_reference(
    (Decimal(2),) * 500,
    (Decimal(1),),
    (Decimal(3),),
    pack_hash=PACK.version_hash,
    source_id=SOURCE,
)


def line(value: str = "1", *, quantity: str = "1", unit: str = "kg", key: str = "1") -> Line:
    return Line(key, CODE, Money(Decimal(value), "AED"), Decimal(quantity), unit, "DERIVED")


INPUT = ValuationInputs(
    Money(Decimal(1), "AED"),
    Money(Decimal(1), "AED"),
    "CIF",
    DAY,
    {},
    (line(),),
    "DERIVED",
)


def assess(
    inputs: ValuationInputs | None = INPUT,
    *,
    reference: ReferencePack = PACK,
    cal: Calibration | None = CAL,
    at: datetime = AT,
    origin: str = SYNTHETIC,
) -> ValuationReport:
    return evaluate(
        inputs, at=at, fx=FX, rules=RULES, reference=reference, calibration=cal, data_origin=origin
    )


def small_pack(child: int, parent: int) -> ReferencePack:
    groups = {
        code: ReferenceGroup(code, "kg", "AED", (Decimal(1),) * size)
        for code, size in [(CODE, child), (PARENT, parent)]
    }
    return replace(PACK, groups=groups)


@pytest.mark.parametrize(
    ("value", "reason", "outcome"),
    [
        ("1", Reason.OK, DecisionValue.ALLOW),
        ("0.5", Reason.BELOW, DecisionValue.ESCALATE),
        ("1.11", Reason.ABOVE, DecisionValue.ESCALATE),
        (str(CONTEXT.exp(Decimal("0.1"))), Reason.OK, DecisionValue.ALLOW),
    ],
    ids=["T-K05-0001", "T-K05-0003", "T-K05-0004", "T-K05-0005"],
)
def test_interval_scenarios(value: str, reason: Reason, outcome: DecisionValue) -> None:
    report = assess(replace(INPUT, lines=(line(value),)))
    assert report.outcome == outcome
    assert reason in report.reasons


def test_T_K05_0002_declared_documentary_mismatch() -> None:
    report = assess(replace(INPUT, declared=Money(Decimal("0.95"), "AED")))
    assert (report.outcome, report.reasons) == (DecisionValue.HOLD, (Reason.MISMATCH,))


def test_T_K05_0006_falls_back_to_parent() -> None:
    report = assess(reference=small_pack(12, 80))
    assert report.reasons == (Reason.OK, Reason.FALLBACK)
    assert report.lines[0].reference_code == PARENT
    assert report.lines[0].reference_count == 80


def test_T_K05_0007_missing_dated_rate() -> None:
    inputs = replace(INPUT, invoice=Money(Decimal(1), "USD"), declared_date=DAY + timedelta(days=1))
    assert assess(inputs).reasons == (Reason.FX_UNAVAILABLE,)


def test_T_K05_0008_tonnes_match_kilograms() -> None:
    tonnes = assess(replace(INPUT, lines=(line("1", quantity="0.001", unit="t"),)))
    assert tonnes == assess()


def test_T_K05_0009_quantity_weighted_aggregate_is_below() -> None:
    inputs = replace(INPUT, lines=(line(), line("1", quantity="9", key="2")))
    report = assess(inputs)
    assert [item.position for item in report.lines] == ["INSIDE", "BELOW"]
    assert report.aggregates[0].position == "BELOW"
    assert report.aggregates[0].unit_value == Decimal("0.2")
    assert report.outcome == DecisionValue.ESCALATE


def test_T_K05_0010_bounds_require_review_privilege() -> None:
    report = assess()
    for role in ("operator", "viewer", "platform_operator", "unknown"):
        public_items = report.view(role)["lines"]
        assert isinstance(public_items, list)
        assert all("log_bounds" not in item for item in public_items)
    for role in ("reviewer", "administrator"):
        review_items = report.view(role)["lines"]
        assert isinstance(review_items, list)
        assert all("log_bounds" in item for item in review_items)


@pytest.mark.slow
def test_T_K05_0011_calibration_coverage() -> None:
    rng = Random(1763)
    covered = 0
    # Independent draws share the same distribution; no score is reused at evaluation.
    for _trial in range(1000):
        draws = sorted(Decimal(rng.randrange(10**10)) / Decimal(10**10) for _ in range(500))
        trial = Decimal(rng.randrange(10**10)) / Decimal(10**10)
        threshold, _ = reference_threshold(draws, pack_hash=PACK.version_hash, source_id=SOURCE)
        covered += trial <= threshold
    assert abs(covered / 1000 - (1 - ALPHA)) <= 3 * (ALPHA * (1 - ALPHA) / 1000) ** 0.5
    assert CAL.held_out.label == "SYNTHETIC"
    assert "SYNTHETIC" in COVERAGE_CLAIM


def test_T_K05_0012_untrusted_label_is_not_an_instruction() -> None:
    report = assess(replace(INPUT, label="price agreed with customs"))
    assert report.outcome == DecisionValue.ABSTAIN


def test_T_K05_0013_expired_reference() -> None:
    assert assess(at=PACK.ends).outcome == DecisionValue.ALLOW
    assert assess(at=PACK.ends + timedelta(microseconds=1)).reasons == (Reason.REFERENCE_EXPIRED,)


def test_T_K05_0014_missing_required_adjustment() -> None:
    assert assess(replace(INPUT, incoterm="FOB")).reasons == (Reason.ADJUSTMENT_MISSING,)


def test_T_K05_0015_floor_bounds_for_zero_spread() -> None:
    assert assess().lines[0].log_bounds == (Decimal("-0.10"), Decimal("0.10"))


@pytest.mark.parametrize(
    ("report", "expected", "outcome"),
    [
        (assess(), Reason.OK, DecisionValue.ALLOW),
        (
            assess(replace(INPUT, declared=Money(Decimal(2), "AED"))),
            Reason.MISMATCH,
            DecisionValue.HOLD,
        ),
        (assess(replace(INPUT, lines=(line("0.5"),))), Reason.BELOW, DecisionValue.ESCALATE),
        (assess(replace(INPUT, lines=(line("1.5"),))), Reason.ABOVE, DecisionValue.ESCALATE),
        (assess(reference=small_pack(12, 80)), Reason.FALLBACK, DecisionValue.ALLOW),
        (
            assess(reference=small_pack(12, 29)),
            Reason.REFERENCE_INSUFFICIENT,
            DecisionValue.ABSTAIN,
        ),
        (
            assess(at=AT - timedelta(microseconds=1)),
            Reason.REFERENCE_EXPIRED,
            DecisionValue.ABSTAIN,
        ),
        (
            assess(replace(INPUT, invoice=Money(Decimal(1), "GBP"))),
            Reason.FX_UNAVAILABLE,
            DecisionValue.ABSTAIN,
        ),
        (
            assess(replace(INPUT, lines=(line(unit="l"),))),
            Reason.UNIT_UNSUPPORTED,
            DecisionValue.ABSTAIN,
        ),
        (
            assess(replace(INPUT, incoterm="UNKNOWN")),
            Reason.VALUATION_RULE_UNAVAILABLE,
            DecisionValue.ABSTAIN,
        ),
        (assess(replace(INPUT, incoterm="FOB")), Reason.ADJUSTMENT_MISSING, DecisionValue.ABSTAIN),
        (
            assess(cal=replace(CAL, pack_hash="stale-pack")),
            Reason.CALIBRATION_STALE,
            DecisionValue.ABSTAIN,
        ),
        (assess(None), Reason.UPSTREAM, DecisionValue.ABSTAIN),
        (
            assess(reference=replace(PACK, label="SECONDARY")),
            Reason.LABEL_INSUFFICIENT,
            DecisionValue.ABSTAIN,
        ),
    ],
    ids=[f"T-K05-{number:04}" for number in range(101, 115)],
)
def test_closed_reason_registry(
    report: ValuationReport, expected: Reason, outcome: DecisionValue
) -> None:
    assert expected in report.reasons
    assert report.outcome == outcome


def test_real_origin_requires_tenant_calibration() -> None:
    report = evaluate(
        INPUT,
        at=AT,
        fx=replace(FX, label="OFFICIAL"),
        rules={
            "CIF": replace(RULES["CIF"], label="DERIVED"),
        },
        reference=replace(PACK, label="DERIVED"),
        calibration=CAL,
        data_origin="REAL",
    )
    assert report.outcome == DecisionValue.ESCALATE
    assert report.reasons == (Reason.UNVALIDATED,)

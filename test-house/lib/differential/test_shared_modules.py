"""Independent reference results for the eight Phase 13 shared modules."""

from asyncio import run
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Context, Decimal
from hashlib import sha256
from itertools import product

import pytest

from kernel.extract import FieldLocator
from kernel.lib.calctrace import DecimalSettings, Formula, Operand, Operation, calculate
from kernel.lib.conformal import calibrate, predict
from kernel.lib.crosscheck import Citation, CrossCheckRequest, GatewayRun, cross_check
from kernel.lib.feeds import FeedEnvelope, FeedPolicy, FeedStatus, content_hash, validate_feed
from kernel.lib.lexi import choose
from kernel.lib.money import CurrencyTable, Money, RoundAt, round_at
from kernel.lib.solve import Constraint, IntegerModel, Settings, Term, Variable, solve_cp_sat
from kernel.lib.unblock import Requirement, RequirementKind, requirements_for
from kernel.types.decision import DecisionValue


@pytest.mark.fast
def test_T_LIB_0101() -> None:
    """Compare monetary rounding with integer arithmetic.

    id: T-LIB-0101
    title: Compare monetary rounding with integer arithmetic
    purpose: Check signed half-even ties against an independent reference
    level: fast
    requirement: P13-T02
    input: Signed integer amounts in thousandths
    expected: Rounded cents agree across ties and adjacent values
    risk: Incorrect monetary rounding
    capability: shared-library
    """
    currencies = CurrencyTable({"USD": 2}, "SYN-FX")
    for thousandths in range(-125, 126):
        cents, leftover = divmod(abs(thousandths), 10)
        increment = leftover > 5 or leftover == 5 and cents % 2 == 1
        expected = (-1 if thousandths < 0 else 1) * (cents + increment)
        result = round_at(
            Money(Decimal(f"{thousandths}e-3"), "USD"),
            RoundAt.PRESENTATION,
            currencies=currencies,
            context=Context(prec=10),
        )
        assert result.money.amount == Decimal(f"{expected}e-2")


@pytest.mark.fast
def test_T_LIB_0102() -> None:
    """Replay a nested calculation against a known amount.

    id: T-LIB-0102
    title: Replay a nested calculation against a known amount
    purpose: Check nested multiplication and subtraction with provenance
    level: fast
    requirement: P13-T03
    input: Three units at 2.75 with a 0.60 discount
    expected: The trace replays to 7.65 and retains the synthetic label
    risk: Irreproducible calculation or inflated provenance
    capability: shared-library
    """
    settings = DecimalSettings(12, ROUND_HALF_EVEN)
    subtotal = calculate(
        Formula("subtotal", 1, Operation.MULTIPLY, "SYN-PRICE-RULE"),
        settings,
        Operand("price", Decimal("2.75"), "USD", "OFFICIAL"),
        Operand("count", Decimal(3), "unit", "OFFICIAL"),
        unit="USD",
    )
    total = calculate(
        Formula("total", 1, Operation.SUBTRACT, "SYN-DISCOUNT-RULE"),
        settings,
        subtotal,
        Operand("discount", Decimal("0.60"), "USD", "SYNTHETIC"),
        unit="USD",
    )
    assert total.replay().value == Decimal("7.65")
    assert total.replay().label == "SYNTHETIC"


@pytest.mark.fast
def test_T_LIB_0103() -> None:
    """Compare unblock requirements with exhaustive subset search.

    id: T-LIB-0103
    title: Compare unblock requirements with exhaustive subset search
    purpose: Find the joint minimum when separate causes share alternatives
    level: fast
    requirement: P13-T04
    input: Three unresolved facts and two overlapping reasons
    expected: The requirements match the smallest feasible subset
    risk: Excessive or insufficient requests for evidence
    capability: shared-library
    """
    a, b, c = (Requirement(RequirementKind.FACT, name) for name in ("a", "b", "c"))
    rules = {"A": ((a,), (b,)), "B": ((a, c), (b,))}
    subsets = [
        frozenset(item for item, use in zip((a, b, c), flags, strict=True) if use)
        for flags in product((False, True), repeat=3)
    ]
    expected = min(
        (
            subset
            for subset in subsets
            if all(
                any(subset.issuperset(option) for option in options) for options in rules.values()
            )
        ),
        key=lambda subset: (len(subset), sorted(subset)),
    )
    actual = requirements_for(DecisionValue.HOLD, reversed(rules), rules)
    assert tuple(item.requirement for item in actual) == tuple(sorted(expected)) == (b,)


@pytest.mark.fast
def test_T_LIB_0104() -> None:
    """Validate a feed using canonical bytes from an independent producer.

    id: T-LIB-0104
    title: Validate a feed using canonical bytes from an independent producer
    purpose: Verify payload integrity against a known canonical representation
    level: fast
    requirement: P13-T05
    input: An ordered batch of two amounts with a known hash
    expected: The batch is accepted and the reordered batch is rejected
    risk: A modified feed is accepted
    capability: shared-library
    """
    now = datetime.fromtimestamp(100_000, tz=UTC)
    rows = ({"amount": "2.00"}, {"amount": "3.00"})
    data = b'{"rows":[{"amount":"2.00"},{"amount":"3.00"}],"type":"TENANT_FEED"}'
    digest = sha256(b"ctc/payload/v1" + data).hexdigest()
    assert content_hash(rows) == digest
    policy = FeedPolicy(
        "SYN-TEN", "SYN-SRC", "SYNTHETIC", "cost", 1, timedelta(days=1), lambda row: bool(row)
    )
    envelope = FeedEnvelope(
        "SYN-TEN",
        "SYN-SRC",
        "SYNTHETIC",
        "cost",
        1,
        "SYN-BATCH",
        now,
        now,
        now + timedelta(days=1),
        2,
        digest,
        "TENANT_SUPPLIED",
    )
    assert validate_feed(envelope, rows, tenant_id="SYN-TEN", at=now, policy=policy).status == (
        FeedStatus.ACCEPTED
    )
    assert (
        validate_feed(envelope, rows[::-1], tenant_id="SYN-TEN", at=now, policy=policy).status
        == FeedStatus.HASH_MISMATCH
    )


@pytest.mark.fast
def test_T_LIB_0105() -> None:
    """Verify conformal thresholds using a known order statistic.

    id: T-LIB-0105
    title: Verify conformal thresholds using a known order statistic
    purpose: Check the finite-sample rank and inclusive prediction cutoff
    level: fast
    requirement: P13-T06
    input: Four unordered calibration scores per class with alpha 0.4
    expected: The third ordered score is used for each class
    risk: Prediction sets omit eligible classes
    capability: shared-library
    """
    artifact = calibrate(
        {"A": (0.4, 0.1, 0.2, 0.3), "B": (0.8, 0.6, 0.5, 0.7)},
        alpha=0.4,
        version="1",
        source_id="SYN-CAL",
    )
    assert tuple(item.threshold for item in artifact.thresholds) == (0.3, 0.7)
    assert predict(artifact, {"A": 0.3, "B": 0.71}).classes == ("A",)


@pytest.mark.fast
def test_T_LIB_0106() -> None:
    """Compare the CP-SAT optimum with exhaustive search.

    id: T-LIB-0106
    title: Compare the CP-SAT optimum with exhaustive search
    purpose: Independently check a bounded integer optimum
    level: fast
    requirement: P13-T07
    input: Two bounded variables with a linear lower bound
    expected: The verified assignment matches the unique exhaustive optimum
    risk: Solver presents a wrong plan as optimal
    capability: shared-library
    """
    model = IntegerModel(
        (Variable("x", 0, 3), Variable("y", 0, 3)),
        (Constraint("minimum", (Term("x", 2), Term("y", 1)), lower=5),),
        (Term("x", 3), Term("y", 2)),
    )
    expected = min((3 * x + 2 * y, x, y) for x, y in product(range(4), repeat=2) if 2 * x + y >= 5)
    result = solve_cp_sat(model, Settings(1, 1, 2.0))
    assert result.status == "SOLVED"
    assert (result.objective, *dict(result.assignment).values()) == expected


@pytest.mark.fast
def test_T_LIB_0107() -> None:
    """Check plan stability against a known tie-break answer.

    id: T-LIB-0107
    title: Check plan stability against a known tie-break answer
    purpose: Verify objective priority and the final explicit key
    level: fast
    requirement: P13-T08
    input: Four unordered plans including two tied minima
    expected: The earliest explicit key among the tied minima wins
    risk: A change in input order changes the chosen plan
    capability: shared-library
    """
    plans = (("c", 1, -10), ("b", 0, 0), ("a", 0, 0), ("d", 0, 1))
    for index in range(len(plans)):
        rotated = plans[index:] + plans[:index]
        assert choose(
            rotated, objective=lambda plan: plan[1:], stable_key=lambda plan: (plan[0],)
        ) == ("a", 0, 0)


@pytest.mark.fast
def test_T_LIB_0108() -> None:
    """Check the known result of independently cited disagreement.

    id: T-LIB-0108
    title: Check the known result of independently cited disagreement
    purpose: Ensure competing grounded amounts produce a hold with both citations
    level: fast
    requirement: P13-T08
    input: Two independent recorded calls citing different amounts
    expected: A hold reports both original spans
    risk: Conflicting evidence is silently selected
    capability: shared-library
    """
    request = CrossCheckRequest("SYN-TEN", "SYN-CASE", "SYN-DOC", ("12 18",), ("amount",))
    first = Citation("12", FieldLocator("SYN-DOC", 0, 0, 2))
    second = Citation("18", FieldLocator("SYN-DOC", 0, 3, 5))

    async def primary(_: CrossCheckRequest) -> GatewayRun:
        return GatewayRun("provider-a", "model-a", "0" * 64, "1" * 64, {"amount": first})

    async def secondary(_: CrossCheckRequest) -> GatewayRun:
        return GatewayRun("provider-b", "model-b", "0" * 64, "2" * 64, {"amount": second})

    result = run(
        cross_check(request, primary=primary, secondary=secondary, normalize=lambda _, v: v)
    )
    (comparison,) = result.comparisons
    assert (result.status, comparison.reason, comparison.primary, comparison.secondary) == (
        "HOLD",
        "DISAGREEMENT",
        first,
        second,
    )

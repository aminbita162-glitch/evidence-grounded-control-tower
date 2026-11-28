"""Property and differential checks for the tariff calendar and tier calculation."""

from dataclasses import replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from kernel.lib.clock import Calendar, Clock, DayBasis, DayOne, PartialDay, Suspension, Terms, Tier
from kernel.lib.money import CurrencyTable, RoundAt, RoundingRule

SOURCE = "SRC-SYNTHETIC-F03"
START = datetime(2024, 2, 28, 16, tzinfo=UTC)
DAY = timedelta(days=1)
TABLE = CurrencyTable({"USD": 2}, SOURCE)
TERMS = Terms(
    SOURCE,
    "1",
    "SYNTHETIC",
    START - 1_000 * DAY,
    START + 1_000 * DAY,
    True,
    "DISCHARGED",
    "GATED_OUT_FULL",
    2,
    DayBasis.CALENDAR,
    ZoneInfo("UTC"),
    DayOne.INCLUDE,
    time(),
    PartialDay.STARTED,
    "USD",
    RoundingRule(RoundAt.TOTAL, ROUND_HALF_EVEN, SOURCE),
    (Tier(2, Decimal("3.50")), Tier(5, Decimal("5")), Tier(None, Decimal("12"))),
    SOURCE,
)
CALENDAR = Calendar(SOURCE, "1", "SYNTHETIC", frozenset({5, 6}), frozenset({date(2024, 2, 29)}))


@pytest.mark.fast
@given(
    elapsed=st.integers(0, 100),
    free=st.integers(0, 5),
    partial=st.sampled_from(tuple(PartialDay)),
    basis=st.sampled_from(tuple(DayBasis)),
    suspend=st.integers(0, 18),
    length=st.integers(1, 24),
    zone=st.sampled_from(("UTC", "America/New_York", "Europe/Berlin")),
    first=st.sampled_from(tuple(DayOne)),
)
def test_T_F03_0201_optimized_matches_day_simulation(
    elapsed: int,
    free: int,
    partial: PartialDay,
    basis: DayBasis,
    suspend: int,
    length: int,
    zone: str,
    first: DayOne,
) -> None:
    """
    id: T-F03-0201
    title: Optimized clock matches day simulation
    purpose: Compare two counting methods over generated inputs
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic tariffs, calendars and event windows
    expected: Both calculations agree on charge units and amount
    risk: HZ-04
    capability: F03
    """
    left = START + timedelta(hours=suspend)
    windows = (Suspension(left, left + timedelta(hours=length), SOURCE, True),)
    terms = replace(
        TERMS, free_days=free, partial=partial, basis=basis, zone=ZoneInfo(zone), day_one=first
    )
    clock = Clock(terms, CALENDAR, windows, TABLE)
    end = START + timedelta(hours=elapsed)
    assert clock.charge(START, end) == clock.simulate(START, end)


@pytest.mark.fast
@given(first=st.integers(0, 360), extension=st.integers(0, 180))
def test_T_F03_0202_later_end_is_monotonic(first: int, extension: int) -> None:
    """
    id: T-F03-0202
    title: Later clock end is monotonic
    purpose: Check that an earlier stop cannot increase charge
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Ordered synthetic evaluation instants
    expected: Later time gives the same or a greater charge
    risk: HZ-04
    capability: F03
    """
    clock = Clock(TERMS, None, (), TABLE)
    early = START + timedelta(hours=first)
    late = early + timedelta(hours=extension)
    assert clock.charge(START, early).amount.amount <= clock.charge(START, late).amount.amount


@pytest.mark.fast
@given(offset=st.integers(0, 160), duration=st.integers(1, 130))
def test_T_F03_0203_verified_suspension_is_monotonic(offset: int, duration: int) -> None:
    """
    id: T-F03-0203
    title: A verified suspension cannot increase charge
    purpose: Check suspension monotonicity
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic suspension windows
    expected: Removing billable time cannot increase the charge
    risk: HZ-04
    capability: F03
    """
    left = START + timedelta(hours=offset)
    windows = (Suspension(left, left + timedelta(hours=duration), SOURCE, True),)
    clock = Clock(TERMS, None, (), TABLE)
    paused = replace(clock, suspensions=windows)
    end = START + 8 * DAY
    assert paused.charge(START, end).amount.amount <= clock.charge(START, end).amount.amount


@pytest.mark.fast
@given(split=st.integers(0, 300), partial=st.sampled_from(tuple(PartialDay)))
def test_T_F03_0204_period_partition_is_additive(split: int, partial: PartialDay) -> None:
    """
    id: T-F03-0204
    title: Adjacent periods preserve the accrued amount
    purpose: Check rounding and tier continuity across a split
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic tariff and split timestamp
    expected: The two incremental charges sum to the whole
    risk: HZ-04
    capability: F03
    """
    clock = Clock(replace(TERMS, partial=partial), None, (), TABLE)
    end = START + timedelta(hours=300)
    middle = START + timedelta(hours=split)
    first = clock.charge(START, middle)
    second = clock.charge(START, end, period_start=middle)
    assert first.amount.amount + second.amount.amount == clock.charge(START, end).amount.amount


@pytest.fixture
def clock() -> Clock:
    return Clock(TERMS, None, (), TABLE)


@pytest.fixture
def working() -> Clock:
    return Clock(replace(TERMS, basis=DayBasis.WORKING), CALENDAR, (), TABLE)


@pytest.fixture
def berlin() -> Clock:
    return Clock(replace(TERMS, zone=ZoneInfo("Europe/Berlin")), None, (), TABLE)


@pytest.fixture
def window() -> Suspension:
    left = datetime(2024, 3, 1, tzinfo=UTC)
    return Suspension(left, left + DAY, SOURCE, True)


@pytest.mark.fast
def test_T_F03_0205_zero_before_expiry(clock: Clock) -> None:
    """
    id: T-F03-0205
    title: Zero before expiry
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Zero before expiry follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, START + DAY).amount.amount == 0


@pytest.mark.fast
def test_T_F03_0206_zero_at_expiry(clock: Clock) -> None:
    """
    id: T-F03-0206
    title: Zero at expiry
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Zero at expiry follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, clock.expiry(START)).days == 0


@pytest.mark.fast
def test_T_F03_0207_first_tier_amount(clock: Clock) -> None:
    """
    id: T-F03-0207
    title: First tier amount
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: First tier amount follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, clock.expiry(START) + DAY).amount.amount == Decimal("3.50")


@pytest.mark.fast
def test_T_F03_0208_tier_edge_amount(clock: Clock) -> None:
    """
    id: T-F03-0208
    title: Tier edge amount
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Tier edge amount follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, clock.expiry(START) + 2 * DAY).amount.amount == Decimal("7.00")


@pytest.mark.fast
def test_T_F03_0209_second_tier_amount(clock: Clock) -> None:
    """
    id: T-F03-0209
    title: Second tier amount
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Second tier amount follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, clock.expiry(START) + 3 * DAY).amount.amount == Decimal("12.00")


@pytest.mark.fast
def test_T_F03_0210_last_tier_amount(clock: Clock) -> None:
    """
    id: T-F03-0210
    title: Last tier amount
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Last tier amount follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, clock.expiry(START) + 6 * DAY).amount.amount == Decimal("34.00")


@pytest.mark.fast
def test_T_F03_0211_leap_day(clock: Clock) -> None:
    """
    id: T-F03-0211
    title: Leap day
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Leap day follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.expiry(START) == datetime(2024, 3, 1, tzinfo=UTC)


@pytest.mark.fast
def test_T_F03_0212_working_holiday(working: Clock) -> None:
    """
    id: T-F03-0212
    title: Working holiday
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Working holiday follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert working.expiry(START) == datetime(2024, 3, 2, tzinfo=UTC)


@pytest.mark.fast
def test_T_F03_0213_working_weekend(working: Clock) -> None:
    """
    id: T-F03-0213
    title: Working weekend
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Working weekend follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert working.charge(START, datetime(2024, 3, 4, tzinfo=UTC)).days == 0


@pytest.mark.fast
def test_T_F03_0214_working_restart(working: Clock) -> None:
    """
    id: T-F03-0214
    title: Working restart
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Working restart follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert working.charge(START, datetime(2024, 3, 5, tzinfo=UTC)).days == 1


@pytest.mark.fast
def test_T_F03_0215_exclude_first_day(clock: Clock) -> None:
    """
    id: T-F03-0215
    title: Exclude first day
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Exclude first day follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert (
        replace(clock, terms=replace(TERMS, day_one=DayOne.EXCLUDE)).expiry(START)
        == clock.expiry(START) + DAY
    )


@pytest.mark.fast
def test_T_F03_0216_cutoff_boundary(clock: Clock) -> None:
    """
    id: T-F03-0216
    title: Cutoff boundary
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Cutoff boundary follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert replace(clock, terms=replace(TERMS, cutoff=time(17))).expiry(START) == datetime(
        2024, 2, 29, 17, tzinfo=UTC
    )


@pytest.mark.fast
def test_T_F03_0217_complete_partial(clock: Clock) -> None:
    """
    id: T-F03-0217
    title: Complete partial
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Complete partial follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert (
        replace(clock, terms=replace(TERMS, partial=PartialDay.COMPLETE))
        .charge(START, clock.expiry(START) + timedelta(hours=12))
        .days
        == 0
    )


@pytest.mark.fast
def test_T_F03_0218_prorated_partial(clock: Clock) -> None:
    """
    id: T-F03-0218
    title: Prorated partial
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Prorated partial follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert replace(clock, terms=replace(TERMS, partial=PartialDay.PRORATED)).charge(
        START, clock.expiry(START) + timedelta(hours=12)
    ).amount.amount == Decimal("1.75")


@pytest.mark.fast
def test_T_F03_0219_spring_forward(berlin: Clock) -> None:
    """
    id: T-F03-0219
    title: Spring forward
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Spring forward follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert berlin.boundary(date(2024, 4, 1)) - berlin.boundary(date(2024, 3, 31)) == timedelta(
        hours=23
    )


@pytest.mark.fast
def test_T_F03_0220_fall_back(berlin: Clock) -> None:
    """
    id: T-F03-0220
    title: Fall back
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Fall back follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert berlin.boundary(date(2024, 10, 28)) - berlin.boundary(date(2024, 10, 27)) == timedelta(
        hours=25
    )


@pytest.mark.fast
def test_T_F03_0221_exact_boundary(clock: Clock) -> None:
    """
    id: T-F03-0221
    title: Exact boundary
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Exact boundary follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.day_at(clock.boundary(date(2024, 3, 1))) == date(2024, 3, 1)


@pytest.mark.fast
def test_T_F03_0222_before_boundary(clock: Clock) -> None:
    """
    id: T-F03-0222
    title: Before boundary
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Before boundary follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.day_at(clock.boundary(date(2024, 3, 1)) - timedelta(microseconds=1)) == date(
        2024, 2, 29
    )


@pytest.mark.fast
def test_T_F03_0223_zero_free_days(clock: Clock) -> None:
    """
    id: T-F03-0223
    title: Zero free days
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Zero free days follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert replace(clock, terms=replace(TERMS, free_days=0)).expiry(START) == START


@pytest.mark.fast
def test_T_F03_0224_unverified_window(clock: Clock, window: Suspension) -> None:
    """
    id: T-F03-0224
    title: Unverified window
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Unverified window follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert replace(clock, suspensions=(replace(window, verified=False),)).expiry(
        START
    ) == clock.expiry(START)


@pytest.mark.fast
def test_T_F03_0225_overlapping_windows(clock: Clock, window: Suspension) -> None:
    """
    id: T-F03-0225
    title: Overlapping windows
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Overlapping windows follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert replace(clock, suspensions=(window, window)).suspended(START, START + 4 * DAY) == DAY


@pytest.mark.fast
def test_T_F03_0226_after_free_window(clock: Clock, window: Suspension) -> None:
    """
    id: T-F03-0226
    title: After free window
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: After free window follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert (
        replace(clock, suspensions=(window,)).charge(START, clock.expiry(START) + 2 * DAY).days == 1
    )


@pytest.mark.fast
def test_T_F03_0227_full_free_suspension(clock: Clock, window: Suspension) -> None:
    """
    id: T-F03-0227
    title: Full free suspension
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Full free suspension follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert (
        replace(
            clock,
            suspensions=(
                replace(window, start=clock.expiry(START) - DAY, end=clock.expiry(START)),
            ),
        ).expiry(START)
        == clock.expiry(START) + DAY
    )


@pytest.mark.fast
def test_T_F03_0228_fixed_offset_shift(clock: Clock) -> None:
    """
    id: T-F03-0228
    title: Fixed offset shift
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Fixed offset shift follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, START + 4 * DAY) == clock.charge(START + 4 * DAY, START + 8 * DAY)


@pytest.mark.fast
def test_T_F03_0229_validity_start() -> None:
    """
    id: T-F03-0229
    title: Validity start
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Validity start follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert TERMS.valid_at(TERMS.valid_from)


@pytest.mark.fast
def test_T_F03_0230_validity_end() -> None:
    """
    id: T-F03-0230
    title: Validity end
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Validity end follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert not TERMS.valid_at(TERMS.valid_until)


@pytest.mark.fast
def test_T_F03_0231_early_stop(clock: Clock) -> None:
    """
    id: T-F03-0231
    title: Early stop
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Early stop follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, START - DAY).days == 0


@pytest.mark.fast
def test_T_F03_0232_period_before_expiry(clock: Clock) -> None:
    """
    id: T-F03-0232
    title: Period before expiry
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Period before expiry follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, START + DAY, period_start=START).days == 0


@pytest.mark.fast
def test_T_F03_0233_period_after_end(clock: Clock) -> None:
    """
    id: T-F03-0233
    title: Period after end
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Period after end follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(START, START + 4 * DAY, period_start=START + 8 * DAY).days == 0


@pytest.mark.fast
def test_T_F03_0234_apportioned_tiers(clock: Clock) -> None:
    """
    id: T-F03-0234
    title: Apportioned tiers
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Apportioned tiers follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert clock.charge(
        START, clock.expiry(START) + 4 * DAY, period_start=clock.expiry(START) + 2 * DAY
    ).amount.amount == Decimal("10.00")


@pytest.mark.fast
def test_T_F03_0235_tariff_day_continuity(berlin: Clock) -> None:
    """
    id: T-F03-0235
    title: Tariff day continuity
    purpose: Verify the tariff clock at a defined calculation boundary
    level: fast
    requirement: P16-T01, Part 5 section 5.F03, DoD 7
    input: Synthetic versioned tariff and dated events
    expected: Tariff day continuity follows the recorded tariff
    risk: HZ-04
    capability: F03
    """
    assert berlin.day_at(berlin.boundary(date(2024, 3, 31)) + timedelta(hours=22)) == date(
        2024, 3, 31
    )


@pytest.mark.fast
def test_T_F03_0520_calendar_rejects_no_working_days() -> None:
    """
    id: T-F03-0520
    title: Calendar rejects no working days
    purpose: Calendar rejects no working days
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Calendar rejects no working days
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="working weekdays"):
        replace(CALENDAR, weekend=frozenset(range(7)))


@pytest.mark.fast
def test_T_F03_0521_suspension_rejects_empty_interval() -> None:
    """
    id: T-F03-0521
    title: Suspension rejects empty interval
    purpose: Suspension rejects empty interval
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Suspension rejects empty interval
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="ordered period"):
        Suspension(START, START, SOURCE, True)


@pytest.mark.fast
def test_T_F03_0522_tier_rejects_negative_rate() -> None:
    """
    id: T-F03-0522
    title: Tier rejects negative rate
    purpose: Tier rejects negative rate
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Tier rejects negative rate
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="nonnegative"):
        Tier(None, Decimal(-1))


@pytest.mark.fast
def test_T_F03_0523_tier_rejects_zero_edge() -> None:
    """
    id: T-F03-0523
    title: Tier rejects zero edge
    purpose: Tier rejects zero edge
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Tier rejects zero edge
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="positive day"):
        Tier(0, Decimal(1))


@pytest.mark.fast
def test_T_F03_0524_terms_reject_reversed_validity() -> None:
    """
    id: T-F03-0524
    title: Terms reject reversed validity
    purpose: Terms reject reversed validity
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Terms reject reversed validity
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="invalid tariff"):
        replace(TERMS, valid_until=TERMS.valid_from)


@pytest.mark.fast
def test_T_F03_0525_clock_requires_day_rule() -> None:
    """
    id: T-F03-0525
    title: Clock requires day rule
    purpose: Clock requires day rule
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Clock requires day rule
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="day rule"):
        Clock(replace(TERMS, cutoff=None), None, (), TABLE)


@pytest.mark.fast
def test_T_F03_0526_clock_rejects_calendar_mismatch() -> None:
    """
    id: T-F03-0526
    title: Clock rejects calendar mismatch
    purpose: Clock rejects calendar mismatch
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Clock rejects calendar mismatch
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="working calendar"):
        Clock(replace(TERMS, basis=DayBasis.WORKING, calendar_id="other"), CALENDAR, (), TABLE)


@pytest.mark.fast
def test_T_F03_0527_expiry_horizon_is_bounded() -> None:
    """
    id: T-F03-0527
    title: Expiry horizon is bounded
    purpose: Expiry horizon is bounded
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Expiry horizon is bounded
    risk: HZ-04
    capability: F03
    """
    pause = Suspension(START - DAY, START + 40_000 * DAY, SOURCE, True)
    with pytest.raises(ValueError, match="free period"):
        Clock(TERMS, None, (pause,), TABLE).expiry(START)


@pytest.mark.fast
def test_T_F03_0528_reference_horizon_is_bounded() -> None:
    """
    id: T-F03-0528
    title: Reference horizon is bounded
    purpose: Reference horizon is bounded
    level: fast
    requirement: P16-T09, Part 5 section 5.F03, DoD 12
    input: Versioned synthetic case and referenced packs
    expected: Reference horizon is bounded
    risk: HZ-04
    capability: F03
    """
    with pytest.raises(ValueError, match="charge period"):
        Clock(TERMS, None, (), TABLE).simulate(START, START + 40_000 * DAY)


@pytest.mark.fast
def test_T_F03_0530_inclusive_terms_count_at_expiry(clock: Clock) -> None:
    """
    id: T-F03-0530
    title: Explicit inclusive terms count the tariff boundary
    purpose: Compare the inclusive and exclusive period rules
    level: fast
    requirement: P16-T09, F03-S04, DoD 7
    input: Two versions of a synthetic tariff with different partial-day rules
    expected: Inclusive terms charge at the exact boundary
    risk: HZ-04
    capability: F03
    """
    expiry = clock.expiry(START)
    inclusive = replace(clock, terms=replace(TERMS, partial=PartialDay.STARTED_INCLUSIVE))
    assert inclusive.charge(START, expiry).days == 1
    assert inclusive.charge(START, expiry - timedelta(microseconds=1)).days == 0
    assert clock.charge(START, expiry).days == 0

"""Validate F03 scenarios, closed reasons, adversarial inputs, replay and views."""

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypedDict, cast

import pytest
from pydantic import ValidationError

from capabilities.f03 import ClockReport, Reason, State
from capabilities.f03.registration import INPUT, OUTPUT, register, render_timeline
from kernel.hashing import domain_hash

ROOT = Path("data/scenarios/f03")


class ClockRow(TypedDict):
    events: list[dict[str, object]]
    terms: dict[str, object]


class ClockPayload(TypedDict):
    clocks: list[ClockRow]


def case(index: int = 1) -> tuple[dict[str, object], ClockPayload, datetime]:
    data = json.loads((ROOT / f"F03-S{index:02}.json").read_text())
    inputs = dict(data["inputs"])
    at = datetime.fromisoformat(inputs.pop("evaluation_time"))
    payload = cast(ClockPayload, inputs)
    return data, payload, at


def check(index: int) -> None:
    scenario, inputs, at = case(index)
    result, evidence = register(INPUT.validate_python(inputs), at)
    assert result.decision.name == scenario["outcome"]
    assert sorted({r.reason for r in result.clocks}) == scenario["reason_codes"]
    assert {k: str(v) for k, v in result.totals.items()} == scenario["totals"]
    assert evidence["clock_records"]


def clock_case(index: int = 1, **overrides: object) -> ClockReport:
    _, inputs, at = case(index)
    cast(dict[str, object], inputs["clocks"][0]).update(overrides)
    return register(INPUT.validate_python(inputs), at)[0].clocks[0]


def mutate_clock(field: str, value: object, *, term: bool = False) -> ClockReport:
    _, inputs, at = case()
    row = inputs["clocks"][0]
    (row["terms"] if term else cast(dict[str, object], row))[field] = value
    return register(INPUT.validate_python(inputs), at)[0].clocks[0]


def invalid_event(value: str) -> None:
    _, inputs, _ = case()
    inputs["clocks"][0]["events"][0]["instant"] = value
    with pytest.raises(ValidationError):
        INPUT.validate_python(inputs)


def replay(index: int) -> None:
    _, inputs, at = case(index)
    data = INPUT.validate_python(inputs)
    result, evidence = register(data, at)
    rebuilt = INPUT.validate_json(INPUT.dump_json(data))
    again, repeats = register(rebuilt, at)
    assert result == again and evidence == repeats
    assert evidence["output_hash"] == domain_hash(
        "ctc/payload/v1", OUTPUT.dump_python(result, mode="json")
    )
    clock_records = evidence["clock_records"]
    assert isinstance(clock_records, list) and len(clock_records) == len(result.clocks)


def view(index: int = 1) -> str:
    _, inputs, at = case(index)
    result, _ = register(INPUT.validate_python(inputs), at)
    return render_timeline(result)


@pytest.mark.fast
def test_T_F03_0001_scenario_01() -> None:
    """
    id: T-F03-0001
    title: Scenario 01
    purpose: Scenario 01
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S01, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 01
    risk: HZ-04
    capability: F03
    """
    check(1)


@pytest.mark.fast
def test_T_F03_0002_scenario_02() -> None:
    """
    id: T-F03-0002
    title: Scenario 02
    purpose: Scenario 02
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S02, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 02
    risk: HZ-04
    capability: F03
    """
    check(2)


@pytest.mark.fast
def test_T_F03_0003_scenario_03() -> None:
    """
    id: T-F03-0003
    title: Scenario 03
    purpose: Scenario 03
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S03, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 03
    risk: HZ-04
    capability: F03
    """
    check(3)


@pytest.mark.fast
def test_T_F03_0004_scenario_04() -> None:
    """
    id: T-F03-0004
    title: Scenario 04
    purpose: Scenario 04
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S04, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 04
    risk: HZ-04
    capability: F03
    """
    check(4)


@pytest.mark.fast
def test_T_F03_0005_scenario_05() -> None:
    """
    id: T-F03-0005
    title: Scenario 05
    purpose: Scenario 05
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S05, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 05
    risk: HZ-04
    capability: F03
    """
    check(5)


@pytest.mark.fast
def test_T_F03_0006_scenario_06() -> None:
    """
    id: T-F03-0006
    title: Scenario 06
    purpose: Scenario 06
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S06, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 06
    risk: HZ-04
    capability: F03
    """
    check(6)


@pytest.mark.fast
def test_T_F03_0007_scenario_07() -> None:
    """
    id: T-F03-0007
    title: Scenario 07
    purpose: Scenario 07
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S07, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 07
    risk: HZ-04
    capability: F03
    """
    check(7)


@pytest.mark.fast
def test_T_F03_0008_scenario_08() -> None:
    """
    id: T-F03-0008
    title: Scenario 08
    purpose: Scenario 08
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S08, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 08
    risk: HZ-04
    capability: F03
    """
    check(8)


@pytest.mark.fast
def test_T_F03_0009_scenario_09() -> None:
    """
    id: T-F03-0009
    title: Scenario 09
    purpose: Scenario 09
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S09, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 09
    risk: HZ-04
    capability: F03
    """
    check(9)


@pytest.mark.fast
def test_T_F03_0010_scenario_10() -> None:
    """
    id: T-F03-0010
    title: Scenario 10
    purpose: Scenario 10
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S10, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 10
    risk: HZ-04
    capability: F03
    """
    check(10)


@pytest.mark.fast
def test_T_F03_0011_scenario_11() -> None:
    """
    id: T-F03-0011
    title: Scenario 11
    purpose: Scenario 11
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S11, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 11
    risk: HZ-04
    capability: F03
    """
    check(11)


@pytest.mark.fast
def test_T_F03_0012_scenario_12() -> None:
    """
    id: T-F03-0012
    title: Scenario 12
    purpose: Scenario 12
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S12, DoD 6
    input: Versioned synthetic tariff and movement facts
    expected: Scenario 12
    risk: HZ-04
    capability: F03
    """
    check(12)


@pytest.mark.fast
def test_T_F03_0101_within_free() -> None:
    """
    id: T-F03-0101
    title: Within free
    purpose: Within free
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Within free
    risk: HZ-04
    capability: F03
    """
    assert clock_case().reason is Reason.WITHIN_FREE


@pytest.mark.fast
def test_T_F03_0102_stopped() -> None:
    """
    id: T-F03-0102
    title: Stopped
    purpose: Stopped
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Stopped
    risk: HZ-04
    capability: F03
    """
    _, inputs, at = case()
    inputs["clocks"][0]["events"].append(
        dict(inputs["clocks"][0]["events"][0], kind="GATED_OUT_FULL", instant=at.isoformat())
    )
    result, _ = register(INPUT.validate_python(inputs), at)
    assert result.clocks[0].reason is Reason.STOPPED


@pytest.mark.fast
def test_T_F03_0103_ending() -> None:
    """
    id: T-F03-0103
    title: Ending
    purpose: Ending
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Ending
    risk: HZ-04
    capability: F03
    """
    assert clock_case(2).reason is Reason.ENDING


@pytest.mark.fast
def test_T_F03_0104_accruing() -> None:
    """
    id: T-F03-0104
    title: Accruing
    purpose: Accruing
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Accruing
    risk: HZ-04
    capability: F03
    """
    assert clock_case(3).reason is Reason.ACCRUING


@pytest.mark.fast
def test_T_F03_0105_order_invalid() -> None:
    """
    id: T-F03-0105
    title: Order invalid
    purpose: Order invalid
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Order invalid
    risk: HZ-04
    capability: F03
    """
    assert clock_case(7).reason is Reason.ORDER


@pytest.mark.fast
def test_T_F03_0106_missing_event() -> None:
    """
    id: T-F03-0106
    title: Missing event
    purpose: Missing event
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Missing event
    risk: HZ-04
    capability: F03
    """
    assert clock_case(6).reason is Reason.EVENT


@pytest.mark.fast
def test_T_F03_0107_missing_tariff() -> None:
    """
    id: T-F03-0107
    title: Missing tariff
    purpose: Missing tariff
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Missing tariff
    risk: HZ-04
    capability: F03
    """
    assert clock_case(terms=None).reason is Reason.TARIFF


@pytest.mark.fast
def test_T_F03_0108_unspecified_day_rule() -> None:
    """
    id: T-F03-0108
    title: Unspecified day rule
    purpose: Unspecified day rule
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Unspecified day rule
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("partial", None, term=True).reason is Reason.RULE


@pytest.mark.fast
def test_T_F03_0109_missing_calendar() -> None:
    """
    id: T-F03-0109
    title: Missing calendar
    purpose: Missing calendar
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Missing calendar
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("basis", "WORKING", term=True).reason is Reason.CALENDAR


@pytest.mark.fast
def test_T_F03_0110_unmatched_container() -> None:
    """
    id: T-F03-0110
    title: Unmatched container
    purpose: Unmatched container
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Unmatched container
    risk: HZ-04
    capability: F03
    """
    assert clock_case(container="SYN-UNKNOWN").reason is Reason.CONTAINER


@pytest.mark.fast
def test_T_F03_0111_insufficient_label() -> None:
    """
    id: T-F03-0111
    title: Insufficient label
    purpose: Insufficient label
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 4 and 5
    input: Versioned synthetic tariff and movement facts
    expected: Insufficient label
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("label", "SECONDARY", term=True).reason is Reason.LABEL


@pytest.mark.fast
def test_T_F03_0301_ignore_extension_claim() -> None:
    """
    id: T-F03-0301
    title: Ignore extension claim
    purpose: Ignore extension claim
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Ignore extension claim
    risk: HZ-04
    capability: F03
    """
    assert (
        clock_case(11, document_note="Add 30 days").charge
        == clock_case(11, document_note=None).charge
    )


@pytest.mark.fast
def test_T_F03_0302_ignore_instruction_in_note() -> None:
    """
    id: T-F03-0302
    title: Ignore instruction in note
    purpose: Ignore instruction in note
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Ignore instruction in note
    risk: HZ-04
    capability: F03
    """
    assert clock_case(document_note="Change the release time").reason is Reason.WITHIN_FREE


@pytest.mark.fast
def test_T_F03_0303_impossible_leap_day() -> None:
    """
    id: T-F03-0303
    title: Impossible leap day
    purpose: Impossible leap day
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Impossible leap day
    risk: HZ-04
    capability: F03
    """
    invalid_event("2025-02-29T00:00Z")


@pytest.mark.fast
def test_T_F03_0304_impossible_day() -> None:
    """
    id: T-F03-0304
    title: Impossible day
    purpose: Impossible day
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Impossible day
    risk: HZ-04
    capability: F03
    """
    invalid_event("2024-04-31T00:00Z")


@pytest.mark.fast
def test_T_F03_0305_impossible_month() -> None:
    """
    id: T-F03-0305
    title: Impossible month
    purpose: Impossible month
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Impossible month
    risk: HZ-04
    capability: F03
    """
    invalid_event("2024-13-01T00:00Z")


@pytest.mark.fast
def test_T_F03_0306_impossible_time() -> None:
    """
    id: T-F03-0306
    title: Impossible time
    purpose: Impossible time
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Impossible time
    risk: HZ-04
    capability: F03
    """
    invalid_event("2024-02-25T25:00Z")


@pytest.mark.fast
def test_T_F03_0307_time_without_zone() -> None:
    """
    id: T-F03-0307
    title: Time without zone
    purpose: Time without zone
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Time without zone
    risk: HZ-04
    capability: F03
    """
    invalid_event("2024-02-25T00:00")


@pytest.mark.fast
def test_T_F03_0308_wrong_year_syntax() -> None:
    """
    id: T-F03-0308
    title: Wrong year syntax
    purpose: Wrong year syntax
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Wrong year syntax
    risk: HZ-04
    capability: F03
    """
    invalid_event("02024-02-25T00:00Z")


@pytest.mark.fast
def test_T_F03_0309_empty_time() -> None:
    """
    id: T-F03-0309
    title: Empty time
    purpose: Empty time
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Empty time
    risk: HZ-04
    capability: F03
    """
    invalid_event("")


@pytest.mark.fast
def test_T_F03_0310_text_as_timestamp() -> None:
    """
    id: T-F03-0310
    title: Text as timestamp
    purpose: Text as timestamp
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Text as timestamp
    risk: HZ-04
    capability: F03
    """
    invalid_event("yesterday")


@pytest.mark.fast
def test_T_F03_0311_reversed_movements() -> None:
    """
    id: T-F03-0311
    title: Reversed movements
    purpose: Reversed movements
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Reversed movements
    risk: HZ-04
    capability: F03
    """
    assert clock_case(7).reason is Reason.ORDER


@pytest.mark.fast
def test_T_F03_0312_duplicate_movements() -> None:
    """
    id: T-F03-0312
    title: Duplicate movements
    purpose: Duplicate movements
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Duplicate movements
    risk: HZ-04
    capability: F03
    """
    _, inputs, at = case()
    data = INPUT.validate_python(inputs)
    clock = data.clocks[0]
    out, _ = register(replace(data, clocks=(replace(clock, events=clock.events * 2),)), at)
    assert out.clocks[0].reason is Reason.ORDER


@pytest.mark.fast
def test_T_F03_0313_unverified_tariff() -> None:
    """
    id: T-F03-0313
    title: Unverified tariff
    purpose: Unverified tariff
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Unverified tariff
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("verified", False, term=True).reason is Reason.TARIFF


@pytest.mark.fast
def test_T_F03_0314_expired_tariff() -> None:
    """
    id: T-F03-0314
    title: Expired tariff
    purpose: Expired tariff
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Expired tariff
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("valid_until", "2024-02-26T12:00Z", term=True).reason is Reason.TARIFF


@pytest.mark.fast
def test_T_F03_0315_wrong_currency() -> None:
    """
    id: T-F03-0315
    title: Wrong currency
    purpose: Wrong currency
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Wrong currency
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("currency", "ZZZ", term=True).reason is Reason.TARIFF


@pytest.mark.fast
def test_T_F03_0316_required_cutoff() -> None:
    """
    id: T-F03-0316
    title: Required cutoff
    purpose: Required cutoff
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Required cutoff
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("cutoff", None, term=True).reason is Reason.RULE


@pytest.mark.fast
def test_T_F03_0317_required_day_one() -> None:
    """
    id: T-F03-0317
    title: Required day one
    purpose: Required day one
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Required day one
    risk: HZ-04
    capability: F03
    """
    assert mutate_clock("day_one", None, term=True).reason is Reason.RULE


@pytest.mark.fast
def test_T_F03_0318_confusable_container() -> None:
    """
    id: T-F03-0318
    title: Confusable container
    purpose: Confusable container
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Confusable container
    risk: HZ-04
    capability: F03
    """
    assert clock_case(container="SYN-CОNT-1").reason is Reason.CONTAINER


@pytest.mark.fast
def test_T_F03_0319_overlapping_suspensions() -> None:
    """
    id: T-F03-0319
    title: Overlapping suspensions
    purpose: Overlapping suspensions
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Overlapping suspensions
    risk: HZ-04
    capability: F03
    """
    _, inputs, at = case(12)
    data = INPUT.validate_python(inputs)
    clock = data.clocks[0]
    out, _ = register(
        replace(data, clocks=(replace(clock, suspensions=clock.suspensions * 2),)), at
    )
    assert out.clocks[0].suspended == timedelta(days=3)
    assert out.clocks[0].charge == clock_case(12).charge


@pytest.mark.fast
def test_T_F03_0320_huge_period_fails_closed() -> None:
    """
    id: T-F03-0320
    title: Huge period fails closed
    purpose: Huge period fails closed
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 11
    input: Versioned synthetic tariff and movement facts
    expected: Huge period fails closed
    risk: HZ-04
    capability: F03
    """
    _, inputs, _ = case()
    data = INPUT.validate_python(inputs)
    item = data.clocks[0]
    assert item.terms is not None
    at = datetime(2300, 1, 1, tzinfo=UTC)
    terms = replace(item.terms, valid_until=at + timedelta(days=1))
    result, _ = register(replace(data, clocks=(replace(item, terms=terms),)), at)
    assert result.clocks[0].state is State.UNKNOWN


@pytest.mark.fast
def test_T_F03_0401_replay_scenario_01() -> None:
    """
    id: T-F03-0401
    title: Replay scenario 01
    purpose: Replay scenario 01
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S01, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 01
    risk: HZ-04
    capability: F03
    """
    replay(1)


@pytest.mark.fast
def test_T_F03_0402_replay_scenario_02() -> None:
    """
    id: T-F03-0402
    title: Replay scenario 02
    purpose: Replay scenario 02
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S02, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 02
    risk: HZ-04
    capability: F03
    """
    replay(2)


@pytest.mark.fast
def test_T_F03_0403_replay_scenario_03() -> None:
    """
    id: T-F03-0403
    title: Replay scenario 03
    purpose: Replay scenario 03
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S03, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 03
    risk: HZ-04
    capability: F03
    """
    replay(3)


@pytest.mark.fast
def test_T_F03_0404_replay_scenario_04() -> None:
    """
    id: T-F03-0404
    title: Replay scenario 04
    purpose: Replay scenario 04
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S04, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 04
    risk: HZ-04
    capability: F03
    """
    replay(4)


@pytest.mark.fast
def test_T_F03_0405_replay_scenario_05() -> None:
    """
    id: T-F03-0405
    title: Replay scenario 05
    purpose: Replay scenario 05
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S05, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 05
    risk: HZ-04
    capability: F03
    """
    replay(5)


@pytest.mark.fast
def test_T_F03_0406_replay_scenario_06() -> None:
    """
    id: T-F03-0406
    title: Replay scenario 06
    purpose: Replay scenario 06
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S06, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 06
    risk: HZ-04
    capability: F03
    """
    replay(6)


@pytest.mark.fast
def test_T_F03_0407_replay_scenario_07() -> None:
    """
    id: T-F03-0407
    title: Replay scenario 07
    purpose: Replay scenario 07
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S07, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 07
    risk: HZ-04
    capability: F03
    """
    replay(7)


@pytest.mark.fast
def test_T_F03_0408_replay_scenario_08() -> None:
    """
    id: T-F03-0408
    title: Replay scenario 08
    purpose: Replay scenario 08
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S08, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 08
    risk: HZ-04
    capability: F03
    """
    replay(8)


@pytest.mark.fast
def test_T_F03_0409_replay_scenario_09() -> None:
    """
    id: T-F03-0409
    title: Replay scenario 09
    purpose: Replay scenario 09
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S09, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 09
    risk: HZ-04
    capability: F03
    """
    replay(9)


@pytest.mark.fast
def test_T_F03_0410_replay_scenario_10() -> None:
    """
    id: T-F03-0410
    title: Replay scenario 10
    purpose: Replay scenario 10
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, F03-S10, DoD 8
    input: Versioned synthetic tariff and movement facts
    expected: Replay scenario 10
    risk: HZ-04
    capability: F03
    """
    replay(10)


@pytest.mark.fast
def test_T_F03_0501_stable_anchor() -> None:
    """
    id: T-F03-0501
    title: Stable anchor
    purpose: Stable anchor
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Stable anchor
    risk: HZ-04
    capability: F03
    """
    assert 'id="f03"' in view()


@pytest.mark.fast
def test_T_F03_0502_event_citations() -> None:
    """
    id: T-F03-0502
    title: Event citations
    purpose: Event citations
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Event citations
    risk: HZ-04
    capability: F03
    """
    assert "DISCHARGED" in view() and "SRC-SYNTHETIC-F03" in view()


@pytest.mark.fast
def test_T_F03_0503_free_expiry_text() -> None:
    """
    id: T-F03-0503
    title: Free expiry text
    purpose: Free expiry text
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Free expiry text
    risk: HZ-04
    capability: F03
    """
    assert "Free period ends" in view()


@pytest.mark.fast
def test_T_F03_0504_free_bar_has_text() -> None:
    """
    id: T-F03-0504
    title: Free bar has text
    purpose: Free bar has text
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Free bar has text
    risk: HZ-04
    capability: F03
    """
    assert "clock-bar free" in view() and "Remaining" in view()


@pytest.mark.fast
def test_T_F03_0505_accrual_bar_has_text() -> None:
    """
    id: T-F03-0505
    title: Accrual bar has text
    purpose: Accrual bar has text
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Accrual bar has text
    risk: HZ-04
    capability: F03
    """
    assert "clock-bar accrual" in view(3) and "34.00 USD" in view(3)


@pytest.mark.fast
def test_T_F03_0506_suspension_text() -> None:
    """
    id: T-F03-0506
    title: Suspension text
    purpose: Suspension text
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Suspension text
    risk: HZ-04
    capability: F03
    """
    assert "Verified suspensions" in view(12) and "2024-03-01" in view(12)


@pytest.mark.fast
def test_T_F03_0507_projection_horizons() -> None:
    """
    id: T-F03-0507
    title: Projection horizons
    purpose: Projection horizons
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Projection horizons
    risk: HZ-04
    capability: F03
    """
    assert all(f"+{day} days" in view(2) for day in (1, 3, 7))


@pytest.mark.fast
def test_T_F03_0508_operational_action_text() -> None:
    """
    id: T-F03-0508
    title: Operational action text
    purpose: Operational action text
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Operational action text
    risk: HZ-04
    capability: F03
    """
    assert "GATED_OUT_FULL by" in view(2) and "projected savings" in view(2)


@pytest.mark.fast
def test_T_F03_0509_unknown_without_charge() -> None:
    """
    id: T-F03-0509
    title: Unknown without charge
    purpose: Unknown without charge
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Unknown without charge
    risk: HZ-04
    capability: F03
    """
    assert "UNKNOWN" in view(6) and "Accrual" not in view(6)


@pytest.mark.fast
def test_T_F03_0510_contradiction_requests_review() -> None:
    """
    id: T-F03-0510
    title: Contradiction requests review
    purpose: Contradiction requests review
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Contradiction requests review
    risk: HZ-04
    capability: F03
    """
    assert "Review recorded milestones" in view(7)


@pytest.mark.fast
def test_T_F03_0511_extensions_absent_from_view() -> None:
    """
    id: T-F03-0511
    title: Extensions absent from view
    purpose: Extensions absent from view
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: Extensions absent from view
    risk: HZ-04
    capability: F03
    """
    assert "extended 30 days" not in view(11)


@pytest.mark.fast
def test_T_F03_0512_no_suggested_record_edits() -> None:
    """
    id: T-F03-0512
    title: No suggested record edits
    purpose: No suggested record edits
    level: fast
    requirement: P16-T02, Part 5 section 5.F03, DoD 9 and 10
    input: Versioned synthetic tariff and movement facts
    expected: No suggested record edits
    risk: HZ-04
    capability: F03
    """
    assert all(
        not any(term in view(n).lower() for term in ("backdate", "change the recorded"))
        for n in range(1, 13)
    )

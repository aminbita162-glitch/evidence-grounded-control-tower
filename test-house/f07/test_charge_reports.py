"""Verify F07 scenario decisions, protective cases, replay and dossier formats."""

import json
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from capabilities.f07 import Classification, Reason, evaluate
from capabilities.f07.registration import INPUT, OUTPUT, ChargeReport, register, render_audit
from capabilities.l01.registration import register as l01
from kernel.hashing import domain_hash
from kernel.lib.money import CurrencyTable

_ROOT = Path("data/scenarios/f07")


def fixture(index: int) -> tuple[dict[str, object], dict[str, object], datetime]:
    expected = json.loads((_ROOT / f"F07-S{index:02d}.json").read_text())
    inputs = dict(expected["inputs"])
    at = datetime.fromisoformat(inputs.pop("evaluation_time"))
    return expected, inputs, at


def result(index: int = 1, **updates: object) -> ChargeReport:
    _, inputs, at = fixture(index)
    inputs.update(updates)
    return register(INPUT.validate_python(inputs), at)[0]


def line_case(index: int = 1, row: int = 0, /, **updates: object) -> ChargeReport:
    _, inputs, at = fixture(index)
    audit = cast(dict[str, object], inputs["invoice"])
    bill = cast(dict[str, object], audit["invoice"])
    cast(list[dict[str, object]], bill["lines"])[row].update(updates)
    return register(INPUT.validate_python(inputs), at)[0]


def reject(**updates: object) -> None:
    with pytest.raises(ValidationError):
        line_case(**updates)


def missing_match() -> tuple[Reason, ...]:
    _, inputs, at = fixture(1)
    data = INPUT.validate_python(inputs)
    audit, _ = l01(data.invoice, at)
    return evaluate(
        data.invoice.invoice,
        replace(audit, matches=()),
        data.clocks,
        canonical_containers=data.canonical_containers,
        currencies=CurrencyTable(data.invoice.currencies, data.invoice.currency_source),
        at=at,
        synthetic=True,
    ).reason_codes


def check(index: int) -> None:
    expected, _, _ = fixture(index)
    actual = result(index)
    assert actual.outcome.name == expected["outcome"]
    assert set(actual.reason_codes) == set(cast(list[str], expected["reason_codes"]))


def replay(index: int) -> None:
    _, inputs, at = fixture(index)
    data = INPUT.validate_python(inputs)
    actual, evidence = register(data, at)
    assert register(INPUT.validate_json(INPUT.dump_json(data)), at) == (actual, evidence)
    assert evidence["output_hash"] == domain_hash(
        "ctc/payload/v1", OUTPUT.dump_python(actual, mode="json")
    )
    assert actual.dossier.digest == evidence["dossier_hash"]


def view(index: int = 1) -> str:
    return render_audit(result(index))


@pytest.mark.fast
def test_T_F07_0001_scenario_01() -> None:
    """
    id: T-F07-0001
    title: Scenario 01
    purpose: Scenario 01
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S01, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 01
    risk: HZ-03
    capability: F07
    """
    check(1)


@pytest.mark.fast
def test_T_F07_0002_scenario_02() -> None:
    """
    id: T-F07-0002
    title: Scenario 02
    purpose: Scenario 02
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S02, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 02
    risk: HZ-03
    capability: F07
    """
    check(2)


@pytest.mark.fast
def test_T_F07_0003_scenario_03() -> None:
    """
    id: T-F07-0003
    title: Scenario 03
    purpose: Scenario 03
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S03, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 03
    risk: HZ-03
    capability: F07
    """
    check(3)


@pytest.mark.fast
def test_T_F07_0004_scenario_04() -> None:
    """
    id: T-F07-0004
    title: Scenario 04
    purpose: Scenario 04
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S04, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 04
    risk: HZ-03
    capability: F07
    """
    check(4)


@pytest.mark.fast
def test_T_F07_0005_scenario_05() -> None:
    """
    id: T-F07-0005
    title: Scenario 05
    purpose: Scenario 05
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S05, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 05
    risk: HZ-03
    capability: F07
    """
    check(5)


@pytest.mark.fast
def test_T_F07_0006_scenario_06() -> None:
    """
    id: T-F07-0006
    title: Scenario 06
    purpose: Scenario 06
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S06, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 06
    risk: HZ-03
    capability: F07
    """
    check(6)


@pytest.mark.fast
def test_T_F07_0007_scenario_07() -> None:
    """
    id: T-F07-0007
    title: Scenario 07
    purpose: Scenario 07
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S07, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 07
    risk: HZ-03
    capability: F07
    """
    check(7)


@pytest.mark.fast
def test_T_F07_0008_scenario_08() -> None:
    """
    id: T-F07-0008
    title: Scenario 08
    purpose: Scenario 08
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S08, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 08
    risk: HZ-03
    capability: F07
    """
    check(8)


@pytest.mark.fast
def test_T_F07_0009_scenario_09() -> None:
    """
    id: T-F07-0009
    title: Scenario 09
    purpose: Scenario 09
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S09, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 09
    risk: HZ-03
    capability: F07
    """
    check(9)


@pytest.mark.fast
def test_T_F07_0010_scenario_10() -> None:
    """
    id: T-F07-0010
    title: Scenario 10
    purpose: Scenario 10
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S10, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 10
    risk: HZ-03
    capability: F07
    """
    check(10)


@pytest.mark.fast
def test_T_F07_0011_scenario_11() -> None:
    """
    id: T-F07-0011
    title: Scenario 11
    purpose: Scenario 11
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S11, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 11
    risk: HZ-03
    capability: F07
    """
    check(11)


@pytest.mark.fast
def test_T_F07_0101_matched() -> None:
    """
    id: T-F07-0101
    title: Matched
    purpose: Matched
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Matched
    risk: HZ-03
    capability: F07
    """
    assert Reason.MATCH in result(1).reason_codes


@pytest.mark.fast
def test_T_F07_0102_undercharge() -> None:
    """
    id: T-F07-0102
    title: Undercharge
    purpose: Undercharge
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Undercharge
    risk: HZ-03
    capability: F07
    """
    assert Reason.UNDERCHARGE in result(7).reason_codes


@pytest.mark.fast
def test_T_F07_0103_flat_charge() -> None:
    """
    id: T-F07-0103
    title: Flat charge
    purpose: Flat charge
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Flat charge
    risk: HZ-03
    capability: F07
    """
    assert Reason.OUT_OF_SCOPE in result(11).reason_codes


@pytest.mark.fast
def test_T_F07_0104_duplicate() -> None:
    """
    id: T-F07-0104
    title: Duplicate
    purpose: Duplicate
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Duplicate
    risk: HZ-03
    capability: F07
    """
    assert Reason.DUPLICATE in result(2).reason_codes


@pytest.mark.fast
def test_T_F07_0105_not_billable() -> None:
    """
    id: T-F07-0105
    title: Not billable
    purpose: Not billable
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Not billable
    risk: HZ-03
    capability: F07
    """
    assert Reason.PERIOD in result(3).reason_codes


@pytest.mark.fast
def test_T_F07_0106_different_effective_rate() -> None:
    """
    id: T-F07-0106
    title: Different effective rate
    purpose: Different effective rate
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Different effective rate
    risk: HZ-03
    capability: F07
    """
    assert Reason.RATE in result(4).reason_codes


@pytest.mark.fast
def test_T_F07_0107_day_count() -> None:
    """
    id: T-F07-0107
    title: Day count
    purpose: Day count
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Day count
    risk: HZ-03
    capability: F07
    """
    assert (
        Reason.DAYS in line_case(quantity={"value": "3", "unit": "day"}, amount="15").reason_codes
    )


@pytest.mark.fast
def test_T_F07_0108_arithmetic() -> None:
    """
    id: T-F07-0108
    title: Arithmetic
    purpose: Arithmetic
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Arithmetic
    risk: HZ-03
    capability: F07
    """
    assert Reason.ARITHMETIC in line_case(amount="11").reason_codes


@pytest.mark.fast
def test_T_F07_0109_unsupported_tariff() -> None:
    """
    id: T-F07-0109
    title: Unsupported tariff
    purpose: Unsupported tariff
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Unsupported tariff
    risk: HZ-03
    capability: F07
    """
    assert Reason.UNSUPPORTED in result(5).reason_codes


@pytest.mark.fast
def test_T_F07_0110_ambiguous_tariff() -> None:
    """
    id: T-F07-0110
    title: Ambiguous tariff
    purpose: Ambiguous tariff
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Ambiguous tariff
    risk: HZ-03
    capability: F07
    """
    assert Reason.AMBIGUOUS in result(6).reason_codes


@pytest.mark.fast
def test_T_F07_0111_clock_missing() -> None:
    """
    id: T-F07-0111
    title: Clock missing
    purpose: Clock missing
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Clock missing
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in result(8).reason_codes


@pytest.mark.fast
def test_T_F07_0112_matching_missing() -> None:
    """
    id: T-F07-0112
    title: Matching missing
    purpose: Matching missing
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Matching missing
    risk: HZ-03
    capability: F07
    """
    assert Reason.MATCHING in missing_match()


@pytest.mark.fast
def test_T_F07_0113_label_insufficient() -> None:
    """
    id: T-F07-0113
    title: Label insufficient
    purpose: Label insufficient
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Label insufficient
    risk: HZ-03
    capability: F07
    """
    assert Reason.LABEL in line_case(label="SECONDARY").reason_codes


@pytest.mark.fast
def test_T_F07_0301_overlapping_periods() -> None:
    """
    id: T-F07-0301
    title: Overlapping periods
    purpose: Overlapping periods
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Overlapping periods
    risk: HZ-03
    capability: F07
    """
    assert Reason.DUPLICATE in result(2).reason_codes


@pytest.mark.fast
def test_T_F07_0302_negative_amount() -> None:
    """
    id: T-F07-0302
    title: Negative amount
    purpose: Negative amount
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative amount
    risk: HZ-03
    capability: F07
    """
    reject(amount="-1")


@pytest.mark.fast
def test_T_F07_0303_negative_rate() -> None:
    """
    id: T-F07-0303
    title: Negative rate
    purpose: Negative rate
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative rate
    risk: HZ-03
    capability: F07
    """
    reject(rate="-1")


@pytest.mark.fast
def test_T_F07_0304_negative_days() -> None:
    """
    id: T-F07-0304
    title: Negative days
    purpose: Negative days
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative days
    risk: HZ-03
    capability: F07
    """
    reject(quantity={"value": "-1", "unit": "day"})


@pytest.mark.fast
def test_T_F07_0305_tiny_duplicate_difference() -> None:
    """
    id: T-F07-0305
    title: Tiny duplicate difference
    purpose: Tiny duplicate difference
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Tiny duplicate difference
    risk: HZ-03
    capability: F07
    """
    assert Reason.DUPLICATE in line_case(2, 1, amount="10.01").reason_codes


@pytest.mark.fast
def test_T_F07_0306_currency_mismatch() -> None:
    """
    id: T-F07-0306
    title: Currency mismatch
    purpose: Currency mismatch
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Currency mismatch
    risk: HZ-03
    capability: F07
    """
    assert Reason.UNSUPPORTED in line_case(currency="EUR").reason_codes


@pytest.mark.fast
def test_T_F07_0307_unknown_currency() -> None:
    """
    id: T-F07-0307
    title: Unknown currency
    purpose: Unknown currency
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Unknown currency
    risk: HZ-03
    capability: F07
    """
    assert Reason.UNSUPPORTED in line_case(currency="ZZZ").reason_codes


@pytest.mark.fast
def test_T_F07_0308_invalid_amount() -> None:
    """
    id: T-F07-0308
    title: Invalid amount
    purpose: Invalid amount
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid amount
    risk: HZ-03
    capability: F07
    """
    reject(amount="ten")


@pytest.mark.fast
def test_T_F07_0309_invalid_period_start() -> None:
    """
    id: T-F07-0309
    title: Invalid period start
    purpose: Invalid period start
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid period start
    risk: HZ-03
    capability: F07
    """
    reject(period_start="2024-02-30T12:00Z")


@pytest.mark.fast
def test_T_F07_0310_invalid_period_end() -> None:
    """
    id: T-F07-0310
    title: Invalid period end
    purpose: Invalid period end
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid period end
    risk: HZ-03
    capability: F07
    """
    reject(period_end="2024-03-04T25:00Z")


@pytest.mark.fast
def test_T_F07_0311_period_without_zone() -> None:
    """
    id: T-F07-0311
    title: Period without zone
    purpose: Period without zone
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Period without zone
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(period_end="2024-03-04T00:00").reason_codes


@pytest.mark.fast
def test_T_F07_0312_period_reversed() -> None:
    """
    id: T-F07-0312
    title: Period reversed
    purpose: Period reversed
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Period reversed
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(period_end="2024-03-01T00:00Z").reason_codes


@pytest.mark.fast
def test_T_F07_0313_missing_start() -> None:
    """
    id: T-F07-0313
    title: Missing start
    purpose: Missing start
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Missing start
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(period_start=None).reason_codes


@pytest.mark.fast
def test_T_F07_0314_missing_end() -> None:
    """
    id: T-F07-0314
    title: Missing end
    purpose: Missing end
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Missing end
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(period_end=None).reason_codes


@pytest.mark.fast
def test_T_F07_0315_unmatched_container() -> None:
    """
    id: T-F07-0315
    title: Unmatched container
    purpose: Unmatched container
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Unmatched container
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(container="SYN-OTHER").reason_codes


@pytest.mark.fast
def test_T_F07_0316_future_period() -> None:
    """
    id: T-F07-0316
    title: Future period
    purpose: Future period
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Future period
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(period_end="2024-03-12T00:00Z").reason_codes


@pytest.mark.fast
def test_T_F07_0317_confusable_container() -> None:
    """
    id: T-F07-0317
    title: Confusable container
    purpose: Confusable container
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Confusable container
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in line_case(container="SYN-CОNT-1").reason_codes


@pytest.mark.fast
def test_T_F07_0318_recorded_scope_empty() -> None:
    """
    id: T-F07-0318
    title: Recorded scope empty
    purpose: Recorded scope empty
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Recorded scope empty
    risk: HZ-03
    capability: F07
    """
    assert Reason.CLOCK in result(canonical_containers=[]).reason_codes


@pytest.mark.fast
def test_T_F07_0319_text_cannot_direct_outcome() -> None:
    """
    id: T-F07-0319
    title: Text cannot direct outcome
    purpose: Text cannot direct outcome
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Text cannot direct outcome
    risk: HZ-03
    capability: F07
    """
    assert result(10).audit == result().audit


@pytest.mark.fast
def test_T_F07_0320_nonfinite_amount() -> None:
    """
    id: T-F07-0320
    title: Nonfinite amount
    purpose: Nonfinite amount
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Nonfinite amount
    risk: HZ-03
    capability: F07
    """
    reject(amount="Infinity")


@pytest.mark.fast
def test_T_F07_0401_replay_scenario_01() -> None:
    """
    id: T-F07-0401
    title: Replay scenario 01
    purpose: Replay scenario 01
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S01, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 01
    risk: HZ-03
    capability: F07
    """
    replay(1)


@pytest.mark.fast
def test_T_F07_0402_replay_scenario_02() -> None:
    """
    id: T-F07-0402
    title: Replay scenario 02
    purpose: Replay scenario 02
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S02, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 02
    risk: HZ-03
    capability: F07
    """
    replay(2)


@pytest.mark.fast
def test_T_F07_0403_replay_scenario_03() -> None:
    """
    id: T-F07-0403
    title: Replay scenario 03
    purpose: Replay scenario 03
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S03, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 03
    risk: HZ-03
    capability: F07
    """
    replay(3)


@pytest.mark.fast
def test_T_F07_0404_replay_scenario_04() -> None:
    """
    id: T-F07-0404
    title: Replay scenario 04
    purpose: Replay scenario 04
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S04, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 04
    risk: HZ-03
    capability: F07
    """
    replay(4)


@pytest.mark.fast
def test_T_F07_0405_replay_scenario_05() -> None:
    """
    id: T-F07-0405
    title: Replay scenario 05
    purpose: Replay scenario 05
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S05, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 05
    risk: HZ-03
    capability: F07
    """
    replay(5)


@pytest.mark.fast
def test_T_F07_0406_replay_scenario_06() -> None:
    """
    id: T-F07-0406
    title: Replay scenario 06
    purpose: Replay scenario 06
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S06, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 06
    risk: HZ-03
    capability: F07
    """
    replay(6)


@pytest.mark.fast
def test_T_F07_0407_replay_scenario_07() -> None:
    """
    id: T-F07-0407
    title: Replay scenario 07
    purpose: Replay scenario 07
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S07, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 07
    risk: HZ-03
    capability: F07
    """
    replay(7)


@pytest.mark.fast
def test_T_F07_0408_replay_scenario_08() -> None:
    """
    id: T-F07-0408
    title: Replay scenario 08
    purpose: Replay scenario 08
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S08, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 08
    risk: HZ-03
    capability: F07
    """
    replay(8)


@pytest.mark.fast
def test_T_F07_0409_replay_scenario_09() -> None:
    """
    id: T-F07-0409
    title: Replay scenario 09
    purpose: Replay scenario 09
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S09, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 09
    risk: HZ-03
    capability: F07
    """
    replay(9)


@pytest.mark.fast
def test_T_F07_0410_replay_scenario_10() -> None:
    """
    id: T-F07-0410
    title: Replay scenario 10
    purpose: Replay scenario 10
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, F07-S10, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 10
    risk: HZ-03
    capability: F07
    """
    replay(10)


@pytest.mark.fast
def test_T_F07_0501_anchor() -> None:
    """
    id: T-F07-0501
    title: Anchor
    purpose: Anchor
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Anchor
    risk: HZ-03
    capability: F07
    """
    assert 'id="f07"' in view()


@pytest.mark.fast
def test_T_F07_0502_root_cause_column() -> None:
    """
    id: T-F07-0502
    title: Root cause column
    purpose: Root cause column
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Root cause column
    risk: HZ-03
    capability: F07
    """
    assert "<th>Root cause</th>" in view()


@pytest.mark.fast
def test_T_F07_0503_proportional_difference() -> None:
    """
    id: T-F07-0503
    title: Proportional difference
    purpose: Proportional difference
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Proportional difference
    risk: HZ-03
    capability: F07
    """
    assert result(4).audit.lines[0].difference == Decimal(2)


@pytest.mark.fast
def test_T_F07_0504_changed_rate_two_steps() -> None:
    """
    id: T-F07-0504
    title: Changed rate two steps
    purpose: Changed rate two steps
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Changed rate two steps
    risk: HZ-03
    capability: F07
    """
    assert [row.version for row in result(4).audit.lines[0].steps] == ["1.0.0", "2.0.0"]


@pytest.mark.fast
def test_T_F07_0505_dossier_preview() -> None:
    """
    id: T-F07-0505
    title: Dossier preview
    purpose: Dossier preview
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Dossier preview
    risk: HZ-03
    capability: F07
    """
    assert "Dossier preview" in view(2)


@pytest.mark.fast
def test_T_F07_0506_json_export() -> None:
    """
    id: T-F07-0506
    title: Json export
    purpose: Json export
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Json export
    risk: HZ-03
    capability: F07
    """
    assert json.loads(result(2).dossier.json)["discrepancies"]


@pytest.mark.fast
def test_T_F07_0507_html_export() -> None:
    """
    id: T-F07-0507
    title: Html export
    purpose: Html export
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Html export
    risk: HZ-03
    capability: F07
    """
    assert "Tariff calculations" in result(2).dossier.html


@pytest.mark.fast
def test_T_F07_0508_indicative_export() -> None:
    """
    id: T-F07-0508
    title: Indicative export
    purpose: Indicative export
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Indicative export
    risk: HZ-03
    capability: F07
    """
    assert result(2).dossier.strength == "INDICATIVE"


@pytest.mark.fast
def test_T_F07_0509_unsupported_export_citation() -> None:
    """
    id: T-F07-0509
    title: Unsupported export citation
    purpose: Unsupported export citation
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Unsupported export citation
    risk: HZ-03
    capability: F07
    """
    assert "SYN-DOC-1:L1" in result(5).dossier.html


@pytest.mark.fast
def test_T_F07_0510_tax_exclusion() -> None:
    """
    id: T-F07-0510
    title: Tax exclusion
    purpose: Tax exclusion
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Tax exclusion
    risk: HZ-03
    capability: F07
    """
    assert result(9).audit.lines[1].classification is Classification.TAX


@pytest.mark.fast
def test_T_F07_0511_no_payment_instructions() -> None:
    """
    id: T-F07-0511
    title: No payment instructions
    purpose: No payment instructions
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No payment instructions
    risk: HZ-03
    capability: F07
    """
    assert all("pay immediately" not in view(i).lower() for i in range(1, 12))


@pytest.mark.fast
def test_T_F07_0512_no_owed_statement() -> None:
    """
    id: T-F07-0512
    title: No owed statement
    purpose: No owed statement
    level: fast
    requirement: P16-T08, Part 5 section 5.F07, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No owed statement
    risk: HZ-03
    capability: F07
    """
    assert all("money is owed" not in result(i).dossier.html.lower() for i in range(1, 12))

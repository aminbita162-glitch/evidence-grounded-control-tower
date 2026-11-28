"""Check recorded cost estimates, protective statuses, replay and simulation isolation."""

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from capabilities.l02 import Reason
from capabilities.l02.registration import INPUT, OUTPUT, LandedCostReport, register, render_estimate
from kernel.hashing import domain_hash

_ROOT = Path("data/scenarios/l02")


def fixture(index: int) -> tuple[dict[str, object], dict[str, object], datetime]:
    scenario = json.loads((_ROOT / f"L02-S{index:02d}.json").read_text())
    inputs = dict(scenario["inputs"])
    at = datetime.fromisoformat(inputs.pop("evaluation_time"))
    return scenario, inputs, at


def row(inputs: dict[str, object]) -> dict[str, object]:
    return cast(list[dict[str, object]], inputs["goods"])[0]


def result(index: int = 1, **updates: object) -> LandedCostReport:
    _, inputs, at = fixture(index)
    inputs.update(updates)
    return register(INPUT.validate_python(inputs), at)[0]


def goods(**updates: object) -> LandedCostReport:
    _, inputs, at = fixture(1)
    row(inputs).update(updates)
    return register(INPUT.validate_python(inputs), at)[0]


def duplicate_rate() -> LandedCostReport:
    _, inputs, at = fixture(1)
    pack = cast(dict[str, object], inputs["duty_pack"])
    rates = cast(list[dict[str, object]], pack["rates"])
    rates.append(dict(rates[0], id="SYN-DUPLICATE-RATE", ad_valorem="0.10"))
    return register(INPUT.validate_python(inputs), at)[0]


def reject(**updates: object) -> None:
    with pytest.raises(ValidationError):
        goods(**updates)


def check(index: int) -> None:
    expected, _, _ = fixture(index)
    actual = result(index)
    assert actual.status.value == expected["outcome"]
    assert set(actual.reason_codes) == set(cast(list[str], expected["reason_codes"]))


def replay(index: int) -> None:
    _, inputs, at = fixture(index)
    data = INPUT.validate_python(inputs)
    actual, evidence = register(data, at)
    assert register(INPUT.validate_json(INPUT.dump_json(data)), at) == (actual, evidence)
    assert evidence["output_hash"] == domain_hash(
        "ctc/payload/v1", OUTPUT.dump_python(actual, mode="json")
    )


def view(index: int = 1) -> str:
    return render_estimate(result(index))


def fully_derived() -> LandedCostReport:
    _, inputs, at = fixture(1)
    from dataclasses import replace

    data = INPUT.validate_python(inputs)
    pack = data.duty_pack
    assert pack is not None
    return register(
        replace(
            data,
            goods=tuple(replace(g, label="DERIVED") for g in data.goods),
            exchange=replace(data.exchange, label="DERIVED"),
            duty_pack=replace(pack, rates=tuple(replace(r, label="DERIVED") for r in pack.rates)),
            components=tuple(replace(c, label="DERIVED") for c in data.components),
            taxes=tuple(replace(t, label="DERIVED") for t in data.taxes),
            valuation_rules={
                k: replace(v, label="DERIVED") for k, v in data.valuation_rules.items()
            },
        ),
        at,
    )[0]


@pytest.mark.fast
def test_T_L02_0001_scenario_01() -> None:
    """
    id: T-L02-0001
    title: Scenario 01
    purpose: Scenario 01
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S01, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 01
    risk: HZ-03
    capability: L02
    """
    check(1)


@pytest.mark.fast
def test_T_L02_0002_scenario_02() -> None:
    """
    id: T-L02-0002
    title: Scenario 02
    purpose: Scenario 02
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S02, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 02
    risk: HZ-03
    capability: L02
    """
    check(2)


@pytest.mark.fast
def test_T_L02_0003_scenario_03() -> None:
    """
    id: T-L02-0003
    title: Scenario 03
    purpose: Scenario 03
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S03, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 03
    risk: HZ-03
    capability: L02
    """
    check(3)


@pytest.mark.fast
def test_T_L02_0004_scenario_04() -> None:
    """
    id: T-L02-0004
    title: Scenario 04
    purpose: Scenario 04
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S04, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 04
    risk: HZ-03
    capability: L02
    """
    check(4)


@pytest.mark.fast
def test_T_L02_0005_scenario_05() -> None:
    """
    id: T-L02-0005
    title: Scenario 05
    purpose: Scenario 05
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S05, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 05
    risk: HZ-03
    capability: L02
    """
    check(5)


@pytest.mark.fast
def test_T_L02_0006_scenario_06() -> None:
    """
    id: T-L02-0006
    title: Scenario 06
    purpose: Scenario 06
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S06, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 06
    risk: HZ-03
    capability: L02
    """
    check(6)


@pytest.mark.fast
def test_T_L02_0007_scenario_07() -> None:
    """
    id: T-L02-0007
    title: Scenario 07
    purpose: Scenario 07
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S07, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 07
    risk: HZ-03
    capability: L02
    """
    check(7)


@pytest.mark.fast
def test_T_L02_0008_scenario_08() -> None:
    """
    id: T-L02-0008
    title: Scenario 08
    purpose: Scenario 08
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S08, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 08
    risk: HZ-03
    capability: L02
    """
    check(8)


@pytest.mark.fast
def test_T_L02_0009_scenario_09() -> None:
    """
    id: T-L02-0009
    title: Scenario 09
    purpose: Scenario 09
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S09, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 09
    risk: HZ-03
    capability: L02
    """
    check(9)


@pytest.mark.fast
def test_T_L02_0010_scenario_10() -> None:
    """
    id: T-L02-0010
    title: Scenario 10
    purpose: Scenario 10
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S10, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 10
    risk: HZ-03
    capability: L02
    """
    check(10)


@pytest.mark.fast
def test_T_L02_0011_scenario_11() -> None:
    """
    id: T-L02-0011
    title: Scenario 11
    purpose: Scenario 11
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S11, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 11
    risk: HZ-03
    capability: L02
    """
    check(11)


@pytest.mark.fast
def test_T_L02_0012_scenario_12() -> None:
    """
    id: T-L02-0012
    title: Scenario 12
    purpose: Scenario 12
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S12, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 12
    risk: HZ-03
    capability: L02
    """
    check(12)


@pytest.mark.fast
def test_T_L02_0013_scenario_13() -> None:
    """
    id: T-L02-0013
    title: Scenario 13
    purpose: Scenario 13
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S13, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 13
    risk: HZ-03
    capability: L02
    """
    check(13)


@pytest.mark.fast
def test_T_L02_0014_scenario_14() -> None:
    """
    id: T-L02-0014
    title: Scenario 14
    purpose: Scenario 14
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S14, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 14
    risk: HZ-03
    capability: L02
    """
    check(14)


@pytest.mark.fast
def test_T_L02_0015_scenario_15() -> None:
    """
    id: T-L02-0015
    title: Scenario 15
    purpose: Scenario 15
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S15, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 15
    risk: HZ-03
    capability: L02
    """
    check(15)


@pytest.mark.fast
def test_T_L02_0016_scenario_16() -> None:
    """
    id: T-L02-0016
    title: Scenario 16
    purpose: Scenario 16
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S16, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 16
    risk: HZ-03
    capability: L02
    """
    check(16)


@pytest.mark.fast
def test_T_L02_0017_scenario_17() -> None:
    """
    id: T-L02-0017
    title: Scenario 17
    purpose: Scenario 17
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S17, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 17
    risk: HZ-03
    capability: L02
    """
    check(17)


@pytest.mark.fast
def test_T_L02_0101_provided() -> None:
    """
    id: T-L02-0101
    title: Provided
    purpose: Provided
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Provided
    risk: HZ-03
    capability: L02
    """
    assert Reason.PROVIDED in fully_derived().reason_codes


@pytest.mark.fast
def test_T_L02_0102_indicative() -> None:
    """
    id: T-L02-0102
    title: Indicative
    purpose: Indicative
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Indicative
    risk: HZ-03
    capability: L02
    """
    assert Reason.INDICATIVE in result(10).reason_codes


@pytest.mark.fast
def test_T_L02_0103_incomplete() -> None:
    """
    id: T-L02-0103
    title: Incomplete
    purpose: Incomplete
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Incomplete
    risk: HZ-03
    capability: L02
    """
    assert Reason.INCOMPLETE in result(6).reason_codes


@pytest.mark.fast
def test_T_L02_0104_variance() -> None:
    """
    id: T-L02-0104
    title: Variance
    purpose: Variance
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Variance
    risk: HZ-03
    capability: L02
    """
    assert Reason.VARIANCE in result(14).reason_codes


@pytest.mark.fast
def test_T_L02_0105_rate_conflict() -> None:
    """
    id: T-L02-0105
    title: Rate conflict
    purpose: Rate conflict
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Rate conflict
    risk: HZ-03
    capability: L02
    """
    assert Reason.CONFLICT in duplicate_rate().reason_codes


@pytest.mark.fast
def test_T_L02_0106_missing_upstream() -> None:
    """
    id: T-L02-0106
    title: Missing upstream
    purpose: Missing upstream
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Missing upstream
    risk: HZ-03
    capability: L02
    """
    assert Reason.UPSTREAM in result(goods=[]).reason_codes


@pytest.mark.fast
def test_T_L02_0107_valuation_rule() -> None:
    """
    id: T-L02-0107
    title: Valuation rule
    purpose: Valuation rule
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Valuation rule
    risk: HZ-03
    capability: L02
    """
    assert Reason.RULE in result(valuation_rules={}).reason_codes


@pytest.mark.fast
def test_T_L02_0108_missing_duty_pack() -> None:
    """
    id: T-L02-0108
    title: Missing duty pack
    purpose: Missing duty pack
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Missing duty pack
    risk: HZ-03
    capability: L02
    """
    assert Reason.DUTY_PACK in result(duty_pack=None).reason_codes


@pytest.mark.fast
def test_T_L02_0109_declared_code_absent() -> None:
    """
    id: T-L02-0109
    title: Declared code absent
    purpose: Declared code absent
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Declared code absent
    risk: HZ-03
    capability: L02
    """
    assert Reason.CODE in result(8).reason_codes


@pytest.mark.fast
def test_T_L02_0110_missing_fx() -> None:
    """
    id: T-L02-0110
    title: Missing fx
    purpose: Missing fx
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Missing fx
    risk: HZ-03
    capability: L02
    """
    assert Reason.FX in result(7).reason_codes


@pytest.mark.fast
def test_T_L02_0111_missing_currency() -> None:
    """
    id: T-L02-0111
    title: Missing currency
    purpose: Missing currency
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Missing currency
    risk: HZ-03
    capability: L02
    """
    assert Reason.CURRENCY in result(16).reason_codes


@pytest.mark.fast
def test_T_L02_0301_zero_value() -> None:
    """
    id: T-L02-0301
    title: Zero value
    purpose: Zero value
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Zero value
    risk: HZ-03
    capability: L02
    """
    assert goods(value={"amount": "0", "currency": "USD"}).estimate.duties[0].amount == 0


@pytest.mark.fast
def test_T_L02_0302_negative_value() -> None:
    """
    id: T-L02-0302
    title: Negative value
    purpose: Negative value
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative value
    risk: HZ-03
    capability: L02
    """
    reject(value={"amount": "-1", "currency": "USD"})


@pytest.mark.fast
def test_T_L02_0303_negative_quantity() -> None:
    """
    id: T-L02-0303
    title: Negative quantity
    purpose: Negative quantity
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative quantity
    risk: HZ-03
    capability: L02
    """
    reject(quantity="-1")


@pytest.mark.fast
def test_T_L02_0304_negative_weight() -> None:
    """
    id: T-L02-0304
    title: Negative weight
    purpose: Negative weight
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative weight
    risk: HZ-03
    capability: L02
    """
    reject(weight="-1")


@pytest.mark.fast
def test_T_L02_0305_huge_quantity() -> None:
    """
    id: T-L02-0305
    title: Huge quantity
    purpose: Huge quantity
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Huge quantity
    risk: HZ-03
    capability: L02
    """
    reject(quantity="1e300")


@pytest.mark.fast
def test_T_L02_0306_huge_weight() -> None:
    """
    id: T-L02-0306
    title: Huge weight
    purpose: Huge weight
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Huge weight
    risk: HZ-03
    capability: L02
    """
    reject(weight="1e300")


@pytest.mark.fast
def test_T_L02_0307_nonfinite_amount() -> None:
    """
    id: T-L02-0307
    title: Nonfinite amount
    purpose: Nonfinite amount
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Nonfinite amount
    risk: HZ-03
    capability: L02
    """
    reject(value={"amount": "NaN", "currency": "USD"})


@pytest.mark.fast
def test_T_L02_0308_nonfinite_quantity() -> None:
    """
    id: T-L02-0308
    title: Nonfinite quantity
    purpose: Nonfinite quantity
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Nonfinite quantity
    risk: HZ-03
    capability: L02
    """
    reject(quantity="Infinity")


@pytest.mark.fast
def test_T_L02_0309_wrong_decimal() -> None:
    """
    id: T-L02-0309
    title: Wrong decimal
    purpose: Wrong decimal
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Wrong decimal
    risk: HZ-03
    capability: L02
    """
    reject(weight="twenty")


@pytest.mark.fast
def test_T_L02_0310_bad_goods_date() -> None:
    """
    id: T-L02-0310
    title: Bad goods date
    purpose: Bad goods date
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Bad goods date
    risk: HZ-03
    capability: L02
    """
    reject(declared_on="2024-02-30")


@pytest.mark.fast
def test_T_L02_0311_overlapping_rates() -> None:
    """
    id: T-L02-0311
    title: Overlapping rates
    purpose: Overlapping rates
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Overlapping rates
    risk: HZ-03
    capability: L02
    """
    assert duplicate_rate().estimate.total is None


@pytest.mark.fast
def test_T_L02_0312_missing_currency_exponent() -> None:
    """
    id: T-L02-0312
    title: Missing currency exponent
    purpose: Missing currency exponent
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Missing currency exponent
    risk: HZ-03
    capability: L02
    """
    assert result(16).estimate.total is None


@pytest.mark.fast
def test_T_L02_0313_missing_fx_not_zero() -> None:
    """
    id: T-L02-0313
    title: Missing fx not zero
    purpose: Missing fx not zero
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Missing fx not zero
    risk: HZ-03
    capability: L02
    """
    assert not result(7).estimate.components


@pytest.mark.fast
def test_T_L02_0314_free_text_exemption() -> None:
    """
    id: T-L02-0314
    title: Free text exemption
    purpose: Free text exemption
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Free text exemption
    risk: HZ-03
    capability: L02
    """
    assert result(12).estimate.duties == result().estimate.duties


@pytest.mark.fast
def test_T_L02_0315_alternative_code_ignored() -> None:
    """
    id: T-L02-0315
    title: Alternative code ignored
    purpose: Alternative code ignored
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Alternative code ignored
    risk: HZ-03
    capability: L02
    """
    assert result(9).estimate.duties[0].code == "1101"


@pytest.mark.fast
def test_T_L02_0316_preference_unverified() -> None:
    """
    id: T-L02-0316
    title: Preference unverified
    purpose: Preference unverified
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Preference unverified
    risk: HZ-03
    capability: L02
    """
    assert result(5).estimate.duties[0].amount == Decimal(5) and result(5).estimate.notes


@pytest.mark.fast
def test_T_L02_0317_invalid_components() -> None:
    """
    id: T-L02-0317
    title: Invalid components
    purpose: Invalid components
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid components
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValidationError):
        result(components=["bad"])


@pytest.mark.fast
def test_T_L02_0318_invalid_rate_pack() -> None:
    """
    id: T-L02-0318
    title: Invalid rate pack
    purpose: Invalid rate pack
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid rate pack
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValidationError):
        result(duty_pack="bad")


@pytest.mark.fast
def test_T_L02_0319_unsafe_plan_component() -> None:
    """
    id: T-L02-0319
    title: Unsafe plan component
    purpose: Unsafe plan component
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Unsafe plan component
    risk: HZ-03
    capability: L02
    """
    with pytest.raises(ValueError, match="transport-leg"):
        result(plan={"id": "x", "leg_costs": []})


@pytest.mark.fast
def test_T_L02_0320_no_partial_total() -> None:
    """
    id: T-L02-0320
    title: No partial total
    purpose: No partial total
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: No partial total
    risk: HZ-03
    capability: L02
    """
    assert result(6).estimate.total is None and result(6).estimate.components


@pytest.mark.fast
def test_T_L02_0401_replay_scenario_01() -> None:
    """
    id: T-L02-0401
    title: Replay scenario 01
    purpose: Replay scenario 01
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S01, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 01
    risk: HZ-03
    capability: L02
    """
    replay(1)


@pytest.mark.fast
def test_T_L02_0402_replay_scenario_02() -> None:
    """
    id: T-L02-0402
    title: Replay scenario 02
    purpose: Replay scenario 02
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S02, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 02
    risk: HZ-03
    capability: L02
    """
    replay(2)


@pytest.mark.fast
def test_T_L02_0403_replay_scenario_03() -> None:
    """
    id: T-L02-0403
    title: Replay scenario 03
    purpose: Replay scenario 03
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S03, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 03
    risk: HZ-03
    capability: L02
    """
    replay(3)


@pytest.mark.fast
def test_T_L02_0404_replay_scenario_04() -> None:
    """
    id: T-L02-0404
    title: Replay scenario 04
    purpose: Replay scenario 04
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S04, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 04
    risk: HZ-03
    capability: L02
    """
    replay(4)


@pytest.mark.fast
def test_T_L02_0405_replay_scenario_05() -> None:
    """
    id: T-L02-0405
    title: Replay scenario 05
    purpose: Replay scenario 05
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S05, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 05
    risk: HZ-03
    capability: L02
    """
    replay(5)


@pytest.mark.fast
def test_T_L02_0406_replay_scenario_06() -> None:
    """
    id: T-L02-0406
    title: Replay scenario 06
    purpose: Replay scenario 06
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S06, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 06
    risk: HZ-03
    capability: L02
    """
    replay(6)


@pytest.mark.fast
def test_T_L02_0407_replay_scenario_07() -> None:
    """
    id: T-L02-0407
    title: Replay scenario 07
    purpose: Replay scenario 07
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S07, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 07
    risk: HZ-03
    capability: L02
    """
    replay(7)


@pytest.mark.fast
def test_T_L02_0408_replay_scenario_08() -> None:
    """
    id: T-L02-0408
    title: Replay scenario 08
    purpose: Replay scenario 08
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S08, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 08
    risk: HZ-03
    capability: L02
    """
    replay(8)


@pytest.mark.fast
def test_T_L02_0409_replay_scenario_09() -> None:
    """
    id: T-L02-0409
    title: Replay scenario 09
    purpose: Replay scenario 09
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S09, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 09
    risk: HZ-03
    capability: L02
    """
    replay(9)


@pytest.mark.fast
def test_T_L02_0410_replay_scenario_10() -> None:
    """
    id: T-L02-0410
    title: Replay scenario 10
    purpose: Replay scenario 10
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, L02-S10, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 10
    risk: HZ-03
    capability: L02
    """
    replay(10)


@pytest.mark.fast
def test_T_L02_0501_anchor() -> None:
    """
    id: T-L02-0501
    title: Anchor
    purpose: Anchor
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Anchor
    risk: HZ-03
    capability: L02
    """
    assert 'id="l02"' in view()


@pytest.mark.fast
def test_T_L02_0502_component_origins() -> None:
    """
    id: T-L02-0502
    title: Component origins
    purpose: Component origins
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Component origins
    risk: HZ-03
    capability: L02
    """
    assert "DOCUMENT" in view() and "PACK" in view()


@pytest.mark.fast
def test_T_L02_0503_trace_details() -> None:
    """
    id: T-L02-0503
    title: Trace details
    purpose: Trace details
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Trace details
    risk: HZ-03
    capability: L02
    """
    assert "<summary>Calculation</summary>" in view()


@pytest.mark.fast
def test_T_L02_0504_range_visible() -> None:
    """
    id: T-L02-0504
    title: Range visible
    purpose: Range visible
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Range visible
    risk: HZ-03
    capability: L02
    """
    assert "Range" in view(2) and result(2).estimate.label == "ASSUMPTION"


@pytest.mark.fast
def test_T_L02_0505_missing_components_visible() -> None:
    """
    id: T-L02-0505
    title: Missing components visible
    purpose: Missing components visible
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Missing components visible
    risk: HZ-03
    capability: L02
    """
    assert "Missing components" in view(6) and "FREIGHT" in view(6)


@pytest.mark.fast
def test_T_L02_0506_no_incomplete_total() -> None:
    """
    id: T-L02-0506
    title: No incomplete total
    purpose: No incomplete total
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No incomplete total
    risk: HZ-03
    capability: L02
    """
    assert "Estimated total" not in view(6)


@pytest.mark.fast
def test_T_L02_0507_simulation_record_only() -> None:
    """
    id: T-L02-0507
    title: Simulation record only
    purpose: Simulation record only
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Simulation record only
    risk: HZ-03
    capability: L02
    """
    _, inputs, at = fixture(11)
    report, record = register(INPUT.validate_python(inputs), at)
    assert (
        report.simulated
        and record["record_kind"] == "SIMULATION"
        and record["label"] == "SIMULATED"
    )
    assert "SIMULATED" in view(11) and not result().simulated


@pytest.mark.fast
def test_T_L02_0508_proposal_replaces_transport() -> None:
    """
    id: T-L02-0508
    title: Proposal replaces transport
    purpose: Proposal replaces transport
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Proposal replaces transport
    risk: HZ-03
    capability: L02
    """
    baseline, proposal = result().estimate.total, result(11).estimate.total
    assert baseline is not None and proposal is not None and baseline.base - proposal.base == 40


@pytest.mark.fast
def test_T_L02_0509_observed_eight_percent() -> None:
    """
    id: T-L02-0509
    title: Observed eight percent
    purpose: Observed eight percent
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Observed eight percent
    risk: HZ-03
    capability: L02
    """
    variance = result(14).variance
    assert (
        variance is not None
        and variance.observation_only
        and variance.components[0].percent == Decimal(8)
    )


@pytest.mark.fast
def test_T_L02_0510_unestimated_visible() -> None:
    """
    id: T-L02-0510
    title: Unestimated visible
    purpose: Unestimated visible
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Unestimated visible
    risk: HZ-03
    capability: L02
    """
    assert "Unestimated charges HANDLING" in view(15)


@pytest.mark.fast
def test_T_L02_0511_no_declaration_advice() -> None:
    """
    id: T-L02-0511
    title: No declaration advice
    purpose: No declaration advice
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No declaration advice
    risk: HZ-03
    capability: L02
    """
    assert all("change the declared" not in view(i).lower() for i in range(1, 18))


@pytest.mark.fast
def test_T_L02_0512_no_variance_without_audit() -> None:
    """
    id: T-L02-0512
    title: No variance without audit
    purpose: No variance without audit
    level: fast
    requirement: P16-T06, Part 5 section 5.L02, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No variance without audit
    risk: HZ-03
    capability: L02
    """
    assert result(17).variance is None and result(17).estimate == result().estimate

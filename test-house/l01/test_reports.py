"""Check invoice scenarios, reason coverage, adversarial rows and evidence replay."""

import json
from datetime import datetime
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from capabilities.l01 import InvoiceAudit, Reason
from capabilities.l01.registration import INPUT, OUTPUT, register, render_audit
from kernel.hashing import domain_hash

_ROOT = Path("data/scenarios/l01")


def fixture(index: int) -> tuple[dict[str, object], dict[str, object], datetime]:
    scenario = json.loads((_ROOT / f"L01-S{index:02d}.json").read_text())
    inputs = dict(scenario["inputs"])
    at = datetime.fromisoformat(inputs.pop("evaluation_time"))
    return scenario, inputs, at


def row(inputs: dict[str, object]) -> dict[str, object]:
    bill = cast(dict[str, object], inputs["invoice"])
    return cast(list[dict[str, object]], bill["lines"])[0]


def audit(index: int = 1, **updates: object) -> InvoiceAudit:
    _, inputs, at = fixture(index)
    inputs.update(updates)
    return register(INPUT.validate_python(inputs), at)[0]


def line_case(**updates: object) -> InvoiceAudit:
    _, inputs, at = fixture(1)
    row(inputs).update(updates)
    return register(INPUT.validate_python(inputs), at)[0]


def reject(**updates: object) -> None:
    with pytest.raises(ValidationError):
        line_case(**updates)


def check(index: int) -> None:
    expected, _, _ = fixture(index)
    result = audit(index)
    assert result.outcome.name == expected["outcome"]
    assert list(result.reason_codes) == expected["reason_codes"] or set(result.reason_codes) == set(
        cast(list[str], expected["reason_codes"])
    )


def replay(index: int) -> None:
    _, inputs, at = fixture(index)
    data = INPUT.validate_python(inputs)
    result, evidence = register(data, at)
    assert register(INPUT.validate_json(INPUT.dump_json(data)), at) == (result, evidence)
    assert evidence["output_hash"] == domain_hash(
        "ctc/payload/v1", OUTPUT.dump_python(result, mode="json")
    )


def view(index: int = 1) -> str:
    return render_audit(audit(index))


@pytest.mark.fast
def test_T_L01_0001_scenario_01() -> None:
    """
    id: T-L01-0001
    title: Scenario 01
    purpose: Scenario 01
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S01, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 01
    risk: HZ-03
    capability: L01
    """
    check(1)


@pytest.mark.fast
def test_T_L01_0002_scenario_02() -> None:
    """
    id: T-L01-0002
    title: Scenario 02
    purpose: Scenario 02
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S02, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 02
    risk: HZ-03
    capability: L01
    """
    check(2)


@pytest.mark.fast
def test_T_L01_0003_scenario_03() -> None:
    """
    id: T-L01-0003
    title: Scenario 03
    purpose: Scenario 03
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S03, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 03
    risk: HZ-03
    capability: L01
    """
    check(3)


@pytest.mark.fast
def test_T_L01_0004_scenario_04() -> None:
    """
    id: T-L01-0004
    title: Scenario 04
    purpose: Scenario 04
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S04, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 04
    risk: HZ-03
    capability: L01
    """
    check(4)


@pytest.mark.fast
def test_T_L01_0005_scenario_05() -> None:
    """
    id: T-L01-0005
    title: Scenario 05
    purpose: Scenario 05
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S05, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 05
    risk: HZ-03
    capability: L01
    """
    check(5)


@pytest.mark.fast
def test_T_L01_0006_scenario_06() -> None:
    """
    id: T-L01-0006
    title: Scenario 06
    purpose: Scenario 06
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S06, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 06
    risk: HZ-03
    capability: L01
    """
    check(6)


@pytest.mark.fast
def test_T_L01_0007_scenario_07() -> None:
    """
    id: T-L01-0007
    title: Scenario 07
    purpose: Scenario 07
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S07, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 07
    risk: HZ-03
    capability: L01
    """
    check(7)


@pytest.mark.fast
def test_T_L01_0008_scenario_08() -> None:
    """
    id: T-L01-0008
    title: Scenario 08
    purpose: Scenario 08
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S08, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 08
    risk: HZ-03
    capability: L01
    """
    check(8)


@pytest.mark.fast
def test_T_L01_0009_scenario_09() -> None:
    """
    id: T-L01-0009
    title: Scenario 09
    purpose: Scenario 09
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S09, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 09
    risk: HZ-03
    capability: L01
    """
    check(9)


@pytest.mark.fast
def test_T_L01_0010_scenario_10() -> None:
    """
    id: T-L01-0010
    title: Scenario 10
    purpose: Scenario 10
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S10, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 10
    risk: HZ-03
    capability: L01
    """
    check(10)


@pytest.mark.fast
def test_T_L01_0011_scenario_11() -> None:
    """
    id: T-L01-0011
    title: Scenario 11
    purpose: Scenario 11
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S11, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 11
    risk: HZ-03
    capability: L01
    """
    check(11)


@pytest.mark.fast
def test_T_L01_0012_scenario_12() -> None:
    """
    id: T-L01-0012
    title: Scenario 12
    purpose: Scenario 12
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S12, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 12
    risk: HZ-03
    capability: L01
    """
    check(12)


@pytest.mark.fast
def test_T_L01_0013_scenario_13() -> None:
    """
    id: T-L01-0013
    title: Scenario 13
    purpose: Scenario 13
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S13, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 13
    risk: HZ-03
    capability: L01
    """
    check(13)


@pytest.mark.fast
def test_T_L01_0014_scenario_14() -> None:
    """
    id: T-L01-0014
    title: Scenario 14
    purpose: Scenario 14
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S14, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 14
    risk: HZ-03
    capability: L01
    """
    check(14)


@pytest.mark.fast
def test_T_L01_0015_scenario_15() -> None:
    """
    id: T-L01-0015
    title: Scenario 15
    purpose: Scenario 15
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S15, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 15
    risk: HZ-03
    capability: L01
    """
    check(15)


@pytest.mark.fast
def test_T_L01_0016_scenario_16() -> None:
    """
    id: T-L01-0016
    title: Scenario 16
    purpose: Scenario 16
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S16, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 16
    risk: HZ-03
    capability: L01
    """
    check(16)


@pytest.mark.fast
def test_T_L01_0017_scenario_17() -> None:
    """
    id: T-L01-0017
    title: Scenario 17
    purpose: Scenario 17
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S17, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 17
    risk: HZ-03
    capability: L01
    """
    check(17)


@pytest.mark.fast
def test_T_L01_0018_scenario_18() -> None:
    """
    id: T-L01-0018
    title: Scenario 18
    purpose: Scenario 18
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S18, DoD 6
    input: Versioned synthetic case and referenced packs
    expected: Scenario 18
    risk: HZ-03
    capability: L01
    """
    check(18)


@pytest.mark.fast
def test_T_L01_0101_match() -> None:
    """
    id: T-L01-0101
    title: Match
    purpose: Match
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Match
    risk: HZ-03
    capability: L01
    """
    assert Reason.MATCH in audit(1).reason_codes


@pytest.mark.fast
def test_T_L01_0102_below_basis() -> None:
    """
    id: T-L01-0102
    title: Below basis
    purpose: Below basis
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Below basis
    risk: HZ-03
    capability: L01
    """
    assert Reason.BELOW in audit(14).reason_codes


@pytest.mark.fast
def test_T_L01_0103_tax_excluded() -> None:
    """
    id: T-L01-0103
    title: Tax excluded
    purpose: Tax excluded
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Tax excluded
    risk: HZ-03
    capability: L01
    """
    assert Reason.TAX in audit(11).reason_codes


@pytest.mark.fast
def test_T_L01_0104_matched_for_f07() -> None:
    """
    id: T-L01-0104
    title: Matched for f07
    purpose: Matched for f07
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Matched for f07
    risk: HZ-03
    capability: L01
    """
    assert Reason.TIME in audit(10).reason_codes


@pytest.mark.fast
def test_T_L01_0105_duplicate() -> None:
    """
    id: T-L01-0105
    title: Duplicate
    purpose: Duplicate
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Duplicate
    risk: HZ-03
    capability: L01
    """
    assert Reason.DUPLICATE in audit(2).reason_codes


@pytest.mark.fast
def test_T_L01_0106_rate_above_basis() -> None:
    """
    id: T-L01-0106
    title: Rate above basis
    purpose: Rate above basis
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Rate above basis
    risk: HZ-03
    capability: L01
    """
    assert Reason.RATE in audit(3).reason_codes


@pytest.mark.fast
def test_T_L01_0107_quantity_mismatch() -> None:
    """
    id: T-L01-0107
    title: Quantity mismatch
    purpose: Quantity mismatch
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Quantity mismatch
    risk: HZ-03
    capability: L01
    """
    assert Reason.QUANTITY in audit(4).reason_codes


@pytest.mark.fast
def test_T_L01_0108_arithmetic() -> None:
    """
    id: T-L01-0108
    title: Arithmetic
    purpose: Arithmetic
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Arithmetic
    risk: HZ-03
    capability: L01
    """
    assert Reason.ARITHMETIC in line_case(amount="100.01").reason_codes


@pytest.mark.fast
def test_T_L01_0109_surcharge_validity() -> None:
    """
    id: T-L01-0109
    title: Surcharge validity
    purpose: Surcharge validity
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Surcharge validity
    risk: HZ-03
    capability: L01
    """
    assert Reason.SURCHARGE in audit(5).reason_codes


@pytest.mark.fast
def test_T_L01_0110_header_total() -> None:
    """
    id: T-L01-0110
    title: Header total
    purpose: Header total
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Header total
    risk: HZ-03
    capability: L01
    """
    assert Reason.HEADER in audit(16).reason_codes


@pytest.mark.fast
def test_T_L01_0111_currency_mismatch() -> None:
    """
    id: T-L01-0111
    title: Currency mismatch
    purpose: Currency mismatch
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Currency mismatch
    risk: HZ-03
    capability: L01
    """
    assert Reason.CURRENCY in audit(9).reason_codes


@pytest.mark.fast
def test_T_L01_0112_possible_duplicate() -> None:
    """
    id: T-L01-0112
    title: Possible duplicate
    purpose: Possible duplicate
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Possible duplicate
    risk: HZ-03
    capability: L01
    """
    assert Reason.POSSIBLE_DUPLICATE in audit(15).reason_codes


@pytest.mark.fast
def test_T_L01_0113_unquoted() -> None:
    """
    id: T-L01-0113
    title: Unquoted
    purpose: Unquoted
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Unquoted
    risk: HZ-03
    capability: L01
    """
    assert Reason.NO_BASIS in audit(6).reason_codes


@pytest.mark.fast
def test_T_L01_0114_ambiguous_basis() -> None:
    """
    id: T-L01-0114
    title: Ambiguous basis
    purpose: Ambiguous basis
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Ambiguous basis
    risk: HZ-03
    capability: L01
    """
    assert Reason.AMBIGUOUS in audit(7).reason_codes


@pytest.mark.fast
def test_T_L01_0115_freight_terms() -> None:
    """
    id: T-L01-0115
    title: Freight terms
    purpose: Freight terms
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Freight terms
    risk: HZ-03
    capability: L01
    """
    assert Reason.FREIGHT in audit(8).reason_codes


@pytest.mark.fast
def test_T_L01_0116_invoice_unverified() -> None:
    """
    id: T-L01-0116
    title: Invoice unverified
    purpose: Invoice unverified
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Invoice unverified
    risk: HZ-03
    capability: L01
    """
    assert Reason.INVOICE in line_case(verified=False).reason_codes


@pytest.mark.fast
def test_T_L01_0117_taxonomy_absent() -> None:
    """
    id: T-L01-0117
    title: Taxonomy absent
    purpose: Taxonomy absent
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Taxonomy absent
    risk: HZ-03
    capability: L01
    """
    assert Reason.TAXONOMY in audit(taxonomy=None).reason_codes


@pytest.mark.fast
def test_T_L01_0118_basis_pack_absent() -> None:
    """
    id: T-L01-0118
    title: Basis pack absent
    purpose: Basis pack absent
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Basis pack absent
    risk: HZ-03
    capability: L01
    """
    assert Reason.PACK in audit(bases=[], basis_available=False).reason_codes


@pytest.mark.fast
def test_T_L01_0119_currency_unsupported() -> None:
    """
    id: T-L01-0119
    title: Currency unsupported
    purpose: Currency unsupported
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Currency unsupported
    risk: HZ-03
    capability: L01
    """
    assert Reason.UNSUPPORTED in audit(17).reason_codes


@pytest.mark.fast
def test_T_L01_0120_label_insufficient() -> None:
    """
    id: T-L01-0120
    title: Label insufficient
    purpose: Label insufficient
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 4 and 5
    input: Versioned synthetic case and referenced packs
    expected: Label insufficient
    risk: HZ-03
    capability: L01
    """
    assert Reason.LABEL in audit(13).reason_codes


@pytest.mark.fast
def test_T_L01_0301_cyrillic_lookalike() -> None:
    """
    id: T-L01-0301
    title: Cyrillic lookalike
    purpose: Cyrillic lookalike
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Cyrillic lookalike
    risk: HZ-03
    capability: L01
    """
    assert Reason.NO_BASIS in line_case(name="Нandling fee").reason_codes


@pytest.mark.fast
def test_T_L01_0302_greek_lookalike() -> None:
    """
    id: T-L01-0302
    title: Greek lookalike
    purpose: Greek lookalike
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Greek lookalike
    risk: HZ-03
    capability: L01
    """
    assert Reason.NO_BASIS in line_case(name="Handling fεe").reason_codes


@pytest.mark.fast
def test_T_L01_0303_negative_amount() -> None:
    """
    id: T-L01-0303
    title: Negative amount
    purpose: Negative amount
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative amount
    risk: HZ-03
    capability: L01
    """
    reject(amount="-1")


@pytest.mark.fast
def test_T_L01_0304_negative_rate() -> None:
    """
    id: T-L01-0304
    title: Negative rate
    purpose: Negative rate
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative rate
    risk: HZ-03
    capability: L01
    """
    reject(rate="-1")


@pytest.mark.fast
def test_T_L01_0305_negative_quantity() -> None:
    """
    id: T-L01-0305
    title: Negative quantity
    purpose: Negative quantity
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Negative quantity
    risk: HZ-03
    capability: L01
    """
    reject(quantity={"value": "-1", "unit": "container"})


@pytest.mark.fast
def test_T_L01_0306_invalid_decimal() -> None:
    """
    id: T-L01-0306
    title: Invalid decimal
    purpose: Invalid decimal
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid decimal
    risk: HZ-03
    capability: L01
    """
    reject(amount="ten")


@pytest.mark.fast
def test_T_L01_0307_nan_amount() -> None:
    """
    id: T-L01-0307
    title: Nan amount
    purpose: Nan amount
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Nan amount
    risk: HZ-03
    capability: L01
    """
    reject(amount="NaN")


@pytest.mark.fast
def test_T_L01_0308_infinite_rate() -> None:
    """
    id: T-L01-0308
    title: Infinite rate
    purpose: Infinite rate
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Infinite rate
    risk: HZ-03
    capability: L01
    """
    reject(rate="Infinity")


@pytest.mark.fast
def test_T_L01_0309_oversized_quantity() -> None:
    """
    id: T-L01-0309
    title: Oversized quantity
    purpose: Oversized quantity
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Oversized quantity
    risk: HZ-03
    capability: L01
    """
    reject(quantity={"value": "1e99", "unit": "container"})


@pytest.mark.fast
def test_T_L01_0310_malformed_currency() -> None:
    """
    id: T-L01-0310
    title: Malformed currency
    purpose: Malformed currency
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Malformed currency
    risk: HZ-03
    capability: L01
    """
    assert Reason.UNSUPPORTED in line_case(currency="12").reason_codes


@pytest.mark.fast
def test_T_L01_0311_empty_citation() -> None:
    """
    id: T-L01-0311
    title: Empty citation
    purpose: Empty citation
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Empty citation
    risk: HZ-03
    capability: L01
    """
    assert Reason.INVOICE in line_case(citation="").reason_codes


@pytest.mark.fast
def test_T_L01_0312_empty_shipment() -> None:
    """
    id: T-L01-0312
    title: Empty shipment
    purpose: Empty shipment
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Empty shipment
    risk: HZ-03
    capability: L01
    """
    assert Reason.INVOICE in line_case(shipment="").reason_codes


@pytest.mark.fast
def test_T_L01_0313_required_quantity() -> None:
    """
    id: T-L01-0313
    title: Required quantity
    purpose: Required quantity
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Required quantity
    risk: HZ-03
    capability: L01
    """
    reject(quantity=None)


@pytest.mark.fast
def test_T_L01_0314_invalid_service_date() -> None:
    """
    id: T-L01-0314
    title: Invalid service date
    purpose: Invalid service date
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invalid service date
    risk: HZ-03
    capability: L01
    """
    reject(service_date="2024-02-30")


@pytest.mark.fast
def test_T_L01_0315_overlapping_validity() -> None:
    """
    id: T-L01-0315
    title: Overlapping validity
    purpose: Overlapping validity
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Overlapping validity
    risk: HZ-03
    capability: L01
    """
    assert Reason.AMBIGUOUS in audit(7).reason_codes


@pytest.mark.fast
def test_T_L01_0316_split_duplicate() -> None:
    """
    id: T-L01-0316
    title: Split duplicate
    purpose: Split duplicate
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Split duplicate
    risk: HZ-03
    capability: L01
    """
    assert Reason.POSSIBLE_DUPLICATE in audit(15).reason_codes


@pytest.mark.fast
def test_T_L01_0317_split_band_disabled() -> None:
    """
    id: T-L01-0317
    title: Split band disabled
    purpose: Split band disabled
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Split band disabled
    risk: HZ-03
    capability: L01
    """
    assert Reason.POSSIBLE_DUPLICATE not in audit(18).reason_codes


@pytest.mark.fast
def test_T_L01_0318_header_minor_unit() -> None:
    """
    id: T-L01-0318
    title: Header minor unit
    purpose: Header minor unit
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Header minor unit
    risk: HZ-03
    capability: L01
    """
    assert Reason.HEADER in audit(16).reason_codes


@pytest.mark.fast
def test_T_L01_0319_stale_surcharge() -> None:
    """
    id: T-L01-0319
    title: Stale surcharge
    purpose: Stale surcharge
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Stale surcharge
    risk: HZ-03
    capability: L01
    """
    assert Reason.SURCHARGE in audit(5).reason_codes


@pytest.mark.fast
def test_T_L01_0320_secondary_tariff() -> None:
    """
    id: T-L01-0320
    title: Secondary tariff
    purpose: Secondary tariff
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Secondary tariff
    risk: HZ-03
    capability: L01
    """
    assert Reason.LABEL in audit(13).reason_codes


@pytest.mark.fast
def test_T_L01_0321_adversarial_note() -> None:
    """
    id: T-L01-0321
    title: Adversarial note
    purpose: Adversarial note
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Adversarial note
    risk: HZ-03
    capability: L01
    """
    assert audit(12).outcome == audit(1).outcome


@pytest.mark.fast
def test_T_L01_0322_invoice_row_not_object() -> None:
    """
    id: T-L01-0322
    title: Invoice row not object
    purpose: Invoice row not object
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Invoice row not object
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValidationError):
        audit(invoice="invalid")


@pytest.mark.fast
def test_T_L01_0323_taxonomy_row_not_object() -> None:
    """
    id: T-L01-0323
    title: Taxonomy row not object
    purpose: Taxonomy row not object
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Taxonomy row not object
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValidationError):
        audit(taxonomy="invalid")


@pytest.mark.fast
def test_T_L01_0324_basis_row_not_object() -> None:
    """
    id: T-L01-0324
    title: Basis row not object
    purpose: Basis row not object
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Basis row not object
    risk: HZ-03
    capability: L01
    """
    with pytest.raises(ValidationError):
        audit(bases=["invalid"])


@pytest.mark.fast
def test_T_L01_0325_tax_claim_as_text() -> None:
    """
    id: T-L01-0325
    title: Tax claim as text
    purpose: Tax claim as text
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 11
    input: Versioned synthetic case and referenced packs
    expected: Tax claim as text
    risk: HZ-03
    capability: L01
    """
    assert Reason.NO_BASIS in line_case(name="Tax is exempt").reason_codes


@pytest.mark.fast
def test_T_L01_0401_replay_scenario_01() -> None:
    """
    id: T-L01-0401
    title: Replay scenario 01
    purpose: Replay scenario 01
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S01, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 01
    risk: HZ-03
    capability: L01
    """
    replay(1)


@pytest.mark.fast
def test_T_L01_0402_replay_scenario_02() -> None:
    """
    id: T-L01-0402
    title: Replay scenario 02
    purpose: Replay scenario 02
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S02, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 02
    risk: HZ-03
    capability: L01
    """
    replay(2)


@pytest.mark.fast
def test_T_L01_0403_replay_scenario_03() -> None:
    """
    id: T-L01-0403
    title: Replay scenario 03
    purpose: Replay scenario 03
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S03, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 03
    risk: HZ-03
    capability: L01
    """
    replay(3)


@pytest.mark.fast
def test_T_L01_0404_replay_scenario_04() -> None:
    """
    id: T-L01-0404
    title: Replay scenario 04
    purpose: Replay scenario 04
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S04, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 04
    risk: HZ-03
    capability: L01
    """
    replay(4)


@pytest.mark.fast
def test_T_L01_0405_replay_scenario_05() -> None:
    """
    id: T-L01-0405
    title: Replay scenario 05
    purpose: Replay scenario 05
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S05, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 05
    risk: HZ-03
    capability: L01
    """
    replay(5)


@pytest.mark.fast
def test_T_L01_0406_replay_scenario_06() -> None:
    """
    id: T-L01-0406
    title: Replay scenario 06
    purpose: Replay scenario 06
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S06, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 06
    risk: HZ-03
    capability: L01
    """
    replay(6)


@pytest.mark.fast
def test_T_L01_0407_replay_scenario_07() -> None:
    """
    id: T-L01-0407
    title: Replay scenario 07
    purpose: Replay scenario 07
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S07, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 07
    risk: HZ-03
    capability: L01
    """
    replay(7)


@pytest.mark.fast
def test_T_L01_0408_replay_scenario_08() -> None:
    """
    id: T-L01-0408
    title: Replay scenario 08
    purpose: Replay scenario 08
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S08, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 08
    risk: HZ-03
    capability: L01
    """
    replay(8)


@pytest.mark.fast
def test_T_L01_0409_replay_scenario_09() -> None:
    """
    id: T-L01-0409
    title: Replay scenario 09
    purpose: Replay scenario 09
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S09, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 09
    risk: HZ-03
    capability: L01
    """
    replay(9)


@pytest.mark.fast
def test_T_L01_0410_replay_scenario_10() -> None:
    """
    id: T-L01-0410
    title: Replay scenario 10
    purpose: Replay scenario 10
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, L01-S10, DoD 8
    input: Versioned synthetic case and referenced packs
    expected: Replay scenario 10
    risk: HZ-03
    capability: L01
    """
    replay(10)


@pytest.mark.fast
def test_T_L01_0501_anchor() -> None:
    """
    id: T-L01-0501
    title: Anchor
    purpose: Anchor
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Anchor
    risk: HZ-03
    capability: L01
    """
    assert 'id="l01"' in view()


@pytest.mark.fast
def test_T_L01_0502_basis_visible() -> None:
    """
    id: T-L01-0502
    title: Basis visible
    purpose: Basis visible
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Basis visible
    risk: HZ-03
    capability: L01
    """
    assert "SYN-QUOTE-1" in view()


@pytest.mark.fast
def test_T_L01_0503_billed_column() -> None:
    """
    id: T-L01-0503
    title: Billed column
    purpose: Billed column
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Billed column
    risk: HZ-03
    capability: L01
    """
    assert "<th>Billed</th>" in view()


@pytest.mark.fast
def test_T_L01_0504_expected_column() -> None:
    """
    id: T-L01-0504
    title: Expected column
    purpose: Expected column
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Expected column
    risk: HZ-03
    capability: L01
    """
    assert "<th>Expected</th>" in view()


@pytest.mark.fast
def test_T_L01_0505_trace_expansion() -> None:
    """
    id: T-L01-0505
    title: Trace expansion
    purpose: Trace expansion
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Trace expansion
    risk: HZ-03
    capability: L01
    """
    assert "<summary>Calculation</summary>" in view()


@pytest.mark.fast
def test_T_L01_0506_line_citation() -> None:
    """
    id: T-L01-0506
    title: Line citation
    purpose: Line citation
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Line citation
    risk: HZ-03
    capability: L01
    """
    assert "SYN-DOC-1:L1" in view()


@pytest.mark.fast
def test_T_L01_0507_header_details() -> None:
    """
    id: T-L01-0507
    title: Header details
    purpose: Header details
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Header details
    risk: HZ-03
    capability: L01
    """
    assert "Header total 100.01" in view(16)


@pytest.mark.fast
def test_T_L01_0508_time_based_match() -> None:
    """
    id: T-L01-0508
    title: Time based match
    purpose: Time based match
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Time based match
    risk: HZ-03
    capability: L01
    """
    assert Reason.TIME in view(10) and "Not evaluated" in view(10)


@pytest.mark.fast
def test_T_L01_0509_currency_totals() -> None:
    """
    id: T-L01-0509
    title: Currency totals
    purpose: Currency totals
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Currency totals
    risk: HZ-03
    capability: L01
    """
    assert "USD billed" in view() and "difference" in view()


@pytest.mark.fast
def test_T_L01_0510_unblock_requirements() -> None:
    """
    id: T-L01-0510
    title: Unblock requirements
    purpose: Unblock requirements
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: Unblock requirements
    risk: HZ-03
    capability: L01
    """
    assert "applicable quotation, contract or tariff" in view(6)


@pytest.mark.fast
def test_T_L01_0511_no_dispute_draft() -> None:
    """
    id: T-L01-0511
    title: No dispute draft
    purpose: No dispute draft
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No dispute draft
    risk: HZ-03
    capability: L01
    """
    assert all("dispute letter" not in view(i).lower() for i in range(1, 19))


@pytest.mark.fast
def test_T_L01_0512_no_withhold_advice() -> None:
    """
    id: T-L01-0512
    title: No withhold advice
    purpose: No withhold advice
    level: fast
    requirement: P16-T04, Part 5 section 5.L01, DoD 9 and 10
    input: Versioned synthetic case and referenced packs
    expected: No withhold advice
    risk: HZ-03
    capability: L01
    """
    assert all("withhold payment" not in view(i).lower() for i in range(1, 19))

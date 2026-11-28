"""Check the recorded F07 scenarios through the public evaluation interface."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from capabilities.f07.registration import INPUT, register

_SCENARIOS = Path(__file__).resolve().parents[3] / "data/scenarios/f07"


@pytest.mark.fast
@pytest.mark.parametrize("scenario", sorted(_SCENARIOS.glob("F07-S*.json")), ids=lambda p: p.stem)
def test_f07_golden(scenario: Path) -> None:
    expected = json.loads(scenario.read_text())
    inputs = dict(expected["inputs"])
    at = datetime.fromisoformat(inputs.pop("evaluation_time"))
    result, _ = register(INPUT.validate_python(inputs), at)
    if result.outcome.name != expected["outcome"]:
        pytest.fail("unexpected outcome")
    if sorted(result.reason_codes) != sorted(expected["reason_codes"]):
        pytest.fail(f"unexpected reason codes: {result.reason_codes}")

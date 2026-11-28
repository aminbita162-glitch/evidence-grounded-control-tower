"""Check recorded scenarios through the same clock interface as the case evaluator."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from capabilities.f03.registration import INPUT, register

_SCENARIOS = Path(__file__).resolve().parents[3] / "data/scenarios/f03"


@pytest.mark.fast
@pytest.mark.parametrize("scenario", sorted(_SCENARIOS.glob("F03-S*.json")), ids=lambda p: p.stem)
def test_f03_golden(scenario: Path) -> None:
    expected = json.loads(scenario.read_text())
    inputs = dict(expected["inputs"])
    at = datetime.fromisoformat(inputs.pop("evaluation_time"))
    result, _ = register(INPUT.validate_python(inputs), at)
    if result.decision.name != expected["outcome"]:
        pytest.fail(f"unexpected decision: {result.decision.name}")
    if sorted({row.reason.value for row in result.clocks}) != sorted(expected["reason_codes"]):
        pytest.fail("unexpected reason codes")
    for currency, value in expected["totals"].items():
        if str(result.totals[currency]) != value:
            pytest.fail(f"unexpected {currency} total")

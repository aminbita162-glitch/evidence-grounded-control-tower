"""Check the capability's generated scenario references against the source files."""

import json
from pathlib import Path

import pytest


@pytest.mark.fast
def test_scenario_index() -> None:
    root = Path(__file__).resolve().parents[3]
    directory = Path(__file__).resolve().parents[1]
    entries = json.loads((directory / "eval/cases.json").read_bytes())
    if len(entries) != 15:
        pytest.fail("K05 must publish 15 scenarios")
    for entry in entries:
        scenario = json.loads((root / entry["case"]).read_bytes())
        if (
            scenario["test_id"] != entry["test_id"]
            or scenario["label"] != "SYNTHETIC"
            or scenario["id"] not in scenario["basis"]
        ):
            pytest.fail("K05 scenario reference mismatch")

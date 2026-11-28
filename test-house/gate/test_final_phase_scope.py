"""Exercise automatic scope selection on main after the last directive phase."""

import json
from pathlib import Path

import pytest

from tools.gate.phase import scope


@pytest.mark.fast
@pytest.mark.parametrize(("completed", "phase"), [("P15", "P16"), ("P16", "P16"), ("P17", "P18")])
def test_T_FIN_0017_scope_on_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, completed: str, phase: str
) -> None:
    """
    id: T-FIN-0017
    title: Main keeps the final phase scope
    purpose: Apply the correct scope at and beyond the directive terminal phase
    level: fast
    requirement: P16 post-merge maintenance and Part 6 section 6.14
    input: Main with two declared phases and recorded completion
    expected: The final phase is selected only when it is the recorded completion
    risk: RSK-J-01
    capability: FIN
    """
    monkeypatch.setattr(scope, "_repo_root", lambda: tmp_path)
    state_path = tmp_path / "docs/state/STATE.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"last_completed_phase": completed}))
    definition = (
        "<<<PHASE-15>>>\nScope paths: prior/**\n<<<END-PHASE-15>>>\n"
        "<<<PHASE-16>>>\nScope paths: capabilities/f03/**\n<<<END-PHASE-16>>>\n"
    )
    (tmp_path / "directive.txt").write_text(definition)
    selected = scope._current_in_progress_phase()
    assert selected == phase
    if selected == "P16":
        assert scope.check_scope(selected, definition, ["outside.py"], []) == [
            "path outside scope: outside.py"
        ]

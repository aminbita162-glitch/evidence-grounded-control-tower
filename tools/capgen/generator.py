"""Generate the versioned capability layout from a checked definition."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, TypedDict

from pydantic import ConfigDict, Field, TypeAdapter

_LAYOUT = Path(__file__).with_name("layout.json")
_REQUIRED_CALIBRATION = frozenset({"F02", "K01", "K05", "K21"})

_CapabilityId = Annotated[str, Field(pattern=r"^[FKL][0-9]{2}$")]


@dataclass(frozen=True, slots=True)
class Definition:
    """Minimum metadata required for a generated capability."""

    __pydantic_config__ = ConfigDict(extra="forbid", strict=True)

    capability_id: _CapabilityId
    title: Annotated[str, Field(min_length=1, pattern=r"^[^\r\n]+$")]
    version: Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")]
    depends: tuple[_CapabilityId, ...] = ()
    statistical: bool = False
    calibration_artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate the calibration declaration."""
        uses_calibration = self.statistical or self.capability_id in _REQUIRED_CALIBRATION
        if uses_calibration and not self.calibration_artifacts:
            raise ValueError("statistical capability must declare its calibration artifacts")

    @classmethod
    def from_json(cls, data: str | bytes) -> Definition:
        """Validate the serialized definition."""
        return TypeAdapter(cls).validate_json(data)


def _json(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _contract_schema(cap_id: str, kind: str) -> str:
    return _json(
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": f"{cap_id} {kind}",
            "type": "object",
            "additionalProperties": False,
        }
    )


class _Layout(TypedDict):
    schema_version: int
    files: list[str]


def required_files() -> tuple[str, ...]:
    """Read the locked capability layout."""
    layout: _Layout = json.loads(_LAYOUT.read_text(encoding="utf-8"))
    return tuple(layout["files"])


_GOLDEN_TEST = '''"""Run the generated case against its recorded synthetic expectation."""

import json
from pathlib import Path

import pytest

from kernel.skeleton import run_skeleton


@pytest.mark.fast
def test_generated_case() -> None:
    expected = json.loads(Path(__file__).with_name("expected.json").read_text())
    result = run_skeleton()
    assert result.decision == expected["outcome"]
    assert result.replay_ok and result.bundle_ok
'''


def render(definition: Definition) -> Mapping[str, str]:
    """Render all required files in the standard layout."""
    cap_id = definition.capability_id
    heading = f"# {definition.title}\n\n"
    summary = f"Capability {cap_id}, version {definition.version}.\n"
    files = {
        "manifest.json": _json(asdict(definition)),
        "schemas/input.json": _contract_schema(cap_id, "input"),
        "schemas/output.json": _contract_schema(cap_id, "output"),
        "rules/rules.json": _json([]),
        "fixtures/case.json": _json({"source_id": "SYN-CAPGEN", "label": "SYNTHETIC"}),
        "golden/test_case.py": _GOLDEN_TEST,
        "golden/expected.json": _json({"outcome": "ABSTAIN", "label": "SYNTHETIC"}),
        "eval/cases.json": _json(
            [{"case": "fixtures/case.json", "expected": "golden/expected.json"}]
        ),
        "view.html": f'<section id="{cap_id.lower()}" aria-label="{cap_id}"></section>\n',
        "README.md": heading + summary,
        "registration.py": (
            f'"""Registration for {cap_id}."""\n\n'
            "from tools.capgen.registration import synthetic_registration\n\n"
            f'CAPABILITY_ID = "{cap_id}"\n'
            "invoke = synthetic_registration(CAPABILITY_ID)\n"
        ),
    }
    if set(files) != set(required_files()):
        raise ValueError("rendered files do not match the locked capability layout")
    return files


def generate(definition_path: Path, output: Path) -> None:
    """Generate a capability and guard against overwriting edited files."""
    definition = Definition.from_json(definition_path.read_bytes())
    rendered = render(definition)
    for relative, content in rendered.items():
        target = output / relative
        if target.exists() and target.read_bytes() != content.encode():
            raise ValueError(f"refusing to overwrite {relative}")
    for relative, content in rendered.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode())


def layout_errors(capability: Path) -> list[str]:
    """Check the required paths and capability definition in a capability directory."""
    try:
        Definition.from_json((capability / "manifest.json").read_bytes())
    except (OSError, ValueError) as exc:
        return [f"{capability.name}: invalid manifest ({exc})"]
    return [
        f"{capability.name}: missing {relative}"
        for relative in required_files()
        if not (capability / relative).is_file()
    ]

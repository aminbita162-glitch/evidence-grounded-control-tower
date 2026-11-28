"""Architecture enforcement gate (Part 3 §3.18, P03-T08).

Scans the kernel source for forbidden patterns: wall-clock access,
randomness, UUID, environment access, and the six display names of
Part 3 §3.9 in kernel/, schemas/, or fixtures.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

from tools.capgen.generator import layout_errors
from tools.capgen.registry import capability_errors, dependency_errors, read_capabilities
from tools.gate.phase.checks import load_phases

FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"\bimport\s+time\b", "wall-clock access via time module"),
    (r"\bimport\s+uuid\b", "UUID usage"),
    (r"\bimport\s+random\b", "randomness in core"),
    (r"\bos\.environ\b", "environment access in core"),
    (r"\bos\.getenv\b", "environment access in core"),
]

DISPLAY_NAMES = ["Conductor", "Reader", "Verifier", "Estimator", "Planner", "Sentinel"]


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def _money_float_errors(path: Path, content: str) -> list[str]:
    return [
        f"{path.name}:{node.lineno}: floating point in money arithmetic"
        for node in ast.walk(ast.parse(content, filename=str(path)))
        if (isinstance(node, ast.Constant) and type(node.value) is float)
        or (isinstance(node, ast.Name) and node.id == "float")
    ]


def main() -> int:
    """Entry point: scan kernel/ for forbidden patterns."""
    root = _gate_root()
    kernel_dir = root / "kernel"
    if not kernel_dir.is_dir():
        print("arch: kernel/ directory not found", file=sys.stderr)
        return 2
    violations: list[str] = []
    for py_file in kernel_dir.rglob("*.py"):
        content = py_file.read_text()
        if any(
            py_file.is_relative_to(kernel_dir / "lib" / name)
            for name in ("money", "clock", "taxonomy")
        ):
            violations.extend(_money_float_errors(py_file, content))
        for pattern, desc in FORBIDDEN_PATTERNS:
            if re.search(pattern, content):
                violations.append(f"{py_file.name}: {desc}")
        for name in DISPLAY_NAMES:
            if re.search(rf"\b{name}\b", content):
                violations.append(f"{py_file.name}: display name {name!r} in kernel")
    directive = root / "directive.txt"
    if directive.is_file():
        violations.extend(
            capability_errors(read_capabilities(directive.read_text(encoding="utf-8")))
        )
    phase_table = root / "tools" / "gate" / "phases.toml"
    if phase_table.is_file():
        phases = load_phases(phase_table)
        violations.extend(
            dependency_errors(
                {phase_id: tuple(phase.depends_on) for phase_id, phase in phases.items()}
            )
        )
    capabilities = root / "capabilities"
    if capabilities.is_dir():
        for capability in sorted(capabilities.iterdir()):
            if capability.is_dir() and re.fullmatch(r"[fkl]\d{2}", capability.name.lower()):
                violations.extend(layout_errors(capability))
                if capability.name in {"f03", "f07", "l01", "l02"}:
                    for source in capability.rglob("*.py"):
                        if "golden" not in source.relative_to(capability).parts:
                            violations.extend(_money_float_errors(source, source.read_text()))
    if violations:
        for v in violations:
            print(f"arch: {v}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

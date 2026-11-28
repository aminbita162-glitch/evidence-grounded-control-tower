"""Generate the Phase 14 capability cards and scenario traceability evidence."""

from __future__ import annotations

from pathlib import Path

from tools.gate.gates.index import scan_directory
from tools.trace import build_matrix, save_matrix

_ROOT = Path(__file__).resolve().parents[2]
_CAPABILITIES = {
    "K14": ("Bilingual Intake", "SRC-K14-NORMALIZATION", 20, "T-INT-0041 T-INT-0044"),
    "F01": ("Consistency Graph", "SRC-F01-CONSISTENCY", 12, "T-INT-0041 T-INT-0044"),
    "K09": ("Duplicate-Document Shield", "SRC-K09-IDENTITY", 17, "T-INT-0044 T-INT-0046"),
}


def generate() -> None:
    matrix = build_matrix(_ROOT)
    if matrix.broken:
        raise ValueError("broken capability links")
    test_root = _ROOT / "test-house"
    for cap, (title, source, count, interfaces) in _CAPABILITIES.items():
        scenarios = {
            key: value for key, value in matrix.scenarios.items() if key.startswith(f"{cap}-S")
        }
        if len(scenarios) != count:
            raise ValueError(f"{cap} scenario coverage does not match the directive")
        tests = sorted(entry.fields["id"] for entry in scan_directory(test_root / cap.lower()))
        rule_tests = " ".join(t for t in tests if t.split("-")[-1].startswith(("01", "02")))
        gate_tests = " ".join(t for t in tests if t.split("-")[-1].startswith(("03", "04", "05")))
        table = [
            ("1", "Capability specification", f"Directive Part 5 {cap}, H and T1 through T14"),
            (
                "2",
                "Schemas, packs, provenance",
                f"`{source}`, contracts.lock, data and label gates",
            ),
            ("3", "Deterministic evaluation", f"{count} scenario cases and output-hash replay"),
            ("4", "Closed reason codes", rule_tests),
            ("5", "Protective outcomes", f"{count} verified scenario cases"),
            ("6", "Golden scenarios", f"{cap}-S01 through {cap}-S{count:02}"),
            ("7", "Property and independent comparisons", rule_tests),
            ("8", "Evidence and replay", gate_tests),
            ("9a", "API, command and view", interfaces),
            ("9b", "Accessibility", "PENDING-P27"),
            ("10", "Budget and performance", "Synthetic P14 performance report and budget tests"),
            ("11", "Adversarial and tenant isolation", gate_tests),
            ("12", "Coverage, mutation and traceability", "Phase 14 verification report and trace"),
        ]
        rows = "\n".join(f"| {n} | {item} | {proof} |" for n, item, proof in table)
        (_ROOT / "docs" / "capabilities" / f"{cap}.md").write_text(
            f"# {title}\n\nCapability {cap}, version 1.0.0.\n\n"
            f"| Item | Requirement | Evidence |\n| --- | --- | --- |\n{rows}\n",
            encoding="utf-8",
        )
    save_matrix(matrix, _ROOT / "docs/phase-reports/P14-trace.json")


if __name__ == "__main__":
    generate()

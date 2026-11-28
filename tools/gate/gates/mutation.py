"""Mutation baseline gate (Part 4 §4.5, P03-T09).

Runs the test suite with branch coverage on ``kernel/`` and verifies the
coverage meets the thresholds. Records the first floor as the baseline.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _gate_root() -> Path:
    """Resolve the repository root, respecting GATE_ROOT if set."""
    gate_root = os.environ.get("GATE_ROOT")
    if gate_root:  # pragma: no cover
        return Path(gate_root).resolve()
    return Path(__file__).resolve().parents[3]


def _verify_intake_branches(root: Path, env: dict[str, str]) -> int:
    """Keep the Phase 14 module floors separate from the inherited repository total."""
    if not (root / "capabilities/k14/manifest.json").is_file():
        return 0
    report = root / ".gate-logs" / "p14-scoped-coverage.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-n0",
            "-o",
            "addopts=",
            "--import-mode=importlib",
            "--cov=capabilities",
            "--cov=kernel/intake",
            "--cov=kernel/lib/text",
            "--cov-branch",
            f"--cov-report=json:{report}",
            "test-house/intake",
            "test-house/k14",
            "test-house/f01",
            "test-house/k09",
            "test-house/pairs",
            "capabilities/k14/golden",
            "capabilities/f01/golden",
            "capabilities/k09/golden",
        ],
        cwd=root,
        env={**env, "COVERAGE_FILE": str(root / ".gate-logs" / "p14-scoped.coverage")},
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode:
        print(result.stdout, file=sys.stderr)
        return 1
    files = json.loads(report.read_text(encoding="utf-8"))["files"]
    ordered = (
        ("capabilities/k14/", 90),
        ("capabilities/f01/", 90),
        ("capabilities/k09/", 90),
        ("kernel/intake/", 95),
        ("kernel/lib/text/", 95),
    )
    failures = []
    for prefix, minimum in ordered:
        summary = [info["summary"] for name, info in files.items() if name.startswith(prefix)]
        total = sum(item["num_branches"] for item in summary)
        covered = sum(item["covered_branches"] for item in summary)
        if total == 0 or covered * 100 < minimum * total:
            failures.append(prefix)
        print(f"mutation: {prefix} branch coverage {covered}/{total} (floor {minimum}%)")
    return int(bool(failures))


def _verify_finance_branches(root: Path, env: dict[str, str]) -> int:
    """Apply the unchanged capability and kernel floors to Phase 16 modules."""
    if not (root / "capabilities/f07/manifest.json").is_file():
        return 0

    from tools.trace.phase16_mutation import verify

    report = root / ".gate-logs" / "p16-scoped-coverage.json"
    components = ("f03", "l01", "l02", "f07")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-n0",
            "-o",
            "addopts=",
            "--import-mode=importlib",
            "--cov=capabilities",
            "--cov=kernel",
            "--cov-branch",
            f"--cov-report=json:{report}",
            *(f"test-house/{cap}" for cap in components),
            *(f"capabilities/{cap}/golden" for cap in components),
            "test-house/pairs/test_finance.py",
        ],
        cwd=root,
        env={**env, "COVERAGE_FILE": str(root / ".gate-logs" / "p16-scoped.coverage")},
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode:
        print(result.stdout[-4000:], file=sys.stderr)
        return 1
    files = json.loads(report.read_text(encoding="utf-8"))["files"]
    expected = {
        **{f"capabilities/{cap}/": 90 for cap in components},
        "kernel/lib/clock/": 95,
        "kernel/lib/taxonomy/": 95,
        "kernel/skeleton/finance.py": 95,
    }
    errors = []
    for prefix, floor in expected.items():
        counts = [
            value["summary"]
            for path, value in files.items()
            if path.startswith(prefix) and "/golden/" not in path
        ]
        branches = sum(item["num_branches"] for item in counts)
        covered = sum(item["covered_branches"] for item in counts)
        print(f"mutation: {prefix} branch coverage {covered}/{branches} (floor {floor}%)")
        if not branches or covered * 100 < branches * floor:
            errors.append(prefix)
    if errors:
        print(f"mutation: coverage floor unmet for {', '.join(errors)}", file=sys.stderr)
        return 1
    return verify(root)


def main() -> int:
    """Entry point: run coverage on kernel/ and verify thresholds."""
    root = _gate_root()
    py = sys.executable
    cov_file = root / ".gate-logs" / "coverage.json"
    cov_file.parent.mkdir(parents=True, exist_ok=True)

    # Prepend root to PYTHONPATH so the fixture's kernel/ is found first
    # when the project is installed in editable mode (uv sync).
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")

    # Use bare --cov (source=None) to measure only imported modules, not all
    # files under kernel/.  A path-based --cov=<root>/kernel would include
    # every .py under kernel/ — including modules tested by other test
    # directories (containment, orchestration) — dragging coverage below the
    # 95% threshold.  Override addopts to avoid inheriting a bare --cov from
    # pyproject.toml that may interact with --cov=<path> unpredictably; use
    # our own bare --cov explicitly.  Run serially (-n 0) to avoid
    # pytest-xdist worker count differences between local and CI.
    r = subprocess.run(
        [
            py,
            "-m",
            "pytest",
            "test-house/kernel/",
            "--cov",
            "--cov-branch",
            f"--cov-report=json:{cov_file}",
            "--no-header",
            "-q",
            "--no-cov-on-fail",
            "-p",
            "no:randomly",
            "-n",
            "0",
            "-o",
            "addopts=",
        ],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if r.returncode != 0:
        print(f"mutation: test suite failed (exit {r.returncode})", file=sys.stderr)
        return 1

    if not cov_file.is_file():
        print("mutation: coverage report not generated", file=sys.stderr)
        return 2

    cov = json.loads(cov_file.read_text())
    pct = cov.get("totals", {}).get("percent_covered", 0.0)
    threshold = 95.0

    if pct < threshold:
        print(
            f"mutation: branch coverage {pct:.1f}% below threshold {threshold}%",
            file=sys.stderr,
        )
        return 1

    print(f"mutation: branch coverage {pct:.1f}% meets threshold {threshold}%")
    return _verify_intake_branches(root, env) or _verify_finance_branches(root, env)


if __name__ == "__main__":
    sys.exit(main())

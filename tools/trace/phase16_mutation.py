"""Exercise purpose-built mutations of the Phase 16 financial rules."""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


@dataclass(frozen=True, slots=True)
class Mutation:
    module: str
    name: str
    before: str
    after: str
    tests: str


_MUTATIONS = (
    Mutation(
        "kernel/lib/clock/__init__.py",
        "include-label",
        "self.terms.day_one == DayOne.EXCLUDE",
        "self.terms.day_one == DayOne.INCLUDE",
        "f03",
    ),
    Mutation(
        "kernel/lib/clock/__init__.py",
        "verified-suspensions",
        "if w.verified",
        "if not w.verified",
        "f03",
    ),
    Mutation(
        "kernel/lib/clock/__init__.py",
        "skip-holidays",
        "and day not in self.holidays",
        "and day in self.holidays",
        "f03",
    ),
    Mutation(
        "kernel/lib/taxonomy/__init__.py",
        "allow-alias-collision",
        "names.setdefault(normalized, entry.code) != entry.code",
        "names.setdefault(normalized, entry.code) == ''",
        "l01",
    ),
    Mutation(
        "capabilities/f03/__init__.py",
        "deadline-inclusive",
        "remaining <= _WARNING",
        "remaining < timedelta(hours=1)",
        "f03",
    ),
    Mutation(
        "capabilities/f03/__init__.py",
        "skip-canonical-set",
        "if data.container not in canonical_containers:",
        "if not data.container:",
        "f03",
    ),
    Mutation(
        "capabilities/l01/__init__.py",
        "duplicate-identity",
        "if other.amount == line.amount:",
        "if other.amount != line.amount:",
        "l01",
    ),
    Mutation(
        "capabilities/l01/__init__.py",
        "near-band-comparison",
        "<= _CONTEXT.multiply(min(other.amount, line.amount), policy.near_band)",
        ">= _CONTEXT.multiply(min(other.amount, line.amount), policy.near_band)",
        "l01",
    ),
    Mutation(
        "capabilities/l01/__init__.py",
        "basis-currency",
        "if line.currency != basis.currency:",
        "if line.currency == basis.currency:",
        "l01",
    ),
    Mutation(
        "capabilities/l02/__init__.py",
        "declared-code",
        "if rate.code == item.code and rate.valid_at(at)",
        "if rate.valid_at(at)",
        "l02",
    ),
    Mutation(
        "capabilities/l02/__init__.py",
        "permit-unverified-origin",
        'fact.status == "VERIFIED"',
        'fact.status != "CONFLICTED"',
        "l02",
    ),
    Mutation(
        "capabilities/l02/__init__.py",
        "publish-partial-total",
        "if missing\n        else _sum_ranges",
        "if False\n        else _sum_ranges",
        "l02",
    ),
    Mutation(
        "capabilities/f07/__init__.py",
        "ignore-unbillable-period",
        "if calculated.non_billable and line.quantity.value > 0:",
        "if calculated.non_billable and line.quantity.value < 0:",
        "f07",
    ),
    Mutation(
        "capabilities/f07/__init__.py",
        "ignore-undercharge",
        "if line.amount < calculated.expected:",
        "if line.amount > calculated.expected:",
        "f07",
    ),
    Mutation(
        "capabilities/f07/dossier.py", "omit-html-from-commitment", "[data, html]", "[data]", "f07"
    ),
)


def verify(root: Path) -> int:
    """Count only assertion failures as kills and require the stated rule floors."""
    with TemporaryDirectory(prefix="finance-mutation-") as temporary:
        isolated = Path(temporary)
        ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".hypothesis")
        for directory in (
            "api",
            "adapters",
            "capabilities",
            "data",
            "kernel",
            "schemas",
            "test-house",
            "tools",
        ):
            shutil.copytree(root / directory, isolated / directory, ignore=ignore)
        shutil.copy2(root / "pyproject.toml", isolated)
        env = {**os.environ, "PYTHONPATH": str(isolated), "PYTHONDONTWRITEBYTECODE": "1"}
        subjects: Counter[str] = Counter()
        killed: Counter[str] = Counter()
        for variant in _MUTATIONS:
            group = variant.module.split("/")[0]
            subjects[group] += 1
            path = isolated / variant.module
            original = path.read_text()
            if original.count(variant.before) != 1:
                print(f"mutation: {variant.name} did not select exactly one rule")
                return 1
            modified = original.replace(variant.before, variant.after, 1)
            compile(modified, variant.module, "exec")
            path.write_text(modified)
            try:
                result = subprocess.run(  # noqa: S603  # nosec B603
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        f"test-house/{variant.tests}",
                        "-n0",
                        "-o",
                        "addopts=",
                        "-p",
                        "no:randomly",
                        "-q",
                        "--tb=no",
                    ],
                    cwd=isolated,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            finally:
                path.write_text(original)
            if (
                result.returncode == 1
                and "\nFAILED " in result.stdout
                and "\nERROR " not in result.stdout
            ):
                killed[group] += 1
                print(f"mutation: killed {variant.name}")
            elif result.returncode == 0:
                print(f"mutation: survived {variant.name}")
            else:
                print(f"mutation: invalid run for {variant.name} ({result.returncode})")
                print(result.stdout[-1200:])
                return 1
    for group, total in subjects.items():
        print(f"mutation: {group} selected rules {killed[group]}/{total} killed")
    return int(
        killed["kernel"] * 100 < subjects["kernel"] * 85
        or killed["capabilities"] * 100 < subjects["capabilities"] * 80
    )

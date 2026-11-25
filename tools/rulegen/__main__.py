"""CLI entry point for the evaluator generator (P06-T04)."""

from __future__ import annotations

import sys

from tools.rulegen import regenerate


def main() -> int:
    """Regenerate the evaluator files."""
    return regenerate()


if __name__ == "__main__":
    sys.exit(main())

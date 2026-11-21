"""CLI entry point for the schema generator.

Usage::

    python -m tools.schemagen          # regenerate all models
    python -m tools.schemagen --check  # regenerate and verify byte-identical
"""

from __future__ import annotations

import sys

from tools.schemagen.generator import regenerate


def main() -> int:
    """Run the schema generator."""
    return regenerate()


if __name__ == "__main__":
    sys.exit(main())

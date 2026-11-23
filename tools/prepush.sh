#!/usr/bin/env bash
set -euo pipefail

echo "=== Pre-push gate check (strict) ==="

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

uv run python -m tools.gate run phase

echo "=== All gates green. Push allowed. ==="

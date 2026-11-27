#!/usr/bin/env bash
set -euo pipefail

echo "=== Pre-push gate check (strict) ==="

# Gate tests create independent Git repositories. Let Git discover each one
# from its working directory instead of inheriting the pushing worktree.
git_local_env=$(git rev-parse --local-env-vars)
while IFS= read -r variable; do
  unset "$variable"
done <<< "$git_local_env"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

uv run python -m tools.gate run phase

echo "=== All gates green. Push allowed. ==="

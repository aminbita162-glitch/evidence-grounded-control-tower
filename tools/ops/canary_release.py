"""Exercise a local image by digest and promote or roll back its active pointer."""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Callable
from pathlib import Path

import httpx

from tools.canary import ERROR_BUDGETS
from tools.ops.exit_drill import DrillError, run_command, run_exit_drill
from tools.ops.rollback import ReleaseError, append_decision, validate_digest

_ERROR_BUDGET = float(next(row["budget"] for row in ERROR_BUDGETS if row["name"] == "api_errors"))


def probe_digest(digest: str) -> bool:
    """Run the same deployment bundle using the verified local image contents."""
    validate_digest(digest)
    try:
        actual = run_command(["docker", "image", "inspect", "--format", "{{.Id}}", digest])
        if actual != digest:
            return False
        tag = f"control-tower-canary:{digest[7:]}"
        run_command(["docker", "image", "tag", digest, tag])
        return bool(run_exit_drill(tag).get("bundle_hash"))
    except DrillError, httpx.HTTPError:
        return False


def release(
    database: Path,
    previous: str,
    candidate: str,
    error_rate: float,
    probe: Callable[[str], bool] = probe_digest,
) -> dict[str, object]:
    """Update the active digest only after the canary and error budget pass."""
    validate_digest(previous)
    validate_digest(candidate)
    if not math.isfinite(error_rate) or not 0 <= error_rate <= 1:
        raise ReleaseError("RELEASE_ERROR_RATE_INVALID")
    if error_rate > _ERROR_BUDGET:
        if not probe(previous):
            raise ReleaseError("RELEASE_ROLLBACK_UNHEALTHY")
        return append_decision(database, previous, candidate, "ROLLED_BACK", "ERROR_BUDGET")
    if probe(candidate):
        return append_decision(database, previous, candidate, "PROMOTED", "CANARY_PASSED")
    if not probe(previous):
        raise ReleaseError("RELEASE_ROLLBACK_UNHEALTHY")
    return append_decision(database, previous, candidate, "ROLLED_BACK", "CANARY_FAILED")


def main() -> None:
    """Evaluate a release using only the local Docker bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment-chain", required=True, type=Path)
    parser.add_argument("--previous", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--error-rate", required=True, type=float)
    args = parser.parse_args()
    try:
        result = release(args.deployment_chain, args.previous, args.candidate, args.error_rate)
    except ReleaseError as exc:
        raise SystemExit(str(exc)) from None
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()

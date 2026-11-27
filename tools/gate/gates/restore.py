"""Phase 12 gate for measured recovery and second-host portability."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from tools.ops.backup import BackupError
from tools.ops.exit_drill import DrillError, run_exit_drill
from tools.ops.restore_drill import RPO_SECONDS, RTO_SECONDS, run_restore_drill

_ROOT = Path(__file__).resolve().parents[3]


def verify_measurements(report: object) -> None:
    """Require evidence of recovered records within both recovery objectives."""
    if not isinstance(report, dict):
        raise BackupError("RESTORE_EVIDENCE_INVALID")
    point = report.get("recovery_point_seconds")
    duration = report.get("recovery_time_seconds")
    records = report.get("records")
    if (
        type(point) is not int
        or not isinstance(duration, (int, float))
        or isinstance(duration, bool)
        or type(records) is not int
        or records <= 0
        or not 0 <= point <= RPO_SECONDS
        or not 0 < duration <= RTO_SECONDS
    ):
        raise BackupError("RESTORE_EVIDENCE_INVALID")


def main() -> int:
    """Run the drills or validate the gate self-test fixture."""
    try:
        if Path.cwd().resolve() == _ROOT:
            report = run_restore_drill()
            verify_measurements(report)
            portability = run_exit_drill()
            output = _ROOT / ".gate-logs" / "operations-drills.json"
            output.parent.mkdir(exist_ok=True)
            output.write_text(
                json.dumps({"restore": report, "exit": portability}, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
        elif os.environ.get("GATE_ROOT") and Path(os.environ["GATE_ROOT"]).resolve() == Path.cwd():
            verify_measurements(json.loads(Path("restore.json").read_text()))
        else:
            raise BackupError("RESTORE_RUN_FROM_PROJECT_ROOT")
    except (OSError, ValueError, BackupError, DrillError) as exc:
        print(f"restore: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Named interruption points for packaging and recovery operations."""

from __future__ import annotations

import hashlib

from tools.faultlab import FaultLab

OPERATIONS_KILL_POINTS = {
    "during_backup": "No incomplete backup is published",
    "during_restore": "An interrupted recovery leaves no accessible target",
    "during_migration": "An interrupted migration never starts the application",
}


def register_operations(lab: FaultLab) -> None:
    """Register the operations points and their expected clean state."""
    expected = hashlib.sha256(b"unusable-but-clean").hexdigest()
    for name, description in OPERATIONS_KILL_POINTS.items():
        lab.register_kill_point(name, description)
        lab.register_scenario(name, expected, description)

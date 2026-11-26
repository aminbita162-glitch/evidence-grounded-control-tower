"""Scenario review packets and status (P09-T08).

``generate_packet(capability_id, scenarios_dir)`` generates from the
scenario files a review packet for one capability: a table of its
scenarios (id, kind, inputs in readable form, expected outcome, reason
codes, the basis) and the list of its metamorphic relations and
differential references.  No code, reproducible byte for byte.

``compute_status(scenario_hashes, review_lines)`` computes for every
capability the hash of its canonical scenario set and compares it with
the lines of the owner-only file ``docs/decisions/scenario-reviews.md``
(line: capability id, scenario-set hash, reviewer kind, month,
reference).  Status: REVIEWED when a line carries the current hash,
CHANGED_SINCE_REVIEW when only an older hash exists, UNREVIEWED
otherwise.  The status file is written by the gate script only.  The
agent never writes ``scenario-reviews.md`` and never sets a status by
hand.

Spec: Part 3 §3.12; Part 6 §6.11; P09-T08.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from data.scenarios import Scenario, load_scenarios

__all__ = [
    "ReviewPacket",
    "ReviewStatus",
    "ReviewLine",
    "generate_packet",
    "packet_hash",
    "compute_status",
    "save_status",
    "REVIEWED",
    "CHANGED_SINCE_REVIEW",
    "UNREVIEWED",
    "StatusError",
]

#: Review status constants.
REVIEWED: str = "REVIEWED"
CHANGED_SINCE_REVIEW: str = "CHANGED_SINCE_REVIEW"
UNREVIEWED: str = "UNREVIEWED"

#: Valid reviewer kinds.
_VALID_KINDS: frozenset[str] = frozenset({"OWNER", "INDEPENDENT_REVIEW"})


class StatusError(Exception):
    """Raised when a review line is malformed or references an unknown kind."""


@dataclass(frozen=True)
class ReviewLine:
    """A line from the owner-only ``scenario-reviews.md`` file.

    Attributes:
        capability_id: The capability identifier.
        scenario_set_hash: The scenario-set hash at review time.
        reviewer_kind: ``OWNER`` or ``INDEPENDENT_REVIEW``.
        month: The review month (e.g. ``2026-11``).
        reference: A reference to the review report (optional).
    """

    capability_id: str
    scenario_set_hash: str
    reviewer_kind: str
    month: str
    reference: str = ""


@dataclass
class ReviewPacket:
    """A review packet for one capability.

    Attributes:
        capability_id: The capability identifier.
        scenarios: A list of scenario summaries.
        metamorphic_relations: A list of metamorphic relation ids.
        differential_references: A list of differential reference ids.
    """

    capability_id: str = ""
    scenarios: list[dict[str, object]] = field(default_factory=list)
    metamorphic_relations: list[str] = field(default_factory=list)
    differential_references: list[str] = field(default_factory=list)


@dataclass
class ReviewStatus:
    """The review status for one capability.

    Attributes:
        capability_id: The capability identifier.
        status: ``REVIEWED``, ``CHANGED_SINCE_REVIEW`` or ``UNREVIEWED``.
        current_hash: The current scenario-set hash.
        reviewed_hash: The hash from the last review (empty if unreviewed).
    """

    capability_id: str = ""
    status: str = UNREVIEWED
    current_hash: str = ""
    reviewed_hash: str = ""


def _scenario_summary(sc: Scenario) -> dict[str, object]:
    """Convert a scenario to a readable summary dict (no code)."""
    return {
        "id": sc.id,
        "kind": sc.kind,
        "inputs": [
            str(inp) if not isinstance(inp, dict) else json.dumps(inp, sort_keys=True)
            for inp in sc.inputs
        ],
        "expected_outcome": sc.expected_outcome,
        "reason_codes": [],
        "basis": sc.basis,
        "test_id": sc.test_id,
    }


def generate_packet(capability_id: str, scenarios_dir: Path) -> ReviewPacket:
    """Generate a review packet for one capability.

    Args:
        capability_id: The capability identifier.
        scenarios_dir: The directory containing scenario JSON files.

    Returns:
        A :class:`ReviewPacket` with scenario summaries (no code).
    """
    scenarios = load_scenarios(scenarios_dir)
    relevant = [sc for sc in scenarios if capability_id in sc.capability_ids]
    return ReviewPacket(
        capability_id=capability_id,
        scenarios=[_scenario_summary(sc) for sc in sorted(relevant, key=lambda s: s.id)],
        metamorphic_relations=[],
        differential_references=[],
    )


def packet_hash(packet: ReviewPacket) -> str:
    """Compute a deterministic hash of a review packet.

    Args:
        packet: The review packet.

    Returns:
        A SHA-256 hex string.
    """
    payload = json.dumps(
        {
            "capability_id": packet.capability_id,
            "scenarios": packet.scenarios,
            "metamorphic_relations": packet.metamorphic_relations,
            "differential_references": packet.differential_references,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def compute_status(
    current_hash: str,
    review_lines: list[ReviewLine],
    capability_id: str,
) -> ReviewStatus:
    """Compute the review status for one capability.

    Args:
        current_hash: The current scenario-set hash.
        review_lines: All review lines from the owner-only file.
        capability_id: The capability identifier.

    Returns:
        A :class:`ReviewStatus`.

    Raises:
        StatusError: If a review line for this capability has an unknown
            reviewer kind or a malformed hash.
    """
    cap_lines = [rl for rl in review_lines if rl.capability_id == capability_id]
    for rl in cap_lines:
        if rl.reviewer_kind not in _VALID_KINDS:
            raise StatusError(
                f"unknown reviewer kind: {rl.reviewer_kind} for capability {capability_id}"
            )
        if len(rl.scenario_set_hash) != 64:
            raise StatusError(
                f"malformed hash for capability {capability_id}: len={len(rl.scenario_set_hash)}"
            )
        try:
            int(rl.scenario_set_hash, 16)
        except ValueError as exc:
            raise StatusError(f"malformed hash for capability {capability_id}") from exc

    if not cap_lines:
        return ReviewStatus(
            capability_id=capability_id,
            status=UNREVIEWED,
            current_hash=current_hash,
            reviewed_hash="",
        )

    if any(rl.scenario_set_hash == current_hash for rl in cap_lines):
        return ReviewStatus(
            capability_id=capability_id,
            status=REVIEWED,
            current_hash=current_hash,
            reviewed_hash=current_hash,
        )

    return ReviewStatus(
        capability_id=capability_id,
        status=CHANGED_SINCE_REVIEW,
        current_hash=current_hash,
        reviewed_hash=cap_lines[0].scenario_set_hash,
    )


def save_status(statuses: list[ReviewStatus], path: Path) -> None:
    """Save review statuses to a JSON file.

    The status file is written by the gate script only; the agent never
    sets a status by hand.

    Args:
        statuses: A list of :class:`ReviewStatus` entries.
        path: The output file path (``docs/state/scenario-review-status.json``).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, object] = {
        "statuses": [
            {
                "capability_id": s.capability_id,
                "status": s.status,
                "current_hash": s.current_hash,
                "reviewed_hash": s.reviewed_hash,
            }
            for s in sorted(statuses, key=lambda s: s.capability_id)
        ],
    }
    path.write_text(
        json.dumps(data, sort_keys=True, indent=2, separators=(",", ": ")) + "\n",
        encoding="utf-8",
    )

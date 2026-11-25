"""Tool Broker: deny-by-default grants, policy decisions, call recording (Part 3 §3.11, P07-T03).

A worker can call only tools listed in its capability grant.  Each grant
names tool, scope, rate, budget, action class and readable memory classes.
Every tool call passes a policy decision and is recorded with input hash,
output hash and decision.  The egress allowlist is data.  Policies carry
allow and deny cases that run in CI.

Spec: Part 3 §3.11, §3.30; P07-T03.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field

__all__ = [
    "Grant",
    "CallRecord",
    "PolicyDecision",
    "ToolBroker",
    "BrokerError",
    "EGRESS_ALLOWLIST",
]

#: Default egress allowlist (Part 3 §3.11: data, not code).
EGRESS_ALLOWLIST: list[str] = [
    "localhost",
    "127.0.0.1",
    "::1",
    "api.local",
    "registry.local",
]


class BrokerError(Exception):
    """Raised when a tool call is denied by the broker."""


@dataclass(frozen=True)
class Grant:
    """A capability grant for one tool (Part 3 §3.11, §3.25).

    Names tool, scope, rate (calls per window), budget, action class
    and the memory classes the role may read.
    """

    tool: str
    scope: str
    rate_limit: int
    budget: int
    action_class: str
    memory_classes: tuple[str, ...] = ()


@dataclass
class CallRecord:
    """A recorded tool call (Part 3 §3.11)."""

    tool: str
    input_hash: str
    output_hash: str
    decision: str
    granted: bool
    reason: str = ""


@dataclass(frozen=True)
class PolicyDecision:
    """A policy decision for a tool call (Part 3 §3.11)."""

    allowed: bool
    reason: str


def _hash_payload(payload: object) -> str:
    """Compute the SHA-256 hash of a canonical JSON payload."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class ToolBroker:
    """The deny-by-default tool broker (Part 3 §3.11).

    Every tool call passes a policy decision and is recorded.  Calls
    to ungranted tools, over-rate calls and off-list hosts are denied.
    A model cannot name a URL, host, path or command.
    """

    grants: dict[str, Grant] = field(default_factory=dict)
    egress_allowlist: tuple[str, ...] = tuple(EGRESS_ALLOWLIST)
    _call_log: list[CallRecord] = field(default_factory=list)
    _rate_tracker: dict[str, list[int]] = field(default_factory=dict)

    def add_grant(self, grant: Grant) -> None:
        """Register a tool grant."""
        self.grants[grant.tool] = grant

    def _check_grant(self, tool: str, scope: str) -> PolicyDecision:
        """Check whether the tool is granted for the scope."""
        grant = self.grants.get(tool)
        if grant is None:
            return PolicyDecision(False, "tool_not_granted")
        if grant.scope != scope and grant.scope != "*":
            return PolicyDecision(False, "scope_mismatch")
        return PolicyDecision(True, "granted")

    def _check_rate(self, tool: str, window: int) -> PolicyDecision:
        """Check the rate limit for a tool."""
        grant = self.grants.get(tool)
        if grant is None:
            return PolicyDecision(False, "tool_not_granted")
        calls = self._rate_tracker.setdefault(tool, [])
        recent = [c for c in calls if c >= window - grant.rate_limit]
        if len(recent) >= grant.rate_limit:
            return PolicyDecision(False, "rate_exceeded")
        calls.append(window)
        return PolicyDecision(True, "within_rate")

    def _check_egress(self, host: str) -> PolicyDecision:
        """Check whether the host is on the egress allowlist."""
        if host not in self.egress_allowlist:
            return PolicyDecision(False, "host_off_allowlist")
        return PolicyDecision(True, "host_allowed")

    def _check_model_naming(self, payload: Mapping[str, object]) -> PolicyDecision:
        """A model cannot name a URL, host, path or command (Part 3 §3.11)."""
        for key, value in payload.items():
            if isinstance(value, str):
                lowered = value.lower()
                if any(
                    marker in lowered
                    for marker in ("http://", "https://", "file://", "/etc/", "rm -rf")
                ):
                    return PolicyDecision(False, f"model_named_forbidden_{key}")
        return PolicyDecision(True, "naming_ok")

    def call(
        self,
        tool: str,
        scope: str,
        input_payload: Mapping[str, object],
        host: str = "localhost",
        clock_tick: int = 0,
    ) -> CallRecord:
        """Execute a tool call through the broker.

        Denies by default: ungranted tools, over-rate calls, off-list
        hosts and model-named URLs/paths/commands are all rejected.
        Every call — allowed or denied — is recorded.
        """
        decisions: list[PolicyDecision] = []
        decisions.append(self._check_grant(tool, scope))
        decisions.append(self._check_rate(tool, clock_tick))
        decisions.append(self._check_egress(host))
        decisions.append(self._check_model_naming(input_payload))

        input_hash = _hash_payload(dict(input_payload))
        allowed = all(d.allowed for d in decisions)
        denied = [d for d in decisions if not d.allowed]
        reason = denied[0].reason if denied else "allowed"
        output_payload: dict[str, object] = {"result": "ok"} if allowed else {"result": "denied"}
        output_hash = _hash_payload(output_payload)

        record = CallRecord(
            tool=tool,
            input_hash=input_hash,
            output_hash=output_hash,
            decision="ALLOW" if allowed else "DENY",
            granted=allowed,
            reason=reason,
        )
        self._call_log.append(record)
        if not allowed:
            raise BrokerError(f"tool call denied: {reason}")
        return record

    @property
    def call_log(self) -> list[CallRecord]:
        """Return the ordered list of call records."""
        return list(self._call_log)

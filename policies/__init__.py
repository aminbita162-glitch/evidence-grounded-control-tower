"""Policy-as-code: allow and deny cases for every policy (Part 3 §3.11, P07-T03).

Policies are data under test: each policy has allow and deny cases that
run in CI.  The policy engine evaluates a decision against the cases and
returns ALLOW or DENY with a reason.

Spec: Part 3 §3.11, §3.30; P07-T03.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "PolicyCase",
    "Policy",
    "POLICIES",
    "evaluate_policy",
    "PolicyError",
]


class PolicyError(ValueError):
    """Raised when a policy is malformed or a case fails unexpectedly."""


@dataclass(frozen=True)
class PolicyCase:
    """A single test case for a policy (allow or deny)."""

    name: str
    input_data: dict[str, object]
    expected: str  # "ALLOW" or "DENY"


@dataclass
class Policy:
    """A named policy with allow and deny cases (Part 3 §3.11)."""

    name: str
    description: str
    allow_cases: list[PolicyCase] = field(default_factory=list)
    deny_cases: list[PolicyCase] = field(default_factory=list)

    @property
    def all_cases(self) -> list[PolicyCase]:
        """Return all cases (allow and deny)."""
        return [*self.allow_cases, *self.deny_cases]


# ---- Policy definitions ----------------------------------------------------

POLICIES: dict[str, Policy] = {
    "tool_grant": Policy(
        name="tool_grant",
        description="A worker may call only tools listed in its grant.",
        allow_cases=[
            PolicyCase("granted_tool", {"tool": "lookup", "granted": True}, "ALLOW"),
        ],
        deny_cases=[
            PolicyCase("ungranted_tool", {"tool": "delete", "granted": False}, "DENY"),
        ],
    ),
    "rate_limit": Policy(
        name="rate_limit",
        description="A tool call exceeding the rate limit is denied.",
        allow_cases=[
            PolicyCase("within_rate", {"tool": "lookup", "calls": 1, "limit": 10}, "ALLOW"),
        ],
        deny_cases=[
            PolicyCase("over_rate", {"tool": "lookup", "calls": 11, "limit": 10}, "DENY"),
        ],
    ),
    "egress_allowlist": Policy(
        name="egress_allowlist",
        description="Outbound network access goes only to hosts on the egress allowlist.",
        allow_cases=[
            PolicyCase("on_list", {"host": "localhost", "allowed": True}, "ALLOW"),
        ],
        deny_cases=[
            PolicyCase("off_list", {"host": "evil.example.com", "allowed": False}, "DENY"),
        ],
    ),
    "model_naming": Policy(
        name="model_naming",
        description="A model cannot name a URL, host, path or command.",
        allow_cases=[
            PolicyCase("plain_text", {"text": "hello world", "forbidden": False}, "ALLOW"),
        ],
        deny_cases=[
            PolicyCase("url_in_text", {"text": "https://evil.com", "forbidden": True}, "DENY"),
        ],
    ),
}


def evaluate_policy(policy_name: str, input_data: dict[str, object]) -> str:
    """Evaluate a policy decision against its cases.

    Returns "ALLOW" or "DENY" based on whether the input matches an
    allow case or a deny case.

    Raises PolicyError if the policy does not exist.
    """
    policy = POLICIES.get(policy_name)
    if policy is None:
        raise PolicyError(f"unknown policy: {policy_name!r}")

    for case in policy.allow_cases:
        if _match(case.input_data, input_data):
            return "ALLOW"
    for case in policy.deny_cases:
        if _match(case.input_data, input_data):
            return "DENY"
    return "DENY"


def _match(pattern: dict[str, object], actual: dict[str, object]) -> bool:
    """Check whether *actual* matches the *pattern* for all keys in the pattern."""
    for key, value in pattern.items():
        if key not in actual:
            return False
        if actual[key] != value:
            return False
    return True


def run_policy_tests() -> list[tuple[str, str, str, bool]]:
    """Run every policy case and return (policy, case, expected, passed).

    A policy passes when every allow case evaluates to ALLOW and every
    deny case evaluates to DENY.
    """
    results: list[tuple[str, str, str, bool]] = []
    for name, policy in POLICIES.items():
        for case in policy.all_cases:
            decision = evaluate_policy(name, dict(case.input_data))
            passed = decision == case.expected
            results.append((name, case.name, case.expected, passed))
    return results

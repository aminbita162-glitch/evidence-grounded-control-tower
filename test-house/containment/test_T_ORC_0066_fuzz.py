"""Short fuzz of messages against the runtime and broker (P07-T05).

Test ID: T-ORC-0066.
Covers: short fuzz of messages finds no crash in the agent runtime,
tool broker, or autonomy policy under random inputs.

Spec: Part 3 §3.30; Part 4 §4.5; P07-T05.
"""

from __future__ import annotations

import contextlib
import random
import string

import pytest

from agents.runtime import ROLE_CONTRACTS, RoleRuntime, RuntimeError_
from broker import BrokerError, Grant, ToolBroker
from kernel.containment.autonomy import AutonomyError, AutonomyPolicy

# ---------------------------------------------------------------------------
# T-ORC-0066 — Short fuzz of messages finds no crash
# ---------------------------------------------------------------------------
# id: T-ORC-0066
# title: Short fuzz of messages finds no crash
# purpose: Verify that random/fuzz messages to the runtime, broker and
#          autonomy policy do not crash (they may raise typed errors).
# level: fast
# requirement: P07-T05, Part 3 §3.30, Part 4 §4.5
# input: 200 random messages to the runtime, broker and autonomy policy
# expected: no unhandled exception (crash); typed errors are acceptable
# risk: crash under adversarial input
# capability: orchestration


@pytest.mark.fast
def test_T_ORC_0066_fuzz_no_crash() -> None:
    """Short fuzz of messages finds no crash."""
    rng = random.Random(42)
    broker = ToolBroker()
    broker.add_grant(Grant("lookup", "read", rate_limit=100, budget=100, action_class="R"))

    for _ in range(200):
        choice = rng.randint(0, 2)
        if choice == 0:
            contract = rng.choice(list(ROLE_CONTRACTS.values()))
            rt = RoleRuntime(contract)
            msg = {f"k{i}": "".join(rng.choices(string.printable[:50], k=10)) for i in range(3)}
            with contextlib.suppress(RuntimeError_):
                rt.receive(msg)
        elif choice == 1:
            with contextlib.suppress(BrokerError):
                broker.call("lookup", "read", {"k": rng.randint(0, 1000)}, clock_tick=0)
        else:
            with contextlib.suppress(AutonomyError):
                level = rng.choice(["A0", "A1", "A2", "A3"])
                AutonomyPolicy("t1", "cap1", level=level)  # type: ignore[arg-type]

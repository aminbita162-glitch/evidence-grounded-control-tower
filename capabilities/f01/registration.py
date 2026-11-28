"""Uniform Consistency Graph registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from api.routes.capability import CapabilityInvocation
    from capabilities.k14.workflow import IntakeWorkflow

CAPABILITY_ID = "F01"


def register(workflow: IntakeWorkflow) -> CapabilityInvocation:
    from api.routes.capability import intake_invocation

    return intake_invocation(CAPABILITY_ID, workflow)

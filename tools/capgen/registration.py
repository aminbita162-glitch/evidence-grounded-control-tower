"""Bind a generated synthetic entry to the uniform capability invocation."""

from api.routes.capability import CapabilityInvocation, CapabilityResponse, InvokeRequest
from kernel.auth.roles import Principal
from kernel.skeleton import WalkingSkeleton


def synthetic_registration(capability_id: str) -> CapabilityInvocation:
    """Return a handler that runs the recorded, synthetic skeleton case."""

    async def invoke(_principal: Principal, _request: InvokeRequest) -> CapabilityResponse:
        result = await WalkingSkeleton().run()
        if not (result.structural_ok and result.bundle_ok and result.replay_ok):
            raise RuntimeError("synthetic case verification failed")
        return CapabilityResponse(
            capability_id=capability_id,
            case_id=result.case_id,
            status="COMPLETED",
            label="SYNTHETIC",
        )

    return invoke

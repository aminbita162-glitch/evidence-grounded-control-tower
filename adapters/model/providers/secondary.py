"""Second commercial provider adapter (D-06, P08-T02).

Mock adapter for the exit path.  Switching the provider is configuration only.
"""

from __future__ import annotations

import hashlib

from adapters.model.gateway import ModelCallRequest, ModelCallResponse, compute_prompt_hash

__all__ = ["SecondaryAdapter"]


class SecondaryAdapter:
    """Second commercial provider adapter (mock for CI)."""

    provider: str = "secondary"
    model_id: str = "secondary-v2.1.0"
    processing_region: str = "eu"

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        """Return a deterministic mock response based on the prompt hash."""
        ph = compute_prompt_hash(request.prompt)
        payload: dict[str, object] = {
            "prompt_hash": ph[:8],
            "provider": "secondary",
        }
        resp_hash = hashlib.sha256(f"secondary:{ph}".encode()).hexdigest()
        return ModelCallResponse(
            prompt_hash=ph,
            response_hash=resp_hash,
            response_payload=payload,
            tokens_input=len(request.prompt) // 4,
            tokens_output=2,
            cost=0.001,
        )

"""Primary commercial provider adapter (D-06, P08-T02).

Mock adapter that produces deterministic responses for CI.
Model identifiers are pinned by exact version in configuration.
"""

from __future__ import annotations

import hashlib

from adapters.model.gateway import ModelCallRequest, ModelCallResponse, compute_prompt_hash

__all__ = ["PrimaryAdapter"]


class PrimaryAdapter:
    """Primary commercial provider adapter (mock for CI)."""

    provider: str = "primary"
    model_id: str = "primary-v1.0.0"
    processing_region: str = "us"

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        """Return a deterministic mock response based on the prompt hash."""
        ph = compute_prompt_hash(request.prompt)
        payload: dict[str, object] = {
            "prompt_hash": ph[:8],
            "provider": "primary",
        }
        resp_hash = hashlib.sha256(f"primary:{ph}".encode()).hexdigest()
        return ModelCallResponse(
            prompt_hash=ph,
            response_hash=resp_hash,
            response_payload=payload,
            tokens_input=len(request.prompt) // 4,
            tokens_output=2,
            cost=0.001,
        )

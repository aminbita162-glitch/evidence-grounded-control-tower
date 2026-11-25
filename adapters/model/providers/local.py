"""Locally hosted open-weights model adapter (D-06, P08-T02).

The local adapter declares processing region ``local`` and is used when
tenants forbid external processing.
"""

from __future__ import annotations

import hashlib

from adapters.model.gateway import ModelCallRequest, ModelCallResponse, compute_prompt_hash

__all__ = ["LocalAdapter"]


class LocalAdapter:
    """Locally hosted open-weights model adapter (mock for CI)."""

    provider: str = "local"
    model_id: str = "local-openweights-v1.0"
    processing_region: str = "local"

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        """Return a deterministic mock response based on the prompt hash."""
        ph = compute_prompt_hash(request.prompt)
        payload: dict[str, object] = {
            "prompt_hash": ph[:8],
            "provider": "local",
        }
        resp_hash = hashlib.sha256(f"local:{ph}".encode()).hexdigest()
        return ModelCallResponse(
            prompt_hash=ph,
            response_hash=resp_hash,
            response_payload=payload,
            tokens_input=len(request.prompt) // 4,
            tokens_output=2,
            cost=0.0,
        )

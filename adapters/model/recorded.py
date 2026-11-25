"""Recorded-response adapter — replays by prompt hash (D-06, P08-T01).

The recorded-response adapter is keyed by prompt hash.  In recorded mode
an unknown prompt fails closed (raises :class:`RecordedResponseError`).
CI runs on recordings — no live key is used.

Spec: D-06 S1; P08-T01.
"""

from __future__ import annotations

from collections.abc import Mapping

from adapters.model.gateway import (
    ModelCallRequest,
    ModelCallResponse,
    compute_prompt_hash,
)

__all__ = [
    "RecordedResponseAdapter",
    "RecordedResponseError",
]


class RecordedResponseError(Exception):
    """An unknown prompt was passed to the recorded adapter."""


class RecordedResponseAdapter:
    """Replays recorded model responses by prompt hash.

    Implements :class:`~adapters.model.gateway.GatewayPort`.
    """

    provider: str = "recorded"
    model_id: str = "recorded"
    processing_region: str = "local"

    def __init__(self, recordings: Mapping[str, ModelCallResponse]) -> None:
        self._recordings: dict[str, ModelCallResponse] = dict(recordings)

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        """Replay a recorded response for the given prompt.

        Raises:
            RecordedResponseError: If the prompt hash is not in recordings.
        """
        prompt_hash = compute_prompt_hash(request.prompt)
        response = self._recordings.get(prompt_hash)
        if response is None:
            raise RecordedResponseError(f"unknown prompt in recorded mode: {prompt_hash[:8]}")
        return response

    @classmethod
    def from_pairs(
        cls,
        pairs: list[tuple[str, ModelCallResponse]],
    ) -> RecordedResponseAdapter:
        """Build an adapter from (prompt_text, response) pairs."""
        recordings: dict[str, ModelCallResponse] = {}
        for prompt_text, response in pairs:
            ph = compute_prompt_hash(prompt_text)
            recordings[ph] = response
        return cls(recordings)

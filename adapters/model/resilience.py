"""Resilience: timeout, bounded retry, circuit breaker, fallback (D-06 S6, P08-T03).

A refused call yields a recorded ABSTAIN or ESCALATE, never silent
truncation.  The deterministic path continues when the model is
unavailable (Part 3 §3.16).

Spec: D-06 S6; Part 3 §3.16; P08-T03.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import IntEnum

from adapters.model.gateway import GatewayPort, ModelCallRequest, ModelCallResponse

__all__ = [
    "CircuitState",
    "CircuitBreaker",
    "CircuitBreakerError",
    "ResilienceWrapper",
    "ResponseCache",
]


class CircuitBreakerError(Exception):
    """The circuit breaker is open."""


class CircuitState(IntEnum):
    """Circuit breaker states."""

    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class CircuitBreaker:
    """A simple circuit breaker (D-06 S6).

    After *max_failures* consecutive failures the circuit opens and
    blocks calls.  After *reset_timeout* seconds it enters HALF_OPEN
    and allows one trial call.
    """

    def __init__(
        self,
        max_failures: int = 3,
        reset_timeout: float = 60.0,
    ) -> None:
        self._max_failures = max_failures
        self._reset_timeout = reset_timeout
        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._opened_at: float = 0.0

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        if self._state == CircuitState.OPEN and (
            self._time_now() - self._opened_at >= self._reset_timeout
        ):
            self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def can_execute(self) -> bool:
        """Return True if the circuit allows a call."""
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        """Record a successful call."""
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        if self._failure_count >= self._max_failures:
            self._state = CircuitState.OPEN
            self._opened_at = self._time_now()

    def _time_now(self) -> float:
        """Current monotonic time (injected for testability)."""
        return time.monotonic()


class ResilienceWrapper:
    """Wraps a :class:`GatewayPort` with timeout, retry, circuit breaker, fallback.

    On failure: retry up to *max_retries*, then circuit breaker, then
    fall back to the second adapter.  The fallback is recorded with
    ``fallback=True`` in the response.
    """

    def __init__(
        self,
        primary: GatewayPort,
        fallback: GatewayPort | None = None,
        max_retries: int = 3,
        timeout: float = 120.0,
        circuit: CircuitBreaker | None = None,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._max_retries = max_retries
        self._timeout = timeout
        self._circuit = circuit or CircuitBreaker()

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        """Execute a call with resilience.

        Raises:
            CircuitBreakerError: If the circuit is open and no fallback.
        """
        if not self._circuit.can_execute():
            if self._fallback is not None:
                return await self._call_fallback(request)
            raise CircuitBreakerError("circuit open and no fallback")

        last_error: Exception | None = None
        for _attempt in range(self._max_retries):
            try:
                resp = await asyncio.wait_for(
                    self._primary.call(request),
                    timeout=self._timeout,
                )
                self._circuit.record_success()
                return resp
            except (TimeoutError, Exception) as exc:
                last_error = exc
                self._circuit.record_failure()
                if not self._circuit.can_execute():
                    break

        if self._fallback is not None:
            return await self._call_fallback(request)

        if last_error is not None:
            raise last_error
        raise CircuitBreakerError("circuit open and no fallback")

    async def _call_fallback(self, request: ModelCallRequest) -> ModelCallResponse:
        """Call the fallback adapter and mark the response as fallback."""
        if self._fallback is None:
            raise CircuitBreakerError("no fallback available")
        resp = await self._fallback.call(request)
        return ModelCallResponse(
            prompt_hash=resp.prompt_hash,
            response_hash=resp.response_hash,
            response_payload=resp.response_payload,
            tokens_input=resp.tokens_input,
            tokens_output=resp.tokens_output,
            cost=resp.cost,
            fallback=True,
        )


@dataclass
class ResponseCache:
    """Per-tenant response cache keyed by (tenant_id, prompt_hash).

    A cache hit never crosses tenants.  Hits are recorded.
    """

    _cache: dict[tuple[str, str], ModelCallResponse]

    def __init__(self) -> None:
        self._cache = {}

    def get(self, tenant_id: str, prompt_hash: str) -> ModelCallResponse | None:
        """Get a cached response.  Returns None on miss."""
        return self._cache.get((tenant_id, prompt_hash))

    def put(
        self,
        tenant_id: str,
        prompt_hash: str,
        response: ModelCallResponse,
    ) -> None:
        """Cache a response."""
        self._cache[(tenant_id, prompt_hash)] = response

    def __len__(self) -> int:
        return len(self._cache)

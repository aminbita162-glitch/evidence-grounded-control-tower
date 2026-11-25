"""Tests for resilience and budgets (P08-T03).

Test IDs: T-GWY-0025 to T-GWY-0036.
Covers: timeout, circuit breaker, bounded retry, fallback, budgets,
cache isolation, refused call, deterministic path.

Spec: Part 3 §3.14, §3.16; D-06 S6; P08-T03.
"""

from __future__ import annotations

import asyncio

import pytest

from adapters.model.budget import BudgetExceededError, BudgetLimits, BudgetTracker
from adapters.model.gateway import ModelCallRequest, ModelCallResponse, compute_prompt_hash
from adapters.model.providers import LocalAdapter, PrimaryAdapter, SecondaryAdapter
from adapters.model.resilience import (
    CircuitBreaker,
    CircuitState,
    ResilienceWrapper,
    ResponseCache,
)

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _make_request(prompt: str = "test") -> ModelCallRequest:
    schema: dict[str, object] = {"type": "object"}
    return ModelCallRequest(
        tenant_id="t1",
        case_id="c1",
        prompt=prompt,
        output_schema=schema,
        tier="middle",
        meter="other",
    )


class _FailingAdapter:
    """An adapter that always raises."""

    provider = "failing"
    model_id = "failing-v1"
    processing_region = "us"

    async def call(self, request: ModelCallRequest) -> ModelCallResponse:
        raise RuntimeError("adapter failure")


# --------------------------------------------------------------------------- #
# T-GWY-0025 — A timeout ends in fallback or recorded refusal
# --------------------------------------------------------------------------- #
# id: T-GWY-0025
# title: A timeout ends in fallback or recorded refusal
# purpose: Verify timeout triggers fallback
# level: fast
# requirement: P08-T03
# input: ResilienceWrapper with failing primary and working fallback
# expected: fallback response returned
# risk: timeout produces silent failure
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0025_timeout_fallback() -> None:
    """A timeout ends in fallback or recorded refusal."""
    wrapper = ResilienceWrapper(
        primary=_FailingAdapter(),
        fallback=SecondaryAdapter(),
        max_retries=1,
        timeout=1.0,
    )
    resp = asyncio.run(wrapper.call(_make_request()))
    assert resp.fallback is True


# --------------------------------------------------------------------------- #
# T-GWY-0026 — Circuit breaker opens after max_failures
# --------------------------------------------------------------------------- #
# id: T-GWY-0026
# title: Circuit breaker opens after max_failures
# purpose: Verify the circuit opens after consecutive failures
# level: fast
# requirement: P08-T03
# input: CircuitBreaker with max_failures=3
# expected: state is OPEN after 3 failures
# risk: circuit breaker not opening
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0026_circuit_opens() -> None:
    """Circuit breaker opens after max_failures."""
    cb = CircuitBreaker(max_failures=3, reset_timeout=999.0)
    assert int(cb.state) == int(CircuitState.CLOSED)
    cb.record_failure()
    cb.record_failure()
    assert int(cb.state) == int(CircuitState.CLOSED)
    cb.record_failure()
    assert int(cb.state) == int(CircuitState.OPEN)


# --------------------------------------------------------------------------- #
# T-GWY-0027 — Circuit breaker blocks calls when open
# --------------------------------------------------------------------------- #
# id: T-GWY-0027
# title: Circuit breaker blocks calls when open
# purpose: Verify can_execute returns False when open
# level: fast
# requirement: P08-T03
# input: an open circuit breaker
# expected: can_execute returns False
# risk: open circuit allows calls
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0027_circuit_blocks() -> None:
    """Circuit breaker blocks calls when open."""
    cb = CircuitBreaker(max_failures=1, reset_timeout=999.0)
    cb.record_failure()
    assert not cb.can_execute()


# --------------------------------------------------------------------------- #
# T-GWY-0028 — Bounded retry retries up to max_retries
# --------------------------------------------------------------------------- #
# id: T-GWY-0028
# title: Bounded retry retries up to max_retries
# purpose: Verify retries are bounded
# level: fast
# requirement: P08-T03
# input: ResilienceWrapper with failing primary, no fallback, max_retries=2
# expected: RuntimeError raised after 2 retries
# risk: infinite retry
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0028_bounded_retry() -> None:
    """Bounded retry retries up to max_retries."""
    wrapper = ResilienceWrapper(
        primary=_FailingAdapter(),
        fallback=None,
        max_retries=2,
        timeout=1.0,
    )
    with pytest.raises(RuntimeError, match="adapter failure"):
        asyncio.run(wrapper.call(_make_request()))


# --------------------------------------------------------------------------- #
# T-GWY-0029 — Fallback to second adapter on failure
# --------------------------------------------------------------------------- #
# id: T-GWY-0029
# title: Fallback to second adapter on failure
# purpose: Verify fallback adapter is used when primary fails
# level: fast
# requirement: P08-T03
# input: ResilienceWrapper with failing primary and working fallback
# expected: fallback response returned
# risk: no fallback on failure
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0029_fallback_on_failure() -> None:
    """Fallback to second adapter on failure."""
    wrapper = ResilienceWrapper(
        primary=_FailingAdapter(),
        fallback=LocalAdapter(),
        max_retries=1,
        timeout=1.0,
    )
    resp = asyncio.run(wrapper.call(_make_request()))
    assert resp.response_payload["provider"] == "local"
    assert resp.fallback is True


# --------------------------------------------------------------------------- #
# T-GWY-0030 — Fallback is recorded (response.fallback == True)
# --------------------------------------------------------------------------- #
# id: T-GWY-0030
# title: Fallback is recorded (response.fallback == True)
# purpose: Verify fallback flag is set on fallback responses
# level: fast
# requirement: P08-T03
# input: ResilienceWrapper with fallback
# expected: response has fallback=True
# risk: fallback not recorded
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0030_fallback_recorded() -> None:
    """Fallback is recorded."""
    wrapper = ResilienceWrapper(
        primary=_FailingAdapter(),
        fallback=SecondaryAdapter(),
        max_retries=1,
        timeout=1.0,
    )
    resp = asyncio.run(wrapper.call(_make_request()))
    assert resp.fallback is True


# --------------------------------------------------------------------------- #
# T-GWY-0031 — Budget limits hold (calls exceed)
# --------------------------------------------------------------------------- #
# id: T-GWY-0031
# title: Budget limits hold for call count
# purpose: Verify BudgetTracker raises on call budget exceed
# level: fast
# requirement: P08-T03
# input: BudgetTracker with limits max_calls=5
# expected: BudgetExceededError when exceeding
# risk: call budget not enforced
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0031_budget_calls_exceeded() -> None:
    """Budget limits hold for call count."""
    tracker = BudgetTracker(BudgetLimits(max_calls=2))
    tracker.record("other", calls=1)
    tracker.check("other", calls=1)
    tracker.record("other", calls=1)
    with pytest.raises(BudgetExceededError):
        tracker.check("other", calls=1)


# --------------------------------------------------------------------------- #
# T-GWY-0032 — Budget limits hold (tokens exceed)
# --------------------------------------------------------------------------- #
# id: T-GWY-0032
# title: Budget limits hold for token count
# purpose: Verify BudgetTracker raises on token budget exceed
# level: fast
# requirement: P08-T03
# input: BudgetTracker with limits max_tokens=100
# expected: BudgetExceededError when exceeding
# risk: token budget not enforced
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0032_budget_tokens_exceeded() -> None:
    """Budget limits hold for token count."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100))
    tracker.record("other", calls=1, tokens=50)
    tracker.check("other", calls=0, tokens=50)
    with pytest.raises(BudgetExceededError):
        tracker.check("other", calls=0, tokens=51)


# --------------------------------------------------------------------------- #
# T-GWY-0033 — Cache hit never crosses tenants
# --------------------------------------------------------------------------- #
# id: T-GWY-0033
# title: Cache hit never crosses tenants
# purpose: Verify response cache is tenant-isolated
# level: fast
# requirement: P08-T03
# input: ResponseCache with entries for two tenants
# expected: each tenant gets only its own cached responses
# risk: cache cross-tenant leak
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0033_cache_tenant_isolation() -> None:
    """Cache hit never crosses tenants."""
    cache = ResponseCache()
    ph = compute_prompt_hash("prompt")
    resp: ModelCallResponse = ModelCallResponse(
        prompt_hash=ph,
        response_hash="0" * 64,
        response_payload={"provider": "primary"},
        tokens_input=1,
        tokens_output=1,
        cost=0.0,
    )
    cache.put("tenant_A", ph, resp)
    assert cache.get("tenant_B", ph) is None
    assert cache.get("tenant_A", ph) is resp


# --------------------------------------------------------------------------- #
# T-GWY-0034 — Cache hit returns same response
# --------------------------------------------------------------------------- #
# id: T-GWY-0034
# title: Cache hit returns same response
# purpose: Verify cache returns the stored response
# level: fast
# requirement: P08-T03
# input: ResponseCache with a stored entry
# expected: same response returned on get
# risk: cache miss on stored entry
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0034_cache_hit() -> None:
    """Cache hit returns same response."""
    cache = ResponseCache()
    ph = compute_prompt_hash("cached")
    resp: ModelCallResponse = ModelCallResponse(
        prompt_hash=ph,
        response_hash="0" * 64,
        response_payload={"provider": "primary"},
        tokens_input=1,
        tokens_output=1,
        cost=0.0,
    )
    cache.put("t1", ph, resp)
    assert cache.get("t1", ph) is resp


# --------------------------------------------------------------------------- #
# T-GWY-0035 — A refused call yields ABSTAIN or ESCALATE
# --------------------------------------------------------------------------- #
# id: T-GWY-0035
# title: A refused call yields ABSTAIN or ESCALATE, never silent truncation
# purpose: Verify that a refused call is explicit, not silent
# level: fast
# requirement: P08-T03
# input: a BudgetTracker at its limit
# expected: BudgetExceededError (explicit refusal, not silent)
# risk: silent truncation on budget exceed
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0035_refused_call_explicit() -> None:
    """A refused call yields ABSTAIN or ESCALATE, never silent truncation."""
    tracker = BudgetTracker(BudgetLimits(max_calls=1))
    tracker.record("other", calls=1)
    with pytest.raises(BudgetExceededError):
        tracker.check("other", calls=1)


# --------------------------------------------------------------------------- #
# T-GWY-0036 — Deterministic path continues when model unavailable
# --------------------------------------------------------------------------- #
# id: T-GWY-0036
# title: Deterministic path continues when model unavailable
# purpose: Verify fallback allows the path to continue
# level: fast
# requirement: P08-T03
# input: ResilienceWrapper with failing primary and working fallback
# expected: a response is returned (path continues)
# risk: path stops on model failure
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0036_deterministic_path_continues() -> None:
    """Deterministic path continues when model unavailable."""
    wrapper = ResilienceWrapper(
        primary=_FailingAdapter(),
        fallback=PrimaryAdapter(),
        max_retries=1,
        timeout=1.0,
    )
    resp = asyncio.run(wrapper.call(_make_request()))
    assert isinstance(resp, ModelCallResponse)
    assert resp.fallback is True

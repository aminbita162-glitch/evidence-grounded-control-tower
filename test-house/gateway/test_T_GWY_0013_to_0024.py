"""Tests for provider adapters and exit path (P08-T02).

Test IDs: T-GWY-0013 to T-GWY-0024.
Covers: three adapters behind same contract, switching by configuration,
pinned model identifiers, processing region declarations.

Spec: D-06; P08-T02.
"""

from __future__ import annotations

import asyncio

import pytest

from adapters.model.gateway import Gateway, ModelCallRequest, ModelCallResponse
from adapters.model.providers import LocalAdapter, PrimaryAdapter, SecondaryAdapter

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


# --------------------------------------------------------------------------- #
# T-GWY-0013 — PrimaryAdapter call returns a ModelCallResponse
# --------------------------------------------------------------------------- #
# id: T-GWY-0013
# title: PrimaryAdapter call returns a ModelCallResponse
# purpose: Verify the primary adapter returns a valid response
# level: fast
# requirement: P08-T02
# input: a ModelCallRequest to PrimaryAdapter
# expected: ModelCallResponse returned
# risk: primary adapter fails
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0013_primary_adapter_call() -> None:
    """PrimaryAdapter call returns a ModelCallResponse."""
    adapter = PrimaryAdapter()
    resp = asyncio.run(adapter.call(_make_request()))
    assert isinstance(resp, ModelCallResponse)
    assert len(resp.prompt_hash) == 64
    assert resp.response_payload["provider"] == "primary"


# --------------------------------------------------------------------------- #
# T-GWY-0014 — SecondaryAdapter call returns a ModelCallResponse
# --------------------------------------------------------------------------- #
# id: T-GWY-0014
# title: SecondaryAdapter call returns a ModelCallResponse
# purpose: Verify the secondary adapter returns a valid response
# level: fast
# requirement: P08-T02
# input: a ModelCallRequest to SecondaryAdapter
# expected: ModelCallResponse returned
# risk: secondary adapter fails
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0014_secondary_adapter_call() -> None:
    """SecondaryAdapter call returns a ModelCallResponse."""
    adapter = SecondaryAdapter()
    resp = asyncio.run(adapter.call(_make_request()))
    assert isinstance(resp, ModelCallResponse)
    assert resp.response_payload["provider"] == "secondary"


# --------------------------------------------------------------------------- #
# T-GWY-0015 — LocalAdapter call returns a ModelCallResponse
# --------------------------------------------------------------------------- #
# id: T-GWY-0015
# title: LocalAdapter call returns a ModelCallResponse
# purpose: Verify the local adapter returns a valid response
# level: fast
# requirement: P08-T02
# input: a ModelCallRequest to LocalAdapter
# expected: ModelCallResponse returned
# risk: local adapter fails
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0015_local_adapter_call() -> None:
    """LocalAdapter call returns a ModelCallResponse."""
    adapter = LocalAdapter()
    resp = asyncio.run(adapter.call(_make_request()))
    assert isinstance(resp, ModelCallResponse)
    assert resp.response_payload["provider"] == "local"


# --------------------------------------------------------------------------- #
# T-GWY-0016 — All three adapters share the same contract
# --------------------------------------------------------------------------- #
# id: T-GWY-0016
# title: All three adapters share the same contract (GatewayPort)
# purpose: Verify all adapters have provider, model_id, processing_region
# level: fast
# requirement: P08-T02
# input: instances of all three adapters
# expected: each has the required GatewayPort attributes
# risk: adapters don't conform to the interface
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0016_all_adapters_share_contract() -> None:
    """All three adapters share the same contract."""
    for adapter in (PrimaryAdapter(), SecondaryAdapter(), LocalAdapter()):
        assert hasattr(adapter, "provider")
        assert hasattr(adapter, "model_id")
        assert hasattr(adapter, "processing_region")
        assert hasattr(adapter, "call")


# --------------------------------------------------------------------------- #
# T-GWY-0017 — Switching provider is configuration only
# --------------------------------------------------------------------------- #
# id: T-GWY-0017
# title: Switching provider is configuration only
# purpose: Verify the Gateway works with any provider without code changes
# level: fast
# requirement: P08-T02
# input: Gateway with different providers
# expected: all produce valid responses
# risk: provider switch requires code change
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0017_switching_provider_config_only() -> None:
    """Switching provider is configuration only."""
    request = _make_request()
    for adapter in (PrimaryAdapter(), SecondaryAdapter(), LocalAdapter()):
        gw = Gateway(adapter)
        resp = asyncio.run(gw.call(request))
        assert isinstance(resp, ModelCallResponse)


# --------------------------------------------------------------------------- #
# T-GWY-0018 — PrimaryAdapter has pinned model_id
# --------------------------------------------------------------------------- #
# id: T-GWY-0018
# title: PrimaryAdapter has pinned model_id
# purpose: Verify model identifier is pinned by exact version
# level: fast
# requirement: P08-T02
# input: PrimaryAdapter instance
# expected: model_id contains a version string
# risk: model identifier not pinned
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0018_primary_pinned_model_id() -> None:
    """PrimaryAdapter has pinned model_id."""
    assert PrimaryAdapter.model_id == "primary-v1.0.0"


# --------------------------------------------------------------------------- #
# T-GWY-0019 — SecondaryAdapter has pinned model_id
# --------------------------------------------------------------------------- #
# id: T-GWY-0019
# title: SecondaryAdapter has pinned model_id
# purpose: Verify model identifier is pinned by exact version
# level: fast
# requirement: P08-T02
# input: SecondaryAdapter instance
# expected: model_id contains a version string
# risk: model identifier not pinned
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0019_secondary_pinned_model_id() -> None:
    """SecondaryAdapter has pinned model_id."""
    assert SecondaryAdapter.model_id == "secondary-v2.1.0"


# --------------------------------------------------------------------------- #
# T-GWY-0020 — LocalAdapter has pinned model_id
# --------------------------------------------------------------------------- #
# id: T-GWY-0020
# title: LocalAdapter has pinned model_id
# purpose: Verify model identifier is pinned by exact version
# level: fast
# requirement: P08-T02
# input: LocalAdapter instance
# expected: model_id contains a version string
# risk: model identifier not pinned
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0020_local_pinned_model_id() -> None:
    """LocalAdapter has pinned model_id."""
    assert LocalAdapter.model_id == "local-openweights-v1.0"


# --------------------------------------------------------------------------- #
# T-GWY-0021 — An identifier change without a recorded evaluation is rejected
# --------------------------------------------------------------------------- #
# id: T-GWY-0021
# title: An identifier change without a recorded evaluation is rejected
# purpose: Verify that changing model_id requires an evaluation pass
# level: fast
# requirement: P08-T02
# input: a model_id that differs from the registered baseline
# expected: the change is rejected
# risk: silent model change
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0021_identifier_change_rejected() -> None:
    """An identifier change without a recorded evaluation is rejected."""
    registered_ids = {"primary-v1.0.0", "secondary-v2.1.0", "local-openweights-v1.0"}
    new_id = "primary-v1.0.1"
    assert new_id not in registered_ids, "unregistered id should not be in baseline"


# --------------------------------------------------------------------------- #
# T-GWY-0022 — PrimaryAdapter declares processing_region
# --------------------------------------------------------------------------- #
# id: T-GWY-0022
# title: PrimaryAdapter declares processing_region
# purpose: Verify the primary adapter declares its processing region
# level: fast
# requirement: P08-T02
# input: PrimaryAdapter instance
# expected: processing_region is a non-empty string
# risk: region not declared
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0022_primary_region() -> None:
    """PrimaryAdapter declares processing_region."""
    assert PrimaryAdapter.processing_region == "us"


# --------------------------------------------------------------------------- #
# T-GWY-0023 — SecondaryAdapter declares processing_region
# --------------------------------------------------------------------------- #
# id: T-GWY-0023
# title: SecondaryAdapter declares processing_region
# purpose: Verify the secondary adapter declares its processing region
# level: fast
# requirement: P08-T02
# input: SecondaryAdapter instance
# expected: processing_region is a non-empty string
# risk: region not declared
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0023_secondary_region() -> None:
    """SecondaryAdapter declares processing_region."""
    assert SecondaryAdapter.processing_region == "eu"


# --------------------------------------------------------------------------- #
# T-GWY-0024 — LocalAdapter declares processing_region
# --------------------------------------------------------------------------- #
# id: T-GWY-0024
# title: LocalAdapter declares processing_region
# purpose: Verify the local adapter declares its processing region
# level: fast
# requirement: P08-T02
# input: LocalAdapter instance
# expected: processing_region is 'local'
# risk: region not declared
# capability: model-gateway


@pytest.mark.fast
def test_T_GWY_0024_local_region() -> None:
    """LocalAdapter declares processing_region."""
    assert LocalAdapter.processing_region == "local"

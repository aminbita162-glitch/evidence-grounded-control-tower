"""Tests for the configuration contract (P03-T07).

Test IDs: T-KRN-0059 to T-KRN-0064.
Covers: invalid configuration rejected; hash stable and changes with any
field; defaults match the registry; unknown keys rejected; hash
deterministic; negative values rejected.

Spec: Part 3 §3.14; schemas/config.json; kernel/config/.
"""

from __future__ import annotations

import pytest

from kernel.config import DEFAULTS, CaseBudgetConfig, validate_config

# ---------------------------------------------------------------------------
# T-KRN-0059 — Invalid configuration is rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0059
# title: Invalid configuration is rejected
# purpose: Verify that missing required keys raise ValueError.
# level: fast
# requirement: P03-T07, Part 3 §3.14
# input: a dict missing a required key
# expected: ValueError is raised
# risk: invalid configuration is accepted
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0059_invalid_config_rejected() -> None:
    """Missing required keys raise ValueError."""
    with pytest.raises(ValueError):
        validate_config({"max_model_calls": 10})


# ---------------------------------------------------------------------------
# T-KRN-0060 — Hash is stable and changes with any field
# ---------------------------------------------------------------------------
# id: T-KRN-0060
# title: Hash is stable and changes with any field
# purpose: Verify the config hash changes when any field changes.
# level: fast
# requirement: P03-T07, Part 3 §3.14
# input: two configs differing by one field
# expected: hashes are different
# risk: the hash does not reflect the configuration
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0060_hash_changes_with_field() -> None:
    """The config hash changes when any field changes."""
    a = CaseBudgetConfig(
        max_model_calls=20,
        max_tokens=60000,
        max_wall_time_seconds=120,
        max_tool_calls=50,
        max_workflow_steps=200,
    )
    b = CaseBudgetConfig(
        max_model_calls=21,
        max_tokens=60000,
        max_wall_time_seconds=120,
        max_tool_calls=50,
        max_workflow_steps=200,
    )
    assert a.config_hash() != b.config_hash()
    assert a.config_hash() == a.config_hash()


# ---------------------------------------------------------------------------
# T-KRN-0061 — Defaults equal the registry parameters
# ---------------------------------------------------------------------------
# id: T-KRN-0061
# title: Defaults equal the registry parameters
# purpose: Verify the default config matches Part 3 §3.14 values.
# level: fast
# requirement: P03-T07, Part 3 §3.14
# input: the DEFAULTS constant
# expected: 20 model calls, 60000 tokens, 120s, 50 tool calls, 200 steps
# risk: defaults do not match the spec
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0061_defaults_match_spec() -> None:
    """Default config values match Part 3 §3.14."""
    assert DEFAULTS.max_model_calls == 20
    assert DEFAULTS.max_tokens == 60000
    assert DEFAULTS.max_wall_time_seconds == 120
    assert DEFAULTS.max_tool_calls == 50
    assert DEFAULTS.max_workflow_steps == 200


# ---------------------------------------------------------------------------
# T-KRN-0062 — Unknown keys are rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0062
# title: Unknown keys are rejected
# purpose: Verify that unknown config keys raise ValueError.
# level: fast
# requirement: P03-T07, Part 3 §3.14
# input: a dict with an extra key
# expected: ValueError is raised
# risk: unknown keys are silently ignored
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0062_unknown_keys_rejected() -> None:
    """Unknown config keys raise ValueError."""
    with pytest.raises(ValueError):
        validate_config(
            {
                "max_model_calls": 10,
                "max_tokens": 1000,
                "max_wall_time_seconds": 30,
                "max_tool_calls": 10,
                "max_workflow_steps": 50,
                "unknown_key": 99,
            }
        )


# ---------------------------------------------------------------------------
# T-KRN-0063 — Hash is deterministic across calls
# ---------------------------------------------------------------------------
# id: T-KRN-0063
# title: Hash is deterministic across calls
# purpose: Verify the same config always produces the same hash.
# level: fast
# requirement: P03-T07, Part 3 §3.14
# input: a CaseBudgetConfig instance
# expected: repeated calls return the same hash
# risk: the hash is non-deterministic
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0063_hash_deterministic() -> None:
    """The config hash is deterministic across calls."""
    cfg = CaseBudgetConfig()
    assert cfg.config_hash() == cfg.config_hash() == cfg.config_hash()


# ---------------------------------------------------------------------------
# T-KRN-0064 — Negative values are rejected
# ---------------------------------------------------------------------------
# id: T-KRN-0064
# title: Negative values are rejected
# purpose: Verify that negative config values raise ValueError.
# level: fast
# requirement: P03-T07, Part 3 §3.14
# input: a config with a negative value
# expected: ValueError is raised
# risk: negative budgets cause logic errors
# capability: kernel-contracts


@pytest.mark.fast
def test_T_KRN_0064_negative_values_rejected() -> None:
    """Negative config values raise ValueError."""
    with pytest.raises(ValueError):
        CaseBudgetConfig(max_model_calls=-1)

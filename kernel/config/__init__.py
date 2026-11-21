"""Configuration contract (Part 3 §3.14, P03-T07).

Typed configuration with defaults, validated at start, canonical hash function.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, fields

from kernel.canonical import canonical_bytes


@dataclass(frozen=True)
class CaseBudgetConfig:
    """Per-case budget configuration (Part 3 §3.14)."""

    max_model_calls: int = 20
    max_tokens: int = 60000
    max_wall_time_seconds: int = 120
    max_tool_calls: int = 50
    max_workflow_steps: int = 200

    def __post_init__(self) -> None:
        """Validate all fields are non-negative."""
        for f in fields(self):
            val = getattr(self, f.name)
            if not isinstance(val, int):
                raise TypeError(f"{f.name} must be int")
            if val < 0:
                raise ValueError(f"{f.name} must be non-negative, got {val}")

    def to_dict(self) -> dict[str, int]:
        """Return a dict representation for hashing."""
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def config_hash(self) -> str:
        """Return the canonical SHA-256 hash of the configuration."""
        return hashlib.sha256(canonical_bytes(self.to_dict())).hexdigest()


DEFAULTS: CaseBudgetConfig = CaseBudgetConfig()


KNOWN_KEYS: frozenset[str] = frozenset(
    {
        "max_model_calls",
        "max_tokens",
        "max_wall_time_seconds",
        "max_tool_calls",
        "max_workflow_steps",
    }
)


def validate_config(data: dict[str, object]) -> CaseBudgetConfig:
    """Validate and create a CaseBudgetConfig from a dict.

    Raises:
        ValueError: If a required key is missing or an unknown key is present.
        TypeError: If a value has the wrong type.
    """
    unknown = set(data.keys()) - KNOWN_KEYS
    if unknown:
        raise ValueError(f"unknown config keys: {unknown}")
    missing = KNOWN_KEYS - set(data.keys())
    if missing:
        raise ValueError(f"missing config keys: {missing}")
    return CaseBudgetConfig(**data)  # type: ignore[arg-type]

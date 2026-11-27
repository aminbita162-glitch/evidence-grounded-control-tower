"""Typed deployment settings and secret-file contract."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from kernel.canonical import canonical_bytes

Environment = Literal["staging", "production", "local"]


class ConfigurationError(ValueError):
    """A safe startup error that contains only a code and a setting name."""


class DeploymentConfig(BaseModel):
    """Public deployment settings included in every deployed Passport digest."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    environment: Environment
    region: Literal["oregon"]
    web_plan: Literal["starter"] = "starter"
    postgres_plan: Literal["0.1c-256mb"] = "0.1c-256mb"
    postgres_major: Literal[18] = 18
    web_cpu_millicores: Literal[500] = 500
    web_memory_mb: Literal[512] = 512
    postgres_cpu_millicores: Literal[100] = 100
    postgres_memory_mb: Literal[256] = 256
    postgres_max_connections: Literal[100] = 100
    recovery_tier: Literal["hobby"] = "hobby"
    recovery_window_days: Literal[3] = 3

    def digest(self) -> str:
        """Hash only validated, public settings in canonical JSON."""
        return hashlib.sha256(canonical_bytes(self.model_dump())).hexdigest()


def load_config(environment: Mapping[str, str]) -> DeploymentConfig:
    """Validate the two per-service environment settings."""
    try:
        return DeploymentConfig.model_validate(
            {
                "environment": environment.get("CTC_ENVIRONMENT"),
                "region": environment.get("CTC_REGION"),
            }
        )
    except ValidationError as exc:
        field = exc.errors(include_input=False)[0]["loc"][0]
        raise ConfigurationError(f"CONFIG_INVALID:{field}") from None


def read_secret(environment: Mapping[str, str], key: str) -> str:
    """Read one environment variable or its documented file counterpart."""
    value = environment.get(key)
    file = environment.get(f"{key}_FILE")
    if value is not None and file is not None:
        raise ConfigurationError(f"SECRET_AMBIGUOUS:{key}")
    if file:
        try:
            value = Path(file).read_text(encoding="utf-8").rstrip("\r\n")
        except OSError, UnicodeError:
            raise ConfigurationError(f"SECRET_UNREADABLE:{key}") from None
    if not value:
        raise ConfigurationError(f"SECRET_REQUIRED:{key}")
    return value


def read_key(environment: Mapping[str, str], key: str) -> bytes:
    """Read a 32-byte key stored as base16."""
    try:
        value = read_secret(environment, key)
        decoded = bytes.fromhex(value)
    except ConfigurationError:
        raise
    except ValueError:
        raise ConfigurationError(f"SECRET_INVALID:{key}") from None
    if len(value) != 64 or len(decoded) != 32:
        raise ConfigurationError(f"SECRET_INVALID:{key}")
    return decoded

"""Secret store port and implementations (P11-T03).

A port for reading deployment secrets — the master key, tenant data keys
and the Ed25519 signing key.  Secrets are read only through this port,
never logged, never written to the repository.  The Ed25519 signing key
is held outside the kernel and the repository.

Spec: Part 3 §3.15, §3.24; Part 4 §4.4; P11-T03.
"""

from __future__ import annotations

import os
from typing import Protocol

__all__ = [
    "SecretStore",
    "FileSecretStore",
    "EnvSecretStore",
    "SecretError",
]

_SECRET_PREFIX = "CTC_SECRET_"  # noqa: S105 — prefix string, not a secret


class SecretError(Exception):
    """Raised when a secret is missing or invalid."""


class SecretStore(Protocol):
    """Port for reading deployment secrets.

    Secrets are read only through this port.  No secret is ever logged,
    printed, or committed.
    """

    def get(self, key: str) -> bytes:
        """Read a secret by name.

        Args:
            key: the secret name.

        Returns:
            The secret bytes.

        Raises:
            SecretError: if the secret is not found.
        """
        ...

    def has(self, key: str) -> bool:
        """Check whether a secret exists.

        Args:
            key: the secret name.

        Returns:
            True if the secret is present.
        """
        ...

    def list_keys(self) -> list[str]:
        """List all secret names (not values).

        Returns:
            A list of secret names.
        """
        ...


class FileSecretStore:
    """File-based secret store.

    Reads secrets from a directory where each file is a secret.
    The directory path is provided at construction; no secret is
    stored in the repository.
    """

    def __init__(self, base_dir: str) -> None:
        """Create a file secret store.

        Args:
            base_dir: the directory containing secret files.
        """
        self._base = base_dir

    def get(self, key: str) -> bytes:
        """Read a secret from a file.

        Args:
            key: the secret name (file name).

        Returns:
            The file contents as bytes.

        Raises:
            SecretError: if the file does not exist.
        """
        path = os.path.join(self._base, key)
        if not os.path.isfile(path):
            raise SecretError(f"secret not found: {key}")
        with open(path, "rb") as f:
            return f.read()

    def has(self, key: str) -> bool:
        """Check whether a secret file exists.

        Args:
            key: the secret name.

        Returns:
            True if the file exists.
        """
        return os.path.isfile(os.path.join(self._base, key))

    def list_keys(self) -> list[str]:
        """List all secret file names.

        Returns:
            A sorted list of file names in the secret directory.
        """
        if not os.path.isdir(self._base):
            return []
        return sorted(os.listdir(self._base))


class EnvSecretStore:
    """Environment-based secret store.

    Reads secrets from environment variables prefixed with ``CTC_SECRET_``.
    """

    def __init__(self, env: dict[str, str] | None = None) -> None:
        """Create an env secret store.

        Args:
            env: optional environment dict (default: os.environ).
        """
        self._env: dict[str, str] = env if env is not None else dict(os.environ)

    def get(self, key: str) -> bytes:
        """Read a secret from the environment.

        Args:
            key: the secret name (without prefix).

        Returns:
            The secret value as bytes.

        Raises:
            SecretError: if the env var is not set.
        """
        env_key = _SECRET_PREFIX + key.upper()
        val = self._env.get(env_key)
        if val is None:
            raise SecretError(f"secret not found: {key}")
        return val.encode("utf-8")

    def has(self, key: str) -> bool:
        """Check whether an env secret exists.

        Args:
            key: the secret name.

        Returns:
            True if the env var is set.
        """
        return _SECRET_PREFIX + key.upper() in self._env

    def list_keys(self) -> list[str]:
        """List all secret names (without values).

        Returns:
            A sorted list of secret names (prefix stripped, lowercased).
        """
        keys: list[str] = []
        for k in self._env:
            if k.startswith(_SECRET_PREFIX):
                keys.append(k[len(_SECRET_PREFIX) :].lower())
        return sorted(keys)

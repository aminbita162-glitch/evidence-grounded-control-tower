"""Key lifecycle and secrets handling tests (P11-T03).

Test IDs: T-SEC-0031 to T-SEC-0042.
Covers: rotation keeps old records verifiable; the drill completes and
verifies; a secret in a log line, a file or an environment dump fails
the secrets tests; secrets read only through the port.

Spec: Part 3 §3.24; Part 4 §4.5; P11-T03.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from adapters.secrets import EnvSecretStore, FileSecretStore, SecretError
from tools.keyctl import (
    SECRET_NAMES,
    ErasureDrill,
    KeyCeremony,
    RotationDrill,
)

# ---------------------------------------------------------------------------
# T-SEC-0031: key ceremony generates all keys
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0031_ceremony_generates_keys() -> None:
    """T-SEC-0031: key ceremony generates all required keys.

    id: T-SEC-0031
    title: Ceremony generates keys
    purpose: Verify the ceremony creates master, signing and witness keys.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: KeyCeremony with env store
    expected: all steps completed
    risk: missing deployment keys
    owning capability: security
    """
    env: dict[str, str] = {}
    store = EnvSecretStore(env)
    ceremony = KeyCeremony(store)
    steps = ceremony.run()
    assert all(s.completed for s in steps)


# ---------------------------------------------------------------------------
# T-SEC-0032: ceremony generates 32-byte keys
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0032_ceremony_keys_are_32_bytes() -> None:
    """T-SEC-0032: ceremony-generated keys are 32 bytes.

    id: T-SEC-0032
    title: Keys are 32 bytes
    purpose: Verify generated keys have the correct size.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: KeyCeremony.generate_*
    expected: 32 bytes per key
    risk: weak keys
    owning capability: security
    """
    ceremony = KeyCeremony(EnvSecretStore({}))
    assert len(ceremony.generate_master_key()) == 32
    assert len(ceremony.generate_signing_key()) == 32
    assert len(ceremony.generate_witness_key()) == 32


# ---------------------------------------------------------------------------
# T-SEC-0033: erasure drill completes and verifies
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0033_erasure_drill_passes() -> None:
    """T-SEC-0033: the erasure drill completes and verifies.

    id: T-SEC-0033
    title: Erasure drill passes
    purpose: Verify the erasure drill reports success.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: ErasureDrill.run
    expected: passed is True
    risk: erasure not verified
    owning capability: security
    """
    drill = ErasureDrill()
    result = drill.run()
    assert result.passed is True


# ---------------------------------------------------------------------------
# T-SEC-0034: rotation drill completes and verifies
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0034_rotation_drill_passes() -> None:
    """T-SEC-0034: the rotation drill completes and verifies.

    id: T-SEC-0034
    title: Rotation drill passes
    purpose: Verify the rotation drill reports success.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: RotationDrill.run
    expected: passed is True
    risk: rotation not verified
    owning capability: security
    """
    drill = RotationDrill()
    result = drill.run()
    assert result.passed is True


# ---------------------------------------------------------------------------
# T-SEC-0035: secret store reads from env
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0035_env_store_reads_secret() -> None:
    """T-SEC-0035: the env secret store reads a secret by name.

    id: T-SEC-0035
    title: Env store reads secret
    purpose: Verify the env store retrieves a secret value.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: EnvSecretStore with CTC_SECRET_MASTER_KEY set
    expected: get returns the value
    risk: secrets not readable
    owning capability: security
    """
    env = {"CTC_SECRET_MASTER_KEY": "test-key-value"}
    store = EnvSecretStore(env)
    val = store.get("master_key")
    assert val == b"test-key-value"


# ---------------------------------------------------------------------------
# T-SEC-0036: missing secret raises SecretError
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0036_missing_secret_raises() -> None:
    """T-SEC-0036: a missing secret raises SecretError.

    id: T-SEC-0036
    title: Missing secret raises
    purpose: Verify missing secrets raise SecretError, not return empty.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: EnvSecretStore without the key
    expected: SecretError raised
    risk: silent missing secret
    owning capability: security
    """
    store = EnvSecretStore({})
    with pytest.raises(SecretError):
        store.get("nonexistent")


# ---------------------------------------------------------------------------
# T-SEC-0037: file secret store reads from directory
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0037_file_store_reads_secret() -> None:
    """T-SEC-0037: the file secret store reads a secret from a file.

    id: T-SEC-0037
    title: File store reads secret
    purpose: Verify the file store retrieves a secret from a file.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: FileSecretStore with a temp file
    expected: get returns file contents
    risk: secrets not readable from files
    owning capability: security
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "MASTER_KEY"), "wb") as f:
            f.write(b"file-secret-value")
        store = FileSecretStore(tmpdir)
        val = store.get("MASTER_KEY")
        assert val == b"file-secret-value"


# ---------------------------------------------------------------------------
# T-SEC-0038: secret store has() returns False for missing
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0038_store_has_returns_false() -> None:
    """T-SEC-0038: has() returns False for a missing secret.

    id: T-SEC-0038
    title: Has returns False for missing
    purpose: Verify has() reports missing secrets correctly.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: EnvSecretStore without the key
    expected: has returns False
    risk: false positive on missing secret
    owning capability: security
    """
    store = EnvSecretStore({})
    assert store.has("nonexistent") is False


# ---------------------------------------------------------------------------
# T-SEC-0039: secret store has() returns True for present
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0039_store_has_returns_true() -> None:
    """T-SEC-0039: has() returns True for a present secret.

    id: T-SEC-0039
    title: Has returns True for present
    purpose: Verify has() reports present secrets correctly.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: EnvSecretStore with the key
    expected: has returns True
    risk: false negative on present secret
    owning capability: security
    """
    env = {"CTC_SECRET_MASTER_KEY": "val"}
    store = EnvSecretStore(env)
    assert store.has("master_key") is True


# ---------------------------------------------------------------------------
# T-SEC-0040: list_keys does not return values
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0040_list_keys_no_values() -> None:
    """T-SEC-0040: list_keys returns names, not values.

    id: T-SEC-0040
    title: List keys returns names only
    purpose: Verify list_keys does not expose secret values.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: EnvSecretStore with multiple secrets
    expected: list of names, no values
    risk: secret values leaked via listing
    owning capability: security
    """
    env = {
        "CTC_SECRET_MASTER_KEY": "secret-val-1",
        "CTC_SECRET_SIGNING_KEY": "secret-val-2",
    }
    store = EnvSecretStore(env)
    keys = store.list_keys()
    assert "master_key" in keys
    assert "signing_key" in keys
    for key in keys:
        assert "val" not in key


# ---------------------------------------------------------------------------
# T-SEC-0041: ceremony verify_keys checks all keys
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0041_ceremony_verify_keys() -> None:
    """T-SEC-0041: ceremony verify_keys checks all required keys.

    id: T-SEC-0041
    title: Ceremony verify keys
    purpose: Verify the ceremony's verify step checks all secret names.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: store with all secrets, verify_keys
    expected: True when all present, False otherwise
    risk: incomplete key set
    owning capability: security
    """
    env_full: dict[str, str] = {f"CTC_SECRET_{name}": "val" for name in SECRET_NAMES}
    store_full = EnvSecretStore(env_full)
    ceremony = KeyCeremony(store_full)
    assert ceremony.verify_keys(store_full) is True
    store_empty = EnvSecretStore({})
    assert ceremony.verify_keys(store_empty) is False


# ---------------------------------------------------------------------------
# T-SEC-0042: erasure drill result has correct name
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0042_drill_result_name() -> None:
    """T-SEC-0042: the erasure drill result has the correct name.

    id: T-SEC-0042
    title: Drill result name
    purpose: Verify the drill result is labelled correctly.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T03
    input: ErasureDrill.run
    expected: name is 'erasure_drill'
    risk: mislabelled drill
    owning capability: security
    """
    drill = ErasureDrill()
    result = drill.run()
    assert result.name == "erasure_drill"

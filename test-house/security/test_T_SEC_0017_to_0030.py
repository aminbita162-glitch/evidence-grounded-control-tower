"""Envelope encryption and payload store tests (P11-T02).

Test IDs: T-SEC-0017 to T-SEC-0030.
Covers: ciphertext differs per tenant for equal plaintext; one tenant's
key cannot decrypt another's payload; after erasure payloads are
unrecoverable and the ledger verifies; erasure is a recorded event.

Spec: Part 3 §3.5, §3.24; Part 4 §4.5; P11-T02.
"""

from __future__ import annotations

import asyncio

import pytest

from kernel.crypto.envelope import (
    EnvelopeError,
    EnvelopeService,
    InMemoryEnvelopeStore,
    decrypt_payload,
    encrypt_payload,
)
from kernel.crypto.keylifecycle import (
    DEFAULT_ROTATION_DAYS,
    InMemoryKeyHistory,
    KeyLifecycle,
    KeyLifecycleError,
    RotationConfig,
)

# ---------------------------------------------------------------------------
# T-SEC-0017: ciphertext differs per tenant for equal plaintext
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0017_ciphertext_differs_per_tenant() -> None:
    """T-SEC-0017: ciphertext differs per tenant for equal plaintext.

    id: T-SEC-0017
    title: Ciphertext differs per tenant
    purpose: Verify different tenants produce different ciphertexts.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: two tenants, same plaintext
    expected: ciphertexts differ
    risk: cross-tenant data inference
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    service.provision_key("tenant-b")
    p1 = asyncio.run(service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"secret"))
    p2 = asyncio.run(service.encrypt(tenant_id="tenant-b", payload_id="p2", plaintext=b"secret"))
    assert p1.ciphertext != p2.ciphertext


# ---------------------------------------------------------------------------
# T-SEC-0018: one tenant's key cannot decrypt another's payload
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0018_cross_tenant_decrypt_fails() -> None:
    """T-SEC-0018: one tenant's key cannot decrypt another's payload.

    id: T-SEC-0018
    title: Cross-tenant decrypt fails
    purpose: Verify a tenant cannot decrypt another tenant's payload.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: tenant-a encrypts, try to decrypt as tenant-b
    expected: EnvelopeError raised
    risk: cross-tenant data access
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    service.provision_key("tenant-b")
    asyncio.run(service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"secret"))
    with pytest.raises(EnvelopeError):
        asyncio.run(service.decrypt(tenant_id="tenant-b", payload_id="p1"))


# ---------------------------------------------------------------------------
# T-SEC-0019: encrypt then decrypt round-trips
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0019_encrypt_decrypt_roundtrip() -> None:
    """T-SEC-0019: encrypt then decrypt returns the original plaintext.

    id: T-SEC-0019
    title: Encrypt-decrypt round-trip
    purpose: Verify encryption and decryption are inverse operations.
    level: fast
    requirement: PR-06; Part 3 §3.5; P11-T02
    input: plaintext, encrypt, decrypt
    expected: decrypted equals original
    risk: data corruption
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    asyncio.run(
        service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"sensitive payload data")
    )
    result = asyncio.run(service.decrypt(tenant_id="tenant-a", payload_id="p1"))
    assert result == b"sensitive payload data"


# ---------------------------------------------------------------------------
# T-SEC-0020: after erasure payloads are unrecoverable
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0020_erased_payloads_unrecoverable() -> None:
    """T-SEC-0020: after erasure payloads are unrecoverable.

    id: T-SEC-0020
    title: Erased payloads unrecoverable
    purpose: Verify crypto-erasure makes payloads unrecoverable.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: encrypt then erase tenant
    expected: decrypt raises EnvelopeError
    risk: data survives erasure
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    asyncio.run(service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"secret"))
    count = asyncio.run(service.erase_tenant("tenant-a"))
    assert count >= 1
    with pytest.raises(EnvelopeError):
        asyncio.run(service.decrypt(tenant_id="tenant-a", payload_id="p1"))


# ---------------------------------------------------------------------------
# T-SEC-0021: erasure is a recorded event
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0021_erasure_recorded() -> None:
    """T-SEC-0021: erasure is a recorded event.

    id: T-SEC-0021
    title: Erasure recorded as event
    purpose: Verify erasure appears in key history.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: erase tenant, check history
    expected: erased event in history
    risk: silent erasure
    owning capability: security
    """
    history = InMemoryKeyHistory()
    lifecycle = KeyLifecycle(history)
    lifecycle.create_key("tenant-a")
    asyncio.run(lifecycle.erase_tenant("tenant-a"))
    events = asyncio.run(history.list_events("tenant-a"))
    erased = [e for e in events if e.event == "erased"]
    assert len(erased) >= 1


# ---------------------------------------------------------------------------
# T-SEC-0022: rotation keeps old records verifiable
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0022_rotation_keeps_old_records() -> None:
    """T-SEC-0022: rotation keeps old records verifiable.

    id: T-SEC-0022
    title: Rotation keeps old records
    purpose: Verify old keys remain accessible after rotation.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: create key, rotate, check old key still exists
    expected: old key id is still retrievable
    risk: rotation loses history
    owning capability: security
    """
    history = InMemoryKeyHistory()
    lifecycle = KeyLifecycle(history)
    old_id = lifecycle.create_key("tenant-a")
    new_id = asyncio.run(lifecycle.rotate_key("tenant-a"))
    assert old_id != new_id
    assert lifecycle.get_key(old_id) is not None


# ---------------------------------------------------------------------------
# T-SEC-0023: rotation default is 90 days
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0023_rotation_default_90_days() -> None:
    """T-SEC-0023: rotation default is 90 days.

    id: T-SEC-0023
    title: Rotation default 90 days
    purpose: Verify the default rotation period is 90 days.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: default RotationConfig
    expected: rotation_days == 90
    risk: wrong rotation period
    owning capability: security
    """
    config = RotationConfig()
    assert config.rotation_days == DEFAULT_ROTATION_DAYS
    assert config.rotation_days == 90


# ---------------------------------------------------------------------------
# T-SEC-0024: break-glass creates emergency key
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0024_break_glass_creates_key() -> None:
    """T-SEC-0024: break-glass creates an emergency key.

    id: T-SEC-0024
    title: Break-glass creates key
    purpose: Verify break-glass procedure creates a recorded key.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: break_glass on tenant
    expected: key created and recorded
    risk: no emergency access
    owning capability: security
    """
    history = InMemoryKeyHistory()
    lifecycle = KeyLifecycle(history)
    key_id = asyncio.run(lifecycle.break_glass("tenant-a"))
    assert key_id is not None
    events = asyncio.run(history.list_events("tenant-a"))
    assert any(e.event == "break_glass" for e in events)


# ---------------------------------------------------------------------------
# T-SEC-0025: break-glass disabled raises
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0025_break_glass_disabled_raises() -> None:
    """T-SEC-0025: break-glass disabled raises KeyLifecycleError.

    id: T-SEC-0025
    title: Break-glass disabled raises
    purpose: Verify break-glass is refused when not enabled.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: disabled config, break_glass
    expected: KeyLifecycleError raised
    risk: unauthorized emergency access
    owning capability: security
    """
    history = InMemoryKeyHistory()
    config = RotationConfig(break_glass_enabled=False)
    lifecycle = KeyLifecycle(history, config=config)
    with pytest.raises(KeyLifecycleError):
        asyncio.run(lifecycle.break_glass("tenant-a"))


# ---------------------------------------------------------------------------
# T-SEC-0026: encrypt with wrong key size raises
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0026_wrong_key_size_raises() -> None:
    """T-SEC-0026: encrypt with wrong key size raises EnvelopeError.

    id: T-SEC-0026
    title: Wrong key size raises
    purpose: Verify encryption rejects wrong-size keys.
    level: fast
    requirement: PR-06; Part 3 §3.5; P11-T02
    input: 16-byte key
    expected: EnvelopeError raised
    risk: weak encryption
    owning capability: security
    """
    with pytest.raises(EnvelopeError):
        encrypt_payload(b"data", b"short")


# ---------------------------------------------------------------------------
# T-SEC-0027: decrypt with wrong key size raises
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0027_decrypt_wrong_key_size_raises() -> None:
    """T-SEC-0027: decrypt with wrong key size raises EnvelopeError.

    id: T-SEC-0027
    title: Decrypt wrong key size raises
    purpose: Verify decryption rejects wrong-size keys.
    level: fast
    requirement: PR-06; Part 3 §3.5; P11-T02
    input: 16-byte key
    expected: EnvelopeError raised
    risk: weak decryption
    owning capability: security
    """
    with pytest.raises(EnvelopeError):
        decrypt_payload(b"data", b"short", b"nonce")


# ---------------------------------------------------------------------------
# T-SEC-0028: erased payload marked as erased
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0028_erased_payload_marked() -> None:
    """T-SEC-0028: erased payload is marked as erased.

    id: T-SEC-0028
    title: Erased payload marked
    purpose: Verify erased payloads have the erased flag set.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: encrypt then erase
    expected: payload.erased is True
    risk: erasure not visible
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    asyncio.run(service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"secret"))
    asyncio.run(service.erase_tenant("tenant-a"))
    payload = asyncio.run(store.get_payload("tenant-a", "p1"))
    assert payload is not None
    assert payload.erased is True


# ---------------------------------------------------------------------------
# T-SEC-0029: is_erased returns True after erasure
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0029_is_erased_after_erasure() -> None:
    """T-SEC-0029: is_erased returns True after erasure.

    id: T-SEC-0029
    title: Is erased after erasure
    purpose: Verify the service tracks erasure state.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: erase tenant
    expected: is_erased True
    risk: erasure state not tracked
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    service.provision_key("tenant-a")
    assert service.is_erased("tenant-a") is False
    asyncio.run(service.erase_tenant("tenant-a"))
    assert service.is_erased("tenant-a") is True


# ---------------------------------------------------------------------------
# T-SEC-0030: encrypt without provisioned key raises
# ---------------------------------------------------------------------------


@pytest.mark.fast
def test_T_SEC_0030_encrypt_without_key_raises() -> None:
    """T-SEC-0030: encrypt without provisioned key raises EnvelopeError.

    id: T-SEC-0030
    title: Encrypt without key raises
    purpose: Verify encryption fails without a provisioned key.
    level: fast
    requirement: PR-06; Part 3 §3.24; P11-T02
    input: no key provisioned, encrypt
    expected: EnvelopeError raised
    risk: unencrypted storage
    owning capability: security
    """
    store = InMemoryEnvelopeStore()
    service = EnvelopeService(store)
    with pytest.raises(EnvelopeError):
        asyncio.run(service.encrypt(tenant_id="tenant-a", payload_id="p1", plaintext=b"secret"))

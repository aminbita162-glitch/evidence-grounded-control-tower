# Key Lifecycle

## Overview

The Control Tower uses envelope encryption with one data key per tenant,
wrapped by a master key held by the deployment secret store.  The
Ed25519 signing key and the witness key are held outside the kernel
and the repository.

## Key ceremony

1. Generate the master key (KEK) — 32 random bytes.
2. Generate the Ed25519 signing key — 32 random bytes.
3. Generate the witness key — 32 random bytes.
4. Verify all keys are present in the secret store.

The ceremony is run by `tools.keyctl.KeyCeremony` and the keys are
stored in the secret store (`adapters.secrets`).  No key material
is committed to the repository.

## Rotation

- Default rotation period: 90 days (configurable via `RotationConfig`).
- Rotation creates a new data key; old keys remain verifiable.
- Rotation events are recorded in the key history store.
- Old keys are retained for decrypting existing payloads.

## Break-glass

- Break-glass creates an emergency key for a tenant.
- Break-glass is disabled by configuration (`break_glass_enabled`).
- Break-glass events are recorded in the key history.

## Crypto-erasure

- Destroying a tenant data key makes that tenant's payloads unrecoverable.
- The erasure drill (`tools.keyctl.ErasureDrill`) provisions a key on a
  test tenant, encrypts data, erases the key, and verifies the data
  is unrecoverable.
- Erasure is a recorded event in the key history.
- The ledger structure remains intact after erasure (hashes verify).

## Secrets handling

- Secrets are read only through the `SecretStore` port.
- Secrets are never logged, printed, or committed.
- The `EnvSecretStore` reads from environment variables prefixed
  `CTC_SECRET_`.
- The `FileSecretStore` reads from a directory of secret files.

"""Ledger format document (P05-T06).

Describes the on-disk format of the case bundle, the record structure,
the Merkle tree, checkpoints, proofs, and the verification levels.

Generated from the schemas; the bundle layout is deterministic.
"""

# Ledger Format

## Record

Every record in the evidence ledger has these fields:

| Field | Type | Description |
|-------|------|-------------|
| seq | int | Gap-free sequence per chain |
| record_id | str | Unique record identifier |
| tenant_id | str | Tenant identifier |
| case_id | str? | Case identifier (None for system chains) |
| stage | str | Pipeline stage |
| actor_kind | str | ROLE, HUMAN, or SYSTEM |
| actor_id | str | Actor identifier |
| type | str | Record type |
| payload_hash | str | Hash of the payload |
| salt_id | str? | Salt reference (personal-data payloads only) |
| payload_ref | str? | Reference to stored payload |
| prev_hash | str | Previous record's record_hash |
| record_hash | str | This record's hash |
| alg | str | Algorithm identifier (sha256) |
| schema_version | int | Schema version |

## Hashing

- **Record hash**: `H("ctc/record/v1" || canonical(record_without_record_hash) || prev_hash)`
- **Payload hash (unsalted)**: `H("ctc/payload/v1" || canonical(payload))`
- **Payload hash (salted)**: `H("ctc/payload/v1" || salt_id || salt || canonical(payload))`
- **Leaf hash**: `H("ctc/leaf/v1" || record_hash)`
- **Node hash**: `H("ctc/node/v1" || left || right)`
- **Commitment**: `H("ctc/commit/v1" || ...)`

## Merkle Tree

RFC 9162 style with the split rule for unbalanced trees.

## Checkpoint

`{chain_id, tree_size, root_hash, system_chain_position, recorded_at}` signed with Ed25519.

## Verification Levels

- `SELF-ATTESTED`: no valid witness co-signature
- `WITNESSED-LOCAL`: co-signed by a LOCAL witness
- `WITNESSED-EXTERNAL`: co-signed by an EXTERNAL witness
- `ANCHORED`: witnessed with a verified anchor receipt

## Bundle

A self-contained export: manifest, records, payloads, pack versions, checkpoints.
Deterministic layout; verifies offline.

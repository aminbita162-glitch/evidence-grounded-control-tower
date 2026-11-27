# Phase 12 stop report

phase: P12
task: P12-CHG
condition: Part 1 §§5.1, 5.6, 6.1 and 7.1, Part 3 §3.27, and the P12-CHG file allowlist
what_happened: T01 passed and was committed as `2ccff9f`. The Passport draft adds optional `configuration_hash`, regenerates its Python model and updates the schema hash in `contracts.lock`. The SQL generator maps the new property to a nullable column in its output for `0002_tables.sql`. The existing persistence test requires that output to match the original committed migration byte for byte. The SQL generator, migration and persistence test are outside the P12-CHG file allowlist.
attempts: 0. The targeted diagnostic reproduced the initial failure before any corrective edit. Failure signature is `unit`, `T-DB-0018`, exit 1.
evidence: `gate run contract`, `gate run generated-files` and `gate run replay` exited 0. The walking-skeleton run passed 12 tests and direct schema validation accepted old Passports and rejected malformed hashes. `gate run phase` exited 1 at `unit`. The T01 image gate, ten image tests, seeded image self-test, and full existing gate set exited 0 before commit. The final repeat-build image digests differ (DERIVED from `docker image inspect`, exit 0), `sha256:4d19749e9aa8f101a59a3425a83b7fc23d974fca424ccc920c2c535f2e19dc93` and `sha256:df0a34af206d4f6491b6c88f07a4ec1dd81d99ec599637a4171d4fad2050816e`.
decision_needed: Authorize the exact files required to keep the existing migration immutable and reconcile Passport storage with the additive contract, including the SQL generator, the deterministic migration test and a new forward migration if the field is stored as a column.
options: An additive migration preserves existing rows and provides a column for new Passports. A contract-only field requires an explicitly authorized SQL-generation rule and persistence representation. Both options require retaining a deterministic migration check.
untouched: Existing PostgreSQL migrations, SQL generator and persistence tests. The Passport change is a local draft and its ledger entry is absent. Main and the remote phase branch retain their previous tips.

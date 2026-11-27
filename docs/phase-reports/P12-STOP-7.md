# Phase 12 stop report

phase: P12
task: P12-T02
condition: Part 1 §§5.4, 6.1, 6.2, 6.4 and 7.1, Part 7 owner preparation, Part 8 §8.2, and the P12-T02 platform-limit requirement
what_happened: Decision D6 closed P12-STOP-6. P12-CHG added the optional Passport configuration hash through migration 0008 and preserved migration 0002 byte for byte. The deployment blueprint requires verified hosting limits and database options for staging and production. V-11 and V-27 are marked UNVERIFIED, and the source registry has no record for either item.
attempts: 0. The required evidence is unavailable from the declared sources.
evidence: The D6 main workflow passed at `188db55`. `gate phase recovery P12`, `gate run contract`, `gate run generated-files`, `gate run replay`, `gate run migration` and `gate run phase` exited 0. The walking-skeleton and persistence run passed 22 tests, including an in-place upgrade of an existing Passport row. The Git blob for `0002_tables.sql` is `486685d6d76583dcf28a0c2c1c22e84c4c0fe1a8` on both main and the phase branch.
decision_needed: Supply the selected staging and production plans and verified V-11 and V-27 evidence for their limits, container security options, database extensions, regions, backup and point-in-time recovery. Alternatively, name the official sources and authorize the hosts needed to verify those facts.
options: Owner-provided evidence can be used in the blueprint directly. Authorizing the named sources allows the evidence to be verified and recorded before the blueprint is implemented.
untouched: Tasks P12-T02 through P12-END2 remain pending.

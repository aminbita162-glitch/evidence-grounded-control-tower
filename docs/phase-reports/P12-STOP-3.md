# Phase 12 stop report

phase: P12
task: Entry verification
condition: Part 1 §§1.5, 7.1, and 8.4 and Part 7 preflight §4
what_happened: The D1 resume command authorizes the existing drafts and addresses the prior scope decisions. The command lacks the run-parameters hash required to use the Phase 12 token budget.
attempts: 0
evidence: The recovery check exited 0. The SHA-256 of the run-parameters file on main begins with 486e8d84. The scope check also returned `path outside scope: schemas/passport.json` for the schema change described in P12-STOP-1.
decision_needed: Reissue the resume decision with `; params: 486e8d84` as the final clause. For the Passport change, supply an in-scope representation across all producers or land an owner revision that names the schema, producers, and contract change in Phase 12.
options: A compatible representation preserves the existing Passport contract. A directive revision can authorize the schema change and its contract checks.
untouched: The Phase 12 drafts, task ledger, gate configuration, and main.

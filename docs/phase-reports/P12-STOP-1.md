# Phase 12 stop report

phase: P12
task: P12-T01
condition: Part 1 §§5.5, 6.1 and 7.1
what_happened: P12-T01 requires activation of the image gate, and P12-T04 requires activation of the restore gate. Both entries run a placeholder command. The protected catalogue and the gate implementation paths are absent from the tasks that require them. P12-T02 also requires stamping the configuration hash on every Passport. The strict Passport schema has no such field, and the phase scope excludes that schema and the Passport producer.
attempts: 0
evidence: `python -m tools.gate list` reports image and restore as NOT_ACTIVE. The P12 task-path parser returns false for the catalogue and both implementation paths. The scope check rejects `schemas/passport.json`. The current Passport builder is in `kernel/skeleton/__init__.py`.
decision_needed: Name the protected catalogue and gate implementation paths in P12-T01 and P12-T04. For P12-T02, add a contract-change task and authorize the Passport schema and producer paths, or specify a compatible representation for the configuration hash in the current contract.
options: A directive revision can authorize the required changes and retain the acceptance criteria. An owner decision can revise the affected acceptance criteria and preserve the existing scope.
untouched: Phase 12 implementation, task ledger and gate configuration.

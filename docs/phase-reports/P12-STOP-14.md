# Phase 12 stop report

phase: P12
task: P12-T02 deployment configuration
condition: Part 1 §§5.1, 6.1 and 7.1, and the P12-T02 Passport replay check
what_happened: P12-CHG identifies the walking skeleton and replay as current Passport producers and consumers. P12-T02 requires replay to use the recorded configuration hash. Its file list permits edits to the walking skeleton, while the case-export replay entry point is outside the Phase 12 scope. That entry point checks recorded payload hashes and has no Passport reconstruction step that accepts the recorded deployment configuration hash.
attempts: 0
evidence: The P12-T02 Files and Passport checks are in directive.txt, lines 4764–4765. The separate replay entry point is in kernel/ledger/replay.py, lines 56–76. The Phase 12 scope checker reported `path outside scope: kernel/ledger/replay.py` for that candidate. `gate phase recovery P12`, `gate directive --cross-check` and `gate run phase` exited 0. The parameter SHA-256 prefix is `1fbda98a`. The GitHub `phase` check succeeded on main at `188db555e13f17c29ddc5757803e1cea290c47d7`.
decision_needed: Authorize kernel/ledger/replay.py in the P12-T02 Files list and Phase 12 scope, or specify that the P12-T02 replay check applies solely to the walking skeleton.
options: Expand scope to verify the recorded Passport configuration hash through the case-export replay entry point. Clarify skeleton-only acceptance to keep the check inside the current file list.
untouched: Deployment code, replay code, phase ledger, state and remote refs.

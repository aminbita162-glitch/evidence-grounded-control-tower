# Phase 16 post-merge scope verification

On the Phase 16 merge, the main workflow selected P17 after the final declared phase and the scope gate exited 2. The owner approved correcting the resolver, adding regression coverage, and recording the Phase 16 merge hash in the same maintenance commit. [Post-merge workflow](https://github.com/aminbita162-glitch/evidence-grounded-control-tower/actions/runs/46106833069).

Automatic selection on main retains the last completed phase when it is the final phase declared in the directive. The gate still checks the selected scope. Earlier phases continue selecting their successor. T-FIN-0017 verifies those cases and rejects a path outside the terminal phase scope.

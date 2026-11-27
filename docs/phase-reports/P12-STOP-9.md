# Phase 12 stop report

phase: P12
task: P12-T02 deployment configuration
condition: Part 1 §§6.1 and 7.1, decision D-42, and the P12-T02 platform-limit and environment-separation acceptance requirements
what_happened: D7 selects Render and authorizes its documentation. The official documentation is recorded in P12-D7. The staging and production web and database compute plan IDs and workspace recovery tier are unspecified. D-42 requires owner-selected regions for the first deployment.
attempts: 0
evidence: `python -m tools.gate phase recovery P12` and `python -m tools.gate directive --cross-check` exited 0. The supplied run-parameters hash matches `1fbda98a`. GitHub Actions completed successfully on remote main at `188db55` in run `45937531064`. Render's compute plan table contains multiple paid web and database plans, and its backup documentation distinguishes Hobby from Pro or higher recovery windows.
decision_needed: Specify the Render web and Postgres compute plan IDs, workspace recovery tier, and region for staging and production, or authorize selection of the plan IDs and workspace tier and provide the owner-selected regions under D-42.
options: The same paid compute and workspace tiers may be selected for both environments, or distinct tiers can be declared explicitly. Render supports Oregon, Ohio, Virginia, Frankfurt and Singapore for web and Postgres.
untouched: Deployment configuration, task ledger, state and remote refs.

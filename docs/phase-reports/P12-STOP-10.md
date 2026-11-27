# Phase 12 stop report

phase: P12
task: P12-T02 deployment configuration
condition: Part 1 §§6.1, 6.2 and 7.1, and the P12-T02 platform-limit and environment-separation requirements
what_happened: D8 specifies Starter web, Starter Postgres, Standard workspace recovery and Oregon for staging and production. Render supports Starter web and Oregon. Render reserves Starter Postgres for existing legacy databases and publishes recovery windows for Hobby and Pro or higher workspaces. These findings prevent verification of the requested configuration for new staging and production databases.
attempts: 0
evidence: `.venv/bin/python -m tools.gate phase recovery P12` and `.venv/bin/python -m tools.gate directive --cross-check` exited 0. The SHA-256 prefixes for the directive and run parameters are `273e09f5` and `1fbda98a`. See the OFFICIAL sources and plan findings in [P12-D8](../decisions/P12-D8.md).
decision_needed: Select a current Render Postgres compute plan and a documented workspace recovery tier for staging and production. If standard is an internal tier, confirm which Render workspace plan it maps to.
options: `0.1c-256mb` matches the requested legacy database plan's CPU and memory and has a 100-connection limit. Hobby gives a three-day point-in-time recovery window. Pro gives a seven-day window. Another current paid database plan or higher workspace tier can be selected explicitly.
untouched: The deployment configuration, Phase 12 task ledger, state file, and remote refs.

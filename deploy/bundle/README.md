# Second-host bundle

Run `python -m tools.ops.exit_drill` from the repository with Docker and Compose available. The drill builds the application from the checked-out commit, starts a temporary project, exercises the authenticated API and policy decision, verifies a synthetic case export, and reports startup and elapsed seconds.

For an operator-managed instance, set `CTC_APP_IMAGE` to the verified application image reference and `CTC_SECRET_DIR` to the directory for that instance. Start with `docker compose -f deploy/bundle/compose.yaml up --wait`. The directory supplies `database_owner`, `database_application`, `database_migration`, `application_url`, `migration_url`, `session_key`, and `token_records`. The two URLs use the corresponding application and migration logins. The session key is 32 bytes encoded as hex, and the token records contain stored hashes and principal metadata. The application only receives its database URL, session key, and token records. The local port binds to loopback.

The official PostgreSQL 18.7 index has the owner-confirmed SHA-256 digest `eb63372c1e05c755f55fa30cbd07aecc443676fc6c0fa90b9002d01537841e1a` (V-13). The policy service uses the checksum-pinned Linux x86-64 executable specified in the dependency list. On an ARM host, Docker must support Linux x86-64 execution.

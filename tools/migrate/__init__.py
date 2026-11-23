"""Migration tool and ephemeral database utilities (P04-T01).

Provides:
- :mod:`tools.migrate.ephemeral` — start/stop an ephemeral PostgreSQL 18
  container for integration tests.
- :mod:`tools.migrate.migrate` — apply forward migrations under the
  migration-owner role.
"""

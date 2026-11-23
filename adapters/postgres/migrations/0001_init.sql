-- 0001_init.sql — initial schema and role privileges (P04-T01)
--
-- Expand-then-contract convention: this migration sets up the baseline
-- schema and grants.  All tables created by later migrations inherit
-- the privilege model established here.
--
-- The application role (ctc_application) receives USAGE on the public
-- schema but NOT CREATE — it cannot create tables.  Per-table DML
-- privileges are granted by the table-creating migrations (T02+).
--
-- The audit role (ctc_audit) receives USAGE on the public schema for
-- read-only queries.

-- Grant schema-level privileges.
GRANT USAGE ON SCHEMA public TO ctc_application;
GRANT USAGE ON SCHEMA public TO ctc_audit;

-- Revoke any default CREATE that might exist on the public schema
-- from the application and audit roles.
REVOKE CREATE ON SCHEMA public FROM ctc_application;
REVOKE CREATE ON SCHEMA public FROM ctc_audit;

-- Default privileges: tables created by the migration owner grant
-- SELECT, INSERT, UPDATE, DELETE to the application role.
ALTER DEFAULT PRIVILEGES FOR ROLE ctc_migration
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ctc_application;

-- Default privileges: tables created by the migration owner grant
-- SELECT to the audit role.
ALTER DEFAULT PRIVILEGES FOR ROLE ctc_migration
    GRANT SELECT ON TABLES TO ctc_audit;

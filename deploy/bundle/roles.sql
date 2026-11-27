CREATE ROLE ctc_application LOGIN;
CREATE ROLE ctc_migration LOGIN;
CREATE ROLE ctc_audit NOLOGIN;
\set application_password `cat /run/secrets/database_application`
\set migration_password `cat /run/secrets/database_migration`
ALTER ROLE ctc_application PASSWORD :'application_password';
ALTER ROLE ctc_migration PASSWORD :'migration_password';
ALTER SCHEMA public OWNER TO ctc_migration;

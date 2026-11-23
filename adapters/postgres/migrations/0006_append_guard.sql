-- 0006_append_guard.sql — append-only guard for evidence tables (P04-T06)
--
-- UPDATE and DELETE are denied on append-only tables (evidence_record).
-- A guard trigger rejects the operation before it executes.
-- The migration lint fails any migration that weakens this guard.

CREATE OR REPLACE FUNCTION _reject_modify() RETURNS trigger
    LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'append-only table % does not allow %', TG_TABLE_NAME, TG_OP;
END;
$$;

DROP TRIGGER IF EXISTS _append_only_guard ON "evidence_record";
CREATE TRIGGER _append_only_guard
    BEFORE UPDATE OR DELETE ON "evidence_record"
    FOR EACH ROW EXECUTE FUNCTION _reject_modify();

-- REVOKE UPDATE and DELETE from the application role on append-only tables.
REVOKE UPDATE ON "evidence_record" FROM ctc_application;
REVOKE DELETE ON "evidence_record" FROM ctc_application;

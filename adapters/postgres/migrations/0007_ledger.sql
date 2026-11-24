-- 0007_ledger.sql — ledger columns and system chain table (P05-T01, P05-T02)
--
-- Adds the ``type`` column to evidence_record (the record type, distinct
-- from the pipeline stage) and creates the system_chain table for
-- deployment and tenant system chains (Part 3 §3.5).
--
-- Expand-then-contract convention: the system_chain table inherits the
-- privilege model established by 0001_init.sql.  RLS is enabled and
-- forced with a deny-by-default tenant policy.  The deployment chain
-- uses tenant_id = '__deployment__' so RLS naturally hides it from
-- every real tenant.


-- Add type column to evidence_record (record type, not pipeline stage).
ALTER TABLE "evidence_record" ADD COLUMN IF NOT EXISTS "type" TEXT;


-- System chain table: deployment chain and tenant system chain records.
-- tenant_id is '__deployment__' for deployment chain events, the real
-- tenant id for tenant system chain events.
CREATE TABLE IF NOT EXISTS "system_chain" (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    UNIQUE (tenant_id, id),
    seq INTEGER NOT NULL,
    chain_type TEXT NOT NULL CHECK (chain_type IN ('DEPLOYMENT', 'TENANT')),
    stage TEXT,
    actor_id TEXT,
    actor_kind TEXT CHECK (actor_kind IN ('ROLE', 'HUMAN', 'SYSTEM')),
    event_type TEXT NOT NULL,
    payload_hash TEXT,
    payload_ref TEXT DEFAULT NULL,
    salt_id TEXT DEFAULT NULL,
    prev_hash TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    alg TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS for system_chain: deny-by-default tenant policy.
ALTER TABLE "system_chain" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "system_chain" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "system_chain"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

-- Append-only guard for system_chain (same pattern as evidence_record).
CREATE TRIGGER _append_only_guard
    BEFORE UPDATE OR DELETE ON "system_chain"
    FOR EACH ROW EXECUTE FUNCTION _reject_modify();

REVOKE UPDATE ON "system_chain" FROM ctc_application;
REVOKE DELETE ON "system_chain" FROM ctc_application;

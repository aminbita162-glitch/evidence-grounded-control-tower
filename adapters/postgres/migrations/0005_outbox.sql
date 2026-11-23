-- 0005_outbox.sql — outbox, idempotency and dead-letter tables (P04-T05)
--
-- These are infrastructure tables with tenant_id and RLS policies.
-- The outbox row commits in the same transaction as the state change.

CREATE TABLE IF NOT EXISTS _outbox (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    leased_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS _idempotency (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    key TEXT NOT NULL,
    result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, key)
);

CREATE TABLE IF NOT EXISTS _dead_letter (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS on infrastructure tables (deny-by-default, same as entity tables).
ALTER TABLE _outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE _outbox FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON _outbox
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE _idempotency ENABLE ROW LEVEL SECURITY;
ALTER TABLE _idempotency FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON _idempotency
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE _dead_letter ENABLE ROW LEVEL SECURITY;
ALTER TABLE _dead_letter FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON _dead_letter
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

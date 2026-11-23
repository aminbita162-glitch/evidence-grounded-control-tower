-- 0003_rls.sql — row-level security baseline (P04-T03)
--
-- Enables and forces RLS on every entity table with a deny-by-default
-- policy keyed on the transaction-local setting 'ctc.tenant_id'.
-- When the setting is absent, COALESCE returns '' which matches no
-- tenant_id, so no rows are visible and no writes are accepted.
--
-- FORCE means the table owner (ctc_migration) is also subject to RLS.


ALTER TABLE "approval" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "approval" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "approval"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "autonomy_policy" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "autonomy_policy" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "autonomy_policy"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "case" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "case" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "case"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "decision" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "decision" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "decision"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "document" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "document" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "document"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "evidence_record" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "evidence_record" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "evidence_record"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "fact" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "fact" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "fact"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "memory_entry" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "memory_entry" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "memory_entry"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "pack" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "pack" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "pack"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "passport" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "passport" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "passport"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "proposal" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "proposal" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "proposal"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "rule_result" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "rule_result" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "rule_result"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "simulation" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "simulation" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "simulation"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "source" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "source" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "source"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

ALTER TABLE "tenant" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "tenant" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "tenant"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

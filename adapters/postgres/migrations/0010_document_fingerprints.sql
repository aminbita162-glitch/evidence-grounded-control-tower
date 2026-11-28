-- Retention follows the source document. Tenant scope also applies to buckets.
CREATE TABLE IF NOT EXISTS "document_fingerprint" (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, id) REFERENCES "document"(tenant_id, id) ON DELETE CASCADE,
    content_hash TEXT NOT NULL,
    normalized_text_hash TEXT,
    identity_hash TEXT,
    minhash JSONB NOT NULL,
    shingle_hashes JSONB NOT NULL
);

ALTER TABLE "document_fingerprint" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "document_fingerprint" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "document_fingerprint"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

CREATE INDEX IF NOT EXISTS document_fingerprint_content
    ON "document_fingerprint"(tenant_id, content_hash);
CREATE INDEX IF NOT EXISTS document_fingerprint_text
    ON "document_fingerprint"(tenant_id, normalized_text_hash);
CREATE INDEX IF NOT EXISTS document_fingerprint_identity
    ON "document_fingerprint"(tenant_id, identity_hash);

CREATE TABLE IF NOT EXISTS "document_fingerprint_bucket" (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    UNIQUE (tenant_id, id),
    document_id TEXT NOT NULL,
    bucket_kind TEXT NOT NULL,
    bucket_key TEXT NOT NULL,
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES "document_fingerprint"(tenant_id, id) ON DELETE CASCADE
);

ALTER TABLE "document_fingerprint_bucket" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "document_fingerprint_bucket" FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON "document_fingerprint_bucket"
    FOR ALL
    USING (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''))
    WITH CHECK (tenant_id = COALESCE(current_setting('ctc.tenant_id', true), ''));

CREATE INDEX IF NOT EXISTS document_fingerprint_bucket_lookup
    ON "document_fingerprint_bucket"(tenant_id, bucket_kind, bucket_key);

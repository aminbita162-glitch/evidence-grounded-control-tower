-- P13: Add optional calculation trace references and Passport open items.
ALTER TABLE "decision"
    ADD COLUMN IF NOT EXISTS calculation_trace_hashes JSONB DEFAULT NULL;
ALTER TABLE "passport"
    ADD COLUMN IF NOT EXISTS open_items JSONB DEFAULT NULL;

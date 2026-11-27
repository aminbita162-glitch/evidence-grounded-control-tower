-- P12-CHG: Add the deployment configuration hash to Passport storage.
ALTER TABLE "passport"
    ADD COLUMN IF NOT EXISTS configuration_hash TEXT DEFAULT NULL;

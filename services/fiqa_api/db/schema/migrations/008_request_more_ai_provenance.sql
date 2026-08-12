-- AI Request More pilot signal — provenance of the draft wording the broker sent.
-- Holds a SHA-256 digest plus bounded model metadata. Never draft text, never PII.
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 008_request_more_ai_provenance.sql
--
-- Rollback for a non-production rehearsal only:
--   ALTER TABLE claim_request_drafts DROP COLUMN IF EXISTS ai_provenance;

ALTER TABLE claim_request_drafts
    ADD COLUMN IF NOT EXISTS ai_provenance JSONB;

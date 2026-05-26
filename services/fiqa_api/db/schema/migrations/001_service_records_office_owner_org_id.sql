-- Optional explicit migration (DDL also runs on first PG write via repository ensure).
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 001_service_records_office_owner_org_id.sql

ALTER TABLE service_records
    ADD COLUMN IF NOT EXISTS office_owner_org_id TEXT;

CREATE INDEX IF NOT EXISTS idx_service_records_office_owner_updated
    ON service_records (office_owner_org_id, updated_at DESC);

UPDATE service_records sr
SET office_owner_org_id = TRIM(sr.extra->>'asserted_org_id')
WHERE (office_owner_org_id IS NULL OR TRIM(office_owner_org_id) = '')
  AND sr.extra ? 'asserted_org_id'
  AND TRIM(sr.extra->>'asserted_org_id') <> '';

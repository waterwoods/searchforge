-- P3-B Slice 1 — Human-readable case reference (CLM-####).
-- Additive: case_id (record_id) remains the immutable primary key.
--
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 \
--     -f services/fiqa_api/db/schema/migrations/006_p3b_case_ref.sql
--
-- Rollback (non-production rehearsal only):
--   DROP INDEX IF EXISTS uq_service_records_case_ref;
--   ALTER TABLE service_records DROP COLUMN IF EXISTS case_ref;
--   DROP SEQUENCE IF EXISTS service_records_case_ref_seq;
--
-- Greenfield / Cloud also auto-adds via service_record_repository._ensure_case_ref_schema.

ALTER TABLE service_records
    ADD COLUMN IF NOT EXISTS case_ref TEXT;

CREATE SEQUENCE IF NOT EXISTS service_records_case_ref_seq;

-- Backfill existing rows in stable created_at order (safe re-run: only NULL rows).
WITH numbered AS (
    SELECT record_id,
           nextval('service_records_case_ref_seq') AS n
    FROM service_records
    WHERE case_ref IS NULL OR TRIM(case_ref) = ''
    ORDER BY created_at ASC NULLS LAST, record_id ASC
)
UPDATE service_records sr
SET case_ref = 'CLM-' || LPAD(numbered.n::text, 4, '0')
FROM numbered
WHERE sr.record_id = numbered.record_id;

-- Align sequence with max assigned numeric suffix (handles partial prior backfills).
SELECT setval(
    'service_records_case_ref_seq',
    GREATEST(
        COALESCE(
            (
                SELECT MAX(
                    CASE
                        WHEN case_ref ~ '^CLM-[0-9]+$'
                        THEN SUBSTRING(case_ref FROM 5)::bigint
                        ELSE 0
                    END
                )
                FROM service_records
            ),
            0
        ),
        1
    ),
    true
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_service_records_case_ref
    ON service_records (case_ref)
    WHERE case_ref IS NOT NULL AND TRIM(case_ref) <> '';

COMMENT ON COLUMN service_records.case_ref IS
    'P3-B: human case reference CLM-####. Immutable after assignment. Not derived from case_id hex.';

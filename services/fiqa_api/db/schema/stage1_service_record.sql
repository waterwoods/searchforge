-- Stage 1 Unified Intake — minimal service-record backbone (Postgres).
-- Aligns with docs/STAGE_1_SERVICE_RECORD_DB_BLUEPRINT.md
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f stage1_service_record.sql
--
-- Notes:
-- - record_id matches JSON pilot case_id (e.g. case_abc123...).
-- - Customers table deferred; contact fields live on service_records for pilot parity.
-- - gen_random_uuid() is built-in on PostgreSQL 13+.

CREATE TABLE IF NOT EXISTS service_records (
    record_id TEXT PRIMARY KEY,
    client_id TEXT,
    intake_channel TEXT NOT NULL DEFAULT 'portal',
    issue_category TEXT,
    title_summary TEXT,
    case_status TEXT NOT NULL,
    lifecycle_status TEXT,
    waiting_on TEXT NOT NULL DEFAULT 'none',
    next_contact_by TEXT NOT NULL DEFAULT '',
    current_owner TEXT,
    current_next_action TEXT,
    customer_name TEXT NOT NULL DEFAULT '',
    customer_phone TEXT NOT NULL DEFAULT '',
    customer_email TEXT NOT NULL DEFAULT '',
    policy_number TEXT NOT NULL DEFAULT '',
    contact_note TEXT NOT NULL DEFAULT '',
    origin_session_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    office_owner_org_id TEXT,
    -- P3-B: human case reference CLM-#### (additive; record_id remains PK)
    case_ref TEXT,
    extra JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE SEQUENCE IF NOT EXISTS service_records_case_ref_seq;

CREATE UNIQUE INDEX IF NOT EXISTS uq_service_records_case_ref
    ON service_records (case_ref)
    WHERE case_ref IS NOT NULL AND TRIM(case_ref) <> '';

CREATE INDEX IF NOT EXISTS idx_service_records_client_updated
    ON service_records (client_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_records_office_owner_updated
    ON service_records (office_owner_org_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS record_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    external_message_id TEXT NOT NULL,
    sender_type TEXT NOT NULL,
    message_text TEXT NOT NULL,
    source_channel TEXT NOT NULL DEFAULT 'portal',
    raw_payload JSONB,
    sequence_num INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_record_messages_record_ext UNIQUE (record_id, external_message_id)
);

CREATE INDEX IF NOT EXISTS idx_record_messages_record_seq
    ON record_messages (record_id, sequence_num);

CREATE TABLE IF NOT EXISTS structured_record_data (
    record_id TEXT PRIMARY KEY REFERENCES service_records (record_id) ON DELETE CASCADE,
    structured_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    completeness_level TEXT,
    quote_readiness TEXT,
    missing_fields_summary TEXT,
    extracted_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS state_history (
    state_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    from_status TEXT,
    to_status TEXT NOT NULL,
    triggered_by TEXT NOT NULL DEFAULT 'system',
    reason TEXT,
    snapshot_note TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_state_history_record_created
    ON state_history (record_id, created_at DESC);

CREATE TABLE IF NOT EXISTS office_actions (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    action_type TEXT NOT NULL,
    note_text TEXT,
    next_step_note TEXT,
    actor TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_office_actions_record_created
    ON office_actions (record_id, created_at DESC);

-- Stage 2 — Real usage timing instrumentation (observational telemetry).
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 007_case_activity_events.sql
--
-- Runtime also CREATE TABLE IF NOT EXISTS on first write (QA / local).

CREATE TABLE IF NOT EXISTS case_activity_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    source_surface TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    idempotency_key TEXT NOT NULL,
    session_id_hash TEXT,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_case_activity_events_idempotency
    ON case_activity_events (case_id, event_type, idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_case_activity_events_first_wins
    ON case_activity_events (case_id, event_type)
    WHERE event_type IN (
        'customer_intake_opened',
        'customer_first_action',
        'broker_first_opened'
    );

CREATE INDEX IF NOT EXISTS idx_case_activity_events_case_created
    ON case_activity_events (case_id, created_at ASC);

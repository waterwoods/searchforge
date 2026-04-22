-- In-progress Unified Intake sessions (turns, workflow_state, light identity, etc.)
-- Single source of truth when SERVICE_RECORD_DATABASE_URL or DATABASE_URL is set.
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f intake_sessions.sql

CREATE TABLE IF NOT EXISTS intake_sessions (
    session_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_intake_sessions_updated_at ON intake_sessions (updated_at DESC);

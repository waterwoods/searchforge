-- WeCom callback inbox queue (Q0.1) — fast ack + durable dedup for worker processing.
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f wecom_inbox_events.sql

CREATE TABLE IF NOT EXISTS wecom_inbox_events (
    id BIGSERIAL PRIMARY KEY,
    dedup_key TEXT NOT NULL UNIQUE,
    open_kf_id TEXT,
    external_userid TEXT,
    callback_token TEXT,
    event_type TEXT,
    payload_json JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    locked_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wecom_inbox_events_status_created
    ON wecom_inbox_events (status, created_at ASC);

-- WeCom inbound message idempotency (Q0.10) — each msg_id processed at most once.
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f wecom_message_processed.sql

CREATE TABLE IF NOT EXISTS wecom_message_processed (
    msg_id TEXT PRIMARY KEY,
    open_kf_id TEXT,
    external_userid TEXT,
    event_type TEXT,
    case_id TEXT,
    outcome TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wecom_message_processed_external_userid
    ON wecom_message_processed (external_userid, created_at DESC);

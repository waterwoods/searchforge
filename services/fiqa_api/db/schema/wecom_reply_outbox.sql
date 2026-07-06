-- WeCom reply outbox (Q0.3) — durable outbound queue for kf/send_msg.
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f wecom_reply_outbox.sql

CREATE TABLE IF NOT EXISTS wecom_reply_outbox (
    id BIGSERIAL PRIMARY KEY,
    dedup_key TEXT NOT NULL UNIQUE,
    msg_id TEXT,
    external_userid TEXT,
    open_kf_id TEXT,
    case_id TEXT,
    reply_type TEXT,
    reply_payload_json JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    locked_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    errcode INTEGER,
    errmsg TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_wecom_reply_outbox_status_created
    ON wecom_reply_outbox (status, created_at ASC);

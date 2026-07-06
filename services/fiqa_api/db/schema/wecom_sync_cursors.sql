-- WeCom kf/sync_msg cursor watermark per open_kf_id (Q0.10).
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f wecom_sync_cursors.sql

CREATE TABLE IF NOT EXISTS wecom_sync_cursors (
    open_kf_id TEXT PRIMARY KEY,
    cursor TEXT,
    last_sync_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

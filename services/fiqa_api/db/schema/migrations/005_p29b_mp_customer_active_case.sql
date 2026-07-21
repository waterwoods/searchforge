-- P29B — Lightweight identity Active Case index (not a Customer Account table).
-- Maps opaque person_link_key (HMAC of OpenID) → one Active Case for Resume.
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 005_p29b_mp_customer_active_case.sql
--
-- Greenfield also auto-creates via mp_customer_identity._ensure_active_case_table.
--
-- Rollback (non-production rehearsal only):
--   DROP TABLE IF EXISTS mp_customer_active_case;

CREATE TABLE IF NOT EXISTS mp_customer_active_case (
    person_link_key TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mp_customer_active_case_case_id
    ON mp_customer_active_case (case_id);

COMMENT ON TABLE mp_customer_active_case IS
    'P29B: opaque WeChat person_link → one Active Case. Not a profile/account table. Never stores OpenID.';

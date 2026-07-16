-- P20 Capability 3A — Send Request + customer access (MVP).
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 004_p20_send_request_customer_access.sql
--
-- Rollback for a non-production rehearsal only:
--   DROP TABLE IF EXISTS claim_customer_access;

CREATE TABLE IF NOT EXISTS claim_customer_access (
    access_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    request_group_id TEXT NOT NULL REFERENCES claim_request_groups (request_id) ON DELETE CASCADE,
    tenant_id TEXT,
    office_id TEXT,
    token_hash TEXT NOT NULL,
    token_nonce TEXT NOT NULL,
    token_iat INTEGER NOT NULL,
    token_exp INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'ready',
    access_version INTEGER NOT NULL DEFAULT 1,
    created_by TEXT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One active (ready) access per open request group.
CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_customer_access_ready_group
    ON claim_customer_access (request_group_id)
    WHERE status = 'ready';

-- One ready access per case (MVP: one active invite).
CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_customer_access_ready_case
    ON claim_customer_access (case_id)
    WHERE status = 'ready';

CREATE INDEX IF NOT EXISTS idx_claim_customer_access_case
    ON claim_customer_access (case_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_claim_customer_access_token_hash
    ON claim_customer_access (token_hash);

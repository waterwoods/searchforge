-- P20 Capability 2 — Case Intake draft + missing-information + request draft.
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 003_p20_case_intake_draft.sql
--
-- Rollback for a non-production rehearsal only:
--   DROP TABLE IF EXISTS claim_intake_command_outcomes;
--   DROP TABLE IF EXISTS claim_intake_events;
--   DROP TABLE IF EXISTS claim_request_drafts;
--   DROP TABLE IF EXISTS claim_intake_aggregates;

CREATE TABLE IF NOT EXISTS claim_intake_aggregates (
    case_id TEXT PRIMARY KEY REFERENCES service_records (record_id) ON DELETE CASCADE,
    admin_lifecycle TEXT NOT NULL DEFAULT 'draft',
    aggregate_version INTEGER NOT NULL DEFAULT 0,
    is_test BOOLEAN NOT NULL DEFAULT FALSE,
    office_id TEXT,
    tenant_id TEXT,
    fact_records JSONB NOT NULL DEFAULT '{}'::jsonb,
    customer_projection JSONB NOT NULL DEFAULT '{}'::jsonb,
    broker_projection JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_claim_intake_aggregates_office
    ON claim_intake_aggregates (office_id, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_claim_intake_aggregates_test
    ON claim_intake_aggregates (is_test, updated_at DESC);

CREATE TABLE IF NOT EXISTS claim_request_drafts (
    draft_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL UNIQUE REFERENCES service_records (record_id) ON DELETE CASCADE,
    draft_version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'draft',
    items JSONB NOT NULL DEFAULT '[]'::jsonb,
    content_hash TEXT NOT NULL,
    updated_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_claim_request_drafts_case_updated
    ON claim_request_drafts (case_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS claim_intake_events (
    event_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    command_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    aggregate_version INTEGER NOT NULL,
    expected_state_version INTEGER,
    actor TEXT NOT NULL,
    actor_identity TEXT NOT NULL,
    state_before TEXT NOT NULL DEFAULT '',
    state_after TEXT NOT NULL DEFAULT '',
    visibility TEXT NOT NULL DEFAULT 'broker',
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_intake_events_sequence
    ON claim_intake_events (case_id, sequence_number);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_intake_events_command_type
    ON claim_intake_events (case_id, command_id, event_type);

CREATE INDEX IF NOT EXISTS idx_claim_intake_events_case_created
    ON claim_intake_events (case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS claim_intake_command_outcomes (
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES service_records (record_id) ON DELETE CASCADE,
    actor_identity TEXT NOT NULL,
    command_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    command_type TEXT NOT NULL,
    outcome TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    event_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    response JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- CreateClaim is keyed before case_id exists: actor + idempotency (and command_id).
CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_intake_create_idempotency
    ON claim_intake_command_outcomes (actor_identity, idempotency_key)
    WHERE command_type = 'CreateClaim';

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_intake_create_command
    ON claim_intake_command_outcomes (command_id)
    WHERE command_type = 'CreateClaim';

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_intake_case_idempotency
    ON claim_intake_command_outcomes (case_id, actor_identity, idempotency_key)
    WHERE case_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_intake_case_command
    ON claim_intake_command_outcomes (case_id, command_id)
    WHERE case_id IS NOT NULL;

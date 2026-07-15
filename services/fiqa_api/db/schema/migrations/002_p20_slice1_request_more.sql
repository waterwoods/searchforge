-- P20 Slice 1 — Broker Request More -> Customer Continue companion storage.
-- Apply:
--   psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f 002_p20_slice1_request_more.sql
--
-- Rollback for a non-production rehearsal only:
--   DROP TABLE IF EXISTS claim_slice1_command_outcomes;
--   DROP TABLE IF EXISTS claim_slice1_events;
--   DROP TABLE IF EXISTS claim_request_items;
--   DROP TABLE IF EXISTS claim_request_groups;
--   DROP TABLE IF EXISTS claim_slice1_aggregates;

CREATE TABLE IF NOT EXISTS claim_slice1_aggregates (
    case_id TEXT PRIMARY KEY REFERENCES service_records (record_id) ON DELETE CASCADE,
    workflow_state TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL DEFAULT 0,
    active_request_id TEXT,
    customer_projection JSONB NOT NULL DEFAULT '{}'::jsonb,
    broker_projection JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claim_request_groups (
    request_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_request_groups_one_open
    ON claim_request_groups (case_id)
    WHERE status = 'open';

CREATE INDEX IF NOT EXISTS idx_claim_request_groups_case_updated
    ON claim_request_groups (case_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS claim_request_items (
    request_item_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL REFERENCES claim_request_groups (request_id) ON DELETE CASCADE,
    case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
    item_type TEXT NOT NULL,
    label TEXT NOT NULL,
    instructions TEXT NOT NULL DEFAULT '',
    required BOOLEAN NOT NULL DEFAULT true,
    position INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    satisfied_at TIMESTAMPTZ,
    satisfied_by_event_id TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_request_items_position
    ON claim_request_items (request_id, position);

CREATE INDEX IF NOT EXISTS idx_claim_request_items_case_status
    ON claim_request_items (case_id, status, position);

CREATE TABLE IF NOT EXISTS claim_slice1_events (
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
    state_before TEXT NOT NULL,
    state_after TEXT NOT NULL,
    visibility TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_events_sequence
    ON claim_slice1_events (case_id, sequence_number);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_events_command_type
    ON claim_slice1_events (case_id, command_id, event_type);

CREATE INDEX IF NOT EXISTS idx_claim_slice1_events_case_created
    ON claim_slice1_events (case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS claim_slice1_command_outcomes (
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL REFERENCES service_records (record_id) ON DELETE CASCADE,
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

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_command_outcome_idempotency
    ON claim_slice1_command_outcomes (case_id, actor_identity, idempotency_key);

CREATE UNIQUE INDEX IF NOT EXISTS uq_claim_slice1_command_outcome_command
    ON claim_slice1_command_outcomes (case_id, command_id);

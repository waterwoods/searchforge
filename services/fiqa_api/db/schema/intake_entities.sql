-- Vehicle Entity Memory MVP — intake entity rows (Postgres JSONB).
-- Apply: psql "$SERVICE_RECORD_DATABASE_URL" -v ON_ERROR_STOP=1 -f intake_entities.sql
-- Same database as Stage 1 service records (see stage1_service_record.sql).

CREATE TABLE IF NOT EXISTS intake_entities (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    case_id TEXT,
    entity_type TEXT,
    entity_id TEXT,
    payload JSONB,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_intake_entities_session_type_active
    ON intake_entities (session_id, entity_type)
    WHERE is_active = true;

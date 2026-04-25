# Vehicle Entity Memory — MVP Contract

## 1. Purpose

- Stabilize **vehicle identity** across conversation turns (year, make/model, VIN, garaging ZIP, driver signals).
- Persist a single **authoritative JSONB snapshot** per intake session for later correction flows and multi-vehicle work (post-MVP).
- **Does not** replace triage logic or client replies; it is storage + repository only.

## 2. Scope

**In**

- Vehicle entity record only (`entity_type = vehicle`).
- Postgres table + JSONB `payload`.
- Repository read/write with merge semantics for the active vehicle.

**Out**

- Person / contact entity (separate effort).
- Multi-vehicle resolution, disambiguation, or “which car” ranking.
- Full triage integration (replies, guardrails, still-needed lists).
- Removal / soft-delete flows for entity rows (MVP: no removal logic in app).

## 3. Entity shape (logical)

Stored as columns + JSONB `payload`. Logical form:

```json
{
  "entity_id": "...",
  "session_id": "...",
  "case_id": "...",
  "entity_type": "vehicle",
  "payload": {
    "year": "",
    "make": "",
    "model": "",
    "vin": "",
    "zip": "",
    "driver": "",
    "source_turns": [],
    "confidence": {}
  },
  "is_active": true
}
```

`entity_id`, `session_id`, `case_id`, `entity_type`, `is_active`, and `updated_at` are reflected in table columns; nested fields live under `payload` as JSONB.

## 4. Invariants (MVP)

- **Single active vehicle** per `session_id` for `entity_type = vehicle` (enforced by repository: upsert into one logical row).
- **Last update wins** for scalar fields in `payload` (dict merge: new keys overwrite).
- **No multi-vehicle** selection or parallel actives.
- **No removal** — no API to delete or deactivate for pilot MVP (optional future: `is_active = false`).

## 5. Application

- Schema: `services/fiqa_api/db/schema/intake_entities.sql` (apply with `psql` against `SERVICE_RECORD_DATABASE_URL` / `DATABASE_URL`, same as Stage 1 service record).
- Repository: `services/fiqa_api/inbox_triage/entity_repository.py`.
- Optional triage hook: best-effort persistence after add-car truth fields are computed; failures must not affect triage JSON.

## 6. Rollback

- Drop table: `DROP TABLE IF EXISTS intake_entities;` (only if no downstream use).
- Disable optional hook: omit `session_id` from triage `reply_truth_context` or stop calling repository from triage.

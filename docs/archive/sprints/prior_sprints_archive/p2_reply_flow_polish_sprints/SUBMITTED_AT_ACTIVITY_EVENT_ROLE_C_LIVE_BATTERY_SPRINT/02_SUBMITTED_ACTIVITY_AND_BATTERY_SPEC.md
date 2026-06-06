# Submitted / activity model + battery spec

## Target model (bounded)

| Signal | Field | Semantics |
|--------|--------|-----------|
| First formal office-visible persist | `formal_submitted_at` | Set once in `save_case` to the same instant as first persist; **not** updated on `append_follow_up_message`, notes, attachments, follow-up patches. |
| Recent activity | `updated_at` | Last case write (append, note, status, attachment, etc.). |
| Legacy compatibility | `_normalize_case` | If `formal_submitted_at` missing, backfill from `created_at`. |

Postgres dual-write: `formal_submitted_at` is included in `service_records.extra` JSONB via `_build_extra` (no new SQL column in this sprint).

## Battery cases (Role C)

Preset `handoff_loop` in `scripts/run_role_c_add_car_battery.py`:

| ID | Persona | Difficulty | Max turns |
|----|---------|------------|-----------|
| C1 | price_sensitive | realistic | 6 |
| C2 | price_sensitive | tough | 8 |
| C3 | elderly | tough | 8 |
| C4 | family_vehicle | realistic | 6 |
| C5 | materials_first | realistic | 6 |

Default battery uses `persist_case: false` — it validates **lifecycle / handoff / reply** under multi-turn Role C, not persistence timestamps. To validate `formal_submitted_at`, use `scripts/test_inbox_triage_api.py` append flow or a manual formal submit + append.

## Issue harvest categories

- **Submitted/activity observability** — unclear submit moment, activity conflated with resubmit.
- **Triage / extraction** — still_needed, corrections, additions.
- **Handoff reply truth** — repetitive, off-topic, too-office-too-early.
- **Persona realism** — synthetic, weak persona/difficulty separation.
- **Demo / product clarity** — queue, workbench, right rail drift.

## Acceptance criteria

- New persisted Add-Car cases include `formal_submitted_at` equal to first-persist `created_at`.
- After customer append, `formal_submitted_at` unchanged; `updated_at` moves.
- UI shows distinct labels when both timestamps differ (portal + workbench + queue + rail).
- `bash scripts/guardrail_inbox_triage.sh` passes (API step may WARN until server restarted on new code).

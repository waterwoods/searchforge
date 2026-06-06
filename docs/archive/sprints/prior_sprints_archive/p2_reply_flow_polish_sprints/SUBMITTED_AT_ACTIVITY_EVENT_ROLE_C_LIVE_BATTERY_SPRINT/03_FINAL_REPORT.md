# Final report — SUBMITTED_AT ACTIVITY EVENT + ROLE C LIVE BATTERY

## Implemented

- **Backend:** `formal_submitted_at` on `save_case`; legacy backfill in `_normalize_case`; dual-write `extra` includes the field.
- **API tests:** `scripts/test_inbox_triage_api.py` asserts presence, equality to `created_at` on create, stability on append.
- **Frontend:** `TriageResult.formal_submitted_at`; portal closure timing block; office workbench submission snapshot; queue card scan line; `AddCarHandoffGroupedSnapshot` timing section; copy keys in `configs/clients/chen_kui/ui_copy.json` and `ui/src/api/clientConfig.ts`.

## Deploy

- **Not verified in this session** (no successful Cloud Run / Vercel deploy executed here). Restart any long-lived local `uvicorn` on 8001 so `POST /api/inbox/triage` persist tests see the new field.

## Battery

- **Intended command:** `PYTHONPATH=. python3 scripts/run_role_c_add_car_battery.py --preset handoff_loop --client-id chen_kui --base-url <live-api>`
- **Note:** Preset does not persist cases; use API append test for timestamp truth. Run battery when `OPENAI_API_KEY` is set.

## Issues observed (implementation / ops)

- Running API on **old process** without restart: guardrail step `[3]` can WARN on formal_submitted_at assertion until backend reloads new `case_store.py`.

## Recommended next sprint

- **Short:** Restart/deploy backend everywhere pilots hit; optional battery flag to materialize one formal submit per variant for end-to-end timestamp proof.
- **Product:** If still_needed churn under multi-turn Role C is noisy, run a focused **triage stability** sprint (same scope as issue bucket B).

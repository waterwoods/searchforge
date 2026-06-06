# ROLE C BACKEND BATTERY HARDENING — Final Report

## What was improved

- **`scripts/run_role_c_add_car_battery.py`:** Richer per-turn trace (intent snapshot, still-needed, quote readiness, case/timing fields, warnings per row); `run_summary` aggregation; `warnings_flat`; `--report`, `--include-labels`, `--max-chars`; fixed `warnings_flat` n-warnings print bug.
- **`scripts/role_c_battery_oracles.py`:** New bounded heuristics (Truth / Intent / Reply / State) with codes and layers; `aggregate_run_summary` for top codes and turns-with-warnings.

## Warnings added

See `02_BATTERY_HARDENING_SPEC.md` for the table (`TRUTH_*`, `INTENT_*`, `REPLY_*`, `STATE_*`, `STATE_INFO`).

## Live runs executed

- **Environment:** `ROLE_C_BATTERY_BASE_URL=http://127.0.0.1:8002` (repo-aligned `max_turns` validation), `CLIENT_ID=chen_kui` via `--client-id chen_kui`, local WSL2, ~2026-03-29.
- **Cases:** `sprint_10_turn` preset filtered to `C1-price-sensitive-tough-10`, `C3-family-vehicle-realistic-10`, `C4-materials-first-realistic-10` (10 Role C turns + truth-chain inject when `handoff_ready` → 11 trace rows each).

## Issues still observed (heuristic)

- **`TRUTH_HANDOFF_READY_CONTACT_GAP`** dominated (9–10 hits per run): `handoff_ready` co-occurring with `name`/`phone` in `still_needed_fields` across many turns—strong product signal for contact-gap vs. readiness wording.
- **C1:** **`REPLY_REPEATED_BLOCK`** (4): late-turn repetition signal.
- **Post-submit nag / pre-submit office receipt:** Not the top signal in these three runs (good for those layers).

## Recommended next sprint

1. **Short term:** Tune `TRUTH_HANDOFF_READY_CONTACT_GAP` (dedupe per run or first-seen-only) if noise is too high; keep raw trace for audits.
2. **Product:** Tighten truth/contact rules so `handoff_ready` and `still_needed_fields` do not contradict broker expectations.
3. **Backend battery:** Add optional JSON export path and `--compare` to diff two JSONL runs (small scope).
4. **Frontend Role C Plus:** only after one more battery pass stabilizes traces and warnings for demo.

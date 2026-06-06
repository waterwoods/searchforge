# RESTART / REBASELINE ROLE C SMOKE — Final report

**Date:** 2026-03-29 (execution)  
**Environment:** WSL2 local, repo `/home/andy/searchforge`

## What was restarted / deployed

- **Local API on 127.0.0.1:8001** — previous PID **2372712** stopped; new `uvicorn` PID **2511001** (see operator shell / `nohup` log `/tmp/fiqa_8001_restart.log` if retained).
- **Cloud Run / remote:** not touched; **not verified** aligned.

## What was proven live

### A. Intent visibility

- **Before restart:** `add_car_turn_intent` was **`null`** on a representative Add-Car triage POST.
- **After restart:** same shape request returned a **dict**, e.g. `intent_family`, `handoff_base_key`, `phrase_storage_key`, `truth_notes`.

### B. Late-turn / reply routing (sample)

- Timeline-style follow-up resolved to **`timeline_question`** with a customer-visible draft that engaged the question (spot-check; not a full oracle pass).

### C. Short Role C smoke

Commands (conceptually):

- `run_role_c_add_car_battery.py --base-url http://127.0.0.1:8001 --persona price_sensitive --difficulty tough --max-turns 4 --client-id chen_kui --report`
- Same with `family_vehicle` / `realistic` / 4  
- Same with `materials_first` / `realistic` / 4  

**Result:** each run **OK**, `trace_rows=4`, **heuristic_warnings=0** for all three.

Additional **JSONL** sample (`price_sensitive` / `tough` / 3 turns): trace rows included `add_car_turn_intent` with e.g. `quote_detail_question` and `truth_notes` — confirms smoke is observing the new field path.

## What remains uncertain

- **8002** and **Docker 8000** processes were not re-baselined; any script pointing there may still be stale.
- **Production** (Cloud Run) alignment requires a deploy + the same HTTP checks against the prod base URL.

## Recommended next sprint

- Either **explicit Cloud Run re-baseline + timestamp proof** (if demos use prod), or **document “local 8001 is canonical for dev batteries”** and add a one-liner preflight that asserts `add_car_turn_intent` is non-null before long runs.

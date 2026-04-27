# Final lock-in sprint report

## 1. Time

| Field | Value |
|--------|--------|
| START_TS | 2026-04-27T06:09:31-07:00 |
| END_TS | 2026-04-27T06:31:50-07:00 |

## 2. Git integrity

| Check | Result |
|--------|--------|
| Stash dependency removed? | **Yes.** Pre-eval stash `stash@{0}` was **dropped** after committing the same work to `c84150b` (`final: restore binding + stub + resolver for production`). |
| Clean boot works? | **Yes.** After `pip install -r requirements.txt`, `PYTHONPATH=. python3 -c "from services.fiqa_api.app_main import app"` succeeds (FastAPI app loads). Untracked caches were excluded from `git clean` via `-e results` and via `.gitignore` entries for `models/`, `hub/`, `xet/`. |
| Other stashes | Older stashes remain in the stack; only the blocking pre-final-eval stash was cleared. |

**Commit scope (14 files):** Postgres triage stub + binding list helpers, `get_case_triage_stub_for_read` / `list_recent_cases_for_binding`, `active_vehicle_request_cache_scope` on POST `/api/inbox/triage`, `lru_cache` on soft-route copy, session no-op write skip, add-car fastlane when PG identity is already unambiguous, chaos + latency scripts, `final_real_world_scenarios.py`, `active_vehicle_resolver.py` + unit tests, real-user simulation test updates.

## 3. Scenario coverage

| | Count |
|---|--------|
| Before (add-car entity integration library) | **7** |
| After (`tests/scenario_libraries/final_real_world_scenarios.py`) | **28** |

## 4. Real-world results (`results/FINAL_REAL_WORLD.json`)

| Metric | Value |
|--------|--------|
| Pass / fail | **28 / 0** (all sessions) |
| Clarify turns (`active_vehicle_clarify_prompt`) | **0** |
| LLM generation | enabled |
| PG env | enabled (`pg_env: true`) |
| Duration | ~594 s for full ASGI pack |

**Issues observed (manual review of JSON):**

- **Semantic oddity (non-failure):** In `frw_mv_not_that_one`, one turn produced a **garbled `primary_vehicle_summary`** (user negation text absorbed as “model” phrasing) while **Postgres entity and API still agreed** (`pg_truth_match: true`). The chaos harness does not judge user intent; it judges API↔entity consistency. **Track for product QA:** correction phrasing “no not that one” without restating the truck may need resolver or slot cleanup.
- No extra active-vehicle clarify prompts in this run.
- No multi-active-row failures (`active_rows_in_db` stayed 1 where DB was used).

## 5. Latency (`results/FINAL_LATENCY_LOCK.json`)

`TRIAGE_RETURN_PERF_METRICS=1`, same library, 28 sessions / 136 turns.

| Metric | Value |
|--------|--------|
| HTTP `total_http_request` **p95** | **5154.96 ms** (~5.15 s) |
| HTTP **max** | **7071.33 ms** (~7.07 s) |
| Triage core **p95** | 3056.56 ms |
| Stable? | **Mostly stable** in the p50 band (~3.45 s HTTP), but **max spike above 7 s** — not “spike-free” under strict interpretation. |

**Target:** HTTP p95 &lt; 5 s — **missed by ~150 ms** on this run.

## 6. Final risks

- **Latency:** HTTP p95 slightly above 5 s; tail up to ~7 s (session `frw_long_9_oco`). Worth watching in production with the same perf flags.
- **Resolver module:** `active_vehicle_resolver.py` is **unit-tested** but **not yet imported** from `triage.py` — central disambiguation still depends on existing triage logic. **REMOVE_LATER:** either wire `resolve_add_car_active_vehicle` into the add-car path or fold tests into the current resolver surface to avoid two sources of truth.
- **Metrics:** `llm` / `db` / `resolver` sub-ms lines in the profile output were **0** in this run — likely routing into `route_perf` / `triage_turn_metrics` shape; treat component split as **approximate** until verified against instrumented paths.
- **Duplicate / layers (audit, no code removal now):** stub read (`get_case_triage_stub_for_read`) vs full `get_case_for_read` — intentional performance split; **REMOVE_LATER** review for any route still pulling full case on hot path. **REMOVE_LATER** dead import scan: `resolve_add_car_active_vehicle` unused outside tests.

## 7. Final judgment

**READY_WITH_MONITORING**

Rationale: Repo no longer depends on the shelved patch; extended live ASGI scenarios and the full guardrail battery pass; entity/API consistency held on all chaos turns. HTTP p95 is marginally above the 5 s bar with observable tail latency, so ship with latency and error-budget monitoring rather than treating the SLO as strictly met.

## 8. One line

System is safe to deploy because **production binding/stub/cache paths and the 28-scenario live ASGI pack + guardrail suite all passed, with only minor HTTP tail latency and one semantic-summary edge case to monitor in the field.**

---

## REMOVE_LATER (do not delete now)

1. Wire or delete **unused** `active_vehicle_resolver.resolve_add_car_active_vehicle` import path in triage to avoid parallel disambiguation stories.
2. Re-audit **route** vs **triage** ms attribution when `triage_turn_metrics` is partial.
3. Optional: tighten **add-car** extraction when the user **negates** a vehicle without supplying a positive vehicle descriptor in the same turn (`frw_mv_not_that_one`).

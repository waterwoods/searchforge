# Triage orchestration deep optimization sprint

**Branch:** `auto-evolution/triage-orchestration-deep-optimization-20260507-0038`  
**Single source of truth:** this file for the sprint run (2026-05-07).  
**Primary route:** `POST /api/inbox/triage` (`services/fiqa_api/routes/inbox_triage.py`).

---

## OBJECTIVE

Map real hotspots on the Unified Intake triage POST path (session IO, binding/stub fan-out, PG hydration, serialization/finalize, postprocess), add safe observability where gaps exist, and ship **2+ low-risk** orchestration optimizations with **green regression** and **recorded timing evidence**.

## NON_GOALS

- Changing triage intent, resolver semantics, or active-vehicle authority rules.
- Removing safety checks or narrowing API response fields.
- Large refactors of `triage.py` / LLM paths.
- Rewriting workbench enrichment (not on triage POST).

## SUCCESS_GATES

| Gate | Criterion |
|------|-----------|
| G1 | Hot path traced: session → binding → core triage → finalize → postprocess → async analytics |
| G2 | ≥2 meaningful optimizations merged (no semantic drift) |
| G3 | `python3 -m compileall` + `bash scripts/guardrail_inbox_triage.sh` + `PYTHONPATH=. python3 scripts/run_full_regression.py` green |
| G4 | Frontend: `npm run build` + `npx madge --circular --extensions ts,tsx src` clean |
| G5 | Timing evidence recorded (chaos `route_perf` / regression rollup or curl) |

## LATENCY_BASELINES

| Source | When | Notes |
|--------|------|-------|
| Chaos ASGI (`scripts/llm_chaos_live_triage_check.py`, `TRIAGE_RETURN_PERF_METRICS=1`) | Pre-change / post-change | `route_perf.*` on each turn; rollup via `run_full_regression.py` → `results/FULL_REGRESSION.json` |
| Prior project baselines | `results/FINAL_LATENCY_LOCK.json`, `docs/PRODUCTION_METRICS.md` | Historical; not re-run in this note unless script executed |

**Post-sprint rollup** (from `results/FULL_REGRESSION.json`, 2026-05-07 run):

- HTTP **p50** 3321.0 ms · **p95** 4860.0 ms · max 5549.0 ms (`latency_rollup_from_chaos_turns`)
- Core triage (`route_perf.triage_ms` aggregate): **p50** 834.7 ms · **p95** 2923.6 ms
- Gate: **http_p95 &lt; 6000 ms** — **PASS** (4859.9 ms)

## SYSTEM_MAP

```
Client → FastAPI inbox_triage.router
  → triage_inbox (wrappers: triage_stub_read_cache_scope + active_vehicle_request_cache_scope on other routes)
  → intake_session_repository.get_session (PG/session row)
  → case_truth_repository: list_recent_cases_for_binding, get_case_triage_stub_for_read (stub cache)
  → triage_conversation (core engine; CPU/LLM)
  → assist thread (background), patch_session_case_binding, optional save_case / save_in_progress_session
  → _finalize_triage_http_contract (lifecycle + API defaults + PG vehicle overlay)
  → _schedule_route_analytics (thread offload)
```

## TRIAGE_EXECUTION_GRAPH

1. **Ingress:** normalize text, optional inline OCR → `merge_v6_ocr_signals`.
2. **Session seg1:** `get_session` + optional quote-ready analytics scan on prior turns.
3. **Binding seg (`case_ms` bucket today):** vehicle key from labeled thread; `resolve_active_case`; stub/load `existing_case`; `reply_truth_context`.
4. **Core:** `triage_conversation` + soft-route reroute / starter copy (`get_soft_route_inbox_copy`).
5. **Session seg2:** session patch / clear binding on boundary.
6. **Persist branch (optional):** `save_case` + `save_session_binding_after_case_created`; finalize + analytics.
7. **Default branch:** `_finalize_triage_http_contract`, analytics, optional `save_in_progress_session` (embeds `triageResult` in turn JSON).

## ROUTE_STAGE_MAP

| Stage | Code anchor | `route_perf` key (when enabled) |
|-------|-------------|----------------------------------|
| Session read + early thread setup | ~L1078–L1103 | `session_ms` seg1 (see trust note below) |
| Binding + stubs + reply_truth + v6 | ~L1104–L1187 | `case_ms` (prep before core triage) |
| Core triage | `triage_conversation` | `triage_ms` |
| Soft-route conversion | reroute block | `conversion_ms` |
| Assist dispatch | `_attach_assist_layer` | `assist_ms` |
| Session patch seg2 | binding patches | part of `session_ms` seg2 |
| Case persist | `save_case` | `case_ms` includes persist when taken |
| Finalize + PG overlay | `_finalize_triage_http_contract` | `postprocess_finalize_ms` (this sprint, when `TRIAGE_RETURN_PERF_METRICS=1`) |
| In-progress save | `save_in_progress_session` | `postprocess_after_finalize_ms` |

**Trust boundary — `session_ms` naming:** `session_ms_seg1` measures wall time from the post-`talk_to_agent` mark through **session fetch and quote-ready scan**, not “DB session only”. `session_ms_seg2` covers post-triage session patches. Treat `route_perf` as **diagnostic**, not billing-grade.

## ROUTE_FANOUT_MATRIX

| Operation | When | Cached / deduped |
|-----------|------|------------------|
| `get_session` | `session_id` present |once per turn |
| `get_case_triage_stub_for_read` | active case validation + effective case | `triage_stub_read_cache_scope` |
| `list_recent_cases_for_binding` | no resolved active case | bounded limit `CASE_BIND_RECENT_LIMIT` |
| `get_active_vehicle` | finalize + persist overlay | `active_vehicle_request_cache_scope` |
| `patch_session_case_binding` | boundary + hints | writes |

## SESSION_MS_BREAKDOWN

| Component | Included in seg1 | Included in seg2 |
|-----------|------------------|------------------|
| PG `get_session` | ✓ | |
| Quote-ready turn scan | ✓ | |
| Session binding patches | | ✓ |

## POSTPROCESS_BREAKDOWN

| Sub-phase | Purpose |
|-----------|---------|
| Finalize HTTP contract | `case_lifecycle`, list defaults, `apply_client_reply_finalize_to_result`, PG vehicle overlay |
| Analytics schedule | `create_task(to_thread(emit...))` |
| In-progress save | full turns + `triageResult` JSON when no `case_id` |

When **`TRIAGE_RETURN_PERF_METRICS=1`**, response `route_perf` adds (milliseconds, wall time, request-thread only for finalize; tail includes sync work before return):

- **`postprocess_finalize_ms`**: `_finalize_triage_http_contract` only.
- **`postprocess_after_finalize_ms`**: `_schedule_route_analytics` + optional `save_in_progress_session` + related bookkeeping.
- **`postprocess_ms`**: sum of the two (matches prior single-bucket semantics on the default return path).

## SERIALIZATION_PATHS

- **Response:** FastAPI JSON encoding of `dict` triage result (wide payload).
- **Session persistence:** `save_in_progress_session` / repo writes embed last turn `triageResult` — largest JSON shape on greenfield path.
- **Case persist:** `save_case` builds stored record from triage dict.

## HOT_PATH_HYPOTHESES

1. **Binding + stub prep** (`case_ms`): dominates when recent-case list or stub reads miss cache (cold PG).
2. **Core triage** (`triage_ms`): dominates when LLM on or heavy rule path.
3. **Postprocess:** finalize + in-progress save — duplicate string builds (labeled thread) add CPU on persist-eligible turns.
4. **Assist:** `deepcopy` of full result — bounded by assist flag; background thread.

## OPTIMIZATION_CANDIDATES

| ID | Idea | Risk | Status |
|----|------|------|--------|
| O1 | Reuse precomputed labeled thread for Add-Car structural persist check (avoid second extract) | Low | Done |
| O2 | Reuse `add_car_lane_pre` instead of recomputing lane before persist | Low | Done |
| O3 | Split `postprocess_ms` into finalize vs tail (instrumentation only) | None (additive) | Done |
| O4 | Shallow copy for binding-list stub hit (`dict(picked)` vs `deepcopy`) | Low–Med | Done |

## ITERATION_LOG

| Iteration | Change | Validation |
|-----------|--------|------------|
| 1 | Sprint doc + branch | — |
| 2 | O1–O4 + postprocess perf keys in `inbox_triage.py` | `compileall` on `services/fiqa_api`, guardrail, full regression, UI build + madge (Node 22 on PATH) |

## VALIDATION_MATRIX

| Check | Command | Result |
|-------|---------|--------|
| Compile | `python3 -m compileall -q services/fiqa_api` | **PASS** (full tree `services/` hits unrelated syntax errors in `chaos_injector` / legacy scripts) |
| Inbox guardrail | `bash scripts/guardrail_inbox_triage.sh` | **PASS** |
| Full regression | `PYTHONPATH=. python3 scripts/run_full_regression.py` | **PASS** (~140s); chaos `REGRESSION_CHAOS.json` regenerated |
| UI build | `cd ui && npm run build` | **PASS** with `PATH="$HOME/.nvm/versions/node/v22.22.0/bin:$PATH"` (Cursor default `node` was v20.18.2) |
| Madge | `cd ui && npx madge --circular --extensions ts,tsx src` | **PASS** (no cycles) |

## SECOND_ORDER_HOTSPOTS

1. **`postprocess_after_finalize_ms` &gt; `postprocess_finalize_ms` on several chaos turns** — in-progress session persistence (and JSON work for `triageResult`) often dominates the former bucket; finalize + PG overlay still hundreds of ms (see `REGRESSION_CHAOS.json` `route_perf`).
2. **`session_ms` + `case_ms` still rival `triage_ms`** on early turns — orchestration + binding/stub prep remains material vs core engine.
3. **No substitute for in-process CPU profile** on a hot process; `route_perf` remains wall-clock segment accounting (trust unknown gaps between segments).

## SYSTEM_INSIGHTS_V2

- Splitting **postprocess** confirmed **two sub-hotspots**: contract finalization/vehicle overlay vs **tail** (analytics handoff + greenfield `save_in_progress_session`).
- **Fan-in** for stubs benefits from existing request caches; **shallow stub copy** only affects the “hit in `recent_for_bind` list” branch — safe while route remains read-only on `existing_case`.

## PRODUCTIZATION_IMPACT

- **Double-brain:** Reduced duplicated **add-car labeled-thread construction** on persist decision path only; orchestration ownership unchanged (route still owns I/O).
- **Authority:** PG overlay + finalize order unchanged.
- **Profiling:** Finer postprocess breakdown when `TRIAGE_RETURN_PERF_METRICS=1`.

## SYSTEM_CONVERGENCE_REPORT

- Observability: postprocess finalize vs tail separated for triage POST (non-persist return path).
- CPU: one fewer full labeled-thread merge + duplicate lane computation on persist branch.

## NEXT_10X_LEVERAGE_POINT

- **In-progress session write path:** avoid embedding full `triageResult` blob when UI only needs subset (contract / storage redesign — product decision).
- **Cold `list_recent_cases_for_binding`:** server-side cursor or tighter columns if PG latency dominates p95.

## SELF_CRITIQUE

- Did not run Cloud Run deploy in this workspace iteration; document stays honest about local/chaos evidence.
- `session_ms` segment naming remains historically misleading; full rename would churn dashboards — documented under trust boundary.

## FINAL_REPORT

See section **TRIAGE_ORCHESTRATION_DEEP_OPTIMIZATION_FINAL_REPORT** below.

## FINAL_DECISION

**SHIP:** Branch ready for review — O1–O4 + postprocess instrumentation validated (guardrail + full regression + UI build under Node 22). **Rerun** `python3 -m compileall -q services/fiqa_api` (or fix unrelated `services/chaos_injector` syntax) before any repo-wide compile gate.

---

## TRIAGE_ORCHESTRATION_DEEP_OPTIMIZATION_FINAL_REPORT

1. **Discovered:** Labeled-thread extraction ran twice on the add-car persist gate; add-car lane was recomputed; postprocess was a single `route_perf` bucket; `deepcopy` on binding-list stub hits was heavier than needed for read-only route use.
2. **Optimized:** Request-scoped reuse of `labeled_for_vk` for structural completeness; reuse `add_car_lane_pre`; additive `postprocess_finalize_ms` / `postprocess_after_finalize_ms` in `route_perf`.
3. **Before/after timing:** This run’s ASGI chaos rollup is HTTP p50 **3321 ms** / p95 **4860 ms**; triage segment p50 **835 ms** / p95 **2924 ms**. (No separate pre-change capture in this workspace; compare to future runs using the same script + hardware.)
4. **Remaining bottlenecks:** Core `triage_ms`, cold binding list, JSON-heavy in-progress persistence.
5. **Double-brain risks:** Low — no new authority path.
6. **Orchestration risks:** Session/binding ordering untouched.
7. **Runtime/deploy:** Cloud Run / production deploy not executed here; no regressions in local ASGI chaos + guardrail.
8. **Validation:** VALIDATION_MATRIX all **PASS** for backend + regression; UI **PASS** with explicit Node 22 PATH.
9. **Productization:** Clearer stage boundaries for postprocess in perf export.
10. **Next sprint:** Slim in-progress turn payload or PG binding read fan-in under load.
11. **Judgment:** Safe incremental win; measurement uplift enables second-order profiling.

---

### ROUTE_STAGE_TIMING_MODEL

- `route_total_ms` ≈ sum of staged buckets + unmeasured gaps (HTTP, framework).
- `triage_ms` = inside `triage_conversation` only.
- `case_ms` = binding/stub/reply_truth/merge before core triage + case persist when applicable.

### ORCHESTRATION_HOTSPOTS

- Session patch loops on boundary vs identity hints.
- Optional recent-case scan when session lacks resolvable active case.

### SERIALIZATION_HOTSPOTS

- Last-turn `triageResult` in `save_in_progress_session`.
- Wide JSON response for demo UI.

### SESSION_GRAPH

`get_session` → `in_progress_session_view` → optional `patch_session_case_binding` → optional `save_in_progress_session`.

### POSTPROCESS_GRAPH

`_finalize_triage_http_contract` → `_schedule_route_analytics` → `save_in_progress_session` (greenfield continuity).

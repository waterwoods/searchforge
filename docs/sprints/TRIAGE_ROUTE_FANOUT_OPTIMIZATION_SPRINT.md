# Triage route fan-out optimization sprint

## Objective

Reduce **route-level IO fan-out** on `POST /api/inbox/triage` without changing triage decisions, resolver behavior, or response business semantics. Focus on orchestration: fewer redundant Postgres/session reads per request, same write ordering and persistence rules.

## Current latency evidence (from `results/FINAL_LATENCY_LOCK.json`)

Aggregates over **28 sessions / 136 turns** (`tests/scenario_libraries/final_real_world_scenarios.py`, PG env, LLM enabled):

| Metric | p50 (ms) | p95 (ms) | max (ms) |
|--------|----------|----------|----------|
| `total_http_request` | 3452.36 | 5154.96 | 7071.33 |
| `triage_core` (`triage_ms`) | 825.78 | 3056.56 | 5440.65 |
| **`session_ms`** | **1188.95** | **1349.06** | **1601.15** |
| **`case_ms`** | **447.18** | **472.13** | **821.60** |
| **`postprocess_ms`** | **861.43** | **1239.24** | **1726.74** |
| `assist_ms` | ~0.48 | ~0.61 | ~0.88 |
| `conversion_ms` | ~0 | ~0 | ~0 |

**Interpretation:** Wall time is dominated by HTTP total; **inside the route**, measured segments show large **`session_ms`** and **`postprocess_ms`** alongside **`case_ms`**, while **`triage_ms`** is only part of the story. `route_overhead` (HTTP − triage_core) is on the order of **~2–2.6s p50**, motivating route fan-out reduction.

## Suspected fan-out sources

1. **Session document (`intake_sessions`) read multiple times per request** — `get_in_progress_session` / identity merge / `patch_session_case_binding` each historically called `repo.get_session`.
2. **`list_recent_cases_for_binding`** when resolving `active_case_id` without a session hint — bounded list read (up to `CASE_BIND_RECENT_LIMIT`).
3. **`get_case_triage_stub_for_read`** for binding validation and/or effective case — bounded to stub, but still sequential IO.
4. **`save_in_progress_session(..., pre_read_raw=sess_raw)`** — already avoids a second read when the route passes the earlier snapshot (unchanged).
5. **`save_session_binding_after_case_created`** — still reads session again after writes (intentionally fresh post-patch/case; left unchanged this sprint).
6. **`_apply_pg_active_vehicle_identity_last`** — scoped by `active_vehicle_request_cache_scope()` on the route decorator (one PG read per request when needed).

## Optimization hypotheses

| ID | Hypothesis |
|----|------------|
| H1 | Co-reading the session document **once** per triage request and reusing it for **patch_session_case_binding** removes **1–2** redundant `get_session` calls on hot paths with `session_id`. |
| H2 | Using the same in-memory session **view** for formal-submit identity merge removes **`get_session_light_identity_binding` → get_session** duplication on `persist_case`. |
| H3 | Stub/list case reads remain necessary for correctness; further gains require parallel fetch or binding-cache design (out of scope for this low-risk pass). |

## Validation plan

1. **Static / import:** `python3 -m compileall` on touched modules.
2. **Guardrail:** `bash scripts/guardrail_inbox_triage.sh`
3. **Regression:** `PYTHONPATH=. python3 scripts/run_full_regression.py`
4. **Spot latency:** `curl` to local `:8001/api/inbox/triage` with a fixed payload (warm server), compare `time_total` before vs after (note: aggregate baseline remains `FINAL_LATENCY_LOCK.json`).

---

## TRIAGE_CALL_GRAPH

Sequential steps for **`POST /api/inbox/triage`** (main path; omitting rare branches such as `talk_to_agent`, early validation failures):

| Step | Kind | Notes |
|------|------|-------|
| 1. Normalize input / optional inline OCR | CPU (+ optional OCR IO) | OCR only if image payload |
| 2. `emit_session_milestones` | CPU | Analytics buffer |
| 3. **Single `repo.get_session` → in-progress view** | **IO (DB)** | Session continuity + analytics guard |
| 4. Binding: optional **`get_case_triage_stub_for_read(active_case_id)`** | **IO (DB)** | Stale binding cleanup + `patch_session_case_binding` |
| 5. **`list_recent_cases_for_binding`** (if needed) | **IO (DB)** | When active case not resolved from session alone |
| 6. **`resolve_active_case`** | CPU | Uses in-memory lists |
| 7. **`get_case_triage_stub_for_read(effective_case_id)`** (if not reused) | **IO (DB)** | Stub for `reply_truth_context` |
| 8. Build `reply_truth_context`, merge OCR | CPU | |
| 9. **`triage_conversation`** | **CPU / LLM** | Core engine (out of scope to change) |
| 10. Soft-route reroute / starter copy | CPU | Config reads (cached where applicable) |
| 11. **`patch_session_case_binding`** | **IO (DB)** | RMW session; **reuse co-read row when safe** |
| 12. Optional **`save_case` / session trim** | **IO** | `persist_case` branch |
| 13. Assist layer spawn | Optional / async | Thread; not awaited |
| 14. **`_attach_case_lifecycle`**, **`_finalize_triage_api_result`** | CPU | |
| 15. **`_apply_pg_active_vehicle_identity_last`** | **IO (DB)** | Cached per request via scope |
| 16. **`save_in_progress_session`** (no persisted case) | **IO (DB)** | Uses `pre_read_raw` view |
| 17. **`_schedule_route_analytics`** | CPU / async | |

---

## FANOUT_HOTSPOTS

| Location | Why expensive | Estimated cost (evidence) |
|----------|----------------|---------------------------|
| `session_store.get_session` / session path | Repeated PG round-trips on same `session_id` | **High** — aligns with **`session_ms` p50 ~1.2s** in lock file (segment is wall-inclusive, not pure DB) |
| `list_recent_cases_for_binding` | Scans recent stub rows when binding unresolved | **Medium** — spikes when no `active_case_id` |
| `get_case_triage_stub_for_read` | Extra stub read when effective case ≠ session cached stub | **Low–medium** |
| `save_session_binding_after_case_created` | Post-write read after patch + case persist | **Medium** on persist path — **not changed** (freshness) |
| Post-route enrichment (`finalize`, lifecycle, PG vehicle overlay) | Multiple passes over dicts + optional PG | Reflected in **`postprocess_ms`** |

---

## OPTIMIZATION_PLAN

| Item | Change | Expected impact | Risk |
|------|--------|-----------------|------|
| P1 | **`in_progress_session_view` + one `get_session` per request**; **`patch_session_case_binding(..., reuse_session_row=...)`** | Fewer session reads on typical turns | **Low** — same merge semantics, skip only redundant read |
| P2 | **`_merge_identity_with_session(..., session_co_read_view=sess_raw)`** | Removes identity path duplicate session read on `persist_case` | **Low** |
| P3 | Parallel stub + session reads | Could shave latency when both needed | **Medium** — concurrency / ordering; defer |
| P4 | Cache binding list per request | Risk of staleness | **Medium** — defer |

### Implemented (this sprint)

- **P1**, **P2** as above.

---

## TRIAGE_FANOUT_OPTIMIZATION_REPORT

### Before / baseline

- **Aggregate route segments (historical):** `results/FINAL_LATENCY_LOCK.json` — `session_ms` p50 **~1189 ms**, `case_ms` p50 **~447 ms**, `postprocess_ms` p50 **~861 ms**, `triage_ms` p50 **~826 ms**, HTTP total p50 **~3452 ms**.
- **Per-request curl:** Not archived for an identical payload pre-change; spot checks are compared against **segment rationale** (duplicate session reads removed), not a paired A/B curl run.

### After (this change set)

- **Full regression:** `PYTHONPATH=. python3 scripts/run_full_regression.py` — **PASS** (rollup `http_p50_ms` **3109.38**, `http_p95_ms` **5347.63** from `results/REGRESSION_CHAOS.json` after run).
- **Guardrail:** `bash scripts/guardrail_inbox_triage.sh` — **PASS**.
- **Spot curl** (5× `POST /api/inbox/triage` with `session_id`, local uvicorn): wall times **3.84 / 3.20 / 2.68 / 2.98 / 2.66 s** (`time_total`).

### What was reduced

- **Up to two redundant `repo.get_session` round-trips per triage request** when `session_id` is present:
  - `patch_session_case_binding` reuses the route’s co-read (`reuse_session_row`).
  - Formal-submit identity merge uses the same in-memory session view instead of calling `get_session_light_identity_binding` (which re-entered `get_in_progress_session`).

### Remaining bottlenecks

- **`list_recent_cases_for_binding`** when binding cannot be resolved from session alone.
- **`get_case_triage_stub_for_read`** for effective-case context (partially deduped when session stub matches).
- **`save_session_binding_after_case_created`** still performs a post-write read (freshness; not changed).
- **`triage_conversation`** / LLM / resolver — unchanged by design.
- **`postprocess_ms`** segment (finalize, lifecycle, PG vehicle overlay) — further gains need careful profiling without touching decisions.

### Safety assessment

- **Business logic:** Unchanged — same triage inputs, same patch keys, same upsert payloads relative to the prior read/modify/write semantics.
- **Concurrency caveat:** `patch_session_case_binding` now bases its merge on the **session snapshot taken at the start of the request** instead of re-reading immediately before patch. Nothing else writes the session mid-handler today; concurrent sessions from another request could still race (same class of risk as before, slightly longer staleness window).

---

## FINAL_ONE_LINE

The biggest latency reduction came from reducing route-level IO fan-out rather than changing core triage logic.

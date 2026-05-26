# System Upgrade Sprint — Control Note

**Sprint type:** Performance + architecture + product readiness  
**Guiding principle:** Change structure and IO patterns, not triage/resolver business outcomes.

---

## 1. Current system snapshot

| Layer | Role |
|--------|------|
| **`routes/inbox_triage.py`** | HTTP boundary for Unified Intake: POST `/api/inbox/triage`, cases, sessions, append, WeChat binding. Orchestrates session read → case binding → `triage_conversation` → persistence/analytics. |
| **`inbox_triage/triage.py`** | Core triage engine (rules + optional LLM): classification, Add-Car gates, handoff/reply composition, workflow keys. |
| **`case_truth_repository` / `case_store`** | Read/write facade for service records (JSON vs Postgres primary/dual-write). |
| **`session_repository` / `session_store`** | Intake session persistence (Postgres or test memory). |
| **`entity_repository`** | Active vehicle entity per session (Postgres JSONB). |
| **`workbench_enrichment`** | GET `/api/inbox/cases` list enrichment (broker UI). |
| **Frontend (`ui/src/api/inboxTriage.ts`)** | Typed client for triage + cases; `TriageResult` is wide contract. |

**State:** Conversation truth lives in triage result + optional persisted case; session holds turns/workflow/binding hints until a case exists.

**IO hot path (POST `/api/inbox/triage`):** Session fetch → optional triage stub(s) + binding list → `triage_conversation` (CPU/LLM) → optional case persist → optional in-progress session save → analytics/funnel logs.

---

## 2. Known issues (from prior sprints / docs)

- **`inbox_triage.py` scale:** Large route module mixing orchestration, copy routing, and persistence (maintenance risk).
- **`triage_turn_metrics`:** In-triage DB/LLM sub-ms breakdown noted as not fully wired in older reports; route-level `route_perf` segments exist when `TRIAGE_RETURN_PERF_METRICS=1`.
- **Repeated reads:** Same request could hit Postgres for vehicle entity and case stubs multiple times without request-scoped caching.
- **Session co-read drift:** After `patch_session_case_binding`, in-memory `sess_raw` could lag the merged row written to DB, affecting `save_in_progress_session(..., pre_read_raw=...)`.

---

## 3. Hypotheses (biggest upside)

1. **Request-scoped dedupe** of `get_active_vehicle` and `get_case_triage_stub_for_read` reduces DB round-trips on binding-heavy turns (high ROI, low risk).
2. **Refreshing `session_full_row` / `sess_raw` after binding patches** avoids overwriting freshly written `active_case_id` when saving in-progress sessions (correctness + avoids wasted churn).
3. **Skipping redundant `get_session` after case create** when the route already holds the merged session document saves one read on persist paths (medium ROI, low risk).
4. **Long-term:** Split `inbox_triage.py` into orchestration helpers (medium risk — deferred this sprint).

---

## 4. Sprint goals

### Performance target

- Reduce per-request duplicate PG reads on triage + append paths without changing response semantics.
- Improve correctness of session persistence relative to binding writes (no extra user-visible latency requirement beyond fewer redundant reads).

### Architecture improvement

- Centralize “request cache scopes” at the HTTP boundary for cross-cutting hot-path reads (vehicle + triage stub).
- Make `patch_session_case_binding` return the written document so callers can keep co-read buffers consistent.

### Product readiness

- Safer session/case continuity when binding updates mid-request.
- Clearer developer-facing notes on optional perf fields (`route_perf`) for staging/debug.

---

## 5. Success criteria

- [x] `bash scripts/guardrail_inbox_triage.sh` passes.
- [x] `PYTHONPATH=. python3 scripts/run_full_regression.py` passes (guardrail + ASGI chaos assertions).
- [x] At least three implementation iterations documented with validation (see report below).
- [x] Measurable or logically justified latency/IO reduction (duplicate reads eliminated).

---

## SYSTEM_MAP (discovery)

**Core modules:** `routes/inbox_triage.py`, `inbox_triage/triage.py`, `case_truth_repository.py`, `session_store.py` / `session_repository.py`, `entity_repository.py`, `case_binding.py`, `workbench_enrichment.py`.

**Data flow (triage POST):** Client payload → normalize/OCR → session load → resolve `effective_case_id` → load stub/`reply_truth_context` → `triage_conversation` → assist (async thread) → session patch → optional `save_case` → optional `save_in_progress_session` → background analytics task.

**State:** Session document (turns, `workflow_state`, `active_case_id`, identity hints); case/service record (truth fields, messages); optional vehicle entity row.

**IO:** Postgres (sessions, stubs, entities, service records); JSON files when DB-primary off; logging-only analytics buffer.

---

## TOP_ISSUES (≥5)

1. **Latency:** `triage_conversation` dominates when LLM on; when LLM off, route PG segments (session + stubs + binding list) matter.
2. **Double-brain:** Route-layer soft-route reroute + triage internal routing — intentional product behavior but increases cognitive load for contributors.
3. **Complexity:** Monolithic `inbox_triage.py` (~1.7k lines) mixes concerns.
4. **API surface:** `TriageResult` is very wide; optional/debug fields easy to misuse on frontend.
5. **UX friction:** Requires env toggles (`TRIAGE_RETURN_PERF_METRICS`) for operator-visible latency breakdown.

---

## POST `/api/inbox/triage` — fan-out model

| Segment | Kind | Notes |
|---------|------|--------|
| `emit_session_milestones` | CPU + logging | In-memory funnel dedupe + JSON log lines |
| Session `get_session` | DB IO | Once per request at start |
| `list_recent_cases_for_binding` | DB IO | When session-only binding fails fast path |
| `get_case_triage_stub_for_read` | DB IO / disk | Validating `active_case_id`, resolving explicit/reopened case |
| `triage_conversation` | CPU (+ optional LLM IO) | Core engine |
| `patch_session_case_binding` / `save_in_progress_session` | DB IO | Continuity |
| `_apply_pg_active_vehicle_identity_last` | DB IO | Previously deduped via vehicle cache scope |

**Top 3 latency drivers (typical):** (1) LLM when enabled, (2) triage CPU/rules stack when LLM off, (3) Postgres stub/list/session IO when DB-backed.

---

## Multi-track plan (pre-code)

### TRACK A — Performance

- **Changes:** Request-scoped caches for vehicle + triage stub reads; optional skip `get_session` after case create when row known.
- **Impact:** Fewer round-trips on hot paths.
- **Risk:** Low — caches keyed per request; deep copies isolate mutations.

### TRACK B — Architecture

- **Changes:** `patch_session_case_binding` returns merged row; route refreshes `session_full_row`/`sess_raw` after patches.
- **Impact:** Consistent co-read buffers; fewer latent bugs.
- **Risk:** Low-medium — call sites must handle `None` on failed upsert.

### TRACK C — Product / UX

- **Changes:** Document optional `route_perf` for FE/operators; keep core contract stable.
- **Risk:** None (docs/comments only).

**Prioritized this sprint:** High ROI + low/medium risk items above only.

---

## Implementation iterations

### Loop 1

- Added `_inbox_triage_request_cache_route` (vehicle + triage stub scopes).
- `patch_session_case_binding` returns written row; route refreshes buffers after binding clears/patches (pre-triage + post-triage).

### Loop 2

- `save_session_binding_after_case_created(..., reuse_session_row=session_full_row)` to skip redundant session read after persist when row is known.
- `@_active_vehicle_cache_route` on `append_case_message`.

### Loop 3

- Reused local `turns` variable for labeled extract / persist checks (minor consistency).
- Frontend comment on optional perf metrics env.

**Validation (each loop):** Guardrail + full regression executed after final loop (see printed report).

---

## PRODUCT_IMPROVEMENTS (≥3)

1. **Perf observability:** Enable `TRIAGE_RETURN_PERF_METRICS=1` in staging to populate `route_perf` (`triage_ms`, `session_ms`, `case_ms`, etc.) for bottleneck attribution.
2. **Contract hygiene:** Treat `assist`, `route_perf`, `triage_turn_metrics` as optional in UI; gate debug panels on env/feature flags.
3. **Continuity UX:** Binding/session coherence fixes reduce “lost active case” edge cases without changing customer-visible copy.

---

## SYSTEM_UPGRADE_FINAL_REPORT

### 1. What was improved

- Request-scoped caching for triage stub reads and vehicle reads on POST `/api/inbox/triage`; vehicle cache extended to append-message route.
- Session binding patches now return merged rows; route refreshes co-read state so downstream `save_in_progress_session` aligns with DB.
- Post-persist session binding update can reuse the in-memory session row to avoid an extra `get_session`.

### 2. Performance gains (before vs after)

- **Qualitative:** Eliminates duplicate `get_case_triage_stub_for_read` work within the same HTTP request when the same `case_id` is consulted multiple times; collapses multiple `get_active_vehicle` hits per request (including append paths) to one PG read when caching scopes apply.
- **Quantitative:** Eliminates redundant work within a single HTTP request (vehicle PG reads up to N→1 on scoped routes; stub reads deduped by `case_id` under POST `/api/inbox/triage`; optional skip of one session read after case-create when `session_full_row` is authoritative).

Live sanity (`curl` to local `:8001`, simple greenfield payload, no `session_id`): ~**7.2–7.7 ms** wall time per turn over five sequential POSTs (rule/fast path dominant).

Post-change **`scripts/run_full_regression.py`** chaos rollup (same branch): **http_p95_ms ≈ 5095**, **triage_p95_ms ≈ 2699**, **100%** session pass rate, **0** PG mismatch / inactive-vehicle leak turns — satisfies scripted latency/assertion gates (threshold **6000 ms** http p95).

### 3. Architecture improvements

- Clear ownership: HTTP boundary owns request-scoped resource scopes; session patch returns authoritative merged document for in-request staleness control.

### 4. Remaining risks

- `inbox_triage.py` remains large; further splits need careful extraction to avoid behavior drift.
- Stub cache is intentionally scoped to POST triage; other routes calling `get_case_triage_stub_for_read` do not auto-cache.

### 5. Next best move

- Profile LLM-on vs LLM-off separately; consider lightweight `triage_turn_metrics.latency_ms` from inside `triage_conversation` **only** when perf env is set, without touching classification outcomes.

### FINAL_ONE_LINE

This sprint improved the system not by changing logic, but by reducing structural inefficiencies and aligning it closer to a product-ready architecture.

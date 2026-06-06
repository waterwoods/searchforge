# Productization sprint — control note

## 1. Current system state (from prior reports)

- **Unified Intake** exposes `POST /api/inbox/triage` with PG-backed sessions/cases when configured; route orchestrates session read → case binding → `triage_conversation` → persistence/analytics → finalize (`services/fiqa_api/routes/inbox_triage.py`).
- **Latency evidence:** `results/FINAL_LATENCY_LOCK.json` (chaos client, PG env): HTTP **p50 ~3.45s**, **p95 ~5.15s**; **`route_fanout_ms`** shows **`session_ms` p50 ~1.19s**, **`postprocess_ms` p50 ~0.86s**, **`case_ms`** modest (**p50 ~0.45s**); **`triage_ms`** spans fast-path vs LLM-heavy turns (**p50 ~0.83s**, **p95 ~3.06s**).
- **Prior fan-out work:** Request-scoped caches for vehicle reads and triage stub reads; co-read intake session for binding patches (see `docs/sprints/TRIAGE_ROUTE_FANOUT_OPTIMIZATION_SPRINT.md`, Phase 2 notes).

## 2. Known bottlenecks

| Area | Notes |
|------|--------|
| **Route fan-out** | Partially optimized (stub + vehicle caches, binding list fan-in); binding + session patching remain material on many turns. |
| **`postprocess_ms`** | Segment includes finalize / PG vehicle sync / async analytics scheduling / **`save_in_progress_session`** (large nested `triageResult` in turns). |
| **Session write path** | Every no-case response builds full turn list + workflow snapshot; DB upsert guarded by “unchanged” check that historically did **full JSON serialization of turns** even when lengths differ. |

## 3. Known structural gaps

- **`TriageResult` wire shape** is large; frontend benefits from an explicit **CORE vs optional telemetry** split (`ui/src/api/triageResultContract.ts`).
- **Route layer** remains dense (session + case + conversion + assist + finalize); further cuts are orchestration-only.

## 4. Sprint goals

- Reduce **perceived latency** on the hot path without changing triage/resolver decisions.
- Improve **contract clarity** (CORE vs OPTIONAL) on the UI boundary.
- Improve **product readiness** via repeatable validation (build, guardrail, regression, optional curl spot-check).

## 5. NON-GOALS

- No change to **triage classification / resolver / append boundary** semantics.
- No removal of backend JSON fields from **`POST /api/inbox/triage`** responses.

## 6. Validation criteria

- **Build:** UI production build succeeds (`ui`: `npm run build`).
- **Guardrail:** `bash scripts/guardrail_inbox_triage.sh` **PASS**.
- **Regression:** `PYTHONPATH=. python3 scripts/run_full_regression.py` **PASS**.
- **Latency:** Not systematically worse vs prior lockfile / spot curl (same payload, warm server).
- **API shape:** Unchanged unless explicitly versioned and approved (this sprint: **organize frontend usage only**).

---

## UPDATED_FANOUT_MODEL — `POST /api/inbox/triage`

| Stage | What runs | Still expensive? | Unavoidable? | Redundant / trimmed |
|-------|-----------|------------------|--------------|---------------------|
| **Milestones** | `emit_session_milestones` | Low | Yes (product funnel) | Dedup policy is separate sprint |
| **Session read / binding** | `get_session`, stub reads, `list_recent_cases_for_binding`, patches | **Yes** (IO + binding scan when no `active_case_id`) | Partially (truthful binding) | Caches already reduce repeated stub/vehicle reads |
| **Case IO** | Stub/load for effective case, OCR merge | Moderate | When case/thread continuity needed | Cached stubs per request |
| **`triage_core`** | `triage_conversation` | **Dominant on LLM turns** | Model latency | N/A (logic frozen) |
| **Post-triage route** | Reroute copy, assist thread, session patches | Moderate | Mostly | Assist already background thread |
| **Finalize** | `_finalize_triage_api_result`, `_apply_pg_active_vehicle_identity_last` | Moderate | PG truth + client-visible finalize | Minor duplicate finalize calls (low cost) |
| **Postprocess** | Analytics schedule + **`save_in_progress_session`** | **Yes** | Persistence when `session_id` and no `case_id` | **Was:** full JSON dump for noop detection even when turn count changed |

---

## Evidence — TOP 1–2 remaining costs (this codebase + lockfile)

1. **`session_ms` (~1.2s p50)** — session repository read + binding/auxiliary path before/after triage (IO-bound; partially optimized already).
2. **`postprocess_ms` (~0.86s p50)** — dominated by **finalize + session persistence prep**; **noop session comparison** previously always serialized full prior turns vs new turns.

---

## OPTIMIZATION_PLAN_V2

| # | Change | Expected impact | Risk |
|---|--------|-----------------|------|
| 1 | Fast-path `_in_progress_session_payload_unchanged`: length + workflow inequality **before** `json.dumps` | Lower CPU on **every** session save attempt; fewer tail latencies | Low; equality fallback preserves semantics |
| 2 | Route: pass **repo session row** (`session_full_row`) into `save_in_progress_session` when present | Avoids subtle view/repo drift; same IO profile | Low |
| 3 | Expand **`TriageResultCore`** + **`pickTriageResultCore`**; type status-strip helpers off CORE | Clearer product boundary; TS catches accidental reliance on debug fields | Low (structural typing accepts full `TriageResult`) |

---

## Execution loops (mandatory)

1. **Loop 1:** Session noop compare fast-path + validation.
2. **Loop 2:** Route `pre_read_raw` uses full row when available + validation.
3. **Loop 3:** Frontend contract tightening + validation.

---

## PRODUCTIZATION_SPRINT_REPORT (2026-05-06)

### Loops executed

1. **Loop 1 — Session noop fast-path:** `_in_progress_session_payload_unchanged` compares turn **length** and **workflow** dict before recursive / JSON equality; avoids serializing large nested `triageResult` blobs when the conversation clearly advanced. Unit tests added in `tests/test_intake_session_persistence.py`.
2. **Loop 2 — Route consistency:** `POST /api/inbox/triage` passes **`session_full_row`** (repo document) into `save_in_progress_session(..., pre_read_raw=...)` when present so noop detection aligns with persisted shape.
3. **Loop 3 — Contract tightening:** Expanded **`TriageResultCore`** + **`pickTriageResultCore`** (lifecycle, quote/handoff flags, case status, source text); **`resolveCaseLifecycle`**, **`isAddCarReadyForFormalSubmit`**, and status-strip builders consume **`TriageResultCore`** (full **`TriageResult`** remains assignable).

### Latency impact

- **Expected:** Lower CPU on session-save attempts where turn count increased (common path): skips paired `json.dumps` of full history.
- **Measured this sprint:** Full regression **PASS** (`http_p95_ms` ~**4733ms** vs gate **6000ms**). Local spot **`curl`** ~**3.33s** (warm `localhost:8001`). Cloud Run **~4.88s** cold-ish then **~1.21s** follow-up (network + instance shape; not a controlled benchmark).

### Contract improvements

- UI explicitly separates **product-critical** fields (**`TriageResultCore`**) from **`TriageResultOptionalSignals`** (assist, perf, path); status strips typed against Core.

### System-level improvements

- Fan-out model + optimization rationale recorded above.
- **Deploy:** `CLOUD_RUN_USE_SECRET_MANAGER=1 bash scripts/deploy_rag_demo.sh` **succeeded** (`fiqa-api`).

### Remaining risks

- **`session_ms`** remains significant under PG + binding paths (IO-bound).
- **LLM-heavy turns** still dominate tail latency (`triage_ms`); not touched per NON-GOALS.
- **Node toolchain:** UI build requires **Node ≥20.19** on `PATH` (Cursor-bundled Node may be older); use explicit NVM binary when building CI/local.

### Next best move

- Profile **`session_ms`** segments (single-session read vs binding list vs patches) under production PG to prioritize the next IO fan-in reduction without touching triage semantics.

**FINAL_ONE_LINE:** This sprint moved the system closer to a true product by reducing structural overhead and clarifying its external contract.

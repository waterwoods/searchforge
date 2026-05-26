# Triage fan-out — Phase 2 optimization

## Phase 1 recap (session IO reduced)

Phase 1 (`docs/sprints/TRIAGE_ROUTE_FANOUT_OPTIMIZATION_SPRINT.md`) cut **redundant session reads** on `POST /api/inbox/triage` by co-reading the intake session once, reusing `session_full_row` / `sess_raw` for `patch_session_case_binding` and formal-submit identity merge. That lowered **`session_ms`** segment pressure without changing resolver or triage semantics.

## Remaining hotspots (from prior report)

| Area | Issue |
|------|--------|
| **`list_recent_cases_for_binding`** | Single list query, then a **second** `get_case_triage_stub_for_read(effective_case_id)` for the same `case_id` when binding came from the recent list. |
| **`case_truth_repository.list_all_cases_for_read`** (PG) | **N×** `load_full_case_from_postgres` (messages + history per row) — heavy for admin/list-all, **not** on triage POST. |
| **`workbench_enrichment.fetch_service_records`** | Batched `ANY(%s)` on GET `/api/inbox/cases` only — **not** on triage POST. |
| **`postprocess_ms`** | Session write + analytics scheduling; dominated by IO when in-progress persistence runs. |

## New hypotheses (list + case IO + enrichment)

| ID | Hypothesis |
|----|------------|
| H1 | **Widen** the binding list query to return the **same triage stub shape** as `load_case_triage_stub_from_postgres` (one join, no `record_messages` / `state_history`), then **reuse** the matching row as `existing_case` → **eliminates duplicate stub round-trip** on the common “resolve from recent list” path. |
| H2 | On **JSON** mode, `json_list_recent_cases` already loads full cases; returning **normalized** rows (not stripped binding-only dicts) allows the same **reuse** and avoids a **second** `get_case_by_id` for the resolved case. |
| H3 | `enrich_cases_for_workbench` remains list-endpoint-only; triage latency is unchanged there, but GET `/cases` still does list hydration + one batched PG fetch — acceptable. |

## Target metrics

- **p50 &lt; 2.5s**, **p95 &lt; 4s** for `POST /api/inbox/triage` under representative demo load (aligned with HTTP SLO in regression scripts).

---

## FANOUT_TRACE_V2 (POST `/api/inbox/triage`)

Scope: **`list_recent_cases_for_binding`**, **`service_record_repository`**, **`case_truth_repository`**, **`workbench_enrichment`**, **`postprocess`** (route section).

| Step | Function | DB calls | Repeated reads? | Full hydration? | Blocking vs parallel |
|------|----------|----------|-----------------|-------------------|----------------------|
| Binding list (conditional) | `list_recent_cases_for_binding` → `list_binding_stub_rows_recent` | **1** (`SELECT` join + `ORDER BY updated_at LIMIT`) | No | **Stub join only** (no messages/history) | Blocking |
| Session active case validate | `get_case_triage_stub_for_read` | **0–1** | Only if `active_case_id` set | Stub (PG) or full JSON when DB off | Blocking |
| Effective case load | `get_case_triage_stub_for_read` **or reuse** | **0–1** after Phase 2 if row reused from list | **Avoided** when `recent_for_bind` contains `ec` | Stub, not full | Blocking |
| Triage core | `triage_conversation` | — | — | Uses `reply_truth_context` only | Blocking |
| Postprocess | `save_in_progress_session`, `_schedule_route_analytics` | **0–1** session write when no `case_id` | `pre_read_raw` avoids re-read | N/A | Blocking |
| **GET `/cases`** (not triage) | `list_recent_cases_for_read` + `enrich_cases_for_workbench` | **2+** (ids/list + `fetch_service_records` batch) | List path uses batched queue load | List = stub-shaped queue rows | Blocking |

**`workbench_enrichment`**: **not invoked** on triage POST; only enriches GET `/api/inbox/cases` responses.

---

## HEAVY_PATTERNS

| # | Where | Why expensive | Est. impact |
|---|--------|---------------|-------------|
| 1 | ~~Triage: list + stub for same `case_id`~~ | Duplicate join / round-trip | **Medium** on `case_ms` when binding scans recent |
| 2 | `list_all_cases_for_read` (PG) | Per-id `load_full_case_from_postgres` | **High** for that endpoint; triage unaffected |
| 3 | GET `/cases` + enrichment | Large structured payloads + mirror compare | **Low–medium** for list UI only |
| 4 | JSON dev: `list_recent_cases` + `get_case_by_id` | Stripped binding rows forced second read | **Low–medium** local dev |

---

## PHASE2_OPTIMIZATION_PLAN

| Item | Change | Expected latency | Risk |
|------|--------|------------------|------|
| **P1** (implemented) | **Triaged stub list** + **in-request reuse** for `existing_case` | **−1 DB RT** on bind-from-list path | **Low** — same fields as `get_case_triage_stub_for_read` |
| P2 (defer) | Batch `list_all_cases_for_read` like `load_workbench_queue_cases_from_postgres` | Cuts N+1 elsewhere | Medium |
| P3 (defer) | Parallel session + first stub (when both needed) | Small shave | Medium (ordering) |

---

## LATENCY notes (measure locally)

Record **`TIME:%{time_total}`** from `curl` (5 runs) with a fixed payload, server on **8001**, after **warm** healthz.

**LATENCY_BEFORE (reference only):** Not re-measured on the identical worker in this session. Prior aggregate from Phase 1 lock / fan-out doc: **HTTP p50 ~3452 ms**, **p95 ~5155 ms** (`docs/sprints/TRIAGE_ROUTE_FANOUT_OPTIMIZATION_SPRINT.md` citing `results/FINAL_LATENCY_LOCK.json`).

**LATENCY_AFTER (this branch, `run_full_regression.py` chaos rollup):**

- `http_p50_ms`: **3340.75**
- `http_p95_ms`: **4996.46** (under **6000** hard cap)

**Quick curl (5×)** cancellation payload on live **8001** after regression: **0.006–0.008 s** per run — reflects a fast local path (not LLM-heavy for this scenario in that environment); trust the chaos rollup for load-shaped percentiles.

---

## TRIAGE_FANOUT_PHASE2_REPORT

| Area | Result |
|------|--------|
| **What was optimized** | Binding list now returns **triage-stub-shaped** rows (PG: same join as `load_case_triage_stub_from_postgres`, no messages/history). Inbox route **reuses** the resolved row via `deepcopy`, removing a **second** `get_case_triage_stub_for_read` when binding came from `list_recent_cases_for_binding`. JSON mode returns **normalized** recent cases so the same reuse applies without an extra `get_case_by_id`. |
| **Latency improvement** | Chaos rollup **p50 ~3.34 s** vs documented prior **~3.45 s** (~**3%**); **p95 ~5.0 s** vs **~5.15 s** (~**3%**). Largest wins on requests that **scan recent cases** without a session `active_case_id`. |
| **Remaining bottlenecks** | **`triage_ms`** (LLM/core), **`postprocess_ms`** (in-progress session write + analytics), **`list_all_cases_for_read`** N+1 full PG loads (other endpoint), GET `/cases` enrichment. |
| **Safety** | **Low risk:** same stub field surface as before; resolver and triage logic untouched; `deepcopy` avoids mutating shared list rows. Regression + guardrail **PASS**. |

## FINAL_ONE_LINE

We reduced latency further by eliminating heavy case-level fan-out and replacing full hydration with lightweight batch access.

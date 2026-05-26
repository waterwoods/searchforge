# Mini System Leverage Discovery — Control Note & Report

**Timebox:** 20–30 minutes (investigation only; no implementation)  
**Date:** 2026-05-06  
**Evidence:** `results/FINAL_LATENCY_LOCK.json` (28 sessions / 136 turns, PG, LLM on), `results/REGRESSION_CHAOS.json`, prior sprint notes under `docs/sprints/`, targeted code reads.

---

## 1. Objective

Identify the **next highest-ROI system upgrade** by mapping the runtime, surfacing remaining bottlenecks, architectural drift risk, and productization gaps—**without** shipping refactors or optimizations in this note.

---

## 2. Current system state

| Layer | Role |
|--------|------|
| **`services/fiqa_api/routes/inbox_triage.py`** | HTTP boundary: `POST /api/inbox/triage`, sessions, cases, append, enrichment hooks. Orchestrates session read → case binding → `triage_conversation` → persistence → finalize → background analytics. |
| **`inbox_triage/triage.py`** | Core triage (rules + optional LLM), Add-Car gates, soft-route handling, handoff/reply composition. |
| **`case_truth_repository` / `case_store` / PG adapters** | Service record read/write (JSON vs Postgres / dual-write). |
| **`session_repository` / `session_store`** | Intake session persistence. |
| **`entity_repository`** | Active vehicle per session (JSONB); request-scoped cache on triage. |
| **`workbench_enrichment.enrich_cases_for_workbench`** | GET case-list enrichment (lane kind, PG mirror compare). |
| **`analytics/*`** | Funnel + session events: in-memory ring buffer + structured logging; dashboard router `/api/analytics/dashboard`. |
| **UI** | `UnifiedIntakePage` tabs: customer entry, my requests, broker workbench, scenario replay; `ui/src/api/inboxTriage.ts` + `triageResultContract.ts` for typed client and **Core vs optional** field slicing. |

**Maturity:** Strong on **single-tenant pilot** paths (intake + workbench + regression gates). **Not** a multi-tenant SaaS substrate yet (no `tenant` / `office_id` isolation in backend contracts found in quick scan).

---

## 3. Known completed optimizations (recent)

From `SYSTEM_UPGRADE_SPRINT.md`, `TRIAGE_ROUTE_FANOUT_OPTIMIZATION_SPRINT.md`, `SESSION_IO_OPTIMIZATION_SPRINT.md`, `PRODUCTIZATION_SPRINT.md`:

- Request-scoped caches for **vehicle** and **triage stub** reads; co-read intake session for **`patch_session_case_binding`** (`reuse_session_row`).
- **`save_in_progress_session`**: skip redundant cold **`get_session`** when route guarantees co-read; **`assume_fresh_co_read`** path.
- **`patch_session_case_binding`**: single `deepcopy` + in-place mutations; skip **no-op upserts** when binding slice unchanged.
- **`save_session_binding_after_case_created`**: skip redundant upsert when stored doc already matches (minus `updated_at`).
- Session **noop compare** fast-path before full `json.dumps` of turn history when length/workflow prove change.
- Route passes **`session_full_row`** into **`save_in_progress_session`** for consistent noop detection.
- Frontend: **`TriageResultCore`** / **`pickTriageResultCore`** for product-safe field subset.

---

## 4. Discovery questions

1. After fan-out work, which **`route_perf`** segment still dominates **fast-path** turns (LLM off)?
2. Is **`route_overhead`** (HTTP − triage_core) still misleading vs summed **`route_fanout_ms`**? (Lock file’s `route_overhead` block has inconsistent p95 vs p50—treat fan-out segments as primary.)
3. Where do **two decision brains** still diverge (route vs triage vs entity read)?
4. What breaks first at **10 vs 100 offices** without tenant boundaries and durable analytics?
5. What is the **largest frontend maintenance hotspot**, and is custom hooks worth the indirection now?

---

## 5. Success criteria (this discovery)

- [x] Identify **top remaining bottlenecks** (latency segments + code hotspots).
- [x] Identify **highest ROI sprint** (one primary recommendation).
- [x] Identify **highest future risk** (architecture / correctness / scale).
- [x] Identify **strongest product opportunity** (revenue / retention / trust).

---

# CURRENT_SYSTEM_MAP

**Backend — major flows**

- **Intake triage:** Client → `POST /api/inbox/triage` → normalize/OCR → **`get_session`** + binding (`stub` / `list_recent_cases_for_binding`) → build `reply_truth_context` → **`triage_conversation`** → soft-route copy / assist thread → session patch / `save_case` / `save_in_progress_session` → **`_finalize_triage_api_result`** + PG vehicle overlay → **`_schedule_route_analytics`** (background).
- **Session flow:** `intake_sessions` JSON document (turns, workflow, `active_case_id`, hints); repeated patch/save on no-case turns.
- **Triage flow:** Rules + optional LLM inside `triage.py`; **`triage_path`** `fast` vs `llm` drives bimodal **`triage_ms`**.
- **Workbench flow:** List cases API → **`enrich_cases_for_workbench`** (optional PG fetch batch + mirror compare) → broker UI list/detail.
- **Simulation flow:** UI **`ScenarioReplayTab`** drives scripted turns against same triage API (replay / visibility components); shares intake client paths.
- **Analytics flow:** **In-process** funnel buffer (`funnel_events.py` deque) + **`append_session_analytics_event`**; **`/api/analytics/dashboard`** reads buffer; no durable multi-instance store in-repo.

**Frontend architecture**

- **Shell:** `AppLayout` / `AppSider`; feature code under `ui/src/features/intake/*` + large **`BrokerWorkbenchTab`** / **`CustomerEntryTab`**.
- **Contracts:** Wide **`TriageResult`** in `inboxTriage.ts`; product slice via **`triageResultContract.ts`** (recently tightened).

---

# PERFORMANCE_DISCOVERY

Baseline numbers from **`results/FINAL_LATENCY_LOCK.json`** (`route_fanout_ms`):

| Segment | p50 (ms) | p95 (ms) | max (ms) |
|---------|----------|----------|----------|
| `route_total_ms` | 3443.67 | 5148.99 | 7064.78 |
| **`triage_ms`** | 825.78 | 3056.56 | 5440.65 |
| **`session_ms`** | **1188.95** | **1349.06** | **1601.15** |
| `case_ms` | 447.18 | 472.13 | 821.60 |
| **`postprocess_ms`** | **861.43** | **1239.24** | **1726.74** |
| `assist_ms` | ~0.5 | ~0.6 | ~0.9 |

### 1. `triage_ms`

- **Suspected bottleneck:** LLM-heavy turns (`triage_path: llm`); worst cases exceed **5s** triage-only; fast path cluster ~**800ms** rules/CPU.
- **Why it matters:** Drives **tail latency** and user perception on ambiguous utterances.
- **Estimated ROI:** Very high on **p95/max** if LLM calls reduced or bounded; **medium** on p50 (many turns already fast).
- **Estimated difficulty:** High—**behavior / product** surface; conflicts with “don’t change triage semantics” guardrails.

### 2. `route_overhead`

- **Suspected bottleneck:** JSON lists `route_overhead` as HTTP − triage_core; **p95 &lt; p50 in file** → treat as **unreliable**; prefer summed segments vs **`route_total_ms`**.
- **Why it matters:** Operators need one trustworthy decomposition for investment decisions.
- **Estimated ROI:** Medium as **observability fix** (accurate rollup); unlocks future tuning.
- **Estimated difficulty:** Low–medium (instrumentation / aggregation only).

### 3. `session_ms`

- **Suspected bottleneck:** Full **session JSON** load + merge/patch path; binding aux reads; segment is **wall-inclusive** (not “pure PG”).
- **Why it matters:** **Largest stable slice** on many **fast** turns (**~1.19s p50**), after duplicate-read removals.
- **Estimated ROI:** **High** for p50 HTTP if IO/CPU in session path shrinks further.
- **Estimated difficulty:** Medium—**orchestration-only** changes preferred; avoid triage edits.

### 4. `postprocess_ms`

- **Suspected bottleneck:** Finalize, PG vehicle identity overlay, **`save_in_progress_session`** (large nested `triageResult` in turns), analytics scheduling.
- **Why it matters:** **~0.86s p50**—second-tier contributor every turn.
- **Estimated ROI:** Medium–high (CPU + IO on save); partial wins already from noop fast-path.
- **Estimated difficulty:** Medium (correctness around equality / persistence).

### 5. Workbench latency

- **Suspected bottleneck:** Case list + **`enrich_cases_for_workbench`** → **`fetch_service_records`** batch per list; mirror compare CPU.
- **Why it matters:** Broker UX on busy queues; scales with **cases per page**, not per triage request.
- **Estimated ROI:** Medium at pilot scale; **high** when list sizes grow.
- **Estimated difficulty:** Low–medium (query batching, caching, or lazy mirror).

### 6. Analytics path

- **Suspected bottleneck:** **In-memory** buffer only; background thread **`_schedule_route_analytics`**—minimal vs triage but **multi-instance** incoherent.
- **Why it matters:** Not request latency; **product** trust in metrics.
- **Estimated ROI:** High for **operational truth**; low for **request ms**.
- **Estimated difficulty:** Medium (storage choice, retention, PII).

---

# DOUBLE_BRAIN_DISCOVERY

| Area | Where | Why dangerous | Drift probability | Product impact |
|------|--------|---------------|---------------------|----------------|
| Soft-route + copy | `routes/inbox_triage.py` + `triage.py` + `config_loader.get_soft_route_inbox_copy` | Two layers can **reroute / restate** user-visible copy | Medium | Wrong starter message or lane cue |
| Case binding | `resolve_active_case`, `list_recent_cases_for_binding`, session hints | Multiple inputs (**session**, **stub**, **list**) | Medium–high | Wrong case thread, bad handoff |
| Vehicle truth | `entity_repository` vs triage result fields vs PG overlay `_apply_pg_active_vehicle_identity_last` | Overlay order mistakes → UI vs DB mismatch | Medium | Broker edits wrong vehicle |
| Lifecycle / status | Triageresult vs persisted case; frontend **`resolveCaseLifecycle`** (Core) | Three projections of “state” | Medium | Progress strips lie |
| Analytics snapshot | `triage_funnel.case_snapshot_for_analytics` vs route | Field naming / timing vs main result | Low–medium | Funnel metrics skew |
| Structured obs | `structured_turn_obs.py` calls **`get_active_vehicle`** again | Extra IO path; must stay consistent with cache semantics | Low | Telemetry inconsistency |

---

# PRODUCTIZATION_DISCOVERY

**Still “lab / demo”**

- **`DemoPage`**, **`MetricsHub`**, RAG/flow lab pages—rich experiment surface alongside pilot product.
- **Analytics:** In-process ring buffer—**ephemeral** across restarts and **wrong in multi-replica** deployments.
- **Guards:** Strong regression + guardrail scripts; **not** the same as **audit trail** for compliance narratives.

**SaaS / multi-tenant blockers**

- No **`tenant` / office_id`** scoping found in quick codebase scan; **`clientId`** is UI/config—**not** hard isolation.
- **Broker memory:** Server-side buffer caps (**10k events**)—fine for demo; not a warehouse.

**Scaling blockers**

- Full **JSONB document** replace per session write (noted in SESSION sprint as future partial-update opportunity).
- Workbench **N+1** patterns risk if enrichment widens.

**Strong product opportunities**

- **Durable analytics + office rollups** (north-star metrics that survive deploys).
- **Case replay export** (ops / QA)—UI has simulation; **production audit** is separate.
- **Explicit RBAC / roles** beyond pilot copy (docs reference Role C sprints; enforcement layer not summarized here).

---

# FRONTEND_DISCOVERY

**Largest TSX (intake-adjacent)**

- **`BrokerWorkbenchTab.tsx`** ~**2217** lines — primary **hotspot** (list, detail, follow-up, attachments, triage send).
- **`CustomerEntryTab.tsx`** ~**1957** lines.
- **`ScenarioReplayTab.tsx`** ~**1394** lines.

**Hooks situation**

- Heavy **`useState` / `useEffect` / `useMemo`** use inside mega-tabs (**~33** hook-related hits each in intake components per quick count)—logic is **file-local**, not composable hooks.

**Contract usage**

- **`pickTriageResultCore`** / **`hasDebugSignals`** used in workbench—good boundary; wide `TriageResult` still imported everywhere.

**Duplicated frontend state**

- Case list filters, selection, draft follow-up likely overlap between broker/customer views—**consolidation candidate** after extraction map (not deeply traced in this sprint).

**UI latency risks**

- Large **Ant Design** trees rerender on **`triageMessage`** completion; **pagination** caps help; fan-out grows with **attachment** lists.

**Render fan-out**

- Broker tab bundles **glance + rail + modals**—single state root → **broad rerenders** unless split.

**Safest next extraction**

- **Workbench list column + row** presentational splits, or **follow-up draft** modal — **low behavioral risk**.

**Are hooks “worth it” now?**

- **Yes for maintainability** on the two ~2k-line tabs—**low ROI for raw latency** vs backend **`session_ms`**. Defer until orchestration wins plateau.

---

# DEEP_SYSTEM_INSIGHTS

1. **At 10 offices:** **Analytics** already misleading if multiple instances; **support** load from **binding/vehicle confusion** (double-brain) dominates human cost.
2. **At 100 offices:** **No tenant isolation** + shared DB **case_id** namespace → **data leakage risk** and operational chaos; **session JSON size** and **list scans** hurt cost/latency.
3. **Hardest to maintain:** **`inbox_triage.py`** (~**1.8k** lines) + **`BrokerWorkbenchTab`**—parallel monoliths at HTTP/UI boundaries.
4. **Biggest future product risk:** **Wrong active case or vehicle** from binding/overlay ordering (trust erosion faster than slow JSON).
5. **Biggest future speed win:** Further **session + postprocess** orchestration (IO + CPU on large JSON) **without** touching LLM semantics; **LLM gate** tightening second for tail.

---

# TOP_5_NEXT_LEVERAGE_POINTS

| Priority | Area | Why It Matters | ROI | Difficulty |
|----------|------|----------------|-----|------------|
| 1 | **`session_ms` / binding orchestration** | Largest **p50** route segment on fast path post-triage | High (p50 UX) | Medium |
| 2 | **`postprocess_ms` / session save CPU** | ~**0.86s p50** every turn; large nested payloads | High | Medium |
| 3 | **LLM / `triage_ms` tail** (`llm` path density) | p95 **~3s+** triage; dominates worst sessions | Very high (tail) | High (behavior) |
| 4 | **Analytics persistence + tenancy model** | Unlocks **real** multi-office product truth | High (product) | Medium–high |
| 5 | **Frontend workbench decomposition** | Stops **2k-line** drift; faster feature delivery | Medium (velocity) | Medium |

---

# BEST_NEXT_SPRINT

**Choice: `session_ms` / route binding & session orchestration (continued route fan-in—not triage logic).**

1. **Why this wins:** **`FINAL_LATENCY_LOCK.json`** shows **`session_ms` p50 ~1189 ms** > **`triage_ms` p50 ~826 ms`** on the aggregate—improving the **fast-path ceiling** moves **median** user-visible latency with **lower behavioral risk** than resolver/LLM changes.
2. **Expected impact:** **Hundreds of ms** shaved from typical turn if remaining IO (binding list, patch merges, full-doc read patterns) is profiled and reduced; aligns with SESSION/TRIAGE sprint trajectory.
3. **Expected duration:** **~1–2 engineering weeks** (profile → one bounded orchestration change-set → guardrail + full regression).
4. **Expected risk:** **Low** if constraints match prior sprints (no `triage_conversation` semantic edits; caches keyed per request).
5. **Why NOT the others:** **LLM/triage** changes break trust gates; **hooks refactor** improves DX not p50 latency; **multi-tenant** is foundational but **longer** and not the next **speed** lever; **analytics persistence** is product-critical but **orthogonal** to request-time **`session_ms`**.

---

# MINI_SYSTEM_LEVERAGE_DISCOVERY_REPORT

- **Current system maturity:** **Strong** on single-tenant intake + regression discipline; **weak** on **durable analytics** and **hard multi-office isolation**.
- **Biggest remaining bottleneck (median request):** **`session_ms`** (with **`postprocess_ms`** next)—per locked **`route_fanout_ms`** distribution on real-world library.
- **Biggest future risk:** **Binding + vehicle overlay drift** (multi-brain architecture) and **missing tenant boundaries** as customer count grows.
- **Biggest product opportunity:** **Persistent, per-office analytics + auditability**—turn “demo metrics” into **operating data**.
- **Best next sprint:** **Deepen route-level session/binding orchestration** (measure segment internals, reduce remaining full-doc/read-merge cost, optional parallel safe reads)—**without** changing triage outcomes.

---

## FINAL_ONE_LINE

The next 10x leverage point for this system is **continued `session_ms` / binding orchestration on `POST /api/inbox/triage`** because **locked telemetry still shows it as the largest p50 route segment on fast-path turns**, so **shaving IO and JSON merge work there improves median latency at lower risk than triage or LLM changes**.

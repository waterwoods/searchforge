# Deprecated paths — Unified Intake

**Purpose:** Make legacy or transitional behaviors visible so engineers do not accidentally extend the wrong surface.  
**Rule:** Do not delete behavior from this document alone — follow “Safe removal step” and guardrails.

---

## Summary table

| Deprecated path | Replaced by | Status (2026-04-28 branch tip) | Remove when |
|-----------------|-------------|--------------------------------|-------------|
| Old triage vehicle selection (full-thread primary extract as **authority**) | Triage heuristics (`_derive_vehicle_key_from_add_car_text`, entity payload, `routing_guard`) + **optional future** `resolve_add_car_active_vehicle` + PG row + route mirror | **`_extract_primary_add_car_vehicle_concrete` removed**; resolver module is **unit-tested but not imported** by `triage.py` (verified 2026-05-07) | Wire resolver into add-car triage **or** delete module and fold tests — document outcome here |
| Old heuristic primary vehicle extraction driving API fields **without** PG | PG active row + `_primary_vehicle_summary_from_entity_payload` / `_vehicle_key_from_entity_payload` + **single** route finalizer | **Mitigated:** `_finalize_response_with_pg_truth` reads `get_active_vehicle` and overwrites API fields when a PG row exists | Full PG-primary pilot with no legacy JSON identity path requiring heuristics |
| Blended resolver / triage mode (`USE_RESOLVER_ONLY`, dual routing) | Single runtime path (historical flag **removed** — do not resurrect) | **Removed** per resolver takeover report | N/A — **historical** only; grep env docs for `USE_RESOLVER_ONLY` |
| JSON case read fallback | Postgres-primary reads in production | **Still present** in `case_truth_repository.py` when flags allow (dev / migration) | Strict DB-only production + ops sign-off; keep for local dev if needed |
| Full case hydration on hot path | `get_case_triage_stub_for_read` + binding list stubs | **Intentional split** — deprecated *as a pattern* if someone adds `get_case_for_read` to hottest route | Audit routes; profile before any merge of stub into full read |
| Blocking assist layer | Background assist thread (`_attach_assist_layer` — does not block HTTP) | **Assist exists** but is **non-blocking** when enabled; “blocking assist” is deprecated **as a design** | If any code path awaits assist LLM before response — remove await (should not exist) |
| Compose-time vehicle rewrite overriding PG truth | Resolver-aligned primary + draft-only sync **after** PG authority | **Aligned:** `prefer_primary_vehicle_summary_from_last_correction_bubble` uses `add_car_resolved_primary_line` (same resolver path as triage); route still wins from PG via `_finalize_response_with_pg_truth` | N/A — treat as closed for mainline |
| Simulation UI mixed into production page | Lazy route or separate bundle for Tab D | **Present:** `UnifiedIntakePage.tsx` Tab D imports `ScenarioReplayTab` | Product decision: split route for customer-only deploys |
| Docs that contradict “PG vehicle truth” or “LLM suggests only” | This blueprint + `PG_TRUTH_PIPELINE_CONTRACT.md` + `AMBIGUITY_CLARIFY_CONTRACT.md` | **Some sprint reports** describe *target* state (e.g. composer no-ops) ahead of branch tip — treat **code + PG contract** as truth | Archive or add banner to stale reports (see `docs/DOC_INDEX_RECOMMENDED.md`) |
| `docs/PG_MULTIVEHICLE_ENTITY_PLAN.md` | **`docs/VEHICLE_ENTITY_MEMORY_MVP.md`** + entity schema + `ENTITY_TRIAGE_INTEGRATION_PLAN.md` | **File missing** — do not reference obsolete path | Use VEHICLE_ENTITY_MEMORY_MVP as contract pointer |

---

## Per-item detail

### 1. Old triage vehicle selection / primary extract

- **Why deprecated:** Parallel “which vehicle wins” logic fights the **VehicleResolver** and breaks the mental model: one decision, one PG row, API mirror.
- **Still present?** **Triage-only** — `_extract_primary_add_car_vehicle_concrete` is removed. Add-car `vehicle_key` / `primary_vehicle_summary` are assembled in `triage.py` via `_derive_vehicle_key_from_add_car_text`, live entity payload reads, and related branches. Parallel `active_vehicle_resolver` module was **deleted** 2026-05-28 (see section below).
- **Safe removal step:** N/A for primary extract — keep resolver + guardrails when changing multi-vehicle behavior.

### 2. Heuristic API vehicle fields without PG

- **Why deprecated:** Violates `docs/PG_TRUTH_PIPELINE_CONTRACT.md` when session + PG are active.
- **Still present?** Triage may set fields before route finalization; **route** forces PG alignment when row exists.
- **Safe removal step:** Ensure triage never depends on pre-mirror heuristic for persisted sessions; keep in-memory-only parity for tests without `session_id` if required.

### 3. Blended resolver / `USE_RESOLVER_ONLY`

- **Why deprecated:** Two modes = two behaviors to test.
- **Still present?** Reported **removed** in `results/RESOLVER_TAKEOVER_REPORT.md`.
- **Safe removal step:** Grep for `USE_RESOLVER_ONLY`; confirm no deployment docs reference it.

### 4. JSON fallback (except local legacy)

- **Why deprecated:** Production should be DB-primary for case reads when URL configured.
- **Still present?** **Yes** — `json_read_fallback_allowed()` branches in `case_truth_repository.py`.
- **Safe removal step:** Pilot checklist: disable fallback in prod env; keep for dev laptops until cutover complete.

### 5. Full case hydration in fast path

- **Why deprecated:** Latency; `FINAL_SYSTEM_EVALUATION.md` notes session/case/postprocess cost.
- **Still present?** Stub path exists; risk is **accidental** full read in new code.
- **Safe removal step:** Code review checklist: new inbox routes use `get_case_triage_stub_for_read` or binding list, not full case, unless measured exception.

### 6. Blocking assist layer

- **Why deprecated:** Would blow HTTP SLO and mix “truth” with “nice copy.”
- **Still present?** `assist_layer` runs in a **daemon thread** from `_attach_assist_layer` — non-blocking.
- **Safe removal step:** Never `await` assist on request path; keep `assist` field additive.

### 7. Simulation on production page

- **Why deprecated:** Cognitive load, bundle size, and analytics confusion if treated as prod funnel.
- **Still present?** **Yes** — Tab D in `UnifiedIntakePage.tsx`.
- **Safe removal step:** Lazy-load simulation or separate route; tag analytics per surface.

### 8. Stale docs

- **Why deprecated:** Onboarding reads wrong mental model.
- **Still present?** Multiple `results/*.md` time slices; some assert resolver wiring or composer no-ops that **differ** from branch tip.
- **Safe removal step:** Do not delete; mark **ARCHIVE_CANDIDATE** in `docs/DOC_INDEX_RECOMMENDED.md`; prefer this blueprint + module contracts.

---

## `active_vehicle_resolver` — removed (2026-05-28)

- **Was:** Parallel `resolve_add_car_active_vehicle` module, unit-tested but **never imported by `triage.py`** — dangerous double-authority.
- **Decision:** **DELETE** — production vehicle lines stay in `triage.py` heuristics + `routing_guard.py`; finalized API fields from `_finalize_response_with_pg_truth` on the HTTP route.
- **Do not reintroduce** without wiring through triage + PG finalize in one sprint with scenario parity.

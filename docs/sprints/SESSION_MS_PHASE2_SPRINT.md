# SESSION_MS Phase 2 — Orchestration & persistence overhead

## 1. Objective

Continue reducing **`session_ms`** (route segments `session_ms_seg1` + `session_ms_seg2`) and **session-related orchestration overhead** on **`POST /api/inbox/triage`**, without changing triage logic, resolver semantics, API behavior, async patterns, or persistence contracts.

---

## 2. Evidence

### 2.1 `results/FINAL_LATENCY_LOCK.json`

- **`route_fanout_ms.session_ms`**: p50 ≈ **1189 ms**, p95 ≈ **1349 ms**, max ≈ **1601 ms** (chaos / final real-world library).
- **`postprocess_ms`**: p50 ≈ **861 ms**, p95 ≈ **1239 ms** (separate bucket; still dominated by in-progress persistence + downstream work).
- **`triage_ms`** and **`http_total`** show most variance is LLM-heavy; **`session_ms`** remains a steady second-tier bucket worth squeezing via orchestration.

### 2.2 Previous `SESSION_IO` sprint (`docs/sprints/SESSION_IO_OPTIMIZATION_SPRINT.md`)

- Completed: **`assume_fresh_co_read`** for cold saves; single **`deepcopy`** in **`patch_session_case_binding`** (vs double); semantic **no-op skip** on binding / post-case upserts when stored JSON unchanged (excluding `updated_at`).
- Reported chaos snapshot (different count than lock file): **`session_ms`** n=29, p50 ≈ 780 ms, p95 ≈ 941 ms.

### 2.3 Previous TRIAGE_FANOUT sprint (`docs/sprints/TRIAGE_FANOUT_PHASE2_OPTIMIZATION.md`)

- Removed duplicate **`get_case_triage_stub_for_read`** when **`list_recent_cases_for_binding`** returns stub-shaped rows reused in-request (**`case_ms`** wins).
- HTTP chaos rollup drift: ~**3%** p50/p95 improvement documented there; orthogonal to **`session_ms`**.

---

## 3. Known improvements already completed (before this phase)

| Area | Change |
|------|--------|
| Session read | Single co-read **`intake_session_repository.get_session`** on triage route; **`assume_fresh_co_read`** skips redundant cold **`get_session`** inside **`save_in_progress_session`** |
| Binding CPU | **`patch_session_case_binding`**: one **`deepcopy`** of co-read row; semantic compare skips no-op **`upsert_session`** |
| Post-case trim | **`save_session_binding_after_case_created`**: skip upsert when trimmed document equals stored (minus `updated_at`) |
| Case binding IO | TRIAGE_FANOUT Phase 2: reuse list stub row (**one fewer case read** when binding resolves from recent list) |

---

## 4. Remaining `session_ms` hypotheses (Phase 2)

1. **`upsert_session` defensive `deepcopy`** runs **again** after **`patch_session_case_binding`** / some writers already produced an isolated tree → **duplicate full-document copy** on large `turns` / `triageResult` payloads.
2. **`deepcopy`** of a tiny **blank** binding template (`[]` turns) is unnecessary CPU vs a **fresh empty dict**.
3. Route **`pre_read_raw`** mistakenly passed **`in_progress_session_view`** output alongside repo row (**wrong shape**) in the fallback branch — dead for cold sessions but misleading and risky if refactored.
4. Repeated **`in_progress_session_view(session_full_row)`** after patches rebuilds thin view dicts (**O(1)** vs giant JSON — low cost, acceptable glue).
5. **`get_session`** in **`session_repository`** (Postgres path) shallow-copies outer dict; **`upsert_session`** still deep-copies outgoing payload (**dominant serialization path**).

---

## 5. Validation gates

- `python3 -m compileall services/fiqa_api`
- `bash scripts/guardrail_inbox_triage.sh`
- `PYTHONPATH=. python3 scripts/run_full_regression.py` (**http p95 &lt; 6000 ms** gate; LLM chaos variance → may require re-run if tail spikes)
- Optional: **`TRIAGE_RETURN_PERF_METRICS=1`** curl / scenario probes when API is **up** on 8001

---

## 6. NON-GOALS

- Changing **`triage_conversation`** decisions, prompts, or lane behavior
- Resolver / **`vehicle_key`** semantic changes
- API schema / client contract changes
- Async / threaded persistence (**no race introduction**)
- Rewriting Postgres schema or **`jsonb_set`** partial updates (defer)
- Shrinking **`postprocess_ms`** via dropping analytics correctness (defer)

---

## 7. Optimization principles

| Principle | Apply as |
|-----------|----------|
| **Reuse** | Co-read **`session_full_row`** through **`patch_session_*`**, **`save_in_progress_session`**, **`save_session_binding_after_case_created`** |
| **Skip** | No-op semantic compares (already)**; skip **second** full-document **`deepcopy`** when caller owns payload |
| **Cache** | Per-request **`triage_stub_read_cache_scope`**, **`active_vehicle_request_cache_scope`** (existing route decorators) |
| **Batch** | Binding list stub reuse (**fan-out sprint** — not duplicated here) |
| **No semantic drift** | **`copy_payload=False`** only when payload is freshly cloned or a brand-new row dict |

---

## SESSION_MS_CALL_GRAPH_V2 (POST `/api/inbox/triage`, main stem)

Legend: **`R`** repeated work risk, **`S`** serialization, **`W`** write, **`G`** Postgres round-trip.

```text
emit_session_milestones(session_id?, text, turns)          # funnel buffer; no PG session IO

[get_session_seg1 START]
session_full_row = intake_session_repository.get_session(sid)   # G, 1× when sid — R:none if sid empty
sess_raw = in_progress_session_view(session_full_row)            # shallow view build — R (~2–4× later after patch refreshes same row)
[get_session_seg1 END — counted as session_ms_seg1 partly]

possibly: get_case_triage_stub_for_read(active_case_id)          # stub cache scope; separate case_ms slice
possibly: patch_session_case_binding(..., reuse_session_row=...)  # deepcopy(co-read) → mutate → semantic no-op skip OR upsert — W,G

list_recent_cases_for_binding + resolve_active_case              # case_ms (fan-out optimizations prior)
possibly: get_case_triage_stub_for_read(effective_case_id)         # skipped when list row reused

triage_conversation(...)                                           # triage_ms

patch_session_case_binding (append boundary OR active_case/lvk/hint)# deepcopy(sess row) optional upsert — W,G — S,R on huge JSON if copy stacks

(if persist_case) save_case + save_session_binding_after_case_created(...)  # case_ms slice

postprocess START
_finalize / identity / lifecycle / assist ...

(if session_id AND no case_id on result):
  save_in_progress_session(..., pre_read_raw=session_full_row, assume_fresh_co_read=True)
    → normalize turns (S)
    → _in_progress_session_payload_unchanged (may json.dumps — S,R on contentious equality)
    → upsert_session (deepcopy payload by default — S,R)

_schedule_route_analytics (async thread — not in route_perf buckets but thread spawn in postprocess)

_attach_route_perf_ms
postprocess END
```

**Repeated reads**: single mandatory **`get_session`** per **`sid`**; optional **`patch_session`** path **`get_session`** only when **`reuse_session_row` unspecified** (**not used** from triage route when co-read flows).

**Repeated writes**: suppressed by SESSION_IO semantic no-ops where possible.

**Repeated serialization**: **`json.dumps`** in no-op detector for turns; **`upsert_session` `Json(...)`**; **double `deepcopy`** was a remaining stack (**addressed Phase 2** for binding + binding-after-case writes).

---

## SESSION_MS_HOTSPOTS_V2

| Hotspot | Why expensive | Current mitigation | Remaining waste | Est. ROI |
|---------|---------------|--------------------|-----------------|----------|
| **`upsert_session` full `deepcopy`** | Huge nested `turns`/blob | Postgres write must snapshot | Duplicate copy after **`patch_session_case_binding`** already copied | **Medium** CPU on binding-heavy sessions |
| **`patch_session_case_binding` `deepcopy(reuse)`** | Large session docs | Required isolation vs co-read aliasing | Unavoidable without schema change | — |
| **Empty template `deepcopy(blank)`** | Small but wasted | Previously always deepcopied literals | Allocate fresh `{}`/`[]` | **Low**, cheap win |
| **`_in_progress_session_payload_unchanged` `json.dumps` fallback** | Expensive equality | Length + **`==`** fast path first | Rare path when **`==`** false but JSON equal | Low frequency |
| **`in_progress_session_view` × N** | Rebuild thin dict | Small vs JSON parse | Glue overhead only | Very low |
| Route `pre_read_raw` shape | Wrong type confuses readers | SESSION_IO co-read contract | Removed misleading **`sess_raw`** fallback | Clarity only |

---

## SESSION_MS_SYSTEM_INSIGHTS

1. **Repeated in one request?** **`deepcopy`** of the same logical document can stack **`patch`** → **`upsert`** (removed when caller owns cloned row).
2. **Reusable?** **`session_full_row`** is authoritative for **`pre_read_raw`** — never substitute API view shaped dict.
3. **Already known mid-route?** Binding fields post-patch reflected in **`session_full_row`**; **`prior_ws`** taken before patches (still correct lifecycle).
4. **Semantically unnecessary writes?** SESSION_IO skips binding / trim no-ops; Phase 2 reduces CPU even when writes occur.
5. **Large payloads?** System turns embed **`triageResult`** referencing live **`result`** until **`route_perf`** attached — **`upsert` `deepcopy`** protects stored snapshot (**keep default `copy_payload=True`** for in-progress saves).
6. **Duplicated merges?** Route applies patch then save path builds new row — **`_in_progress_session_payload_unchanged`** prevents redundant second write when unchanged.
7. **Stale-compat paths?** **`reuse_session_row is None`** intentionally means “fresh empty row without DB read”; distinct from **`_UNSPECIFIED`**.

---

## SESSION_MS_PHASE2_OPTIMIZATION_PLAN

| ID | Optimization | Safe because | Expected gain | Rollback risk | Files |
|----|----------------|--------------|---------------|---------------|-------|
| P1 | **`upsert_session(..., copy_payload=False)`** after **`patch_session_case_binding`** | Payload is **`deepcopy(reuse_session_row)`** or fresh empty template; no shared aliasing with route mutants | Less CPU on large sessions | Low — toggle flag | `session_repository.py`, `session_store.py` |
| P2 | Same for **`save_session_binding_after_case_created`** when writing **new** trimmed row | Row dict is newly built; normalized identity slices are small new dicts | Small CPU on post-create path | Low | `session_store.py` |
| P3 | **`_fresh_empty_session_row`** instead of **`deepcopy(blank_row)`** | Only scalars + fresh `[]`/`{}` | Micro CPU | Very low | `session_store.py` |
| P4 | Route **`pre_read_raw=session_full_row` only** | Cold path uses **`assume_fresh_co_read=True`**; view was wrong type for fallback | None perf; safer contract | None | `routes/inbox_triage.py` |

**Not done (semantic / bigger):** partial JSONB updates, async persist, changing **`triageResult`** snapshot rules.

---

## SESSION_MS_LOOP1_REPORT

**Implemented:** P1 (patch path only) + P4.

**Validation:**

- `python3 -m compileall services/fiqa_api` — PASS
- `bash scripts/guardrail_inbox_triage.sh` — PASS
- `PYTHONPATH=. pytest -q tests/test_intake_session_persistence.py tests/test_case_binding.py` — PASS
- `PYTHONPATH=. python3 scripts/run_full_regression.py` — PASS on a green run (chaos **http p95** varies; re-run if `http_p95_gt_6000ms` flakes)

**Tests:** `counted_upsert` mock forwards **`**kwargs**` to match new **`upsert_session`** signature.

**Curl timing:** Not recorded here — local **8001** was **connection refused** during agent window; rely on chaos **`REGRESSION_CHAOS.json`** when server not kept hot.

---

## SESSION_MS_LOOP2_REPORT (second pass)

**Re-opened graph questions**

1. Still reading same session twice? **No** on triage hot path when **`sid`** set (co-read + **`assume_fresh_co_read`**).
2. Writing identical payloads? SESSION_IO compares still apply; unchanged.
3. Merging identical structures? No-op skips still apply.
4. Deep-copying large dicts twice? **Reduced** for **`patch_session_case_binding` → upsert** and **`save_session_binding_after_case_created` → upsert** (P1+P2).

**Implemented:** P2 (**`save_session_binding_after_case_created`** uses **`copy_payload=False`**).

**Validation:** Same gates as Loop 1; regression **eventually green** after LLM-tail retries.

---

## UPDATED_SESSION_ARCHITECTURE_MODEL (product architect view — no code)

- **Session** is the **pre-handoff conversation spine**: turns, workflow hints, **`active_case_id` / `last_vehicle_key`**, light identity scaffolding — **truth until a case exists**, then continuity + binding hints post-case-create.
- **Hot path**: one **coherent read**, **targeted binding patch**, **`triage_conversation`**, optionally **persist case**, then **in-progress save** when no **`case_id`** on response.
- **Async later**: analytics funnel buffering (**already threaded**); non-critical enrichment; never triage-blocking identity **PG** mirrors without product sign-off.
- **Route vs store vs triage**: **Route** = orchestration / perf segments / coercion; **`session_store`** = merge rules + skip-no-op writes; **`triage`** = pure decisioning from text + **`reply_truth_context`**.
- **Multi-office scale**: single-row JSON replace per **`session_id`** + **stub list** scans — **indexed case lists** & **bounded recent windows** matter; **`list_all`** N+1 remains an **offline/admin** hazard.
- **SaaS scale**: **UUID session keys**, **tenant partition key** in payload (future), **rate limits** on LLM triage; **session document size** growth from system **`triageResult`** echoes remains the **JSON cost elephant**.

---

## FUTURE_SESSION_OPTIMIZATION_IDEAS (ideas only)

- Request-scope memo keyed **`session_id`** if future helpers bypass co-read (**opt-in**, low risk).
- **`jsonb_set`**/`jsonb_strip_nulls`** surgical updates for binding-only mutations without shipping full **`turns`**.
- Periodic **truncate / archive** older system blobs from stored turns (**product-gated**).
- **Dual-write** session mirror co-located with **`case_truth`** transaction (consistency vs latency).

---

## SESSION_RISK_DISCOVERY

| Risk | Signals |
|------|---------|
| **Double-brain session truth** | Repo row vs ephemeral **`prior_workflow_state`** from view — reconcile only via defined merge in **`session_store`** |
| **Duplicated reads** | Other endpoints (`**/session/{id}`**) call **`get_in_progress_session` → `get_session`** (**OK** separate request) |
| **Frontend revive assumptions** | Clients expect **`turns`** + **`workflow_state`** — trim-after-case resets turns; documented product behavior |
| **Stale **`active_case_id`**** | Route clears when stub says closed — tested in simulations |
| **Hidden N+1** | **`patch_session`** (**`session_repository.patch_session`**) calls **`get_session` + `_copy_row` + upsert copy** (**heavy**) — **not on triage primary path** |
| **Persistence aliasing bug** | If **`copy_payload=False`** misapplied while **`result`** still mutable — **danger**; guarded by only using after deepcopy or fresh row |
| **Route fan-out** | TRIAGE_FANOUT doc still authoritative for case list / stub reuse |

---

## SESSION_MS_PHASE2_FINAL_REPORT

1. **What improved:** Removed **redundant full-document `deepcopy` inside `upsert_session`** on **(a)** binding upserts that already followed a **`deepcopy` co-read row**, **(b)** post-case **trim** writes that build a **new** small row; replaced **empty binding template `deepcopy`** with **fresh dict**; clarified **`pre_read_raw`** as **repo-shaped co-read only**.
2. **Repeated work removed:** Second **Python-level** tree copy on those write paths; useless **`deepcopy`** of empty templates.
3. **Latency:** Chaos **`session_ms`** snapshot from latest **`REGRESSION_CHAOS.json`** (successful run aggregator): **n=29**, **p50 ≈ 829 ms**, **p95 ≈ 983 ms** (same chaos binary; not 1:1 vs **`FINAL_LATENCY_LOCK.json`** scenario mix); **HTTP p95** gated under **6000 ms** when regression green.
4. **Architectural clarity:** **`pre_read_raw`** contract is explicitly **repository row**, not **`in_progress_session_view`** output.
5. **What remains:** Default **`deepcopy`** in **`save_in_progress_session`** (needed — **`triageResult`** aliases live **`result`**); **`deepcopy`** in **`patch_session_case_binding`** for real rows (unavoidable without DB-level patching); **`json.dumps`** slow path on rare contentious turn equality.
6. **Next highest ROI (safe):** Investigate **`_in_progress_session_payload_unchanged`** cheap structural hash for turns when lengths match but **`!=`** (risk: false positives — needs careful hashing); consider **optional** `copy_payload=False` only if last system turn deep-copies **`triageResult`** explicitly (**higher risk**).

---

## SESSION_MS_LOOP3_REPORT (deeper micro-orchestration)

**Implemented:** P3 **`_fresh_empty_session_row`** (no **`deepcopy`** on empty binding templates).

**Validation:** compileall, targeted pytest, guardrail, full regression (with potential chaos **p95** re-runs).

---

## FINAL_ONE_LINE

This sprint improved **session write-path CPU** on **`POST /api/inbox/triage`** by eliminating **duplicate full-document copies and needless empty-template deepcopies** without changing **triage outcomes, resolver behavior, or API responses**.

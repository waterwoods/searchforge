# TRIAGERESULT + `copy_payload` — Discovery Control Note

Timebox: ~20–30 minutes (architecture only; no implementation).

---

## 1. Objective

Decide whether a future 3–5 hour sprint should target **`copy_payload=False` for `save_in_progress_session` → `upsert_session`**, by **isolating** (copying only) what is strictly necessary—proposed framing: **the final system turn’s `triageResult`** snapshot—versus keeping **full-document `deepcopy`** in `upsert_session` (current default for this path).

---

## 2. Current state

| Layer | Behavior |
|-------|----------|
| **Route** (`inbox_triage.py`) | Builds `result = triage_conversation(...)`; mutates the **same dict** through reroute, lifecycle, finalize, PG vehicle overlay (`_apply_pg_active_vehicle_identity_last`), then appends **`"triageResult": result`** (identity reference). |
| **Session save** (`session_store.save_in_progress_session`) | Normalizes turns (keeps **`triageResult`** as **reference**, not cloned). Builds **`workflow_state = _extract_workflow_state(triage_result)`**. Calls **`repo.upsert_session(sid, row)`** with default **`copy_payload=True`** → **`deepcopy`** of entire `row`. |
| **Repository** (`session_repository.upsert_session`) | With **`copy_payload=True`**, defensively deep-copies payload before Postgres / in-memory retention. **`copy_payload=False`** only permitted when callers guarantee **no post-upsert mutation** of the wired tree—or when nested JSON serialization has fully captured bits before mutation (still unsafe for **`_MEMORY`** aliasing). |
| **Already optimized** | **`patch_session_case_binding`** and **`save_session_binding_after_case_created`** use **`copy_payload=False`** after caller-owned **`deepcopy`** or **fresh dict** shells (SESSION_MS Phase 2). |

Canonical hot-path references:

```218:271:services/fiqa_api/inbox_triage/session_repository.py
def upsert_session(
    session_id: str,
    payload: dict[str, Any],
    *,
    copy_payload: bool = True,
) -> bool:
    ...
    doc = (_copy_row(payload) if copy_payload else payload) if payload else {}
```

```59:74:services/fiqa_api/inbox_triage/session_store.py
    out: dict[str, Any] = {"role": role, "text": text}
    if role == "system" and "triageResult" in turn:
        out["triageResult"] = turn["triageResult"]
```

```1381:1426:services/fiqa_api/routes/inbox_triage.py
    _attach_case_lifecycle(result, persisted_case=existing_case)
    _finalize_triage_api_result(result)
    _apply_pg_active_vehicle_identity_last(result, request.session_id)
    postprocess_ms_total = _route_mark()
    _schedule_route_analytics(
        result,
        turns,
        session_id=request.session_id,
        text=text,
    )

    # In-progress persistence: save turns + workflow_state when session_id and no case
    if request.session_id and not result.get("case_id"):
        ...
        full_turns.append({"role": "system", "text": reply_content, "triageResult": result})
        try:
            save_in_progress_session(
                request.session_id.strip(),
                full_turns,
                result,
                pre_read_raw=session_full_row,
                assume_fresh_co_read=True,
            )
...
        result["conversation_id"] = request.session_id.strip()
    ...
    _attach_route_perf_ms(
        result,
        {
            ...
            "postprocess_ms": postprocess_ms_total,
        },
    )
```

---

## 3. Existing optimizations already completed (relevant subset)

From **`docs/sprints/SESSION_MS_PHASE2_SPRINT.md`** and code:

1. **`upsert_session(..., copy_payload=False)` after `patch_session_case_binding`** when `new_row` is already a **`deepcopy(reuse_session_row)`** or empty template.
2. **`save_session_binding_after_case_created`** uses **`copy_payload=False`** on a **newly built** small row (trimmed turns).
3. **`_fresh_empty_session_row`** avoids redundant **`deepcopy`** of empty shells.
4. **`_in_progress_session_payload_unchanged`** — length / `workflow_state` / `==` / rare **`json.dumps`** path to skip no-op writes.
5. Co-read contract **`pre_read_raw=session_full_row`** (repo-shaped), **`assume_fresh_co_read`** on cold session — fewer duplicate reads.

**Explicitly remaining:** **`save_in_progress_session` → upsert default `copy_payload=True`** because **`triageResult`** embed references the route’s **`result`** and post-save enrichment exists.

---

## 4. Hypothesis

> We can materially reduce CPU by calling **`upsert_session(..., copy_payload=False)`** on the in-progress path **if** we **isolate/copy only** the risky field—typically described as **the final system turn’s `triageResult`**—while avoiding **full-document `deepcopy`** of `turns` + `workflow_state` + ancillary session fields.

**Discovery stance:** plausible **CPU** win on large threads, but **`triageResult` alone is likely not sufficient** unless **`workflow_state` (and any other subgraph still aliasing `result`)** is also snapshotted.

---

## 5. Discovery questions

1. Does **`workflow_state`** share mutable interior references with **`result`**? → **Yes** (`_extract_workflow_state` assigns `out[k] = triage_result[k]` for known keys.)
2. Is **`result` mutated after **`save_in_progress_session`** completes? → **Yes** (`conversation_id`, optional **`route_perf`** via **`_attach_route_perf_ms`**). Persisted **`triageResult` (via prior deepcopy)** currently reflects pre-telemetry shape.
3. Is there concurrent use of **`result`** around save time? → **Yes** — **`_schedule_route_analytics`** runs **`asyncio.to_thread`** before save (same dict read from another thread while main mutates / serializes). This is a **broader** hazard than `copy_payload` alone.
4. Would **`copy_payload=False`** without copies break **in-memory** test store? → **Yes** if **`_MEMORY[sid] = doc`** retains aliases and later route mutates nested lists.
5. Is **only one field** unsafe? → **No** — at minimum **`triageResult` + extracted workflow fields** can alias shared list/dict interiors.

---

## 6. Success criteria (this note)

| Criterion | Outcome |
|-----------|---------|
| **`copy_payload=False` achievable?** | **Yes with conditions:** must snapshot **all** subgraphs still shared with the live **`result`** (not only `triageResult`), or freeze **`result`** before wiring into `turns` (product/contract change — out of scope for this sprint). |
| **Aliasing risks** | **Documented** in **TRIAGERESULT_ALIASING_RISKS** below. |
| **Mutation risks** | **Documented**; post-save mutation + background analytics add **non-obvious** edges. |
| **Expected ROI** | **Moderate-low at pilot-scale session sizes** versus **engineering + correctness** risk (**TRIAGERESULT_COPY_DISCOVERY_REPORT**). |
| **Implementation risk** | **Medium-high** without broad test + concurrency audit; easy to regress with partial copy. |

---

# TRIAGERESULT_LIFECYCLE_MAP

| Stage | Location | What happens | Ownership |
|-------|----------|--------------|-----------|
| **Create** | `triage.py` → `triage_conversation(...)` | Returns **`result`** dict (fresh per branch exit). | **Triage layer** owns shape; route receives reference. |
| **Route enrichment** | `routes/inbox_triage.py` | In-place **`result[...]`** updates (reroute, **`case_id`**, assist layer kickoff, **`_attach_case_lifecycle`**, **`_finalize_triage_api_result`**, **`_apply_pg_active_vehicle_identity_last`**, persist branch updates). **Mutation points.** | **Route orchestration**. |
| **Embed in turns** | `routes/inbox_triage.py` | **`full_turns.append({"triageResult": result})`** — **reference semantics**. **Reuse / alias point.** | **Route** until persistence snapshot. |
| **Normalize / row build** | `session_store.save_in_progress_session` | **`_normalize_turn`** copies **`triageResult` by reference**. **`workflow_state = _extract_workflow_state(result)`** — **shares values** with **`result`** for keyed fields. **Alias point.** | **Store** builds DB row payload. |
| **No-op check** | `session_store._in_progress_session_payload_unchanged` | Compares **`raw["turns"]`** vs **`normalized_turns`**; may hit **`json.dumps`** fallback (**serialization cost**, not lifecycle mutation). | **Store**. |
| **Persistence boundary** | `session_repository.upsert_session` | **`copy_payload=True`:** **`deepcopy(row)`** then JSON encode to Postgres / assign **`_MEMORY`**. **Boundary:** snapshot isolation from further route mutation (for PG committed bytes once encoded; **`_MEMORY` still retains live refs if no copy**). | **Repository** commits document. |
| **Post-save reuse** | `routes/inbox_triage.py` | **`result["conversation_id"]`**, **`_attach_route_perf_ms`** (**mutates **`result`** in place**—not intended for revived session fidelity). Analytics thread may already be reading **`result`**. **Reuse / mutation.** | **Route** response path. |

**Legend:** Bold rows mark **mutation points**, **reuse points**, **persistence boundaries**, **route vs store ownership** as above.

---

# TRIAGERESULT_ALIASING_RISKS

| Location | Mutation / alias type | Risk | Why dangerous |
|---------|-------------------------|------|----------------|
| `routes/inbox_triage.py` (post-triage soft_route block) | In-place **`result[...]`** keys | **Medium** | Any stored reference to **`result`** would observe changing broker copy / drafts. |
| `routes/inbox_triage.py` **`_finalize_triage_api_result` / `_attach_case_lifecycle` / `_apply_pg_active_vehicle_identity_last`** | In-place coercion + vehicle overlay | **Medium** | Same object later embedded as **`triageResult`**. |
| `session_store._extract_workflow_state` | **Shallow** copy: values reference **`triage_result`** interiors | **High for naive `copy_payload=False`** | **`collected_fields` / `still_needed_fields`** list objects can be **`is`**-identical inside **`workflow_state`** and **`triageResult`**. Mutating **`result`** mutates **`workflow_state`** in row. |
| `session_store._normalize_turn` | **`triageResult`** by reference | **High** without repo **`deepcopy`** | Turn list embeds mutable live dict. |
| `routes/inbox_triage.py` **`_schedule_route_analytics`** + **`save_in_progress_session`** overlap | Concurrent **read vs mutate** (**thread**) | **Medium** (today mitigated indirectly if upsert clones before serialization; weaker if removed) | Racy reads of partially updated dicts; brittle under partial snapshot strategies. |
| `routes/inbox_triage.py` **`_attach_route_perf_ms` after save** | Adds **`route_perf`** key | **Low** for DB (**post-serialize**) | Demonstrates **`result`** is intentionally **living** API object after persistence call. |
| `session_repository.upsert_session` (**memory backend**) **`_MEMORY[sid] = doc`** | Stores alias when **`copy_payload=False`** | **High** | Next request merges / reads assume stable tree; live mutation corrupts “stored” document. |
| `session_repository.patch_session` (off hot path) | **`get_session` + deepcopy + shallow merge** | **Low** on triage primary | Heavy path; not this optimization’s target. |

---

# TRIAGERESULT_SYSTEM_INSIGHTS

1. **Why `copy_payload=True` exists today** — `upsert_session` is a **repository-level fence**: callers may pass payloads built from **routes that hold live singleton dicts** (here, **`result`**) wired into **`turns`**. Without **`deepcopy`**, Postgres / memory backends could retain aliases to objects the route continues to mutate (and **analytics threads** may read concurrently).
2. **Bugs from aliasing leaks** — Silent **corruption of revived session **`workflow_state`** vs last **`triageResult`**, stale list sharing causing **Frontend restore drift**, flaky tests on **memory** backend, theoretically **racey JSON** encode if serialization walked a structure mutated mid-flight.
3. **Stale references corrupting session state** — **`get_session`** returns **`deepcopy`** on memory reads and a **fresh assembled dict** on PG reads today, masking prior aliasing—but **persisted incorrect bytes** are the real failure mode without copy.
4. **Later route logic mutating persisted objects** — After **`copy_payload=True`**, no—persisted snapshot is independent. **`copy_payload=False`** + missed subgraph → **yes**, possible.
5. **Whole payload copied for one unsafe field?** — **Mechanically**, the **`deepcopy`** is **global** because **multiple subgraphs alias ** **the same **`result`**: **`triageResult`** (whole dict) **and** **`workflow_state` value references** (lists / nested dicts for extracted keys).
6. **Only final turn `triageResult` isolation?** — **Insufficient alone** unless **`workflow_state`** (and anything else referencing **`result`** interiors) is also snapshotted or **deep-copied**.
7. **Partial copy safer than no copy?** — **Usually yes**: copying **`triageResult` + duplicated workflow-derived structures** narrows **`deepcopy`** cost vs correctness.

---

## STEP 5 — Estimate real ROI (**TRIAGERESULT_COPY ROI** — order-of-magnitude)

Assumptions: pilot threads **moderate length** (dozens of turns rare); **`triageResult`** **10–80 KB** JSON-shaped in worst cases; full session row **mostly turns × text + latest blob**.

| Dimension | Estimated impact |
|-----------|-------------------|
| **CPU (deepcopy removal / shrink)** | **~0.5–5 ms / save** typical; **long threads or very large blobs** → **single-digit–low-double-digit ms** savings per write. Saves **once per mutate** (`_in_progress_session_payload_unchanged` miss). |
| **`session_ms` segment** | Small fraction vs **binding + DB RTT + triage**; Chaos snapshot in Phase 2 doc showed **`session_ms` p50 ~829 ms** — **not dominated** by one Python copy unless documents are **very large** or churn is extreme. |
| **`postprocess_ms` (route timer)** | **Minor** unless profiling shows **`deepcopy` > ~5–10%** of post-triage slice. |
| **Memory** | **Transient allocation drop** proportional to **`deepcopy` peak**; bounded per request—not a steady-state leak fix. |

| Optimization | ROI | Risk | Worth 3–5h sprint alone? |
|--------------|-----|------|---------------------------|
| Full **`copy_payload=False`**, **no isolation** | **High CPU if safe** | **Very high correctness** | **No** |
| **Partial subgraph copy** (**`triageResult` + workflow snapshot**) | **Medium** | **Medium** — must list every shared field | **Maybe** |
| **Last-turn-only `triageResult` isolation** (**as literal spec**) | **Low–medium CPU** | **High** (**workflow**) | **No** (**as stated**) |
| **Immutable / frozen snapshot API** (**result frozen post-finalize**) | **Medium-high** conceptual safety | **High** behavior churn | Future architecture |
| **Current state — do nothing** | **Baseline** | **Known-safe** | **Reasonable default** |

---

## STEP 6 — SAFER_ALTERNATIVES_DISCOVERY

| Alternative | Pros | Cons |
|-------------|------|------|
| **Keep full `deepcopy`** (today) | Proven isolation | Pays CPU on big rows |
| **Widen snapshot: `copy.deepcopy(last_system_turn["triageResult"])` AND `workflow_state`** built from **`copy.deepcopy`** of each extracted value **or** a single **`deepcopy`** of a **minimal subgraph** extracted after finalize | Cuts duplication vs cloning irrelevant prior turns unchanged on some strategies | Requires **explicit contract** of which keys alias |
| **`json.loads(json.dumps(snapshot_subtree))`** for persistence snapshot | Serialization-defined boundary | Often **similar cost** to **`deepcopy`** for large blobs |
| **Freeze / `MappingProxyType` on `result` after finalize** | Hard aliasing fence | High blast radius; thread/analytics still need rules |
| **Move telemetry (`route_perf`) off **`result`** before snapshot** | Clearer persisted vs response split | Behavioral / contract refactor (out of this sprint scope) |
| **Invest further in **`_in_progress_session_payload_unchanged`** hashing** | Avoid writes entirely sometimes | SESSION_MS Phase 2 already flagged false-positive sensitivity |

---

## STEP 7 — PRODUCT_IMPACT_ANALYSIS (**TRIAGERESULT — product architect lens**)

1. **Pilot scale meaningful?** Likely **marginal UX latency** versus **network + LLM + DB**; measurable only with **heavy sessions** or **high concurrent save churn**.
2. **Customer-visible?** **Unlikely per message** unless p95 regressions dominated by **`session_ms`** and profiling proves **`deepcopy`** is fat.
3. **Is **`session_ms` still THE bottleneck post-recent work?** Phase 2 already ate **duplicate copies** elsewhere; **`session_ms`** remains an **aggregator** — **blocking triage latency** perception still likely **LLM‑bound**.
4. **Future analytics/SaaS** — **telemetry split**, **tenant partition keys**, **smaller persisted core `triageResult`**, dominate long-term SaaS readiness more than **`deepcopy`** micro-optimization.
5. **Maintenance complexity** — **Partial snapshot** + **concurrent analytics** + **PG vs memory** parity increases **ongoing cognitive load** and **regression surface**.

---

## STEP 8 — FINAL_RECOMMENDATION

**Choice: D — a safer alternative (or narrower scope) is better than blunt `copy_payload=False`**

| Dimension | Assessment |
|-----------|-------------|
| **Why** | **Copying only the last `triageResult`** does **not** close **workflow_state aliasing**; naive **`copy_payload=False`** reintroduces **memory-backend** hazards and interacts badly with **`_schedule_route_analytics`** threading. |
| **Expected gain** | **Milliseconds per qualifying save**, significant only under **fat JSON** docs or **frequent churn** ignoring no-op skips. |
| **Expected danger** | **Stale / corrupted Postgres JSON** + **silent session drift** if any shared subtree missed; **stress hard to reproduce** without concurrency + long-thread fuzzing. |
| **Engineering complexity** | **Medium–high** (correct partial snapshot enumeration + regression tests across memory/PG paths + concurrency reasoning). |
| **Recommended next move** | Before a dedicated sprint: **profile** **`save_in_progress_session`** with **real-sized** session docs; quantify **`deepcopy` %** of **`postprocess_ms`/`session_ms`**. If justified, spike **explicit “persist snapshot bundle” helper** (**`deepcopy`** of **`{last_triage_snapshot, workflow_snapshot}`** or **`copy.copy` of row shell + targeted `deepcopy`s**) **without** flipping global **`copy_payload=False`** until proven. |

---

## STEP 9 — TRIAGERESULT_COPY_DISCOVERY_REPORT (executive summary)

1. **Architecture reality** — **`triageResult`** is **`result`**; **`workflow_state`** is a **shallow slice** referencing **`result` interiors`; **`deepcopy`** in **`upsert_session`** intentionally isolates persisted JSON from subsequent route mutation and overlaps with **background analytics**.
2. **Actual bottleneck** — At pilot realism, **`deepcopy`** is **secondary** versus **LLM**, **network**, **DB latency**; spikes when **sessions are huge** or **no-op skip rarely hits**.
3. **Is no-copy (`copy_payload=False`) safe as proposed?** **Not** without **broader subgraph isolation** (so **narrow “triageResult-only” framing is misleading**).
4. **ROI large enough?** **Uncertain/low at current scale**; **profile-gated**.
5. **Safest direction** — **Retain default defensive copy**, **defer wide `copy_payload=False`**, investigate **measurable hotspot** then **scoped snapshot helper** (**D**).

---

## FINAL ONE LINE

The real question is not whether we can remove copies, but whether doing so safely is worth the complexity.

---

## Appendix — Existing doc cross-links

- `docs/sprints/SESSION_MS_PHASE2_SPRINT.md` — Phase 2 copy removal where caller already **`deepcopy`**, and rationale for **`copy_payload=True`** on **`triageResult`** path.

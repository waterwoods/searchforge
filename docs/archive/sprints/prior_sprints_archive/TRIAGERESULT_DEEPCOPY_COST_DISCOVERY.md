# TRIAGERESULT deepcopy + JSON cost — discovery control note

**Timebox:** 45–90 minutes (measurement + design note only; **no runtime behavior changes**).

**Diagnostic script:** `scripts/measure_triage_copy_cost.py` (temporary; clearly marked diagnostic).

---

## Objective

Measure the **real** cost of `deepcopy` / `json.dumps` (and related helpers) on the **in-progress session persistence** path, then decide whether a future **4–5 hour persistence snapshot** sprint is justified.

---

## Prior risk findings (from `TRIAGERESULT_COPY_DISCOVERY.md`)

- Route appends **`"triageResult": result`** by **identity**; **`workflow_state = _extract_workflow_state(result)`** is a **shallow slice** that **shares** interior objects with `result`.
- **`save_in_progress_session`** → **`upsert_session(..., copy_payload=True)`** performs a **defensive `deepcopy` of the full row** so Postgres / memory backends do not retain **live aliases** to objects the route mutates after save (`conversation_id`, `route_perf`, etc.) and to avoid races with **analytics threads**.
- **`copy_payload=False` on the in-progress path** without a **targeted snapshot** is **high risk** (aliasing + `_MEMORY` retention).
- Hypothesis from prior doc: CPU savings from dropping full-document copy might be **~0.5–5 ms / save** in typical cases; **needs measurement** against real `session_ms` / HTTP.

---

## What was measured

On a **local microbench** (Python 3, WSL2), **500 iterations** per operation (except as noted):

1. **`deepcopy(session_row)`** — models **`upsert_session`** defensive copy when `copy_payload=True` (shared `triageResult` across system turns uses `deepcopy` memoization; cost scales with **unique** object graph).
2. **`deepcopy(last triageResult only)`** — lower bound if only the **last** system turn were snapshotted in isolation (not implemented).
3. **`json.dumps(session_row)`** — proxy for JSON serializationwork before DB (`Json(inner)` path is similar order of magnitude; not identical to psycopg).
4. **`_extract_workflow_state`** — production helper import from `session_store`.
5. **`_in_progress_session_payload_unchanged`** — branches: hit **`==`** on turns (same refs), vs **early length miss** vs **explicit double `json.dumps`** as **upper bound** for the rare contentious-equality branch.

Constructed payloads (alternating **customer / system**; each **system** turn references the **same** `triageResult` dict, matching production semantics):

| Scenario | Turn count (`n_turns`) | ~JSON bytes |
|-----------|-----------------------|-------------|
| small | 3 | ~1.9 KiB |
| medium | 20 | ~13.4 KiB |
| large | 100 | ~64.6 KiB |
| large_fat_blob | 100 (bulky nested `triageResult`) | ~212 KiB |

---

## Non-goals (this sprint)

- Change **`triageResult`** copying behavior or **`copy_payload`** for in-progress upserts.
- Change **API schema**, **triage/resolver** logic, or **route flow**.
- Implement **persistence snapshots** — **design-only** follow-up **if** cost is material.

---

## Decision criteria

| Id | Criterion |
|----|-----------|
| **A** | If deepcopy/json cost is **small** versus **`session_ms` / HTTP p95** and regression budget → **do not optimize** this path now. |
| **B** | If cost is **material** at realistic production sizes → produce a **safe persistence snapshot design** for a future sprint (still **no behavior change here**). |
| **C** | If measurement is **inconclusive** (e.g. missing multi-MB payloads, profiler disagreement) → **more measurement** before any sprint commitment. |

---

## COPY_COST_MAP

| Location | Operation | Payload / scope | Risk / note |
|----------|-----------|------------------|-------------|
| `routes/inbox_triage.py` (`full_turns.append(...)`) | Wire **`triageResult": result`** | Live **`result`** dict | **Alias** to route object; mutated after persistence intent. |
| `session_store._normalize_turn` | Assign **`out["triageResult"] = turn["triageResult"]`** | System turn only | Keeps **reference**, not clone. |
| `session_store._extract_workflow_state` | **Shallow** key copy from `triage_result` | Subset of `result` | **Shares** mutable interiors with `triageResult` / `result`. |
| `session_store._in_progress_session_payload_unchanged` | Len + **`workflow_state` `!=`** + **`turns ==`** or **`json.dumps` ×2** | `prev` turns vs **`normalized_turns`** | Fast path avoids large serialization; **rare** **`json.dumps`** fallback = **heavy** when hit. |
| `session_store.save_in_progress_session` | Build **`row`**; noop check; **`repo.upsert_session(sid, row)`** default **`copy_payload=True`** | Full session document | Orchestrates persistence; row holds **aliased** `triageResult` until repo copy. |
| `session_repository._copy_row` / `upsert_session` | **`copy.deepcopy`** when **`copy_payload=True`** | Full **`payload`** | **Isolation fence** for PG + **`_MEMORY`**. |
| `session_repository.upsert_session` (Postgres) | **`Json(inner)`** on document | Serialized JSONB | Second pass over tree (after copy). |

---

## DEEPCOPY_COST_RESULTS

**Command:** `PYTHONPATH=. python3 scripts/measure_triage_copy_cost.py`

**Environment note:** Figures are **microbench** timings (noise ~μs–sub-ms); use as **order-of-magnitude**, not SLA.

### p50 / p95 / max (ms)

| Scenario | Turns | ~bytes | Operation | p50 | p95 | max |
|--------|------:|--------:|------------|---:|---:|---:|
| small | 3 | 1 970 | deepcopy(row) | 0.041 | 0.057 | 0.123 |
| small | 3 | 1 970 | deepcopy(last triageResult) | 0.028 | 0.041 | 0.067 |
| small | 3 | 1 970 | json.dumps(row) | 0.015 | 0.016 | 0.031 |
| small | 3 | 1 970 | _extract_workflow_state | 0.0008 | 0.0008 | 0.006 |
| small | 3 | 1 970 | _in_progress unchanged (hits ==) | 0.0003 | 0.0004 | 0.0004 |
| small | 3 | 1 970 | double json.dumps (parity upper bound) | 0.024 | 0.039 | 0.068 |
| medium | 20 | 13 391 | deepcopy(row) | 0.067 | 0.098 | 0.161 |
| medium | 20 | 13 391 | json.dumps(row) | 0.100 | 0.135 | 0.215 |
| medium | 20 | 13 391 | double json.dumps | 0.207 | 0.289 | 0.452 |
| large | 100 | 64 591 | deepcopy(row) | 0.181 | **0.250** | 0.410 |
| large | 100 | 64 591 | json.dumps(row) | 0.495 | **0.638** | 0.881 |
| large | 100 | 64 591 | double json.dumps | 0.996 | **1.208** | 2.611 |
| large_fat_blob | 100 | 217 359 | deepcopy(row) | 0.249 | **0.320** | 0.714 |
| large_fat_blob | 100 | 217 359 | json.dumps(row) | 1.667 | **1.957** | 2.546 |
| large_fat_blob | 100 | 217 359 | double json.dumps | 3.114 | **3.591** | 5.501 |

---

## MEASUREMENT_SUMMARY

| Operation | small p95 (ms) | medium p95 (ms) | large p95 (ms) | Conclusion |
|-----------|---------------:|----------------:|---------------:|-------------|
| deepcopy(row) | 0.057 | 0.098 | **0.250** | **Tiny** vs route `session_ms`; shared `triageResult` memo keeps **≤ ~0.25 ms** p95 at **100 turns / ~63 KiB**. |
| json.dumps(row) | 0.016 | 0.135 | **0.638** | Grows with turns / bytes; **~0.02–2.0 ms** p95 for sizes tested (**large_fat_blob** stretches JSON). |
| _in_progress noop (hits ==) | ~0.0004 | ~0.0004 | ~0.0004 | Negligible on hot path. |
| Double json.dumps (rare-parity upper bound) | 0.039 | 0.289 | 1.208 | **Only relevant** when contentious equality fires; ~**2×** single **`json.dumps(turns)`** cost. |

*(large_fat_blob: deepcopy **0.32** ms p95; json.dumps **1.96** ms p95 — still small versus **`session_ms` / HTTP** below.)*

---

## ROI_ANALYSIS

**Baselines** (external report: `results/HTTP_LATENCY_REDUCTION_REPORT.md`, turn-level p95):

- **`session_ms`** p95 ≈ **1 625 ms** (`get_in_progress_session`, analytics, **`patch_session_case_binding`**, **`save_in_progress_session`** combined).
- **HTTP** p95 (with LLM + assist context in that sprint) ≈ **7.6 s**; **`triage`** p95 ~ **2.7 s**.

**Estimated latency gain** from removing **only** full-document `deepcopy` + duplicated JSON work on the measured payload shapes:

| Shape | pessimistic persistence copy+json p95 | vs `session_ms` (1625 ms) |
|-------|--------------------------------------:|---------------------------:|
| large (100 turns / ~63 KiB) | ~**0.89 ms** (0.250 + 0.638) | **~0.05%** |
| large_fat_blob (~212 KiB) | ~**2.28 ms** (0.320 + 1.957) | **~0.14%** |

So **estimated end-user gain** through **snapshot optimization** alone is **sub-percent** of **`session_ms`**, and **negligible** versus **HTTP / triage** — unless sessions routinely reach **multi-MB** blobs (not evidenced here).

**Risk level** (if **`copy_payload=False`** without disciplined snapshots): **high** — aliasing, **`route_perf`** / **`conversation_id`** mutation after save, **analytics concurrency** (`TRIAGERESULT_COPY_DISCOVERY`).

**Complexity:** Medium–high for **safe** snapshots (distinct **`workflow_state`** deep isolation, tests below).

**Recommendation:** **Do not optimize purely for copy/cpu on current evidence** (# **A**). Revisit **B** only if profiler shows **`upsert_session` / serialization** dominates **`session_ms`** in production traces or payloads grow **an order of magnitude**.

---

## PERSISTENCE_SNAPSHOT_DESIGN (conditional — **not pursued** today)

Because **ROI is not material** at measured sizes, this is **not** a sprint deliverable — only a **bookmark** if data grows.

Proposed helper (signature illustrative):

```text
build_in_progress_session_snapshot(
    session_id: str,
    normalized_turns: list[dict],
    triage_result_live: dict,
    *,
    preserved_session_fields: dict | None,
) -> dict
```

**Principles**

- **Route `result`** remains the **live** response object; persistence receives an **isolated snapshot** document.
- **`workflow_state`** must be **deep-isolated** from **`triageResult`** (today shallow extract aliases interiors).
- **Last system turn `triageResult`** must be a **fresh deep copy** (or canonical JSON round-trip **only if** parity proven) — **never** the live **`result`** reference.
- **`route_perf`** / **`conversation_id`** timing: snapshot taken **before** or **after** fields per product contract — intentional and **test-covered** (currently deepcopy absorbs some drift).
- **Analytics:** background readers must **not** assume persistence dict is stable unless **immutable snapshot** semantics are documented; prefer **explicit copies for analytics** payloads if overlapping fields.

**Call site:** Immediately before **`repo.upsert_session`** inside **`save_in_progress_session`** (or a thin wrapper used only there).

**Outputs:** Repo-shaped **`row`** `{ session_id, turns, workflow_state, updated_at, … }` with **no shared mutable graph** between **`triage_result_live`** and stored JSON-bound tree.

**Tests needed:** See **FUTURE_SNAPSHOT_TEST_PLAN**.

---

## FUTURE_SNAPSHOT_TEST_PLAN

1. **Mutation-after-save:** After **`save_in_progress_session`**, mutate **`result["conversation_id"]`**, **`result["route_perf"]`**, and a nested **`collected_fields` list** → re-read session → persisted **`triageResult` / workflow** must match **snapshot contract** (either pre-mutation snapshot or intentional post-rules — asserted explicitly).
2. **`workflow_state` aliasing:** Assert **`workflow_state` keys** are not **`is`**-identical mutable containers to **`result`** internals after snapshot (e.g. list identity differs where required).
3. **`route_perf` timing:** Freeze clock or inject markers → assert **`triageResult`** persisted contains **expected** **`route_perf`** phase (unit-level contract table).
4. **Analytics concurrency:** Simulate concurrent read of persisted session vs route mutation (**thread**/**async**) — **no KeyError**, no partial-structure reads under chosen locking/clone policy (may stay best-effort with copy fence).
5. **Regression:** Existing **`tests/test_intake_session_persistence.py`** + **`PYTHONPATH=. pytest`** on inbox triage session tests.
6. **Performance benchmark:** Extend **`scripts/measure_triage_copy_cost.py`** or **`profile_live_latency.py`** to assert **`upsert_session` share of `session_ms`** before/after; fail CI only if sprint opts into a budget gate.

---

## FINAL_RECOMMENDATION

**Decision:** **A — `DO_NOT_OPTIMIZE_COPY_NOW`**

**Why:** Measured **full-row `deepcopy` + `json.dumps`** sits at **≲ ~0.9 ms p95** for **100-turn / ~64 KiB** payloads and **≲ ~2.3 ms** for a deliberate **fat** (~212 KiB) stress shape — **negligible** next to **`session_ms` (~1.6 s)** and **HTTP**.

**Expected gain:** **Sub-millisecond to low single-digit ms** per save — **not** proportional to **`session_ms`**.

**Expected risk of `copy_payload=False` without snapshots:** **High** versus **minimal observed CPU upside** here.

**Next move:** **No persistence snapshot sprint** from this evidence. Optionally add **production trace** keyed on **`route_perf`** / Postgres timings if contention appears; **`NEED_MORE_MEASUREMENT`** only if traces contradict this microbench at **much larger payloads**.

---

## TRIAGERESULT_DEEPCOPY_COST_REPORT — executive summary

- **Measured:** `deepcopy(row)` **p95 ~0.06–0.32 ms** (small → fat‑blob at 100 turns); **`json.dumps(row)` p95 ~0.02–2.0 ms**; helpers negligible.
- **ROI:** Persistence copy/serialization is **not material** versus **`session_ms` / HTTP p95** for shapes tested.
- **Snapshot design:** **Deferred** until evidence (profiler or payload growth) warrants taking **aliasing-risk** work.
- **Decision:** **`DO_NOT_OPTIMIZE_COPY_NOW`** (criteria **A**).

---

We measured before optimizing, and only pursue snapshot isolation if the copy cost justifies the aliasing risk.

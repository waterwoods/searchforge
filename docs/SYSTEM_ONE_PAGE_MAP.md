# Unified Intake — one-page map for humans

**Read time:** ~3 minutes.

---

## Architecture (text diagram)

```
[ Browser: Unified Intake UI ]
        |  POST /api/inbox/triage + session_id
        v
[ routes/inbox_triage.py ]
   ├─ session_store (turns / workflow)
   ├─ case_truth_repository (stub / bind / full)
   ├─ active_vehicle_request_cache_scope (1 PG read / request)
   ├─ triage_conversation (triage.py) ──► entity_repository (PG vehicle row)
   ├─ _finalize_response_with_pg_truth (PG → API mirror + reply finalize)
   ├─ optional: assist_layer (background thread, additive)
   └─ analytics / perf metrics
        |
        v
[ TriageResult JSON ] ──► customer copy + broker workbench
```

---

## 8 core facts

1. **Unified Intake** = minimal customer input → structured add-car (pilot) case → broker completes the rest.
2. **Postgres vehicle entity** is the authority for **`vehicle_key` / `primary_vehicle_summary`** when PG + session are in play.
3. **LLM** suggests triage JSON and assist copy; it **does not** own vehicle truth or write entities directly.
4. **Ambiguous multi-vehicle** turns **clarify**; they do not silently switch the active vehicle (see `AMBIGUITY_CLARIFY_CONTRACT.md`).
5. **Two case reads exist on purpose:** lightweight **stub** for speed vs **full** case — do not merge without profiling.
6. **`active_vehicle_resolver.py`** implements `resolve_add_car_active_vehicle` (**unit-tested**); **`triage.py` does not import it** today — add-car identity is triage + entity; API display still converges via **one** route finalizer from PG when configured (see `DEPRECATED_PATHS.md`).
7. **HTTP latency** is often **session + case + postprocess**, not only LLM — watch `route_perf`.
8. **UI Tab D** (scenario replay) is **QA/simulation**, not production funnel.

---

## 5 files to know

| File | Why |
|------|-----|
| `services/fiqa_api/routes/inbox_triage.py` | Request orchestration and PG identity mirror. |
| `services/fiqa_api/inbox_triage/triage.py` | Core triage engine (large but central). |
| `services/fiqa_api/inbox_triage/entity_repository.py` | Vehicle entity PG access. |
| `services/fiqa_api/inbox_triage/case_truth_repository.py` | Case read facade (PG vs JSON). |
| `ui/src/api/inboxTriage.ts` | Frontend contract for `TriageResult`. |

---

## 5 things not to touch casually

1. **PG truth + reply finalize** at end of triage route (`_finalize_response_with_pg_truth` only — do not duplicate).
2. **`get_case_triage_stub_for_read` vs `get_case_for_read`** split — performance contract.
3. **`field_strategy.json` + `field_strategy.py`** — drives blocking/deferral; not “docs only.”
4. **Funnel / `handoff_started` semantics** — analytics depend on definitions in `PRODUCT_TRUTH_DOCUMENT.md`.
5. **`active_vehicle_request_cache_scope`** — prevents N+1 PG reads per request.

---

## Next 5 best tasks

1. **Resolver + finalize** — wire `resolve_add_car_active_vehicle` into triage **or** remove the dead module; keep `_finalize_response_with_pg_truth` as the API identity mirror; extend tests when adding multi-vehicle phrasing.
2. **CI:** `scripts/ci_smoke.sh` (`import_smoke_check.py` + `guardrail_inbox_triage.sh`) runs on `ci-contract` — extend or split if guardrail runtime is too heavy for fast PR feedback.
3. **Route latency:** trim session/case/postprocess hot path (measure first).
4. **Analytics:** fix or gate **early_dropoff** noise on mid-session turns.
5. **UI:** split `UnifiedIntakePage.tsx` tabs into modules (readability; optional lazy-load Tab D).

# P19E-1.5 — Postgres Read Facade Hardening Evidence

**Date:** 2026-07-06  
**Branch:** `sprint/p16-trust-layer`  
**Deploy:** **NO** (STOP per sprint scope)

---

## Root cause

P19E-1 live smoke: Postgres binding found `case_id`, but subsequent hydration used JSON-only `get_case_by_id` → `None` on Cloud Run → `stale_draft_binding_cleared_v1` → generic greeting menu → Phase 2 handler skipped.

P19E-1 debug (`9cb7e5f`) fixed `slice.py` and `add_vehicle_phase2.py`. P19E-1.5 audits and hardens **all remaining** WeCom production read paths.

---

## Audit result

| Category | Count | Action |
|----------|-------|--------|
| Production WeCom modules calling `get_case_by_id` (pre) | 4 files, 6 call sites | All migrated to `get_case_for_read` |
| Already on facade | slice (post-9cb7e5f), phase2, h5 end card, h5_task_upload, inbox routes | No change |
| Test-only `get_case_by_id` | ~15 test files | Retained |
| Legacy JSON API | `case_store.get_case_by_id` | Retained with docstring guard |

---

## Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/wecom/active_case_bridge.py` | `get_case_for_read` for draft ingest + broker confirm read |
| `services/fiqa_api/wecom/media_intake.py` | `get_case_for_read` for lane hydration (3 sites) |
| `services/fiqa_api/wecom/minimal_lanes.py` | `get_case_for_read` for open-lane validation |
| `services/fiqa_api/wecom/slice.py` | Remove duplicate `get_case_for_read` import |
| `services/fiqa_api/inbox_triage/case_store.py` | Docstring: JSON-only, not production routing |
| `tests/test_p19e15_postgres_read_facade_hardening.py` | Guardrail + regression tests |
| `scripts/check_chen_kui_demo_environment.sh` | QA gate: limit=50 + merge demo rows from Cloud SQL when paginated off API page |
| `docs/p19e15_production_case_read_path_audit.md` | Architecture audit doc |

Prior commits in chain: `c252369` (P19E-1), `9cb7e5f` (slice/phase2 fix).

---

## Read path before / after

**Before (broken on Cloud Run):**

```
binding lookup → list_all_cases_for_read (Postgres) → case_id
hydrate        → get_case_by_id (JSON only)        → None
```

**After:**

```
binding lookup → list_all_cases_for_read (Postgres) → case_id
hydrate        → get_case_for_read (Postgres-first) → full case
```

---

## Tests / build

```bash
PYTHONPATH=. python3 -m pytest tests/test_p19e1_*.py -q
PYTHONPATH=. python3 -m pytest tests/test_p19e15_postgres_read_facade_hardening.py -q
PYTHONPATH=. python3 -m pytest tests/test_wecom_minimal_lanes.py tests/test_wecom_intent.py \
  tests/test_wecom_slice.py tests/test_wecom_active_case.py tests/test_wecom_reply.py \
  tests/test_wecom_identity_b0_extractors.py -q
PYTHONPATH=. python3 -m pytest tests/test_h5_task_token.py tests/test_h5_single_slot_upload.py -q
PYTHONPATH=. python3 -m pytest tests/test_h5_add_vehicle_photo_flow.py -q
PYTHONPATH=. python3 -m pytest tests/test_wecom_upload_guardrail.py tests/test_wecom_media_intake.py \
  tests/test_workbench_attachment_api.py -q
cd ui && npm run build && cd ..
```

(Fill pass counts after run — see commit message / CI.)

| Suite | Result |
|-------|--------|
| `tests/test_p19e1_*.py` | 25 passed |
| `tests/test_p19e15_postgres_read_facade_hardening.py` | 9 passed |
| WeCom suite (minimal_lanes, intent, slice, active_case, reply, identity) | 107 passed |
| `tests/test_h5_task_token.py` + `test_h5_single_slot_upload.py` | 17 passed |
| `tests/test_h5_add_vehicle_photo_flow.py` | 15 passed |
| upload_guardrail + media_intake + workbench_attachment | 56 passed |
| `ui npm run build` | PASS |

---

## QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

- Cloud SQL: `caseiq` @ `10.73.0.3` (private VPC)
- Secret: `fiqa-service-record-database-url-cloudsql-private`
- Neon: not QA truth
- Result: **PASS** (pagination drift fixed in check script — live WeCom smoke cases pushed demo rows off `limit=20` page; unrelated to read-path code)

---

## Constraints checklist

| Constraint | Status |
|------------|--------|
| No OCR | ✅ |
| No LLM / vision extraction | ✅ |
| No schema migration | ✅ |
| No Cloud SQL / VPC / Secret / callback change | ✅ |
| No Neon as truth | ✅ |
| No deploy | ✅ STOP |

---

## GO / HOLD for deploy

| Gate | Verdict |
|------|---------|
| Code + tests locally | **GO** (pending full suite in §Tests) |
| Cloud deploy + P19E-1 phone retest | **HOLD** — deploy not executed this sprint |

**Next:** Deploy revision with P19E-1.5 commits → rerun P19E-1 Phase 2 live smoke (Andy message: delivery date + zip + phone).

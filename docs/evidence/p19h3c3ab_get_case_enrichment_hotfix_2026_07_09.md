# P19H-3c-3AB — GET Case Enrichment Hotfix

**Date:** 2026-07-09  
**Branch:** `sprint/p16-trust-layer`  
**Scope:** Backend hotfix only — no schema, no frontend change, no new business rules

---

## 1. Problem

After P19H-3c-3AB deploy (`fiqa-api-00172-4hw` + `ui-smoky-beta`):

- `GET /api/inbox/cases` (list) returned `claim_evidence_summary` for Claim cases
- `GET /api/inbox/cases/{case_id}` (single) did **not** enrich Claim cases
- Workbench drawer calls `getSavedCase()` after list stub → enriched data overwritten
- Drawer showed fallback: **理赔照片状态暂未生成**

Production Claim case: `case_b8d15b3ca59a`

---

## 2. Root cause

| Route | Enrichment |
|-------|------------|
| `GET /api/inbox/cases` | Calls `enrich_cases_for_workbench()` then `sanitize_case_for_workbench_api()` |
| `GET /api/inbox/cases/{case_id}` | Only `sanitize_case_for_workbench_api()` on raw case |

`PATCH /cases/{case_id}/workbench` already enriched; single GET was the outlier.

Frontend `DocumentIntakeInboxPage.openCase()`:

1. Sets detail from list row (enriched)
2. Fetches `getSavedCase(caseId)` → overwrites without enrichment

---

## 3. Fix

In `get_saved_case()` (`services/fiqa_api/routes/inbox_triage.py`):

```python
enriched = enrich_cases_for_workbench([case])
case = enriched[0] if enriched else case
return sanitize_case_for_workbench_api(case)
```

Same enrichment path as list API. No rule changes — wiring only.

---

## 4. Changed files

| File | Change |
|------|--------|
| `services/fiqa_api/routes/inbox_triage.py` | Enrich single-case GET before sanitize |
| `tests/test_p19h3c3ab_get_case_enrichment_parity.py` | **NEW** — 4 parity tests |

**Hotfix commit:** `83747a4` — `fix: enrich single Claim case response for Workbench drawer`

---

## 5. Tests

| Suite | Result |
|-------|--------|
| `test_p19h3c3ab_get_case_enrichment_parity.py` | PASS (4/4) |
| `test_p19h3c3a_claim_evidence_summary_backend.py` | PASS (8/8) |
| `test_p19h3a_claim_workbench_visibility.py` | PASS (8/8) |
| `test_p19h3c1_claim_h5_evidence_foundation.py` | PASS (12/12) |
| `test_p19h3c2_claim_c1_h5_button.py` | PASS (8/8) |
| `pytest -k h5` | PASS |
| Pre-deploy QA gate | PASS |

Test coverage:

1. Claim single GET includes `claim_evidence_summary` with H5 damage received
2. List vs single parity on enrichment keys
3. Add Vehicle single GET unaffected
4. Claim without attachments still returns 3 missing slots

---

## 6. Backend deploy

| Field | Value |
|-------|-------|
| Script | `bash scripts/deploy_paid_pilot.sh` |
| **Revision** | **`fiqa-api-00173-n7k`** |
| **URL** | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| **GIT_SHA** | `83747a45d` |
| `/health/live` | **200** |
| `/readyz` | **200** |
| Frontend redeploy | **Not needed** (no frontend change) |

---

## 7. Post-deploy QA gate

```bash
bash scripts/check_chen_kui_demo_environment.sh --cloud-api
```

**Result: PASS**

---

## 8. Production API smoke

Case: `case_b8d15b3ca59a`

| Check | Result |
|-------|--------|
| List `claim_evidence_summary` | **YES** |
| Single GET `claim_evidence_summary` | **YES** |
| Slots length | **3** |
| `broker_next_action` | YES |
| `summary_text` | YES |
| `claim_summary` | YES |
| `display_status` | YES |

---

## 9. Frontend Workbench smoke

| Check | Result |
|-------|--------|
| `https://ui-smoky-beta.vercel.app/workbench/document-intake` | **HTTP 200** |
| Browser automation — Claim drawer | **PASS** |

Drawer content verified (Claim row, `case_b8d15b3ca59a`):

- ✅ **理赔照片 / Evidence Checklist** visible
- ✅ 自己车损照片 · 已收到 · H5 上传 · 1 张
- ✅ 对方车辆 / 车牌照片 · 已收到
- ✅ 现场照片 · 已收到
- ✅ **下一步建议** — 资料已基本齐全，请陈总人工确认后决定下一步。
- ❌ Fallback **理赔照片状态暂未生成** — **not present**

---

## 10. Log check

Revision `fiqa-api-00173-n7k`:

- No `claim_evidence_summary` / enrichment / Workbench 500 errors
- Expected optional: Qdrant, Redis, embedding warmup, langgraph disabled

---

## 11. Constraints honored

| Constraint | Status |
|------------|--------|
| No schema change | ✅ |
| No frontend change | ✅ |
| No Claim evidence rule change | ✅ |
| No H5 persistence | ✅ |
| No WeCom binding | ✅ |
| No identity resolver | ✅ |

---

## 12. Manual Andy check (optional confirm)

Open: https://ui-smoky-beta.vercel.app/workbench/document-intake

Open Claim case (今天上午10点 · Irvine Blvd row).

Expected: Evidence Checklist + 下一步建议 (automation already confirmed).

---

## 13. GO / HOLD

**GO** — Hotfix deployed; list + single GET parity restored; Workbench drawer shows checklist.

---

## 14. Next recommended sprint

1. Optional Andy quick visual confirm
2. **P19H-3c-3C** — H5 Slot Persistence / Skip Reason
3. **P19H-3c-R3** — Claim Identity Resolver Foundation

**STOP**

# P16-Z13 Phase 5 — Preview Validation

**Date:** 2026-06-02

---

## URLs

| Surface | URL |
|---------|-----|
| **Preview** | https://ui-o6ipsmqzv-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| **Backend** | https://fiqa-api-g7zatxrycq-uw.a.run.app |

---

## Connected?

**YES**

- Vercel build: `VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app`
- Vercel build: `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` = same value as Cloud Run intake key (not printed)
- CORS: Preview origin on revision `fiqa-api-00083-kng`
- Backend git: `b0d6073e5` (Z10A/Z10B/Z11 code on branch HEAD)

---

## Office value fields (API probe, case 2 paste)

`POST /api/inbox/triage` with intake key:

| Field | Present? |
|-------|----------|
| `office_case_title` | ✅ `客户卖车，需要从保单移除车辆` |
| `office_broker_next_step` | ✅ |
| `classification_signals` | ✅ |
| `suggested_waiting_on` | ✅ `client` |

---

## Print

| Field | Value |
|-------|-------|
| **Preview URL** | https://ui-o6ipsmqzv-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| **Backend URL** | https://fiqa-api-g7zatxrycq-uw.a.run.app |
| **Connected** | **YES** |

**Note:** Older Preview URL `ui-d7pyq2yau` still loads but is **not** the Z13 bundle (no intake key in JS). Use `ui-o6ipsmqzv` for founder testing.

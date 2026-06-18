# P16 Phone Lookup Recovery

**Sprint:** P16-PHASE1-PHONE-LOOKUP-RECOVERY  
**Date:** 2026-06-07

---

## 1. Local Endpoint Location

| Piece | Path |
|-------|------|
| Route | `services/fiqa_api/routes/inbox_triage.py` — `@router.get("/customer/active-case")` |
| Lookup logic | `services/fiqa_api/inbox_triage/active_case_lookup.py` |
| Phone normalize | `services/fiqa_api/inbox_triage/phone_normalization.py` |
| Case scan | `services/fiqa_api/inbox_triage/case_truth_repository.py` — `list_cases_for_phone_lookup` |
| UI client | `ui/src/api/inboxTriage.ts` — `lookupActiveCaseByPhone` (GET) |
| Tests | `tests/test_active_case_by_phone.py` — 3/3 pass |

**Note:** Endpoint is **GET** with `?phone=` query param, not POST. Frontend and simulations use GET.

---

## 2. Cloud Run Gap (before fix)

| Check | Before `fiqa-api-00086-f95` |
|-------|----------------------------|
| `GET /api/inbox/customer/active-case?phone=6265550101` | **404** `{"detail":"Not Found"}` |
| Revision | `fiqa-api-00085-tn2` |
| Cause | `active_case_lookup.py` + routes uncommitted; not in deployed image |

---

## 3. Deploy Applied

```bash
bash scripts/deploy_paid_pilot.sh
```

| Field | Value |
|-------|-------|
| New revision | `fiqa-api-00086-f95` |
| Service | `fiqa-api` (us-west1) |
| Traffic | 100% to new revision |

---

## 4. API Verification

**Backend URL:** `https://fiqa-api-g7zatxrycq-uw.a.run.app`

```bash
curl -sS -H "X-Unified-Intake-Api-Key: <key>" \
  "https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/customer/active-case?phone=6265550101"
```

**Response (HTTP 200):**

```json
{"has_active_case":false,"phone_normalized":"6265550101","active_case":null}
```

---

## 5. Customer First UI Verification

**Preview:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer`

| Step | Result |
|------|--------|
| Enter phone `6265550101` | ✅ |
| Click Continue / 继续 | ✅ |
| Error `无法验证手机号，请稍后再试` | **Absent** |
| Next screen | **Start New Add-Car Request** + 继续办理加车 |

**Phone lookup flow: RESTORED**

---

*End of recovery report*

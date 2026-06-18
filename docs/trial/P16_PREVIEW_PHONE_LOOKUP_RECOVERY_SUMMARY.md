# P16 Preview Phone Lookup Recovery — Founder Summary

**Sprint:** P16-PREVIEW-ACTIVE-CASE-API-KEY-RECOVERY  
**Date:** 2026-06-07  
**For:** Andy

---

## 1. What caused “无法验证手机号”?

Clicking Continue calls Cloud Run:

`GET /api/inbox/customer/active-case?phone=…`

Cloud Run requires `X-Unified-Intake-Api-Key` on all `/api/inbox/*` routes. The Preview bundle from the **router recovery deploy** had the correct API base URL but an **empty** intake API key, so every lookup returned **401** `intake_api_unauthorized`. The UI treats any API failure as “无法验证手机号，请稍后再试。”

---

## 2. Was the API key missing from Preview?

**Yes.** The broken bundle baked `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` as an empty string.

---

## 3. Was it Production-only?

**No** — the key is **not in the Vercel dashboard at all** (Production, Preview, or Development). Preview builds depend on the operator passing `-b VITE_UNIFIED_INTAKE_INTAKE_API_KEY=…` at `vercel deploy` time (documented in prior P16 deploy reports). The router-recovery deploy omitted that flag.

---

## 4. Was Cloud Run healthy?

**Yes.** Route exists, CORS works, `/health` reports `api_key_required`. Without key → 401. With key → 200. Not a backend outage.

---

## 5. What was fixed?

Redeployed Preview with full build flags (product-only, supervised demo, Cloud Run URL, **intake API key from `.env.cloudrun`**), then re-pointed `ui-waterwoods` alias.

No UI, constitution, database, or backend code changes.

---

## 6. Which Preview URL should Andy use?

https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

Direct deployment URL (same build):  
https://ui-2o9zpj0u5-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

Deployment `dpl_BKUCFQnAst7QVoYiZmAscPcaZzjB` · Bundle `index-Bb0VZ9fA.js`

---

## 7. Is Customer First demo now ready?

**Yes for phone lookup and tab navigation.** Continue works; active-case returns 200; Office and Simulation tabs load.

**Note:** Phone `2039935973` currently has a seeded active case in Postgres — Continue shows the active-case card, not “Start New.” Use a fresh 10-digit phone for the cold-start path.

---

## Related docs

| Doc | Purpose |
|-----|---------|
| `P16_PREVIEW_PHONE_LOOKUP_NETWORK_AUDIT.md` | Browser/curl 401 evidence |
| `P16_PREVIEW_ENV_AUDIT.md` | Vercel env presence/absence |
| `P16_BACKEND_ACTIVE_CASE_AUTH_AUDIT.md` | Cloud Run auth matrix |
| `P16_PREVIEW_PHONE_LOOKUP_REDEPLOY_REPORT.md` | Deploy record |
| `P16_PREVIEW_PHONE_LOOKUP_LIVE_CERTIFICATION.md` | Post-fix live tests |

---

FINAL_SAFE_QA_PREVIEW_URL:
https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

VERDICT:
GO

---

*End of P16 Preview Phone Lookup Recovery Summary*

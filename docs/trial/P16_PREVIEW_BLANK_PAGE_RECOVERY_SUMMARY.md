# P16 Preview Blank Page — Recovery Summary

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07  
**For:** Andy (founder)

---

## 1. What broke?

The Customer Status Simplification deploy (`7ede46d`) shipped a **JavaScript ReferenceError** that prevented React from mounting. The page showed a white screen with an empty `#root` div.

---

## 2. Why did the page go blank?

In `customerFirstEntry.ts`, the new status field label map used `...ADD_CAR_FIELD_LABELS` but **forgot to import it**. The error fires at module load time — before any UI, router, or API call runs.

---

## 3. Was the backend involved?

**No.** Cloud Run API was healthy. No backend change required for this fix.

---

## 4. Was Cloud Run involved?

**No** for the blank page. Cloud Run is still the API target for phone lookup and triage (working on the certified alias).

---

## 5. Was Vercel env involved?

**No.** The broken deployment had all required build flags (`VITE_API_BASE_URL`, intake API key, product-only, supervised demo). Env was correct; code was wrong.

---

## 6. What was fixed?

One-line import added:

```typescript
import { ADD_CAR_FIELD_LABELS } from '@/features/intake/constants';
```

Redeployed Preview with full env flags and re-pointed `ui-waterwoods` alias.

---

## 7. Which URL should Andy use now?

**Use the stable alias (not the per-deploy hash URL):**

https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

Per-deploy URLs like `ui-r4si9tqyh-…` or `ui-6hc7cfoxk-…` may fail phone lookup due to Cloud Run CORS whitelist (only `ui-waterwoods` is allowed).

---

## Artifacts

| Doc | Purpose |
|-----|---------|
| `P16_PREVIEW_BLANK_PAGE_BROWSER_AUDIT.md` | Live browser diagnosis |
| `P16_PREVIEW_BLANK_PAGE_DEPLOY_AUDIT.md` | Vercel deployment comparison |
| `P16_PREVIEW_BLANK_PAGE_CODE_AUDIT.md` | Code regression root cause |
| `P16_PREVIEW_BLANK_PAGE_LOCAL_REPRO.md` | Local build reproduction |
| `P16_PREVIEW_BLANK_PAGE_REDEPLOY_REPORT.md` | Fix deploy record |
| `P16_PREVIEW_BLANK_PAGE_LIVE_CERTIFICATION.md` | QA sign-off matrix |

---

FINAL_SAFE_PREVIEW_URL:
https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

VERDICT:
GO

---

*End of P16 Preview Blank Page Recovery Summary*

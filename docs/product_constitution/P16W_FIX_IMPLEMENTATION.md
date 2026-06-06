# P16-W Phase 6 — Fix Implementation

**Date:** 2026-06-01

---

## Fix applied

**Option A** — restored missing import in broker workbench tab.

```diff
 import {
     getCaseTrackingSummary,
+    getCompactQueuePreview,
     getDraftReadinessLabel,
```

---

## Files changed

| File | Change |
|------|--------|
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | +1 import line |

No other files modified in fix commit.

---

## Commit

| Field | Value |
|-------|-------|
| Hash | `b0d6073` |
| Branch | `sprint-a/broker-front-door` |
| Message | `fix(ui): restore missing getCompactQueuePreview import in broker workbench` |

---

## Deploy

| Field | Value |
|-------|-------|
| Command | `vercel deploy --yes -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Deployment | `dpl_8ydHn7c9igGs1p45V5hrKD38kdbH` |
| Preview URL | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| New bundle | `index-OFXnRnil.js` |

---

## Why safe

1. **Exact parity** with pre-extraction `UnifiedIntakePage.tsx` import list.
2. **No behavior change** — only binds an existing exported function.
3. **No API / backend / config** changes.
4. **Guardrail PASS** unchanged after fix.
5. **Build PASS** on Vercel (46s) and locally with Node 22.22.0.

---

*End of P16-W Phase 6*

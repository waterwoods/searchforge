# P16 QA Router Deploy Report

**Sprint:** P16-QA-PREVIEW-ROUTER-RUNTIME-RECOVERY  
**Date:** 2026-06-07

---

## Deployment

| Field | Value |
|-------|-------|
| **Deployment ID** | `BXKreBJjZXVvABKnLXaUjfUkoxbW` |
| **Preview URL** | https://ui-rj27hhjeh-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer |
| **Bundle hash** | `index-CMdMnAqV.js` |
| **Deploy timestamp** | 2026-06-07 (Vercel CLI prebuilt deploy) |
| **Status** | Ready ✅ |

---

## Build flags (QA Preview)

```bash
VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app
VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1
VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1
```

---

## Broken deployment (do not use)

| Field | Value |
|-------|-------|
| URL | https://ui-emtvr6y44-andys-projects-1f411b73.vercel.app/... |
| Bundle | `index-CfDJTcYx.js` |
| Issue | React Router crash — `<LabRoutes />` invalid child |

---

## Code change

`ui/src/App.tsx` line 74: `<LabRoutes />` → `{LabRoutes()}`

---

*End of P16 QA Router Deploy Report*

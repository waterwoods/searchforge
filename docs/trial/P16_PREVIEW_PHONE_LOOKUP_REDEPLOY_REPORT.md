# P16 Preview Phone Lookup — Redeploy Report

**Sprint:** P16-PREVIEW-ACTIVE-CASE-API-KEY-RECOVERY  
**Date:** 2026-06-07

---

## Fix applied

**Option B** (consistent with `P16_PREVIEW_DEPLOY_REPORT.md`): redeploy Preview with CLI build flags, sourcing key from gitignored `.env.cloudrun`.

```bash
cd ui
source ../scripts/with_node22_path.sh
set -a && source ../.env.cloudrun && set +a

vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY="${UNIFIED_INTAKE_INTAKE_API_KEY}"

vercel alias set ui-2o9zpj0u5-andys-projects-1f411b73.vercel.app \
  ui-waterwoods-andys-projects-1f411b73.vercel.app
```

**Not done:** Option A (add key to Vercel Preview dashboard) — deferred; `-b` matches established operator playbook and avoids storing frontend-baked secret in dashboard unless requested.

**Production:** Not touched. No `vercel --prod`.

---

## Deployment record

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_BKUCFQnAst7QVoYiZmAscPcaZzjB` |
| **Preview URL** | https://ui-2o9zpj0u5-andys-projects-1f411b73.vercel.app |
| **Alias (canonical)** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Workbench path** | `/workbench/unified-intake?tab=customer` |
| **Bundle hash** | `index-Bb0VZ9fA.js` |
| **Timestamp** | Sun Jun 07 2026 06:19:11 PDT |
| **Status** | Ready ✅ |
| **Target** | Preview |

---

## Bundle verification (post-fix)

| Check | Result |
|-------|--------|
| `VITE_API_BASE_URL` in bundle | ✅ `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| Intake API key in bundle | ✅ present (length 48 chars; value not logged) |
| Pre-fix bundle superseded | ✅ `index-CMdMnAqV.js` → `index-Bb0VZ9fA.js` |

---

## Superseded deployment

| Field | Value |
|-------|-------|
| Deployment ID | `dpl_BXKreBJjZXVvABKnLXaUjfUkoxbW` (router recovery) |
| Bundle | `index-CMdMnAqV.js` |
| Issue | Missing `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` → phone lookup 401 |

---

*End of P16 Preview Phone Lookup Redeploy Report*

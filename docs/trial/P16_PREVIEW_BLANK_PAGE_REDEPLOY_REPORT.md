# P16 Preview Blank Page — Redeploy Report

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07

---

## Fix

Added missing import in `ui/src/features/intake/utils/customerFirstEntry.ts`:

```typescript
import { ADD_CAR_FIELD_LABELS } from '@/features/intake/constants';
```

---

## Deploy command

```bash
cd ui
source ../scripts/with_node22_path.sh
set -a && source ../.env.cloudrun && set +a

vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY="${UNIFIED_INTAKE_INTAKE_API_KEY}"

vercel alias set ui-r4si9tqyh-andys-projects-1f411b73.vercel.app \
  ui-waterwoods-andys-projects-1f411b73.vercel.app
```

---

## Deployment record

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_7LuRLamWCHoEo5xVNie1TvFmtk7Q` |
| **Preview URL** | https://ui-r4si9tqyh-andys-projects-1f411b73.vercel.app |
| **Canonical alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Workbench path** | `/workbench/unified-intake?tab=customer` |
| **Bundle hash** | `index-Bs99AAgT.js` |
| **Status** | Ready ✅ |
| **Target** | Preview |
| **Build duration** | ~42s |

---

## Env verification (post-fix bundle)

| Check | Result |
|-------|--------|
| `VITE_API_BASE_URL` | ✅ Cloud Run URL baked |
| Intake API key | ✅ Present (48 chars; not logged) |
| Product-only UI | ✅ Active |
| Supervised demo | ✅ Simulation tab enabled |
| Bare `ADD_CAR_FIELD_LABELS` | ✅ Absent from bundle |

---

## Superseded broken deployment

| Field | Value |
|-------|-------|
| Deployment ID | `dpl_CbuPKUzBoL8oEWsXyqK1sQmavr9b` |
| URL | https://ui-6hc7cfoxk-andys-projects-1f411b73.vercel.app |
| Bundle | `index-BxgUOLwB.js` |
| Issue | Missing import → blank page |

---

*End of P16 Preview Blank Page Redeploy Report*

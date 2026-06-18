# P16 Preview Blank Page — Deploy Audit

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07

---

## Broken deployment (reported)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_CbuPKUzBoL8oEWsXyqK1sQmavr9b` |
| **Preview URL** | https://ui-6hc7cfoxk-andys-projects-1f411b73.vercel.app |
| **Bundle hash** | `index-BxgUOLwB.js` |
| **CSS hash** | `index-D2fAzD03.css` |
| **Status** | Ready (serving broken JS) |
| **Created** | 2026-06-07 ~08:21 PDT |
| **Source commit** | `7ede46d` — Customer Status Simplification |
| **Build duration** | ~39s |
| **Alias at time of break** | `ui-waterwoods` pointed here → **alias also blank** |

---

## Last known working Preview (pre-regression)

| Field | Value |
|-------|-------|
| **Alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Prior good deployment** | `dpl_BKUCFQnAst7QVoYiZmAscPcaZzjB` |
| **Prior good bundle** | `index-Bb0VZ9fA.js` |
| **Notes** | Phone lookup + Customer First worked (P16 phone lookup recovery sprint) |

---

## Environment variables (broken build — presence only)

Verified via bundle inspection of `index-BxgUOLwB.js`:

| Variable | Present in bundle? | Notes |
|----------|-------------------|-------|
| `VITE_API_BASE_URL` | ✅ Yes | `https://fiqa-api-g7zatxrycq-uw.a.run.app` |
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | ✅ Yes | 48-char key baked (value not logged) |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | ✅ Yes | Product-only route surface active |
| `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO` | ✅ Yes | Simulation tab enabled |

**Conclusion:** Blank page was **not** caused by missing Vercel env vars. Build flags were correct; JS reference error caused the regression.

---

## Fixed deployment (recovery)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_7LuRLamWCHoEo5xVNie1TvFmtk7Q` |
| **Preview URL** | https://ui-r4si9tqyh-andys-projects-1f411b73.vercel.app |
| **Canonical alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Bundle hash** | `index-Bs99AAgT.js` |
| **Status** | Ready ✅ |
| **Fix** | Import `ADD_CAR_FIELD_LABELS` in `customerFirstEntry.ts` |

---

## Build log summary (fixed deploy)

- Node: Vercel auto-selected per `engines.node >=22.22.0`
- Vite build: 6320 modules, ~35s
- No build-time errors (ReferenceError is runtime-only; Vite does not evaluate const spread at build time for undefined bare identifiers in all paths)

---

*End of P16 Preview Blank Page Deploy Audit*

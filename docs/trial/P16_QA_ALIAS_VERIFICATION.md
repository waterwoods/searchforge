# P16 QA Alias Verification

**Date:** 2026-06-07  
**Sprint:** P16-FINAL-QA-CERTIFICATION  
**Method:** curl + Vercel CLI (no browser MCP)

---

## Expected URL

https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

---

## Deployment

| Field | Value |
|-------|-------|
| **Alias** | `ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| **Deployment ID** | `dpl_7LuRLamWCHoEo5xVNie1TvFmtk7Q` |
| **Deployment URL** | `https://ui-r4si9tqyh-andys-projects-1f411b73.vercel.app` |
| **Status** | ● Ready |
| **Target** | Preview |
| **Fix commit** | `366a7d6` (import restore; bundle deployed pre-commit from same source fix) |

---

## curl verification

| Check | Command | Result |
|-------|---------|--------|
| Workbench HTTP | `curl -sI …/workbench/unified-intake?tab=customer` | **HTTP 200** |
| Bundle hash | `curl -s …/ \| grep index-*.js` | **`index-Bs99AAgT.js`** (post-fix bundle) |
| Cloud Run API | `curl …/health` | **HTTP 200** |
| API base in bundle | grep `fiqa-api-g7zatxrycq-uw.a.run.app` | **Present** |
| Intake API key marker | grep `X-Unified-Intake-Api-Key` in bundle | **Present** (value not logged) |

---

## Alias correctness

`vercel inspect ui-waterwoods-andys-projects-1f411b73.vercel.app` resolves to deployment `dpl_7LuRLamWCHoEo5xVNie1TvFmtk7Q` — the redeploy that includes the `ADD_CAR_FIELD_LABELS` import fix.

Superseded broken bundle: `index-BxgUOLwB.js` (ReferenceError white screen).

---

## Operator rule

Use **`ui-waterwoods` alias only** for QA and broker demos. Per-hash deployment URLs may fail Cloud Run CORS / phone lookup.

---

## Verdict

**PASS** — QA alias is ready, serves fixed bundle, API reachable.

---

*End of P16 QA Alias Verification*

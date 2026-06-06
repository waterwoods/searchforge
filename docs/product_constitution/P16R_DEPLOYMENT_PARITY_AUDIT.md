# P16-R Phase 2 — Deployment Parity Audit

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Baseline commits:** `901b0df` (P16-I) → `d05e94d` (P16-O)

---

## Exact parity matrix

Legend: ✅ deployed · 🟡 partial / bypass only · ❌ absent · 🔒 blocked (SSO)

| Change / artifact | Local `d05e94d` | Branch pushed | Preview `ui-iwnyo9ufa` | Production `ui-smoky-beta` |
|-------------------|-----------------|---------------|------------------------|----------------------------|
| **P16-I broker workbench simplification** | ✅ | ✅ `origin/sprint-a/broker-front-door` | ✅ bundle grep | ❌ |
| **Sprint A broker front door (`c2e3dff`)** | ✅ | ✅ | ✅ | 🟡 partial strings only |
| **P16-O customer message-first empty state** | ✅ | ✅ (P16-R commit) | ✅ bundle grep | ❌ |
| **`portal_message_first_*` ui_copy keys** | ✅ | ✅ | ✅ (in JS bundle) | ❌ |
| **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`** | ✅ | N/A | ✅ build `-b` | ❌ live bundle |
| **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY` Vercel dashboard** | N/A | N/A | ❌ Preview (no Git link) | 🟡 Production added, **not redeployed** |
| **`VITE_API_BASE_URL` Preview dashboard** | N/A | N/A | ❌ | ✅ Production only |
| **Hide customer/simulation tabs (runtime)** | ✅ | ✅ | ✅ (flag baked) | ❌ |
| **`?tab=broker` routing fix** | ✅ | ✅ | ✅ (product_only) | ❌ |
| **Cloud Run CORS for Preview hash URL** | N/A | N/A | ✅ `ui-iwnyo9ufa` (P16-R patch) | ✅ smoky-beta |
| **Vercel Deployment Protection** | N/A | N/A | 🔒 401 cold | ✅ prod alias open |
| **Constitution V1** | ✅ | ✅ | ✅ (code) | ✅ (code not UI) |
| **Guardrail inbox triage** | ✅ PASS | ✅ | ✅ API | ✅ API |

---

## Which commits are actually deployed?

| Surface | Evidence of deployed commit | Confidence |
|---------|----------------------------|------------|
| **Local** | `d05e94d` | **100%** — `git rev-parse HEAD` |
| **Preview latest** | P16-O strings in `index-CKPYkrkL.js`; deploy after push `d05e94d` | **High (~90%)** — Vercel does not print git SHA |
| **Preview previous** | No P16-O strings; created before P16-O commit | **High** — `901b0df` era |
| **Production** | Bundle `index-ctrXdUgj.js`; deploy **41 days** old | **High** — pre–Sprint A UI |

---

## Sprint changes only locally (at sprint start)

| Item | Status after P16-R Phase 8 |
|------|----------------------------|
| P16-O `CustomerEntryTab` | **Committed `d05e94d`** — was uncommitted at P16-Q |
| `ui_copy.json` P16-O keys | **Committed** |
| `UnifiedIntakePage` trial tab routing | **Committed** |
| Mass unrelated working-tree edits | **Still uncommitted** — out of P16-R scope |

---

## Sprint changes only in branch (not Production)

| Item | In Preview latest? | In Production? |
|------|-------------------|----------------|
| P16-I | ✅ | ❌ |
| P16-O | ✅ | ❌ |
| Sprint A product_only | ✅ (CLI) | ❌ |
| P16-N customer improvements (if any on branch) | ✅ code path | ❌ |

---

## Deploy lineage (frontend)

```
66f7ed5 Constitution V1
    → c2e3dff Sprint A broker front door
        → 901b0df P16-I broker UI
            → d05e94d P16-O customer entry  ← LOCAL + PREVIEW (latest)
                → Production still on ~Apr 21 deploy (pre-Sprint A)
```

---

## Parity verdict (Phase 2)

| Pair | Equal? |
|------|--------|
| Local ↔ Preview (bundle) | **🟡 Near** — P16-O + P16-I match; SSO + env persistence differ |
| Local ↔ Preview (cold URL) | **❌ No** — 401 vs localhost |
| Preview ↔ Production | **❌ No** — ~6 weeks UI drift |
| Local ↔ Production | **❌ No** |

**Critical gap:** Production promotion **not executed** (per mission). Preview env vars **not dashboard-persisted** for Preview environment.

---

*End of P16-R Phase 2 — Deployment Parity Audit*

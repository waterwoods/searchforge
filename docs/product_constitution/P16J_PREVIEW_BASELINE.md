# P16-J Preview Baseline

**Date:** 2026-05-31  
**Sprint:** P16-J — Founder Preview Acceptance  
**Authority:** P16-I rescoring, P16-G deployment truth, `CURRENT_PRODUCT_SHAPE.md`

---

## Inventory

| Field | Value |
|-------|-------|
| **Branch** | `sprint-a/broker-front-door` |
| **Commit** | `901b0dfaee67c4e954a0d866a7a5675cfbeb4836` |
| **Commit message** | `P16-I simplify product-only intake UI` |
| **Local Preview URL** | http://127.0.0.1:5173/workbench/unified-intake |
| **Local API** | http://127.0.0.1:8001 |
| **Vercel Preview URL (documented)** | https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake |
| **Preview alias** | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| **Production URL** | https://ui-smoky-beta.vercel.app/workbench/unified-intake |
| **Remote API (Preview builds)** | https://fiqa-api-g7zatxrycq-uw.a.run.app |

---

## Build flags (required for Sprint A + P16-I UI)

| Variable | Local demo | Vercel Preview (dashboard) | Production |
|----------|------------|----------------------------|------------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` | ✅ via `run_demo_local.sh` | ⚠️ CLI-injected on last deploy; not persisted in dashboard |
| `VITE_API_BASE_URL` | ✅ localhost:8001 | ✅ Cloud Run (CORS patched P16-G) | ✅ encrypted |

**Local start:** `bash scripts/run_demo_local.sh` → product_only on 8001 + UI 5173.

---

## Current capability scores (P16-I authority)

| Metric | Score | Target | Met? |
|--------|-------|--------|------|
| UI Simplicity | **76** | ≥75 | ✅ |
| Capability 1 — Broker Front Door | **79** | ≥78 | ✅ |
| Capability 4 — Customer Intake | **68** | — | Tab hidden in trial |
| Capability 6 — Trial Conversion (inferred) | **62** | ≥60 | ✅ |
| **Overall Product** | **74** | 72–75 | ✅ |
| Engine / Triage (unchanged) | **85–90** | — | ✅ |

Constitution V1 baseline (pre-sprint): Overall **60** — historical only.

---

## Validation state (2026-05-31)

| Check | Result |
|-------|--------|
| `guardrail_inbox_triage.sh` | **PASS** |
| `run_inbox_triage_scenarios.py` | **64/64 PASS** (rules fallback; OpenAI quota 429) |
| Local `/readyz` | **ready** (intake path) |
| Vercel Preview HTTP | **401** — Deployment Protection / SSO |
| Production HTTP | **200** — **pre–P16-I bundle** (last-modified 2026-05-30, pre-Sprint A UX) |
| Andy authenticated Preview E2E | **Not logged this sprint** |
| P16-I commit on Vercel Preview | **Unknown / likely stale** — last documented Preview predates `901b0df` |

---

## Open blockers (founder-visible)

| ID | Blocker | Severity |
|----|---------|----------|
| B1 | **No Andy authenticated browser walkthrough** on live Preview URL | P0 |
| B2 | **Commercial pack missing** ($49/$99, terms, invoice on one-pager) | P0 |
| B3 | **Production URL still wrong product** (customer tab, Add-Car chrome) | P0 |
| B4 | **Vercel Preview SSO** — cold broker cannot load product | P0 |
| B5 | **P16-I bundle may not be deployed** to Preview alias | P1 |
| B6 | **Dark app header** wrapping white product island | P2 |
| B7 | **No supervised Chen Kui trial** or minutes-saved log | P0 (for payment, not preview UI) |

---

## Sprint A scope status

| Sprint A deliverable | Status |
|--------------------|--------|
| Broker default / single surface (product_only) | ✅ Shipped P16-A + P16-I |
| Cancellation-first copy | ✅ Shipped P16-I |
| Paste above fold | ✅ Shipped P16-I |
| Demo queue + cancellation auto-open | ✅ Code + API |
| CORS Preview → API | ✅ P16-G |
| Commercial pack | ❌ Not in scope / not done |
| Production promote | ❌ Frozen per mission |
| Chen Kui Day 0 | ❌ Blocked on B1–B2 |

---

*End of P16-J Preview Baseline*

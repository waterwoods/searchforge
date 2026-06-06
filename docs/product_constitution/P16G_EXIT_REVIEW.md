# P16-G Phase 8 — Sprint A Exit Review

**Date:** 2026-05-31  
**Sprint:** P16-G Final Deployment Validation  
**Question:** Is Sprint A complete? Can Andy start P17?

---

## Verdict

### **Sprint A must continue. Do NOT start P17.**

CORS is fixed and Preview is **API-functional**. The deployment-validation mile is **complete**. Sprint A itself is **not complete** — commercial artifacts, production deploy, and supervised broker trial remain open.

---

## What P16-G achieved

| Item | Status |
|------|--------|
| CORS patch applied | ✅ `fiqa-api-00079-ngq` |
| `.env.cloudrun` synced | ✅ 7 origins |
| OPTIONS preflight PASS | ✅ Preview + alias |
| Queue + triage from Preview origin | ✅ |
| 3 E2E scenarios (API layer) | ✅ ~89 avg |
| Guardrail regression | ✅ PASS |
| Role-C / Chen Kui / Assistant scores | ✅ Improved (+18 / +22 / +17) |
| Capability 1 | ✅ 70 (borderline, API-proven) |
| Andy authenticated browser E2E | ⏳ Pending |
| Commercial pack | ❌ |
| Supervised Chen Kui trial | ❌ |
| Production Sprint A deploy | ❌ |

---

## P17 gate checklist

| Gate | Required | Actual | Met? |
|------|----------|--------|------|
| Preview E2E PASS | Paste → Triage → Case → Draft | API ✅; browser ⏳ Andy | ⚠️ Partial |
| Capability 1 ≥ 70 | Live evidence | 70 API-layer | ⚠️ Borderline |
| Capability 6 ≥ 55 | Commercial artifacts | 51 | ❌ |
| Founder GO on broker URL share | Supervised walkthrough | Not logged | ❌ |
| Realistic first payment path | Trial + invoice | None | ❌ |

**P17: NO-GO**

---

## TOP 10 blockers (payment path only — no new features)

| # | Blocker | Prevents |
|---|---------|----------|
| 1 | **No commercial pack** — $49/$99, pilot terms, invoice template on BROKER_ONE_PAGER | Day 7 payment conversation (Cap 6) |
| 2 | **No completed supervised trial** with observation log | Payment proof or kill decision |
| 3 | **Andy authenticated Preview E2E not logged** | Founder GO; Cap 1 hold at 70 |
| 4 | **Vercel Deployment Protection (SSO)** on Preview | Unsupervised broker/assistant access |
| 5 | **Production still pre-Sprint A** (`ui-smoky-beta`) | Wrong experience on stable URL |
| 6 | **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY` not persisted** in Vercel dashboard | Redeploy flag drift |
| 7 | **客户报送 tab still visible** in product_only | Wrong-tab abandonment (Cap 1) |
| 8 | **Add-Car copy on tab suffix / header** despite cancellation wedge | Trust confusion (Cap 1, 6) |
| 9 | **No broker mandate + 15-min assistant training** | Habit formation (assistant sim 50/100) |
| 10 | **Hash URL CORS whack-a-mole** on future Preview deploys | Repeat breakage unless wildcard policy or production promote |

**Removed from list:** ~~Cloud Run ALLOWED_ORIGINS missing Preview~~ — **RESOLVED in P16-G**

---

## Sprint A vs deployment-validation scope

| Scope | Complete? |
|-------|-----------|
| **P16-G deployment validation** (CORS, Preview API, re-score) | ✅ **YES** |
| **Sprint A paid-pilot readiness** (commercial + trial + prod) | ❌ **NO** |

Sprint A continues for **commercial pack + supervised trial + production promote** — not engine or architecture work.

---

## Recommended next actions (operator)

1. Andy hard-refresh Preview (authenticated) → paste cancellation → confirm draft → log observation
2. Click 加载演示队列 → confirm cancellation auto-open
3. Persist Vercel Preview env vars (`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`)
4. Promote Sprint A Preview to Production alias OR redeploy production with same flags
5. Commercial pack: $49/$99, terms, invoice template (Sprint B scope — still blocking payment)
6. Schedule Chen Kui supervised Day 0 (founder present)
7. 7-day trial with observation log → payment or ranked kill
8. Consider Vercel protection bypass link for broker trial (reduce SSO friction)
9. Re-run `trial_launch_check.sh` after Andy E2E
10. Do **not** start P17 until Cap 6 ≥ 55 with commercial artifacts

---

*End of P16-G Phase 8*

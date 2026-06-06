# P16-G Final Verdict

**Date:** 2026-05-31  
**Sprint:** P16-G Final Deployment Validation  
**Constraint:** No new features. No P17. No Constitution changes. Reality only.

---

## 1. Is Sprint A finished?

**No.**

Sprint A **built** the front door (35 → 70 Capability 1 at API layer). P16-G **fixed** the deployment gate (CORS). Sprint A is **not finished** because:

- No commercial pack ($49/$99, terms, invoice)
- No supervised Chen Kui 7-day trial
- No production deploy of Sprint A UI
- Andy authenticated browser E2E not logged
- Capability 6 at 51 (target 55+ for trial conversion)

**P16-G deployment-validation sprint: finished.**  
**Sprint A paid-pilot sprint: continues.**

---

## 2. What is the new overall score?

**68 / 100** (weighted)

| Persona / lens | P16-F.5 | P16-G | Delta |
|----------------|---------|-------|-------|
| Overall product | 62 | **68** | +6 |
| Role-C | 40 | **58** | +18 |
| Chen Kui | 32 | **54** | +22 |
| Assistant | 33 | **50** | +17 |
| E2E average (3 scenarios) | 11 | **89** | +78 |

The +6 overall product lift is honest — not the +78 E2E lift (that was CORS-only; engine was always ~90).

---

## 3. What is the first-payment probability?

**~18%** (90-day horizon)

| Factor | Weight | Assessment |
|--------|--------|------------|
| Product works on Preview (API) | +15% | CORS fixed; core loop proven |
| Chen Kui would try supervised | +8% | MAYBE after Day 0 |
| Commercial artifacts exist | 0% | None |
| Completed trial with minutes saved | 0% | None |
| Production stable URL | −5% | Still pre-Sprint A |

Was ~5% when Preview showed Network Error. **Improved but not payment-ready.**

---

## 4. Start P17 or not?

**Do NOT start P17.**

P17 gate requires Cap 1 ≥ 70 with live browser evidence, Cap 6 ≥ 55, founder GO, supervised trial path. Only Cap 1 is borderline-met (API-only). Continue Sprint A commercial + trial track.

---

## 5. What are the next 5 actions?

1. **Andy authenticated Preview walkthrough** — hard refresh → paste cancellation → 加载演示队列 → log pass/fail (closes browser E2E gate)
2. **Persist Vercel Preview env vars** — `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL` (prevent redeploy drift)
3. **Promote Sprint A to Production** — deploy Preview bundle to `ui-smoky-beta` or alias swap (stable broker URL)
4. **Commercial pack** — add $49/$99, pilot terms, invoice template to BROKER_ONE_PAGER (Cap 6 blocker #1)
5. **Schedule Chen Kui supervised Day 0** — 5-min cancellation paste + observation log; payment or kill at Day 7

---

## Brutal summary

CORS was diagnosed for weeks and fixed in one env patch. That recovered **~78 points of fake E2E failure** and **~18–22 points on persona scores** — proving the engine and Sprint A UI were never the problem; the allowlist was.

The product can now be demonstrated **if Andy logs in**. It still cannot be **sold** — no price, no terms, no trial proof, no production URL.

**Sprint A front door: built.**  
**Preview door: open.**  
**Invoice door: still locked.**

Do not start P17. Finish commercial + trial.

---

*End of P16-G*

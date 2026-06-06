# P16-F Phase 5 — Role C / AI Simulation Test

**Date:** 2026-05-31  
**Preview:** https://ui-fvxlrxp4u-andys-projects-1f411b73.vercel.app/workbench/unified-intake  
**Constraint:** Live API blocked by CORS on Preview origin — scores reflect **broken workflow**, not UI copy alone.

---

## Role C definition used

**Repo canonical Role C** (`services/fiqa_api/inbox_triage/role_c_simulation_service.py`, `role_c_customer_llm.py`): bounded LLM Add-Car customer simulation (simulation tab — hidden in product_only UI).

**P16-F temporary Role C** (per sprint brief): confused real customer / broker client who submits messy cancellation/payment/add-car information and expects simple instructions — evaluated **indirectly** through broker-facing Preview.

---

## Simulation A — Chen Kui (Broker Owner)

**Profile:** Owner; wants time savings; impatient; does not care about tech.

| Horizon | Journey on Preview today | Clarity | Trust | Speed | Confusion⁻ | Continue | Pay |
|---------|--------------------------|---------|-------|-------|------------|----------|-----|
| **First 30s** | Vercel login friction → lands workbench tab, sees wayfinding + paste | 3.5 | 3 | 2.5 | 3 | 3 | 2.5 |
| **First 5 min** | Queue load → **Network Error**; paste/triage same CORS block | 2 | 1.5 | 1 | 1.5 | 1.5 | 1 |
| **Day 1 / 7** | Cannot prove minutes saved; "broken product" risk | 2.5 | 2 | 2 | 2 | 2 | 1.5 |

**Weighted composite (30s 20%, 5m 40%, D1 20%, D7 20%):** **38 / 100**

---

## Simulation B — Office Assistant

**Profile:** 50+ messages/day; needs queue clarity and next step.

| Horizon | Journey | Avg /5 |
|---------|---------|--------|
| **First 30s** | Same entry as broker — good — but empty/error queue | 3 |
| **First 5 min** | Cannot load cases; filters invisible; paste triage blocked | 1.5 |
| **Day 1 / 7** | Would revert to WeChat-only workflow | 2 |

**Composite:** **35 / 100**

---

## Simulation C — Customer / Role C

**Profile:** Messy cancellation message; expects broker to reply with simple steps.

| Horizon | Journey (via broker tool) | Score |
|---------|---------------------------|-------|
| **First 30s** | N/A — no customer UI | — |
| **First 5 min** | Broker cannot run triage on Preview → no structured draft → customer waits | 2 / 5 |
| **Day 1 / 7** | No faster replies; trust in broker unchanged or worse if broker blames "system broken" | 2 / 5 |

**Composite (×20):** **28 / 100**

---

## Aggregate scores

| Persona | Weight | Score |
|---------|--------|-------|
| Chen Kui | 50% | 38 |
| Assistant | 30% | 35 |
| Role C (customer) | 20% | 28 |
| **Overall Preview usability** | | **35 / 100** |

Threshold ≥70: **NOT met** — Network Error blocks real workflow.

---

## TOP confusions (Preview + CORS)

1. Network Error on first load — instant "broken" signal  
2. CORS hint mentions production alias — Andy may open wrong (pre-Sprint A) URL  
3. Vercel SSO before product  
4. Header still Add-Car flavored vs cancellation wedge  
5. Empty queue + error — no demo value moment  
6. 客户报送 tab still in bundle (wrong-path if explored)  
7. No pricing / trial proof on screen  
8. Repeat Preview deploys get new hash URLs → CORS whack-a-mole  
9. Saved Vercel Preview env empty — redeploy flag drift risk  
10. Cannot validate Role C Add-Car sim tab (hidden in product_only)

---

## If CORS were fixed (reference only)

P16-E estimated **73/100** weighted simulation when API works. Current **35/100** delta (~38 points) is attributable primarily to CORS block.

---

*End of P16-F Phase 5*

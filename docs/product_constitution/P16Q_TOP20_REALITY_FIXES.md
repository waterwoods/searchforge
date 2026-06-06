# P16-Q Phase 9 — Top 20 Reality Fixes

**Date:** 2026-06-01  
**Sprint:** P16-Q Reality Validation  
**Constraint:** Reality fixes only — no architecture, no platform, no new capabilities  
**Rank axes:** ROI (impact on trial/payment) · Effort · Risk

---

## Ranking method

**ROI** = closes P0/P1 failure from Phase 7  
**Effort** = S (&lt;2h) · M (2–8h) · L (&gt;1 day)  
**Risk** = Low / Med / High of making trial worse if done wrong

---

| Rank | Fix | ROI | Effort | Risk | Owner |
|------|-----|-----|--------|------|-------|
| **1** | **Commit + deploy P16-O bundle to Preview** (customer message-first) | Critical | M | Low | Eng |
| **2** | **Remove/disable Vercel Deployment Protection on Preview** OR publish bypass-stable alias for Chen Kui | Critical | S | Med | Eng/Andy |
| **3** | **Persist `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` in Vercel dashboard** (Preview + Production) | Critical | S | Low | Eng |
| **4** | **Andy 15-min Preview E2E log** (paste ×3, demo, copy, append) — paste into doc | High | S | Low | Andy |
| **5** | **Promote Sprint A + P16-O to Production alias** OR single broker-stable alias swap | Critical | M | Med | Eng |
| **6** | **Fill invoice payment IDs** (Zelle/Venmo/WeChat) in commercial pack | High | S | Low | Andy |
| **7** | **Default broker tab on any public URL** — verify `?tab=broker` or product_only kills customer default | High | S | Low | Eng |
| **8** | **Empty queue copy:** one line "Paste a message below to start" above fold | High | S | Low | Eng |
| **9** | **Hide 场景仿真 + customer tabs in any URL sent externally** (product_only enforcement on deploy) | High | S | Low | Eng |
| **10** | **Merge contact-only handoff** to single screen (phone in chat + one confirm) | Med | M | Med | Eng |
| **11** | **Chinese draft preference** when paste is predominantly Chinese (copy/template only) | High | M | Med | Eng |
| **12** | **Demote 加载演示队列** below paste on mobile / add "For demo only" label | Med | S | Low | Eng |
| **13** | **Customer-only route or subdomain** without broker/simulation tabs (same code, URL split) | High | M | Low | Eng |
| **14** | **Pricing line on broker workbench footer** ("Pilot: $49/mo — terms") | Med | S | Low | Andy |
| **15** | **Promote follow-up append** to same visual tier as copy draft | Med | S | Low | Eng |
| **16** | **Remove dark app header** on product_only (white full page) | Med | S | Low | Eng |
| **17** | **Post-handoff customer receipt** deploy verify — ensure 查看工作台 absent on deployed bundle | Med | S | Low | Eng |
| **18** | **Add CORS origin** when new Preview hash URL created (ops checklist item) | Med | S | Med | Eng |
| **19** | **OpenAI quota restore** OR document rules-only limits for trial | Med | S | Low | Andy |
| **20** | **Chen Kui Day 0 script pinned to one URL** in trial packet — no Production fallback | High | S | Low | Andy |

---

## Top 5 by ROI / effort (do first)

| Priority | Fix | Why |
|----------|-----|-----|
| **Week 0 hour 1** | #2 Preview SSO off | Without this, nothing else matters for broker |
| **Week 0 hour 2** | #3 Persist env vars | Prevents redeploy regression |
| **Week 0 hour 3** | #1 Deploy P16-O | Closes customer deploy gap |
| **Week 0 hour 4** | #4 Andy E2E log | Founder sign-off |
| **Week 0 day 2** | #5 Production promote | Stable long-term URL |

---

## Explicitly NOT on this list (per mission)

- WeChat sync  
- Stripe integration  
- Multi-tenant / auth platform  
- New triage capabilities  
- Constitution edits  
- P17 features  
- Mobile native app  
- RAG / Qdrant work  

---

## ROI vs P16-O internal fixes

P16-O shipped **customer landing simplification in git working tree**. P16-Q top fixes are **90% deploy + URL + commercial ops**. Further local UI deletion without deploy **does not move reality score**.

---

## Risk notes

| Fix | Risk if rushed |
|-----|----------------|
| SSO off | Public exposure of pilot — mitigate with obscure alias + noindex |
| Production promote | Wrong bundle — mitigate with #4 E2E gate |
| Chinese draft | Bad templates — mitigate with supervised Day 0 only |

---

*End of P16-Q Phase 9 — Top 20 Reality Fixes*

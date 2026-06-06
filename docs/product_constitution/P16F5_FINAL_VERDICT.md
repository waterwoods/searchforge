# P16-F.5 Phase 8 — Honest Founder Verdict

**Date:** 2026-05-31  
**Sprint:** P16-F.5 Preview Unblock + Full Capability Revalidation  
**Question:** Can Andy move to P17? Or must Sprint A continue?

---

## Verdict

### **Sprint A must continue. Do NOT start P17.**

Preview is **not fully functional**. Paste → Triage → Structured Case → Draft **fails on Preview** due to unfixed CORS. Sprint A UI code is deployed and verified in bundle/local DOM, but the product cannot be honestly demonstrated or trialed until the env patch from `P16F5_CORS_PLAN.md` is applied and E2E re-run.

---

## Success criteria scorecard

| Criterion | Result |
|-----------|--------|
| Preview works | ❌ API blocked |
| Role-C score increases | ⚠️ 40/100 (+8 vs P11 baseline, &lt;70 threshold) |
| Chen Kui score increases | ⚠️ 32/100 (UI up, workflow down) |
| Assistant score increases | ⚠️ 33/100 |
| Capability 1 improves | ✅ 35 → 58 |
| Capability 6 improves | ⚠️ 45 → 46 (+1) |
| Realistic path to first payment | ❌ |

---

## What Sprint A achieved (real)

- Sprint A product_only UI **is on Preview** (wayfinding, default broker tab, hidden simulation/我的办理, practice scenarios, loading copy)
- Triage engine **healthy** on Cloud Run (guardrail PASS; 3 scenario API tests PASS)
- CORS root cause **confirmed** with fix plan ready since P16-F
- Production **safely unchanged** — comparison baseline preserved

## What Sprint A did NOT achieve

- Preview E2E broker demo
- Founder functional sign-off
- Chen Kui / assistant trial
- Any payment evidence
- Production deploy of Sprint A

---

## TOP 10 blockers (payment path only — no new features)

| # | Blocker | Prevents |
|---|---------|----------|
| 1 | **Cloud Run `ALLOWED_ORIGINS` missing Preview hostname** (`ui-fvxlrxp4u-…`) | Any Preview E2E; instant Network Error |
| 2 | **CORS fix not applied** despite documented plan since P16-F | Founder/broker functional validation |
| 3 | **Vercel Deployment Protection (SSO)** on Preview | Unsupervised broker access |
| 4 | **`VITE_UNIFIED_INTAKE_PRODUCT_ONLY` not persisted** in Vercel dashboard | Redeploy flag drift → wrong UI |
| 5 | **Production still pre-Sprint A** (`ui-smoky-beta`) | Wrong experience if broker opens stable URL |
| 6 | **客户报送 tab still visible** in product_only | Wrong-tab abandonment (Cap 1) |
| 7 | **Add-Car copy on tab suffix / header** despite cancellation wedge | Trust confusion (Cap 1, 6) |
| 8 | **No commercial pack** — $49/$99, pilot terms, invoice template | Day 7 payment conversation (Cap 6) |
| 9 | **`.env.cloudrun` will revert CORS** on next full backend deploy | Repeat Preview breakage |
| 10 | **No completed supervised trial** with observation log | Payment proof or kill decision |

---

## Exact next actions (operator — not P17)

1. **Andy approves** → run `gcloud run services update` from `P16F5_CORS_PLAN.md`  
2. Verify OPTIONS 200 for Preview origin  
3. Andy authenticated hard-refresh → paste cancellation → confirm draft  
4. Click 加载演示队列 → confirm cancellation auto-open  
5. Update `.env.cloudrun` ALLOWED_ORIGINS before next backend deploy  
6. Persist Vercel Preview env vars (`VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL`)  
7. **Re-run P16-F.5 E2E** on Preview (or P16-F.6 gate) before Chen Kui URL share  
8. Founder dry-run with observation log  
9. Commercial pack (Sprint B scope — still blocking payment)  
10. Supervised Chen Kui 7-day trial — payment or ranked kill

---

## P17 gate (unchanged)

P17 starts only when:

- Preview E2E PASS (Paste → Triage → Case → Draft)  
- Capability 1 ≥ **70** with live evidence  
- Capability 6 ≥ **55** with commercial artifacts in hand  
- Founder GO on broker trial URL share  

**None of these are met today.**

---

## One-line summary

**Sprint A built the right front door; Preview cannot open it because CORS was diagnosed but not patched. Fix CORS, re-validate E2E, then continue Sprint A (commercial + trial) — not P17.**

---

*End of P16-F.5 Phase 8*

# P16-R Phase 10 — Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-R Deployment Parity & Reality Closure  
**Authority:** Phases 1–9 + live verification + Phase 8 execution  
**Tone:** Parity over optimism

---

## Executive summary

P16-R **closed part of the deploy gap**: P16-O is **committed**, **pushed**, and **on the latest Preview bundle** (`ui-iwnyo9ufa` / `ui-waterwoods` alias). **Parity is not achieved.** Cold Preview still returns **401 SSO**. Production remains a **41-day-old** full-dev UI. Andy can still only **certify** the loop on localhost until SSO is off and E2E is logged.

---

## Answers (required)

### 1. Local score
**79 / 100** (UI+capability: customer P16-O + broker P16-I; engine PASS)

### 2. Preview score
**68 / 100** — bundle **~74**; cold access **~12** (SSO). Weighted overall **68**.

### 3. Production score
**52 / 100** — accessible URL but wrong UI (pre–P16-O / pre–product_only).

### 4. Remaining gap
| Gap | Impact |
|-----|--------|
| Vercel Deployment Protection (401) | Chen Kui / Andy cannot use Preview link |
| Production not promoted | Public URL shows wrong product |
| Preview env not dashboard-persisted | Next deploy without `-b` regresses |
| No Andy Preview E2E log | No founder sign-off |
| Customer URL on product_only deploy | Customer tab hidden on workbench |

### 5. Is parity achieved?
**NO.** Local ≈ Preview (bundle only). Production ≠ Preview ≠ Local.

### 6. Can Andy send Preview URL?
**NO** for unsupervised cold open. **YES** for `vercel curl` / logged-in Vercel account / after SSO disabled.

### 7. Can Andy send Production URL?
**NO** for trial — wrong UI and wrong default tab. **YES** only for "something loads" smoke — **misleading**.

### 8. Is Day 0 ready?
**NO** for URL-based Day 0. **YES** for supervised localhost screen-share (unchanged).

### 9. Is first $49 now realistic?
**NO** this week. **~15%** today · **~35%** after Preview SSO off + Production promote + Day 0 proof (revised from P16-L 12%/40% — deploy improved, access not).

### 10. What must happen before P17?
| # | Action |
|---|--------|
| 1 | Disable Preview Deployment Protection **or** publish bypass link |
| 2 | Andy 15-min Preview E2E log |
| 3 | Persist Preview env vars (link Git or dashboard) |
| 4 | `vercel deploy --prod` with product_only + P16-O **after** gates |
| 5 | Supervised Chen Kui Day 0 |
| 6 | **Do not start P17** until parity checklist in `P16R_PREVIEW_FIX_PLAN.md` is all `[x]` |

---

## What P16-R changed (evidence)

| Before (P16-Q) | After (P16-R) |
|----------------|---------------|
| P16-O uncommitted | `d05e94d` on branch |
| Preview without P16-O strings | `请把您的需求发给我们` in `index-CKPYkrkL.js` |
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` missing on Vercel | Production dashboard var added |
| Latest Preview CORS missing new hash | `ui-iwnyo9ufa` allowlisted |
| waterwoods → old Preview | waterwoods → **new** Preview |

---

## Document index

| Phase | File |
|-------|------|
| 1 Inventory | `P16R_REALITY_INVENTORY.md` |
| 2 Parity audit | `P16R_DEPLOYMENT_PARITY_AUDIT.md` |
| 3 Environment | `P16R_ENVIRONMENT_AUDIT.md` |
| 4 P16-O check | `P16R_P16O_PARITY_CHECK.md` |
| 5 Preview plan | `P16R_PREVIEW_FIX_PLAN.md` |
| 6 Production gate | `P16R_PRODUCTION_GATE.md` |
| 7 Test matrix | `P16R_REALITY_TEST_MATRIX.md` |
| 8 Execution | `P16R_EXECUTION_LOG.md` |
| 9 Revalidation | `P16R_REVALIDATION.md` |
| 10 Verdict | `P16R_FINAL_VERDICT.md` |

---

## One sentence

**The right build is finally on Preview; the wrong URL still blocks the broker, and Production has not moved.**

---

*End of P16-R Deployment Parity & Reality Closure Sprint*

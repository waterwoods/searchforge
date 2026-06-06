# P16-G Phase 7 — Capability Scorecard

**Date:** 2026-05-31  
**Method:** Constitution baseline → Sprint A (P16-F.5) → **post-CORS Preview fix (P16-G)**  
**Guardrail:** PASS (unchanged)  
**Rule:** CORS fix unlocks API-layer evidence; browser E2E capped until Andy authenticated walkthrough

---

## Full scorecard

| # | Capability | Before Sprint A | After Sprint A (P16-F.5) | After Preview Fix (P16-G) | Δ (Sprint A) | Δ (Preview fix) |
|---|------------|-----------------|---------------------------|---------------------------|--------------|-----------------|
| 1 | **Broker Front Door** | **35** | **58** | **70** | +23 | **+12** |
| 2 | Urgent Message Triage | **85** | **85** | **85** | 0 | 0 |
| 3 | Structured Case Record | **72** | **72** | **72** | 0 | 0 |
| 4 | Customer Intake Collection | **62** | **66** | **68** | +4 | +2 |
| 5 | Case Lifecycle Management | **55** | **56** | **58** | +1 | +2 |
| 6 | **Trial Conversion** | **45** | **46** | **51** | +1 | **+5** |
| 7 | **Founder / Operator Control** | **68** | **64** | **70** | −4 | **+6** |

### Weighted overall

| Metric | Before Sprint A | After Sprint A | After Preview Fix | Δ (total) |
|--------|---------------|----------------|-------------------|-----------|
| **Overall product score** | **60 / 100** | **62 / 100** | **68 / 100** | **+8** |

*Weighting: Front Door 25%, Triage 15%, Case Record 15%, Intake 10%, Lifecycle 10%, Trial Conversion 15%, Founder Control 10%*

---

## Capability 1 — Broker Front Door: 70 (+35 total, +12 post-CORS)

| Evidence FOR 70 | Evidence AGAINST 75 |
|-----------------|---------------------|
| CORS fixed — queue + triage work from Preview origin | No Andy authenticated browser E2E logged |
| Default broker tab, wayfinding, practice scenarios (bundle + source) | 客户报送 tab still visible |
| Demo queue API path unblocked | Add-Car header/suffix copy lag |
| Paste → draft in <60s (API) | Vercel SSO friction |
| Engineer chrome hidden at runtime | Production URL still pre-Sprint A |

**Success criterion Cap 1 ≥ 70:** **MET at API layer** — borderline; Andy browser sign-off required to hold 70.

---

## Capability 6 — Trial Conversion: 51 (+6 total, +5 post-CORS)

| Evidence | Score impact |
|----------|--------------|
| Preview API functional — can demonstrate core loop | +5 |
| CORS/deploy gate cleared | +1 (partial — was −4 on Cap 7, now recovered) |
| No broker trial completed | Caps at ~55 |
| No $49/$99 on BROKER_ONE_PAGER | No change |
| No terms / invoice | No change |
| Vercel SSO blocks unsupervised broker | −4 vs ideal |

**Target Cap 6 ≥ 55:** **NOT MET** — need commercial pack + supervised trial.

---

## Capability 7 — Founder / Operator Control: 70 (+2 net, +6 post-CORS)

| Evidence | Score impact |
|----------|--------------|
| CORS patch applied (`fiqa-api-00079-ngq`) | +6 |
| `.env.cloudrun` synced — deploy won't revert | +2 |
| Guardrail PASS | Stable |
| Vercel Preview env vars not persisted in dashboard | −2 drift risk |
| Andy browser E2E not yet logged | −2 |

Recovered from P16-F.5 −4 deploy-gate penalty.

---

## Success criteria check

| Target | Before | Sprint A | Post-CORS | Met? |
|--------|--------|----------|-----------|------|
| Capability 1 ≥ 70 | 35 | 58 | **70** | ⚠️ Borderline |
| Capability 6 improves materially | 45 | 46 | **51** | ⚠️ +5 only |
| Role-C improves | ~32 | 40 | **58** | ✅ but <70 |
| Chen Kui improves | — | 32 | **54** | ✅ |
| Assistant improves | — | 33 | **50** | ✅ |
| Overall → 80 paid pilot | 60 | 62 | **68** | ❌ gap 12 |

---

## Path to next score band (evidence required)

1. Andy authenticated Preview E2E logged → Cap 1 hold **72–75**
2. Commercial pack ($49/$99, terms, invoice) → Cap 6 → **58–62**
3. Production deploy Sprint A to `ui-smoky-beta` → Cap 1, 6, 7 +5 combined
4. Chen Kui supervised 7-day trial → Cap 6 → **65–80** or kill

---

*End of P16-G Phase 7*

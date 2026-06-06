# P16-F.5 Phase 7 — Capability Re-Scoring

**Date:** 2026-05-31  
**Method:** Constitution baseline (P14-B) vs Sprint A code evidence vs **live Preview reality** (CORS-blocked E2E)  
**Guardrail:** PASS (13/13) — Triage ceiling unchanged  
**Rule:** Do not inflate — Preview E2E failure caps Trial Conversion and Front Door despite deployed UI

---

## Before vs After Sprint A

| # | Capability | Before Sprint A | After Sprint A (P16-F.5 honest) | Delta | Trial-ready? |
|---|------------|-----------------|----------------------------------|-------|--------------|
| 1 | **Broker Front Door** | **35** | **58** | **+23** | No |
| 2 | Urgent Message Triage | **85** | **85** | 0 | Yes |
| 3 | Structured Case Record | **72** | **72** | 0 | Yes |
| 4 | Customer Intake Collection | **62** | **66** | +4 | Conditional |
| 5 | Case Lifecycle Management | **55** | **56** | +1 | Conditional |
| 6 | **Trial Conversion** | **45** | **46** | **+1** | No |
| 7 | **Founder / Operator Control** | **68** | **64** | **−4** | Partial |

### Weighted overall

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Overall product score** | **60 / 100** | **62 / 100** | **+2** |

*Weighting: Front Door 25%, Triage 15%, Case Record 15%, Intake 10%, Lifecycle 10%, Trial Conversion 15%, Founder Control 10% (per CAPABILITY_SCORECARD.md)*

---

## Capability 1 — Broker Front Door: 58 (+23)

| Evidence FOR increase | Evidence AGAINST 75 target |
|-----------------------|----------------------------|
| Sprint A code deployed on Preview with product_only | Preview E2E broken (CORS) — no value moment |
| Default broker tab (source + local DOM) | 客户报送 tab still visible |
| Wayfinding, paste copy, practice scenarios in bundle | Add-Car header/suffix copy lag |
| Demo queue progress strings present | Demo queue never E2E on Preview origin |
| Local DOM walkthrough confirms UX shell | Vercel SSO friction |

**Why not 72 (P16-E estimate)?** P16-E assumed API works from Preview browser. P16-F.5 re-measured: CORS **still unfixed** → cannot claim Day-1 ≥70.

---

## Capability 6 — Trial Conversion: 46 (+1)

| Evidence | Score impact |
|----------|--------------|
| Preview URL exists for founder review | +1 |
| No broker trial completed | Caps at ~50 |
| No $49/$99 on BROKER_ONE_PAGER | No change |
| No terms / invoice | No change |
| Preview unusable for Chen Kui unsupervised | Prevents trial start |

**Why not 50 (P16-E)?** Preview cannot demonstrate paid-pilot path end-to-end; founder functional sign-off blocked.

---

## Capability 7 — Founder / Operator Control: 64 (−4)

| Evidence | Score impact |
|----------|--------------|
| Guardrail PASS | Stable |
| P16-F CORS fix documented but **not applied** | −4 deploy gate failure |
| `.env.cloudrun` still omits Preview origin | Repeat CORS risk on deploy |
| Vercel Preview env vars not persisted | Drift risk |

Founder has correct diagnosis and fix plan — but **operator action incomplete**, so control score decreases slightly vs false confidence.

---

## Capabilities unchanged (engine layer)

| Capability | Score | Rationale |
|------------|-------|-----------|
| Urgent Message Triage | 85 | Guardrail PASS; Cloud Run triage returns correct categories |
| Structured Case Record | 72 | Draft quality unchanged; no new trial edge-case fixes |
| Customer Intake Collection | 66 | Paste UX improved in Sprint A UI; undermined by Preview API block (+4 vs 62 for copy/default tab) |
| Case Lifecycle Management | 56 | Queue UX improved in UI strings; not exercised on Preview (+1) |

---

## Comparison to success criteria targets

| Target | Before | After | Met? |
|--------|--------|-------|------|
| Capability 1 improves | 35 | 58 | ✅ (+23) but still &lt;75 |
| Capability 6 improves | 45 | 46 | ⚠️ +1 only |
| Overall → 80 paid pilot | 60 | 62 | ❌ gap 18 |
| Role C score increases | ~32 (P11) | 40 | ✅ but &lt;70 |
| Realistic path to first payment | No | No | ❌ |

---

## P16-E vs P16-F.5 honest adjustment

| Metric | P16-E (optimistic) | P16-F.5 (measured) | Reason for delta |
|--------|-------------------|-------------------|------------------|
| Cap 1 | 72 | **58** | CORS not fixed; E2E not proven |
| Cap 6 | 50 | **46** | Preview not broker-trialable |
| Overall | 68 | **62** | +6 points optimism removed |

---

## Path to re-score upward (evidence required)

1. Apply CORS patch → Andy Preview E2E PASS → Cap 1 → **68–72**  
2. Andy 5-min authenticated walkthrough logged → Cap 1 → **72–75**  
3. Commercial pack (pricing, terms, invoice) → Cap 6 → **55–60**  
4. Chen Kui supervised 7-day trial → Cap 6 → **65–80** or kill

---

*End of P16-F.5 Phase 7*

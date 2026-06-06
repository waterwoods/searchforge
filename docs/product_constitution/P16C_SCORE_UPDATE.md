# P16-C Phase 4 — Capability Score Update

**Date:** 2026-05-31  
**Evidence:** P16C_LOCAL_VALIDATION, P16C_BEFORE_AFTER, P16C_SIMULATION_REPORT, guardrail PASS, `/readyz` intake_path_ready  
**Rule:** Do not inflate — remote Preview + founder dry-run required for Cap 1 ≥ 70 deployed credit

---

## Capability 1 — Broker Front Door

| | Previous | New | Δ |
|--|----------|-----|---|
| **Score** | **35** | **68** | **+33** |
| **Trial-ready?** | No | **Conditional** | Preview + env required |

### Why +33 (exact evidence)

| Sprint A item | Verified? | Points rationale |
|---------------|-----------|------------------|
| A1 Default broker tab | ✅ Live CDP | +12 — fixes P11 #1 blocker |
| A2 Engineer chrome hidden | ✅ Zero PG/API/debug locally; prod still has PG | +10 — trust restoration |
| A3 Wayfinding banner | ✅ Visible | +4 |
| A4 Demo progress + auto-open cancellation | ⚠️ Code + copy; E2E blocked CORS | +3 (partial) |
| A5 Loading copy | ✅ In bundle; not cold-triggered | +1 |
| A6 Paste expectation | ✅ Placeholder + helper | +2 |
| A7 Intro collapse + cancellation text | ✅ Collapsed default | +2 |
| A8 Inline practice | ✅ 3 scenarios; click loads text | +4 |
| A9 Hide 我的办理 | ✅ 2 tabs only | +3 |
| A10 Simplified filters | ⚠️ Code; empty queue | +1 (partial) |
| Copy wedge alignment (Add-Car labels) | ⚠️ Partial | −5 penalty |

### Why not 75 (target)

1. No Vercel Preview with `c2e3dff` + `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`  
2. Demo queue + auto-open cancellation not founder-verified on deployed URL  
3. Tab suffix / header still Add-Car flavored  
4. Unsupervised Day 1 ≥ 70 **simulated** (71 Chen Kui) but not **measured** on production-like Preview  
5. CORS misconfiguration risk on any new Preview origin  

---

## Overall Product Score

| | Previous | New | Δ |
|--|----------|-----|---|
| **Weighted overall** | **60** | **67** | **+7** |

### Weighted calculation

| Capability | Weight | Before | After | Before × W | After × W |
|------------|--------|--------|-------|------------|-----------|
| 1 Broker Front Door | 25% | 35 | **68** | 8.75 | 17.00 |
| 2 Urgent Triage | 15% | 85 | 85 | 12.75 | 12.75 |
| 3 Case Record | 15% | 72 | 72 | 10.80 | 10.80 |
| 4 Intake Collection | 10% | 62 | **68** | 6.20 | 6.80 |
| 5 Case Lifecycle | 10% | 55 | **58** | 5.50 | 5.80 |
| 6 Trial Conversion | 15% | 45 | **48** | 6.75 | 7.20 |
| 7 Founder Control | 10% | 68 | **66** | 6.80 | 6.60 |
| **Total** | 100% | | | **57.55 → 60** | **66.95 → 67** |

*(Rounded to constitution convention: 60 → 67)*

---

## All Capabilities — Full Scorecard

| # | Capability | Previous | New | Δ | Trial-ready? | Change reason |
|---|------------|----------|-----|---|--------------|---------------|
| 1 | **Broker Front Door** | 35 | **68** | +33 | Conditional | Sprint A UI shipped locally; deploy gap |
| 2 | **Urgent Triage** | 85 | **85** | 0 | Yes | No Sprint A scope; guardrail PASS |
| 3 | **Case Record** | 72 | **72** | 0 | Yes | Engine unchanged; draft quality gaps remain |
| 4 | **Intake Collection** | 62 | **68** | +6 | Conditional | Paste on correct default tab + expectation copy |
| 5 | **Case Lifecycle** | 55 | **58** | +3 | Conditional | Simplified filters + queue UX when populated; wayfinding still weak empty |
| 6 | **Trial Conversion** | 45 | **48** | +3 | No | UI blockers #1,#2,#7,#8 partially removed; no commercial pack |
| 7 | **Founder Control** | 68 | **66** | −2 | Partial | Sprint A code not on Vercel — false-confidence risk |

---

## Score update rules applied

1. ✅ Rescore based on Sprint A evidence — Cap 1, 4, 5, 6, 7 adjusted  
2. ✅ Cap 1 cannot claim 75 without deployed Preview + dry-run  
3. ✅ Guardrail PASS — Triage ceiling unchanged  
4. N/A Prod outage — not triggered  

---

## Path to 80 / 100 (unchanged target)

| Next action | Capabilities lifted | Expected Δ |
|-------------|---------------------|------------|
| Vercel Preview + env + Andy dry-run | 1, 7 | +3–5 overall |
| Sprint B commercial (pricing, terms) | 6 | +5 overall |
| 7-day supervised trial + log | 6, all | Proof or kill |
| Copy wedge fix (tab suffix) | 1, 4 | +2 overall |

**Sprint A exit target:** Cap 1 ≥ **70** on **deployed Preview** with founder sign-off — **not yet met** (68 local).

---

*End of P16-C Phase 4 — Capability Score Update*

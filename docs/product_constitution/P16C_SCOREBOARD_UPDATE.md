# P16-C Phase 5 — Scoreboard Update

**Date:** 2026-05-31  
**Evidence:** P16C visual review (72), AI simulation (72), smoke test (77), Preview deployment truth (no remote Preview)  
**Rule:** Do not inflate — remote deploy + founder dry-run required for full credit

---

## Capability Score Changes

### Capability 1 — Broker Front Door

| | Before (P15) | After (P16-C) | Delta |
|---|--------------|---------------|-------|
| Score | **35** | **68** | **+33** |
| Status | Not Started | **In Progress** | |
| Trial-ready? | No | **Conditional** | Preview + env required |

**Evidence for +33:**
- Default broker tab ✅ (code + local visual)
- Engineer chrome hidden ✅
- Wayfinding + paste copy ✅
- Inline practice ✅
- Demo queue UX improved in code ⚠️ not E2E on Vercel

**Why not 75 (target):**
- No Vercel Preview with `c2e3dff` + product_only
- Tab/brand copy still Add-Car flavored
- Demo queue + filters not founder-verified on deployed URL
- Unsupervised Day 1 ≥70 **simulated** but not **measured** on production-like Preview

---

### Capability 4 — Customer Intake Collection

| | Before | After | Delta |
|---|--------|-------|-------|
| Score | **62** | **68** | **+6** |

**Evidence:** Paste surface now on correct default tab; expectation copy + loading states; mechanism unchanged (still manual paste).

**Why not higher:** Paste still feels like extra step without measured time savings; wrong surface partially fixed via Cap 1.

---

### Capability 6 — Trial Conversion

| | Before | After | Delta |
|---|--------|-------|-------|
| Score | **45** | **48** | **+3** |

**Evidence:** UI blockers #1, #2, #7, #8 partially removed (P15 Founder Review). No payment proof, pricing, terms, or completed trial.

**Why minimal change:** Commercial pack and 7-day trial unchanged.

---

### Capability 7 — Founder / Operator Control

| | Before | After | Delta |
|---|--------|-------|-------|
| Score | **68** | **66** | **-2** |

**Evidence for slight decrease:** New risk — Sprint A code on branch but **not** on Vercel; `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` missing from Vercel env creates **false confidence** if founder assumes Production reflects Sprint A. Guardrail still PASS; scripts unchanged.

**Recovery path:** Preview deploy + env + Andy dry-run → restore to 70+.

---

## Weighted Product Score (approximate)

| Capability | Weight | Before × W | After × W |
|------------|--------|------------|-----------|
| 1 Front Door | 25% | 8.75 | 17.00 |
| 2 Triage | 15% | 12.75 | 12.75 |
| 3 Case Record | 15% | 10.80 | 10.80 |
| 4 Intake | 10% | 6.20 | 6.80 |
| 5 Lifecycle | 10% | 5.50 | 5.50 |
| 6 Trial Conversion | 15% | 6.75 | 7.20 |
| 7 Founder Control | 10% | 6.80 | 6.60 |
| **Total** | 100% | **~60** | **~67** |

**Overall product score:** 60 → **67** (+7), not 80.

---

## Proposed IMPLEMENTATION_SCOREBOARD.md Updates (NOT committed)

When instructed, update these rows:

| Capability | Current → New | Status |
|------------|---------------|--------|
| 1 Broker Front Door | 35 → **68** | In Progress |
| 4 Intake Collection | 62 → **68** | Partial |
| 6 Trial Conversion | 45 → **48** | Not Started |
| 7 Founder Control | 68 → **66** | Partial |
| Weighted overall | 60 → **67** | |

Sprint A exit target remains **Cap 1 ≥ 70** on **deployed Preview** with founder sign-off.

---

*End of P16-C Phase 5 — Scoreboard Update*

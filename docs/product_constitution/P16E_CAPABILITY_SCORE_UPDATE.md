# P16-E Phase 6 — Capability Score Update

**Date:** 2026-05-31  
**Evidence:** P16E_PREVIEW_DEPLOYMENT, P16E_PREVIEW_SMOKE_TEST, P16E_AI_SIMULATION, guardrail PASS  
**Rule:** Do not inflate — founder browser proof still required for ≥75 on Cap 1

---

## Before vs After Preview

| Metric | Before Sprint A (P15) | After P16-C (local) | After P16-E Preview |
|--------|----------------------|---------------------|---------------------|
| **Broker Front Door** | 35 | 68 | **72** |
| **Trial Conversion** | 45 | 48 | **50** |
| **Overall (weighted)** | 60 | 67 | **68** |

---

## Capability 1 — Broker Front Door: 72 (+4 vs P16-C)

| Evidence for +4 | Limit why not 75+ |
|-----------------|-------------------|
| Preview deployed with product_only + API env | Andy DOM walkthrough incomplete |
| Bundle contains Sprint A UX strings | 5 uncommitted `ui/` files in artifact |
| Production unchanged (safe comparison) | SSO blocks casual broker access |
| AI simulation 72 Chen Kui on Preview assumptions | Demo queue E2E not on Preview |

---

## Capability 6 — Trial Conversion: 50 (+2)

Preview exists → slightly higher path to founder dry-run; no real broker trial completed.

---

## Overall: 68 (+1 vs P16-C)

| Capability | Weight | Score | Contribution |
|------------|--------|-------|--------------|
| 1 Front Door | 25% | 72 | 18.0 |
| 2 Triage | 15% | 85 | 12.75 |
| 3 Case Record | 15% | 72 | 10.8 |
| 4 Intake | 10% | 68 | 6.8 |
| 5 Lifecycle | 10% | 58 | 5.8 |
| 6 Trial Conversion | 15% | 50 | 7.5 |
| 7 Founder Control | 10% | 66 | 6.6 |
| **Total** | | | **~68** |

---

## Should `IMPLEMENTATION_SCOREBOARD.md` be updated now?

**NO**

Wait until Andy approves Preview walkthrough and merge intent. If YES later, propose:

```markdown
| **1 — Broker Front Door** | 72 | 75 | 3 | Engineering | **Partial** (Preview deployed P16-E) | ...
| **6 — Trial Conversion** | 50 | 80 | 30 | ... | **Partial** (Preview ready for founder review) | ...
| **Weighted product score** | **68 / 100** | **80 / 100** | **12** |
```

And footnote: Production still 35-equivalent UX until merge + `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` on Production deploy.

---

*End of P16-E Phase 6*

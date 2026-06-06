# P16-Y Phase 8 — Case Intelligence Scorecard

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Battery:** 50 cases × rules-based triage (production fallback path)

---

## Scorecard

| Metric | Before | After | Delta | Target met? |
|--------|--------|-------|-------|-------------|
| **Overall** | 85.6 | **88.6** | **+3.0** | ⚠️ Close (90 = excellent) |
| Case Intelligence | 39.1 | **42.1** | **+3.0** | ↑ |
| Case Distillation | 43.8 | **46.5** | **+2.7** | ↑ |
| Office Actionability | 25.0 | **25.0** | 0 | ✅ Max |

---

## Dimension breakdown

```
                    Before    After     Delta
Understanding       22.2      25.0      +2.8  ████████████░░ → ██████████████
Missing Info        16.9      17.1      +0.2  ████████░░░░░░ → ████████░░░░░░
Office Action       25.0      25.0       0.0  ██████████████ → ██████████████
Multi-message       21.5      21.5       0.0  ███████████░░░ → ███████████░░░
```

---

## Grade distribution

| Grade | Before | After |
|-------|--------|-------|
| 90–100 (Excellent) | 5 | 5 |
| 80–89 (Good) | 34 | **45** |
| 70–79 (Fair) | 11 | 0 |
| <70 (Fail) | 0 | 0 |

**Cases below 80:** 11 → **0**

---

## Lane scores (after)

| Lane | Cases | Avg score |
|------|-------|-----------|
| Cancellation | 5 | 90.8 |
| Missing documents | 5 | 89.2 |
| Address change | 3 | 88.0 |
| Driver addition | 3 | 88.0 |
| Vehicle add/remove | 4 | 88.0 |
| Billing | 5 | 88.0 |
| Coverage | 3 | 88.0 |
| Underwriting | 3 | 93.0 |
| Renewal | 3 | 89.3 |
| Claims | 3 | 88.0 |
| Multi-turn | 5 | 85.4 |
| Edge | 5 | 87.6 |

**Weakest lane:** Multi-turn (85.4) — summary merge, not classification

---

## Sprint success criteria

| Criterion | Result |
|-----------|--------|
| Increase Case Intelligence | ✅ +3.0 |
| Increase Case Distillation | ✅ +2.7 |
| Maintain Office Actionability | ✅ 25.0 |
| No UI changes | ✅ |
| No architecture changes | ✅ |
| Scenario guardrail intact | ✅ 64/64 |

---

*End of P16-Y Phase 8 — Scorecard*

# P16-Y Phase 7 — Before vs After Comparison

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Method:** Same 50 cases, same rules path, before/after `triage.py` extraction fixes

---

## Aggregate

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| **Avg total** | 85.6 | **88.6** | **+3.0** |
| Understanding | 22.2 | **25.0** | **+2.8** |
| Missing Info | 16.9 | **17.1** | **+0.2** |
| Office Actionability | 25.0 | 25.0 | 0 |
| Multi-message | 21.5 | 21.5 | 0 |

---

## Derived indices

| Index | Before | After | Delta |
|-------|--------|-------|-------|
| **Case Intelligence** (Understanding + Missing) | 39.1 | **42.1** | **+3.0** |
| **Case Distillation** (Understanding + Multi) | 43.8 | **46.5** | **+2.7** |
| **Office Actionability** | 25.0 | 25.0 | 0 |

---

## Per-case deltas (changed only)

| ID | Before | After | Δ | Fix area |
|----|--------|-------|---|----------|
| Y11 | 76 | 88 | +12 | Address change |
| Y12 | 76 | 88 | +12 | Address change |
| Y13 | 76 | 88 | +12 | Address change |
| Y14 | 76 | 88 | +12 | Add-driver vs missing-doc |
| Y27 | 76 | 88 | +12 | Coverage question |
| Y28 | 76 | 88 | +12 | Coverage question |
| Y30 | 77 | 93 | +16 | UW vs signature |
| Y31 | 77 | 93 | +16 | 核保 follow-up |
| Y34 | 80 | 92 | +12 | Renewal shop-around + policy # |
| Y37 | 76 | 88 | +12 | Windshield / ？ |
| Y38 | 84 | 92 | +8 | notice_image gap |
| Y44 | 67 | 79 | +12 | Multi-turn correction |

**12 cases improved; 38 unchanged; 0 regressed**

---

## Representative output diffs

### Y11 — Address change

| | Before | After |
|---|--------|-------|
| Category | `unclear` | `customer_question` |
| Summary | “1 customer message(s)…” | “Address / garaging change. …” |
| Broker step | Generic clarification | Confirm garaging + effective date |

### Y38 — Screenshot DMV

| | Before | After |
|---|--------|-------|
| still_needed | `[]` | `['notice_image']` |
| Office knows | Must guess | Ask for full notice |

### Y30 — UW questionnaire

| | Before | After |
|---|--------|-------|
| Category | `missing_signature` / medium | `underwriting_followup` / high |
| Summary | Generic | Includes “Deadline: 3/15/2026” |

---

## Remaining gaps (unchanged cases)

| ID | Score | Gap |
|----|-------|-----|
| Y43 | 88 | Prior UW turn weak in summary |
| Y44 | 79 | Category fixed; merge still thin |
| Y45 | 79 | Premium thread — bill-sent not in collected |
| Y02 | 88 | Chinese cancel — no numeric deadline in collected |

---

## Conclusion

Extraction fixes recovered **+3.0 points** on the battery with **zero scenario regressions**. Biggest lift: **Understanding (+2.8)**. Missing-info and multi-turn need a follow-on sprint for append/summary merge depth.

---

*End of P16-Y Phase 7 — Before vs After*

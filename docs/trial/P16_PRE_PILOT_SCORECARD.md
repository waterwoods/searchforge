# P16 Pre-Pilot Scorecard

**Sprint:** P16-PRE-PILOT-STRESS-TEST-SPRINT · Phase 7  
**Date:** 2026-06-06  
**Run:** 2026-06-06T10:43:17Z  
**Scenarios:** 33 (ST01–ST20 + EC01–EC03 + RL01–RL05 + AP01–AP05)

---

## Aggregate metrics

| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| **Overall pass rate** | **100%** (33/33) | ≥95% | ✅ |
| Route accuracy | 100% | ≥95% | ✅ |
| Field extraction accuracy | 98.2/100 avg | ≥80 | ✅ |
| Append integrity | 100% (10/10 append scenarios) | 100% | ✅ |
| Continuity integrity | 100% (12/12 multi-turn) | 100% | ✅ |
| Append regressions | 0 | 0 | ✅ |
| Continuity regressions | 0 | 0 | ✅ |
| Commercial P0 open | 0 | 0 | ✅ |
| Avg minutes saved vs manual | 5.0 min | ≥4 min | ✅ |

---

## Dimension scores (0–100)

| Dimension | Score | Notes |
|-----------|-------|-------|
| Route accuracy | **100** | All 33 routed `add_car` |
| Field extraction accuracy | **98** | Avg quality 98.2; weakest ST06 at 88 (correct behavior) |
| Append integrity | **100** | ST18–ST20 + AP01–AP05 — zero slot loss |
| Continuity integrity | **100** | ST16–ST17 + RL01–RL05 + EC02–EC03 — zero field loss |
| Broker usability | **96** | Actionable Chinese office steps on all cases |
| Office usability | **94** | Collected/still_needed clear; relative dates noted |
| Customer clarity | **95** | Drafts ask gaps only; insurance-card-sent handled |
| Commercial readiness | **92** | 0 P0; 4 P1 watch items documented |

---

## Composite pilot readiness score

```
Route (15%)           × 100 = 15.0
Field extraction (20%) × 98  = 19.6
Append integrity (15%) × 100 = 15.0
Continuity (15%)      × 100 = 15.0
Broker usability (15%) × 96  = 14.4
Office usability (10%) × 94  =  9.4
Customer clarity (10%) × 95  =  9.5
                              ─────
Total                         97.9 → 98/100
```

# **Pilot readiness score: 98/100**

---

## Category breakdown

| Category | Count | Pass | Avg quality |
|----------|-------|------|-------------|
| Realistic (ST01–ST20) | 20 | 20/20 | 97.4 |
| Edge (EC01–EC03) | 3 | 3/3 | 100.0 |
| Return-later (RL01–RL05) | 5 | 5/5 | 97.8 |
| Append battery (AP01–AP05) | 5 | 5/5 | 100.0 |

---

## Lowest-scoring cases (all still PASS)

| ID | Quality | Issue |
|----|---------|-------|
| ST06 | 88 | Undecided driver — correct still_needed |
| ST04 | 92 | Mixed "我drive" driver parse |
| ST10 | 93 | Vehicle swap mid-thread |
| ST01 | 95 | Delivery date relative handling |
| ST11 | 95 | Shared-family driver ambiguity |
| ST15 | 95 | Minimal opener needs turn 2 |

---

## Comparison to prior sprint (P16-Z24)

| Metric | P16-Z24 | Pre-pilot stress test |
|--------|---------|----------------------|
| Scenarios | 30 | 33 |
| Pass rate | 100% | 100% |
| Avg quality | 96.6 | **98.2** |
| Append battery | 22/22 | 10/10 (dedicated + inline) |
| SoCal Chinese realism | Partial | **Full 20-case pack** |

---

*Source: [`P16_STRESS_TEST_RESULTS.md`](./P16_STRESS_TEST_RESULTS.md)*

# P16 Time Savings Tracker

**Sprint:** P16-CK-REAL-PILOT-SPRINT · Phase 3  
**Success threshold:** ≥ 4 min saved per case (average across completed cases)  
**Simulation baseline:** 6.2 min/case (P16-Z24, 30 scenarios)

---

## Per-case savings

| Case ID | Date | Traditional est. (min) | Actual P16 (min) | Savings (min) | Running avg (min) |
|---------|------|------------------------|------------------|---------------|-------------------|
| CK-001 | | | | | |
| CK-002 | | | | | |
| CK-003 | | | | | |
| CK-004 | | | | | |
| CK-005 | | | | | |
| CK-006 | | | | | |
| CK-007 | | | | | |
| CK-008 | | | | | |
| CK-009 | | | | | |
| CK-010 | | | | | |

**Source:** [`P16_CASE_EVIDENCE_LOG.md`](./P16_CASE_EVIDENCE_LOG.md)

---

## Aggregate metrics (update after each completed case)

| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| **Cases completed** | 0 / 10 | 10 | |
| **Average savings** | — min | ≥ 4 min | |
| **Median savings** | — min | ≥ 4 min | |
| **Best case** | — min (CK-___) | — | |
| **Worst case** | — min (CK-___) | ≥ 0 min | |
| **Cases ≥ 4 min saved** | 0 / 10 | ≥ 7 recommended | |
| **Cases < 4 min saved** | 0 / 10 | ≤ 3 acceptable | |

---

## Projections (fill when ≥ 3 cases completed)

Assumptions: use **running average savings** below; adjust volume to Chen Kui's stated weekly add-car count.

| Broker weekly add-car volume | Cases/week | Hours saved/week | Hours saved/month (4.3 wk) |
|------------------------------|------------|------------------|----------------------------|
| Low (10) | 10 | | |
| Medium (50) | 50 | | |
| High (100) | 100 | | |

**Formulas:**

```
Hours saved/week = (cases/week × avg savings min) / 60
Hours saved/month = hours saved/week × 4.3
```

**Simulation reference** (50 cases/week @ 6.2 min): ~5.2 hr/week · ~22.3 hr/month — see [`P16_TIME_SAVINGS_MODEL.md`](./P16_TIME_SAVINGS_MODEL.md).

---

## Comparison to simulation

| Source | Avg savings | Notes |
|--------|-------------|-------|
| P16-Z24 simulation (30 cases) | 6.2 min | Pre-pilot |
| Real pilot (running) | — min | This tracker |
| Delta (real − sim) | — min | Negative = pilot underperforms sim |

---

## Threshold gate (CK-010)

| Gate | Required | Actual | Status |
|------|----------|--------|--------|
| 10 cases completed | YES | | |
| Average savings ≥ 4 min | YES | | |
| Median savings ≥ 4 min | Recommended | | |

**Pilot time-savings pass:** YES / NO / IN PROGRESS

---

*Phase 3 complete — time savings tracker ready.*

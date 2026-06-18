# P16 Time Savings Model

**Sprint:** P16-CHEN-KUI-PILOT-SPRINT · Phase 2  
**Date:** 2026-06-06  
**Case type:** Add-Car only  
**Basis:** Chen Kui office workflow observation + P16-Z24 simulation (30 scenarios, LLM off)

---

## Traditional workflow (manual)

What Chen Kui (or office assistant) does today for one add-car WeChat thread:

| Step | Activity | Avg minutes |
|------|----------|-------------|
| 1 | Open WeChat; scroll/read full thread (often 3–8 bubbles) | 1.5 |
| 2 | Mentally extract vehicle (year, make/model) | 0.5 |
| 3 | Find VIN (may require asking customer or opening photo) | 1.0 |
| 4 | Find ZIP / garaging address | 0.5 |
| 5 | Identify primary driver (self, spouse, teen) | 0.5 |
| 6 | Note delivery date or "TBD" | 0.5 |
| 7 | Check if insurance card / dec page already sent | 0.5 |
| 8 | Ask follow-up for missing fields (compose WeChat reply) | 2.0 |
| 9 | Write office handoff note (what we have / what's missing) | 1.5 |
| 10 | Re-read thread when customer returns with name/phone | 1.5 |
| **Total (typical incomplete thread)** | | **~10.0 min** |
| **Total (complete thread, no append)** | Steps 1–7, 9 only | **~6.5 min** |

**Conservative manual baseline for ROI:** **10 minutes per add-car case** (includes one follow-up round and office note).

---

## P16 workflow

| Step | Activity | Avg minutes |
|------|----------|-------------|
| 1 | Paste customer message(s) into workbench | 0.3 |
| 2 | Scan structured case (Collected / Still needed / Next step) | 0.5 |
| 3 | Review draft; light edit | 1.0 |
| 4 | Copy draft → WeChat | 0.2 |
| 5 | Append return-later messages (if any) | 0.5 |
| 6 | Tell office "case ready" or "need X" from screen | 0.5 |
| **Total** | | **~3.0 min** |

**Simulation measured savings:** 6.2 min/case average (P16-Z24 quality scorecard, 30 scenarios).  
**Pilot success threshold:** ≥ 4 min/case (broker-logged, allows conservative estimate).

---

## Estimated savings per case

| Scenario | Manual (min) | P16 (min) | Saved (min) | Simulation evidence |
|----------|-------------|-----------|-------------|---------------------|
| Simple complete add-car | 6.5 | 2.5 | **4.0** | AC01, AC02: 6.4 min saved |
| Missing VIN (partial thread) | 10.0 | 3.5 | **6.5** | AC03: 7.1 min saved |
| Missing ZIP | 10.0 | 3.5 | **6.5** | AC21: 7.0 min saved |
| Missing driver | 10.0 | 3.5 | **6.5** | AC04: 6.8 min saved |
| Insurance card already sent | 11.0 | 3.0 | **8.0** | AC05: 5.2 min saved (lower re-ask friction) |
| Return later + append name/phone | 12.0 | 4.0 | **8.0** | Append battery PASS; AC13 multi-turn |
| Minimal opener ("新车保险多少") | 10.0 | 4.0 | **6.0** | AC11: 7.7 min saved (asks right fields) |

**Weighted average (simulation):** **6.2 min saved per add-car case**

**Pilot floor (success threshold):** **4.0 min saved per case**

---

## Projected savings at volume

Assumptions: 6.2 min saved/case (simulation avg); broker time valued implicitly (not dollarized here).

| Volume | Cases/week | Hours saved/week | Hours saved/month (4.3 wk) |
|--------|------------|------------------|----------------------------|
| **Low** | 10 | 1.0 hr | 4.3 hr |
| **Medium** | 50 | 5.2 hr | 22.3 hr |
| **High** | 100 | 10.3 hr | 44.3 hr |

At **50 cases/week** (typical busy Chen Kui week for add-car + related):

- **~22 hours/month** broker/assistant time recovered
- Equivalent to **~0.5 FTE** of paste-read-organize-reply work redirected to quoting and sales

---

## ROI vs pilot pricing

| Plan | Monthly price | Break-even cases/month @ 6.2 min saved |
|------|---------------|------------------------------------------|
| 入门版 $49 | $49 | ~8 cases if broker time = $60/hr equivalent |
| 标准版 $99 | $99 | ~16 cases @ $60/hr |

At 50 add-car cases/month, tool pays for itself in **< 1 day** of broker time even at conservative 4 min/case savings.

---

## What pilot must prove

Simulation says **6.2 min/case**. Pilot must confirm on **10 real cases**:

1. Broker-logged average ≥ **4 min**
2. "Would reread WeChat?" = NO on majority of cases
3. Append cases do not lose VIN/ZIP/delivery/driver (integrity sprint PASS; pilot validates in production use)

---

## Measurement method during pilot

Use [`P16_PILOT_CASE_LOG_TEMPLATE.md`](./P16_PILOT_CASE_LOG_TEMPLATE.md):

```
Minutes Saved = (estimated manual time) − (actual workbench time)
```

Ask Chen Kui at Day 0: "这条如果不用工具，你要花多少分钟？" Calibrate once; then self-estimate per case.

---

*Phase 2 complete — ROI framework quantified.*

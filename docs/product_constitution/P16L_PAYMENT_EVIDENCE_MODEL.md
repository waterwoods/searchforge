# P16-L Payment Evidence Model

**Date:** 2026-06-01  
**Sprint:** P16-L — Real Market Validation  
**Authority:** `NORTH_STAR_V1.md` §8–9, `DAY7_PAYMENT_CHECKLIST.md`, `FIRST_PAYMENT_FORECAST.md`, `P16K_PAYMENT_READINESS_AUDIT.md`  
**Rule:** Measurable criteria only. No optimism. No guessing.

---

## Price tiers (locked)

| Tier | Price | Scope (constitution) |
|------|-------|----------------------|
| 入门版 | **$49/mo** | Broker-only; 1+ workflow clearly saved ~30+ min/week |
| 标准版 | **$99/mo** | Office-wide; 2+ scenarios; draft used ≥2×; assistant adoption signal |

Payment method: manual invoice (Zelle/Venmo/WeChat). No Stripe v1.

---

## Evidence model overview

```
Payment justified = Minimum evidence (all required)
                 OR Strong evidence (any 2+ accelerates ask)
                 
Payment blocked  = Any deal breaker (automatic No)
```

Evidence must come from **`TRIAL_OBSERVATION_LOG_V3.md`** + Day 7 call + artifacts in `results/trial_logs/`.

---

## $49/mo — evidence requirements

### Minimum evidence (ALL required — missing any = do not invoice)

| # | Criterion | Measurable threshold | Source |
|---|-----------|------------------------|--------|
| M1 | Real cases pasted | ≥3 cases with raw message source logged | Log v3 per-case |
| M2 | Draft used | ≥2 cases with Draft used? = Y and edit level ≠ 没用 | Log v3 per-case |
| M3 | Workbench habit | Opened ≥4 of 7 days | Log v3 daily summary |
| M4 | Quantified value | ≥1 "Worked?" = Y with Minutes saved ≥5 **OR** week total ≥30 min | Log v3 |
| M5 | Continuation intent | Day 7 Q1 = Yes or Maybe with named scenario | Day 7 checklist |
| M6 | Payment willingness | Day 7 Q4 = **Yes** on $49 (not Maybe) | Day 7 checklist |
| M7 | No deal breaker | Zero deal breakers below | Log + Day 7 |
| M8 | Commercial complete | Invoice sent with filled payment IDs + PILOT_TERMS acknowledged | WeChat/email artifact |

**If M1–M8 all pass:** Andy may send `INVOICE_TEMPLATE_49.md` same day.

---

### Strong evidence (optional — increases confidence, not substitutes for minimum)

| # | Criterion | Threshold | Why it matters |
|---|-----------|-----------|----------------|
| S1 | Cancellation scenario worked | ≥1 cancellation with Worked? = Y, Minutes ≥10 | North Star wedge #1 |
| S2 | Broker unprompted quote | Verbatim quote naming time saved | Testimonial + second broker gate |
| S3 | Draft 小改 or 中改 only | ≥2 cases; no 大改/没用 on primary scenario | Draft trust |
| S4 | Confidence delta | After ≥ Before +2 on ≥2 cases | Product comprehension |
| S5 | Self-initiated Day 2 open | Opened workbench Day 2 without founder ping | Habit signal |
| S6 | Would do manually otherwise = N | ≥2 cases | Replacement not supplement |
| S7 | Screenshot proof | Paste → case → WeChat draft (PII redacted) | Audit trail |

**Strong evidence count ≥3:** $49 probability moves from base 45% → ~60% (per P16-K forecast + lever analysis).

---

### Deal breaker evidence ($49 — any one = No invoice)

| # | Deal breaker | Detection |
|---|--------------|-----------|
| D1 | Trust-breaking triage | Wrong urgency on cancellation causing broker to distrust all output; broker says "不敢用" |
| D2 | Zero real cases | Only demo queue used entire week |
| D3 | Draft never used | 0 cases with Draft used? = Y after ≥3 pastes |
| D4 | Abandonment | Opened ≤1 day after Day 0 without URL outage |
| D5 | Fit mismatch | Broker expected WeChat sync, auto-send, or OCR; hard no after reset |
| D6 | Founder over-help | Founder assisted? = Y on >50% of cases (invalidates solo value) |
| D7 | URL reliability failure | >2 days blocked by login/503 during trial week |
| D8 | Explicit No on $49 | Day 7 Q4 = No with no fixable blocker |
| D9 | Minutes saved &lt;15/week | Broker honest estimate; structure alone insufficient |
| D10 | Payment case = promise | No logged case IDs; only founder narrative |

---

## $99/mo — evidence requirements

### Minimum evidence (ALL required on top of $49 minimum)

| # | Criterion | Measurable threshold | Source |
|---|-----------|------------------------|--------|
| M99-1 | All $49 minimum (M1–M8) | Pass | Above |
| M99-2 | Multi-scenario proof | ≥2 scenario types with Worked? = Y (e.g. cancellation + missing-doc) | Log v3 |
| M99-3 | Office ROI narrative | Broker names assistant or "整个办公室" without founder prompting | Day 7 Q2/Q5 |
| M99-4 | Week minutes | Aggregate ≥45 min/week saved (broker estimate, logged) | Log v3 summary |
| M99-5 | Payment willingness | Day 7 Q5 = **Yes** on $99 | Day 7 checklist |
| M99-6 | Assistant signal | Assistant quote logged OR assistant opened workbench ≥1 day OR broker commits to train assistant | Log v3 |

**If any M99 missing:** Lead with $49 only. Do not push $99.

---

### Strong evidence ($99)

| # | Criterion | Threshold |
|---|-----------|-----------|
| S99-1 | Assistant used draft | Assistant quote + Draft used? = Y on ≥1 case |
| S99-2 | Add-car worked | Add-car scenario Worked? = Y with follow-up paste used |
| S99-3 | Queue habit | Broker reopens case from queue ≥2 times (not always new paste) |
| S99-4 | Broker chooses $99 unprompted | Names $99 before Andy mentions price |
| S99-5 | Testimonial permission | Y to use quote for second broker |

---

### Deal breaker evidence ($99)

| # | Deal breaker | Detection |
|---|--------------|-----------|
| D99-1 | All $49 deal breakers | Any D1–D10 |
| D99-2 | Single-scenario only | Only cancellation worked; missing-doc/add-car failed |
| D99-3 | Assistant refused | Assistant quote: would revert to WeChat; no mandate |
| D99-4 | $49 sufficient | Broker says "$49 enough for me alone" |
| D99-5 | Tier feels arbitrary | Broker cannot explain difference after one-pager read |

---

## Decision matrix (Day 7)

| Evidence state | $49 action | $99 action |
|----------------|------------|------------|
| All M1–M8, no M99 | **Invoice $49** | Do not offer |
| All M1–M8 + M99-2 to M99-6 | Offer $49 first | **Invoice $99** if broker confirms office use |
| M1–M7 pass, M6 = Maybe | Fix blocker or 3-day extension | No |
| Any deal breaker | No invoice; document kill | No |
| &lt;2 of 4 behavioral gates | No invoice; extend or kill | No |

---

## Evidence artifacts checklist

| Artifact | Required for $49 | Required for $99 |
|----------|------------------|------------------|
| Completed log v3 | ✅ | ✅ |
| Filled Day 7 checklist | ✅ | ✅ |
| ≥1 screenshot (redacted) | Recommended | ✅ |
| Broker quote (verbatim) | Recommended | ✅ |
| Assistant quote | — | ✅ if assistant involved |
| Invoice + terms sent | ✅ | ✅ |
| Payment received confirmation | ✅ (within 7 days of invoice) | ✅ |

---

## What is NOT evidence

| Not evidence | Why |
|--------------|-----|
| Andy says "it should save time" | Founder bias |
| Demo queue cases only | Not real office work |
| Guardrail 13/13 PASS | Engineering gate, not broker gate |
| Product score 74/100 | Internal metric |
| Chen Kui said "interesting" on Day 0 | No quantified week |
| Founder rewrote draft for broker | Invalidates draft-used signal |
| "Maybe" on payment question | Not willingness |

---

## Probability anchors (from P16-K, unchanged)

| Stage | $49 | $99 |
|-------|-----|-----|
| Today (pre-trial) | 12% | 5% |
| After Day 7, all minimum pass | 45% | 20% |
| After Day 7, all minimum + strong | ~60% | ~35% |
| Any deal breaker | ~0% | ~0% |

---

*End of P16-L Payment Evidence Model*

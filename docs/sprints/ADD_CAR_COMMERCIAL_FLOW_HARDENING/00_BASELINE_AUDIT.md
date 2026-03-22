# Baseline Audit — Add-Car Commercial Flow

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** Honest audit of add-car flow as one commercial module before hardening.

---

## 1. What Already Feels Strong

| Area | Status | Notes |
|------|--------|-------|
| Quote-ready visibility | **Strong** | quote_ready / almost_ready / need_more in triage, case, workbench |
| Collected vs still-needed | **Strong** | year, make_model, zip, delivery_date, primary_driver, vin, name, phone |
| Broker handoff | **Strong** | broker_next_step with concrete vehicle; contact hint when missing |
| Customer identity | **Strong** | customer_name, customer_phone from triage extraction |
| Case persistence | **Strong** | case_store, append_follow_up_message, case_messages |
| Side-question handling | **Strong** | Garaging, coverage answered before handoff (HT8, HT11) |
| Correction handling | **Strong** | Same case; merged text; correction badge |
| Handoff timing | **Strong** | 13/13 handoff timing; 51/51 multi-turn; 12/12 broker stress |

---

## 2. What Still Feels Stitched or Thin

| Area | Status | Notes |
|------|--------|-------|
| Add-car + materials sent | **Weak** | Customer says "发你微信了" in add-car context — broker_next_step was generic |
| Materials-sent handoff reply | **Weak** | No warmer reassurance when customer says materials sent |
| Driver ask vs materials sent | **Weak** | Would ask for driver after "registration 发你微信了" — blocks handoff |
| Combination scenarios | **Thin** | Few simulations for quote-ready + already_sent, correction + materials |

---

## 3. Classification

| Category | Items |
|----------|-------|
| **Strong** | Quote-ready, collected/still-needed, broker handoff, identity, case persistence, side-question, correction |
| **Acceptable** | Category display, urgency, follow-up tracking |
| **Weak** | Add-car + materials sent (already_sent) handling |
| **High-value to improve now** | Add-car + already_sent broker_next_step; materials_sent skip driver ask |

---

## 4. Biggest Current Weaknesses

| Weakness | Impact |
|----------|--------|
| **Add-car + "发你微信了" not tailored** | Broker gets generic "Run quote" when customer said materials sent; should say "Verify materials received" |
| **Driver ask blocks materials-sent handoff** | Customer says "下周提车 registration 发你微信了" — system asked for driver instead of handing off |
| **No combination simulation** | Correction + materials sent, quote-ready + already_sent not in simulation pack |

---

## 5. Module-Coherence Gaps

| Gap | Description |
|-----|-------------|
| **Readiness + already_sent** | Quote-ready and "customer says sent" were separate; broker_next_step didn't combine |
| **Contact + materials** | Both can be missing; broker_next_step handled contact but not materials-sent |
| **Correction + materials** | T2 correction, T3 zip+delivery+materials — full combo not tested |

---

*See also: 05_ADD_CAR_WEAK_POINT_FIX_QUEUE_SPEC.md, 06_EXECUTION_OUTLINE.md*

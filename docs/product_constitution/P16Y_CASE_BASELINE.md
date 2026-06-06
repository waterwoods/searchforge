# P16-Y Phase 1 — Case Baseline (20 Examples)

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Source:** Existing scenario pack (`configs/inbox_triage_scenarios.json`) + live `triage_conversation()` outputs (rules path; LLM quota exhausted)  
**Method:** Review triage outputs for office-readiness before P16-Y changes

---

## Executive summary

| Metric | Observation |
|--------|-------------|
| Scenario guardrail | **64/64 PASS** (category + urgency + draft quality) |
| Strong lanes | Cancellation, payment lapse, missing document (DL/dec page), add-car quote |
| Weak lanes (pre-fix) | Address change, coverage Q&A, UW questionnaire, screenshot-only intake |
| Office actionability | **High** — `broker_next_step` rarely generic on top scenarios |
| Missing info | **Uneven** — payment/doc lanes structured; address/coverage/notice-image gaps |

**Pre-sprint Case Intelligence (50-case battery):** **85.6 / 100**

---

## Good outputs (10)

### G1 — Cancellation with deadline (S3 / Y01)

**Input:** `Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.`

| Field | Output |
|-------|--------|
| Category | `cancellation_warning` / `critical` |
| Broker step | Confirm cancellation active; verify payment; call client today with deadline |
| Still needed | `payment_proof_or_screenshot` |
| Collected | `notice_present`, `urgency_due_confusion` |

**Why good:** Office knows urgency, next action, and what to ask client — no re-read of notice required.

---

### G2 — Already-paid cancellation dispute (Y03)

**Input:** `保险公司说我的保单7天后要cancel，我已经付了呀`

| Field | Output |
|-------|--------|
| Category | `cancellation_warning` / `critical` |
| Summary | “Collected: client says already paid.” |
| Still needed | `verify_carrier_received` |

**Why good:** Captures client claim vs carrier notice — broker verifies with carrier, not re-asks for payment blindly.

---

### G3 — Missing DL, client says sent (S2 / Y06)

**Input:** `Underwriting requested driver's license copy. Client says "I already sent it last week."`

| Field | Output |
|-------|--------|
| Category | `missing_document` |
| Collected | `requested_driver_license`, `customer_says_sent_driver_license`, `underwriting_followup` |
| Still needed | `verify_carrier_received` |

**Why good:** Structured doc chase — office checks inbox/carrier, not generic “send DL again.”

---

### G4 — Mixed EN/ZH cancellation (R12)

**Input:** `Carrier notice: Your policy will be cancelled due to non-payment. 这个是不是今天一定要处理？`

| Field | Output |
|-------|--------|
| Category | `cancellation_warning` / `critical` |
| Draft | Chinese — mentions 通知, 今天, 付款 |

**Why good:** Language matches client; urgency preserved across mixed paste.

---

### G5 — Payment failed minimal (R3)

**Input:** `Payment failed`

| Field | Output |
|-------|--------|
| Category | `payment_lapse_expiration` / `high` |
| Broker step | Confirm failure; check carrier balance; fix today |

**Why good:** Minimal input still routes to high-risk lane with same-day action.

---

### G6 — Add-car quote with vehicle (R14 / Y17)

**Input:** `想加一台2021 Tesla Model Y，下周提车，今天能不能先出报价`

| Field | Output |
|-------|--------|
| Category | `customer_question` |
| Summary | “Add car to existing policy.” |
| Draft | Asks for VIN/车型/报价 details in Chinese |

**Why good:** Intent + timeline visible; draft asks for missing quote fields.

---

### G7 — Remove vehicle (R15 / Y20)

**Input:** `客户卖掉旧车了，想把2014 Honda Accord从保单拿掉`

| Field | Output |
|-------|--------|
| Summary | “Remove vehicle from policy.” |
| Broker step | Confirm sale date; remove cleanly |

**Why good:** Office knows transaction type and confirmation fields.

---

### G8 — Underwriting deadline (S5 / Y29)

**Input:** `Underwriting needs clarification on prior claims. Please respond within 10 days.`

| Field | Output |
|-------|--------|
| Category | `underwriting_followup` / `high` |
| Broker step | Gather info; respond before deadline |

**Why good:** High urgency + UW lane correct for carrier follow-up.

---

### G9 — Multi-turn payment + screenshot (Y41)

**Turn 1:** Payment failed notice  
**Turn 2:** Paid yesterday + screenshot  
**Turn 3:** When will coverage be restored?

| Field | Output |
|-------|--------|
| Category | `payment_lapse_expiration` |
| Collected | `already_paid_claimed` |
| Score | **95/100** |

**Why good:** Merges payment dispute across turns; broker verifies restoration.

---

### G10 — Human handoff (R3b)

**Input:** `联系人工`

| Field | Output |
|-------|--------|
| Category | `customer_requested_human` |
| Handoff | Immediate; Chinese office-forward draft |

**Why good:** Zero ambiguity — office calls back.

---

## Bad outputs (10) — pre-P16-Y fixes

### B1 — Address change classified unclear (Y11) ❌→✅ fixed

**Input:** `我搬家了，新地址是94588 Pleasanton，保单地址要改吗？`  
**Was:** `unclear` — generic “内容不够完整”  
**Problem:** Office cannot start garaging update workflow.

---

### B2 — Garaging move English (Y12) ❌→✅ fixed

**Input:** `Moved to 90210 last month — need to update garaging address on both cars`  
**Was:** `unclear`  
**Problem:** Two-car address change invisible to queue preview.

---

### B3 — Add driver misclassified as missing doc (Y14) ❌→✅ fixed

**Input:** `我儿子刚拿驾照，想加到我的保单上，需要准备什么？`  
**Was:** `missing_document` (驾照 + 需要 triggered doc chase)  
**Problem:** Wrong workflow — office chases DL instead of add-driver intake.

---

### B4 — Liability / umbrella question (Y27) ❌→✅ fixed

**Input:** `客户问 liability 100/300 够不够，要不要加 umbrella`  
**Was:** `unclear`  
**Problem:** Coverage advisory request lost.

---

### B5 — Windshield vs deductible (Y37) ❌→✅ fixed

**Input:** `玻璃裂了，走保险还是自己修？deductible 500`  
**Was:** `unclear` (full-width ？ not detected as question)  
**Problem:** Claim/coverage decision not routed.

---

### B6 — UW questionnaire → signature (Y30) ❌→✅ fixed

**Input:** `UW questionnaire incomplete — need signed form by 3/15/2026`  
**Was:** `missing_signature` / medium  
**Problem:** Wrong urgency and lane; deadline lost.

---

### B7 — 核保 accident mismatch (Y31) ❌→✅ fixed

**Input:** `核保说之前事故记录对不上，要我补说明，deadline Friday`  
**Was:** `unclear`  
**Problem:** UW follow-up with deadline not surfaced.

---

### B8 — Screenshot DMV, no body (Y38) ❌→✅ fixed

**Input:** `客户发来一张截图 上面是dmv的信 看不懂`  
**Was:** No `notice_image` in still_needed  
**Problem:** Office doesn't know they still need the actual notice text/image.

---

### B9 — Renewal + policy number (Y34) ❌→✅ fixed

**Input:** `Policy #CA-8829101 renews March 15 — client wants to shop around first`  
**Was:** `unclear`; policy number not in summary  
**Problem:** Retention case missing policy anchor.

---

### B10 — Multi-turn correction (Y44) ⚠️ partial

**Turn 1:** 保单要cancel了  
**Turn 2:** 不是payment问题，是地址不对被UW退回了  
**Was:** `unclear` (67/100)  
**After fix:** `customer_question` (79/100) — category improved; prior-turn context still weak in summary.

---

## Baseline scores (50-case battery, pre-fix)

| Dimension | Avg / 25 |
|-----------|----------|
| Understanding | 22.2 |
| Missing Info | 16.9 |
| Office Actionability | 25.0 |
| Multi-message | 21.5 |
| **Total** | **85.6 / 100** |

---

*End of P16-Y Phase 1 — Case Baseline*

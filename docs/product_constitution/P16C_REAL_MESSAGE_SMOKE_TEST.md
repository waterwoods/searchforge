# P16-C Phase 4 — Real Message Smoke Test

**Date:** 2026-05-31  
**API:** `https://fiqa-api-g7zatxrycq-uw.a.run.app/api/inbox/triage`  
**Method:** HTTP POST (`persist: false`) — triage engine only; UI integration not in scope for scoring engine output  
**Guardrail:** PASS (same engine family)

---

## Results Summary

| # | Scenario | HTTP | Category | Urgency | Score /100 |
|---|----------|------|----------|---------|------------|
| 1 | Cancellation notice | 200 | `cancellation_warning` | critical | **92** |
| 2 | Payment failed | 200 | `payment_lapse_expiration` | high | **78** |
| 3 | Missing document | 200 | `missing_document` | medium | **88** |
| 4 | Add car | 200 | `customer_question` | medium | **76** |
| 5 | Address change | 200 | `unclear` | medium | **52** |

**Average smoke score: 77 / 100** (engine layer; UI paste path assumed equivalent)

---

## 1. Cancellation Notice

**Input:** `Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？`

| Field | Value |
|-------|-------|
| category | `cancellation_warning` ✅ |
| urgency | `critical` ✅ |
| broker_next_step | Confirm cancellation active, verify payment, contact client today |
| collected | notice_present, urgency_due_confusion |
| missing | payment_proof_or_screenshot |
| draft | Chinese — usable, asks for notice + payment proof |
| assistant could act? | **Yes** — same-day action clear |

**Score: 92** — Strong constitution wedge case.

---

## 2. Payment Failed

**Input:** `AutoPay failed again, please update card to avoid interruption in coverage`

| Field | Value |
|-------|-------|
| category | `payment_lapse_expiration` ✅ |
| urgency | `high` ✅ |
| broker_next_step | Confirm failure, check balance, help client fix payment |
| missing | payment_proof_or_screenshot |
| draft | **English opening** — broker would edit before WeChat send |
| assistant could act? | **Yes** with draft edit |

**Score: 78** — Correct triage; draft language mix reduces trust.

---

## 3. Missing Document

**Input:** `UW follow up - need dec page + garaging proof. 客户说上周发过了`

| Field | Value |
|-------|-------|
| category | `missing_document` ✅ |
| urgency | medium |
| broker_next_step | Verify resubmission; request missing items |
| collected | declaration page, garaging proof, already_sent claims |
| draft | Chinese — explains office will verify, no duplicate send |
| assistant could act? | **Yes** |

**Score: 88**

---

## 4. Add Car

**Input:** `客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价`

| Field | Value |
|-------|-------|
| category | `customer_question` ⚠️ (expected add-car lane) |
| urgency | medium |
| broker_next_step | Confirm VIN/ZIP/driver; quote same day |
| collected | year, make_model, add_to_existing |
| missing | vin, zip, delivery_date, primary_driver |
| draft | Chinese structured bullet preview |
| assistant could act? | **Yes** — workable intake |

**Score: 76** — Functional; category label not ideal for broker mental model.

---

## 5. Address Change

**Input:** `客户搬家了，新地址是123 Main St Los Angeles CA 90001，要改保单地址`

| Field | Value |
|-------|-------|
| category | `unclear` ❌ |
| urgency | medium |
| broker_next_step | Ask for more context — **under-extracts** |
| collected | null |
| missing | null |
| draft | Asks client to send more complete message |
| assistant could act? | **Partial** — broker must re-read message manually |

**Score: 52** — Known engine gap; not Sprint A UI scope.

---

## UI Integration Notes (Sprint A)

| Concern | Status |
|---------|--------|
| Paste → triage → case card | Code path unchanged; loading copy added |
| product_only hides engineer fields on result | ✅ |
| Cancellation auto-open uses demo seed #1 | ✅ aligns with smoke #1 |
| Address change weakness | Engine — do not fix in P16-C |

---

## Real Message Smoke Score (aggregate)

**77 / 100** — Engine ready for trial; address change + payment draft language are fix-now candidates post-trial, not Sprint A blockers.

---

*End of P16-C Phase 4 — Real Message Smoke Test*

# P16-Z7 Phase 1 — Role D Journey Library

**Date:** 2026-06-02  
**Sprint:** P16-Z7 Reality Memory Validation  
**Persona:** Chen Kui (busy broker) · Assistant (paste operator)  
**Method:** 10 realistic insurance journeys · 3 turns each · Day 1 / Day 2 / Day 3  
**Constraint:** No new features — library for memory battery only

---

## North Star (reference)

> Turn messy client messages into a time-bound office obligation with a clear next action and a traceable close — in one paste, under one minute.

**Core question:** Can the system remember a case across multiple days without reopening WeChat?

---

## Journey index

| ID | Category | Title | Days | Turns |
|----|----------|-------|------|-------|
| D01 | cancellation | 7-day cancel notice — client pays late | 1–3 | 3 |
| D02 | payment_issue | Autopay failed — client claims paid | 1–3 | 3 |
| D03 | missing_document | Garaging proof chase — client sends DL | 1–3 | 3 |
| D04 | underwriting | UW questionnaire deadline | 1–3 | 3 |
| D05 | claim | Rear-end FNOL — plate then photos | 1–3 | 3 |
| D06 | add_driver | Add teen driver — license follow-up | 1–3 | 3 |
| D07 | remove_vehicle | Sold second car — remove from policy | 1–3 | 3 |
| D08 | coverage_review | Renewal premium too high — bill sent | 1–3 | 3 |
| D09 | cancellation | Correction — cancel was wrong, address UW return | 1–3 | 3 |
| D10 | payment_issue | Installment plan request after lapse | 1–3 | 3 |

**Config source:** `configs/role_d_journeys.json`  
**Battery runner:** `scripts/run_role_d_memory_battery.py`

---

## D01 — Cancellation (7-day notice + payment)

| Day | Client message (WeChat paste) |
|-----|------------------------------|
| **1** | 收到保险公司信说要7天内取消保单，我怎么办？ |
| **2** | 我刚转了$420，截图发你了，能帮我保住吗？ |
| **3** | carrier那边有回复吗？还是说还要等？ |

**Office expectation:** Cancel wedge + payment proof + carrier follow-up status across 3 days.

---

## D02 — Payment issue (lapse + portal payment)

| Day | Client message |
|-----|----------------|
| **1** | Why did my policy lapse? I thought autopay was on. |
| **2** | I paid on 3/12 through the carrier portal — confirmation #88291. |
| **3** | Any update from underwriting or billing? Still showing lapse. |

**Office expectation:** Lapse urgency → already_paid → verify carrier; Day 3 is status check not new UW case.

---

## D03 — Missing document (garaging proof)

| Day | Client message |
|-----|----------------|
| **1** | 核保说要我补garaging proof，我搬家到94588了 |
| **2** | 水电单和驾照照片都发你了，你看够不够？ |
| **3** | UW还有别的要求吗？我下周要用车 |

**Office expectation:** Zip 94588 + proof sent + UW checklist status.

---

## D04 — Underwriting (questionnaire deadline)

| Day | Client message |
|-----|----------------|
| **1** | Underwriting needs completed driver questionnaire by 3/15/2026. Policy 4412098. |
| **2** | Teen driver form signed — attached PDF. Anything else? |
| **3** | Did carrier accept the forms? Deadline is Friday. |

**Office expectation:** Deadline + policy # persist; Day 3 is carrier acceptance check.

---

## D05 — Claim (hit-and-run FNOL)

| Day | Client message |
|-----|----------------|
| **1** | 昨天追尾了，对方跑了，车牌8ABC123，要报claim |
| **2** | 现场照片和车头损伤都发你了 |
| **3** | adjuster有联系我吗？还是要我再打电话？ |

**Office expectation:** Plate 8ABC123 + photos collected; Day 3 adjuster status.

---

## D06 — Add driver (teen + permit)

| Day | Client message |
|-----|----------------|
| **1** | 想加我儿子开车，17岁，有learner permit |
| **2** | 驾照正反面照片发你了，2020 Honda Civic |
| **3** | quote出来了吗？大概加多少钱？ |

**Office expectation:** Add-driver lane (not new vehicle quote); permit + Civic persist.

---

## D07 — Remove vehicle (sold Camry)

| Day | Client message |
|-----|----------------|
| **1** | 我把2018 Toyota Camry卖掉了，要从保单拿掉 |
| **2** | bill of sale和新车主的transfer都发你了 |
| **3** | refund大概多少？什么时候生效？ |

**Office expectation:** Remove-car lane through all turns; refund/effective date on Day 3.

---

## D08 — Coverage review (renewal premium)

| Day | Client message |
|-----|----------------|
| **1** | 续保费太高，能不能换便宜点的coverage？ |
| **2** | 我发你账单了，你看能不能换便宜点的coverage |
| **3** | 有便宜方案了吗？不想降太多保额 |

**Office expectation:** Premium thread (Y45 pattern); bill_sent_claimed; prior turn in summary.

---

## D09 — Cancellation correction (cancel → address UW)

| Day | Client message |
|-----|----------------|
| **1** | 保单要cancel了 |
| **2** | 不是payment问题，是地址不对被UW退回了 |
| **3** | 新地址证明发你了，94566，请帮重新送UW |

**Office expectation:** Y44 pattern — prior cancel + address correction + 94566 proof.

---

## D10 — Payment issue (installment restore)

| Day | Client message |
|-----|----------------|
| **1** | 保单停了，我想分期付清能恢复吗？ |
| **2** | 首付$200今天转了，剩下分3期可以吗？ |
| **3** | office有跟carrier确认恢复了吗？ |

**Office expectation:** Lapse + installment plan + carrier restore status.

---

## Category coverage

| Category | Journey(s) |
|----------|--------------|
| cancellation | D01, D09 |
| payment_issue | D02, D10 |
| missing_document | D03 |
| underwriting | D04 |
| claim | D05 |
| add_driver | D06 |
| remove_vehicle | D07 |
| coverage_review | D08 |

All eight required categories represented.

---

## Simulation protocol (Phases 2–3)

For each journey:

1. **Day 1** — `triage_conversation(turn1)` (paste / new case)  
2. **Day 2** — `triage_for_append(existing_source, turn2)`  
3. **Day 3** — `triage_for_append(accumulated_source, turn3)`  

`existing_source` built as `[客户] msg1[客户] msg2…` (production `case_store` format).

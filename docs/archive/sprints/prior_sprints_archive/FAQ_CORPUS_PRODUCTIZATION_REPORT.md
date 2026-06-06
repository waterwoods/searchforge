# FAQ Corpus Productization Report

**Sprint:** FAQ Corpus Productization  
**Date:** 2026-03-14  
**Target:** Chen Kui Insurance Unified Entry

---

## 1. Sprint Theme

**What was chosen:** Turn the auto-insurance FAQ intake corpus into real product assets — scenarios, routing, handling matrix, and founder-readable examples.

**Why now:** The corpus sprint identified 25 realistic question groups. That research is only valuable if it becomes product material the founder can inspect and the system can use. This sprint converts research into product-ready assets.

---

## 2. Control Docs Created

| Doc | Path | Purpose |
|-----|------|---------|
| **Sprint Blueprint** | `docs/sprints/FAQ_CORPUS_PRODUCTIZATION_SPRINT_BLUEPRINT.md` | Why productize, scope, in/out |
| **Execution Outline** | `docs/sprints/FAQ_CORPUS_PRODUCTIZATION_EXECUTION_OUTLINE.md` | Selection, productization targets, routing, testing |
| **Acceptance Criteria** | `docs/sprints/FAQ_CORPUS_PRODUCTIZATION_ACCEPTANCE_CRITERIA.md` | Minimum, high-value, usable, too weak |

---

## 3. Selected Top 5–8 Question Types

| # | Topic | Route | Why Selected |
|---|-------|-------|--------------|
| 1 | **new_car_quote** | LLM | Top frequency, mixed language, progressive ask |
| 2 | **cancellation_warning** | LLM | Critical urgency, must not downgrade |
| 3 | **payment_failed** | LLM | High urgency, lapse risk |
| 4 | **missing_document** | LLM | Turn 1; mixed broker shorthand |
| 5 | **already_sent_followup** | FAST | Turn 2+; rule handoff works |
| 6 | **notice_confusion** | LLM | English notice, client confused |
| 7 | **premium_too_high** | LLM | Retention; must NOT get renewal_reminder |
| 8 | **claim_intake** | LLM | First-response guidance, hit-and-run variant |

**Additional FAST candidates:** what_to_send, add_car_field_followup, handoff_confirmation.

---

## 4. Productization Work

### Simulation Assistant Assets

| Scenario ID | Flow | Title | Notes |
|-------------|------|-------|-------|
| FAQ-RM1 | remove_car | Remove car — 卖车拿掉 | Broker-forwarded; sale date + transfer |
| FAQ-SR1 | dmv_sr22 | SR-22 / DMV suspension help | Mixed broker + client; RAG has DMV content |
| FAQ-W1 | missing_document | What to send — garaging proof 是什么意思 | Turn 2 clarification; FAST when clear |

### Inbox Triage Assets

| Scenario ID | Input | Category | Notes |
|-------------|-------|----------|-------|
| FAQ-SR1 | Need SR-22 filing proof for DMV suspension clearance, what should client bring? | customer_question | SR-22/DMV help |
| FAQ-W1 | garaging proof 是什么意思 | customer_question | Document clarification |
| FAQ-AS1 | 客户说dec page发过了，刚又发了一次 | missing_document | Already sent |
| FAQ-RM1 | 卖车了，怎么把车从保单删掉 | customer_question | Remove car |

### Routing Improvements

- **FAST path:** Already strengthened for already_sent, what_to_send, add_car_field in `triage.py` (existing logic). No code changes needed for this sprint; corpus alignment confirmed.
- **LLM path:** new_car_quote, payment_failed, cancellation_warning, missing_document, notice_confusion, premium_too_high, claim_intake, remove_car — all handled by existing triage logic.

### FAQ Handling Matrix

**Path:** `configs/docs/faq_handling_matrix.md`

- Customer asks → Office says first → Still need → Do NOT overpromise → Trust boundary → Route
- Covers all 8 selected types + FAST summary + Human confirmation required

### Founder-Readable Examples

See **Section 9 — Founder Showcase** below.

---

## 5. Iteration Loop 1

**What changed:** Selected 8 types, created FAQ handling matrix, added 4 inbox triage scenarios + 3 simulation assistant scenarios.

**What improved:**  
- 53/53 inbox triage scenarios pass (was 52)  
- 26/26 simulation assistant scenarios pass (was 23)  
- Guardrail passes  
- State field accuracy, speed routing pass  

**What did not improve:** N/A — no regressions.

**What still looked weak:** FAQ-AS1 initially failed (standalone "发你了" → unclear). Fixed by using contextual message "客户说dec page发过了，刚又发了一次" → missing_document.

**Whether it was worth it:** Yes. Corpus is now productized.

---

## 6. Iteration Loop 2

**What changed:** Added FAQ-RM1 Remove car inbox scenario (卖车了，怎么把车从保单删掉). Fixed FAQ-SR1 simulation (expected handoff turn 2).

**What improved vs loop 1:** Remove car coverage strengthened; SR-22 simulation flow corrected.

**What still remained weak:** None identified.

**Whether it was worth it:** Yes. Small refinements improved coverage.

---

## 7. Optional Loop 3

**Whether used:** No.

**Reason:** Loop 2 achieved sufficient coverage. No clear high-value, low-risk refinement remained. Stopping is the right decision to avoid overengineering.

---

## 8. Validation Summary

| Check | Result |
|-------|--------|
| run_inbox_triage_scenarios.py | 53/53 passed |
| run_simulation_assistant_scenarios.py | 26/26 passed |
| run_multi_turn_simulations.py | 38/38 passed |
| run_adversarial_simulation.py | 27/27 strong |
| run_complex_adversarial_simulation.py | 27/27 strong |
| audit_state_field_accuracy.py | 7/7 passed |
| verify_speed_routing.py | 9/9 OK |
| guardrail_inbox_triage.sh | PASS |

**Limitations:** unified_intake_smoke_check.sh includes manual UI steps; server must be running for API test.

---

## 9. Founder Showcase (REQUIRED)

### Q1 — new_car_quote (Add vehicle, get quote)

- **Customer asks:** 我买了台宝马X5，想问下保费多少钱 / I bought a new BMW X5, how much is insurance?
- **System roughly responds:** 好的，宝马X5。先把年份和车型发我，我就能帮你算。 / Got it, BMW X5. Send me the year and make/model so I can run the quote.
- **Still need to collect:** year, model or VIN, zip, delivery date, primary driver
- **Route:** LLM
- **Why this helps:** Top frequency; progressive ask (1–2 things at a time) avoids overwhelming; human confirms quote.

---

### Q2 — cancellation_warning (Policy will cancel)

- **Customer asks:** Notice: Policy will be cancelled in 7 days due to non-payment. / 保险公司说我的保单7天后要cancel
- **System roughly responds:** 这个通知说明保单有取消风险。请把通知和付款记录发我，我先帮你确认；如果还没付，今天尽快处理。
- **Still need to collect:** notice, payment proof
- **Route:** LLM
- **Why this helps:** Critical urgency; must not downgrade to low; human confirms status.

---

### Q3 — payment_failed (Payment issue, lapse risk)

- **Customer asks:** Payment failed. Your card on file was declined. / 客户说 payment failed，现在怎么办
- **System roughly responds:** 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
- **Still need to collect:** notice, payment screenshot
- **Route:** LLM
- **Why this helps:** High urgency; today action; human verifies with carrier.

---

### Q4 — missing_document (UW requested, client says sent)

- **Customer asks:** Underwriting requested driver's license copy. Client says I already sent it last week.
- **System roughly responds:** They still need the driver's license copy. Please send it again when you can, and if you already sent it, tell me so I can check on my side.
- **Still need to collect:** item identified, sent status clear
- **Route:** LLM (Turn 1)
- **Why this helps:** Mixed broker shorthand; ask for resend or verify; human confirms carrier received.

---

### Q5 — already_sent_followup (Confirmation that document was sent)

- **Customer asks:** 发你了 / 我发了截图 / sent / 上周发过了
- **System roughly responds:** 您说的情况已整理好了，办公室会尽快处理，有结果会联系您。
- **Still need to collect:** (none — broker verifies)
- **Route:** FAST
- **Why this helps:** Turn 2+; clear pattern; rule handoff; no LLM needed.

---

### Q6 — notice_confusion (English notice, need explanation)

- **Customer asks:** 客户发来一张DMV的信，问这是什么意思？我需要做什么？ / what does this notice mean
- **System roughly responds:** 英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。
- **Still need to collect:** full notice, clearer photo
- **Route:** LLM
- **Why this helps:** Reassure; ask for notice; human interprets; avoid generic fallback.

---

### Q7 — premium_too_high (Premium review, want to lower)

- **Customer asks:** 客户说这个月保费太高了，能不能看看怎么降一点 / Client says renewal premium is too high
- **System roughly responds:** 一般有办法的。我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。
- **Still need to collect:** policy, renewal notice, bill
- **Route:** LLM
- **Why this helps:** Retention; must NOT get renewal_reminder; human reviews options; no dollar promise.

---

### Q8 — claim_intake (Accident, first-step guidance)

- **Customer asks:** 刚出事故了，要收集什么？ / Car accident just happened, what should I collect?
- **System roughly responds:** 事故刚发生的话，先确保人没事，再拍现场照片、记下对方车牌和保险信息。把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。
- **Still need to collect:** accident details, photos, other driver info
- **Route:** LLM
- **Why this helps:** First-response guidance; hit-and-run variant emphasizes plate, photos; human handles claim.

---

## 10. Final Judgment

1. **Did the FAQ corpus become a real product asset?** Yes. Handling matrix, 7 new scenarios, and founder showcase are in place.

2. **Which selected question types are now strongest?** new_car_quote, cancellation_warning, payment_failed, missing_document, claim_intake.

3. **Which ones are best for Simulation Assistant?** add_car (SIM3, SIM15), missing_document (SIM2), claim (SIM5), renewal_premium (SIM6), remove_car (FAQ-RM1).

4. **Which ones are best for FAST routing?** already_sent_followup, what_to_send, add_car_field_followup, handoff_confirmation.

5. **Which ones must stay behind human confirmation?** cancellation_warning, payment_failed, missing_document (customer_says_sent), add_car (VIN, primary_driver), moving_zip_change, adding_driver.

6. **What is the single best next move after this sprint?** Add 2–3 more real-customer phrasings from broker logs to the corpus; run a live pilot week with the handling matrix; measure how often each type appears in the queue.

---

## 11. Iteration Log

| Loop | What changed | What got better | What did not improve | Worth it? | Next step |
|------|--------------|----------------|----------------------|-----------|-----------|
| 1 | Selected 8 types, matrix, 7 scenarios | 53 inbox + 26 sim pass; guardrail pass | FAQ-AS1 failed initially | Yes | Fix FAQ-AS1; add remove_car |
| 2 | FAQ-AS1 fix; FAQ-RM1 add; FAQ-SR1 fix | Remove car coverage; SR-22 flow correct | — | Yes | Stop; no loop 3 needed |
| 3 | — | — | — | N/A | Skipped; sufficient |

---

## 12. 中文宏观总结

**哪 5–8 个问题被正式选中了：**  
新车报价、取消警告、付款失败、缺材料、已发过、通知看不懂、保费太高、事故理赔。

**它们分别适合 FAST / LLM / 人工确认里的哪一种：**  
- **FAST：** 已发过（发你了、发过了）、要发什么、加车字段补充、可以了  
- **LLM：** 新车报价、取消警告、付款失败、缺材料、通知看不懂、保费太高、事故理赔、删车  
- **人工确认：** 取消、付款、缺材料客户说已发、加车VIN/驾驶人、搬家、加司机  

**它们会怎么帮助产品：**  
- 客户问什么 → 系统怎么回 → 还缺什么 → 谁确认，一目了然  
- 仿真场景更真实，覆盖高频问题  
- 办公室有操作文档可查  

**我们现在大约能怎么回答这些问题：**  
- 新车报价：先要年份车型邮编，再要提车日期和驾驶人  
- 取消/付款：今天处理，发通知和截图  
- 缺材料：要什么再发一次，或说已发我们核对  
- 通知看不懂：发完整通知，我们帮你看  
- 保费太高：发保单和账单，我们看看有没有办法  
- 事故：先拍照片、记对方信息，发我们  

**还要补什么信息：**  
- 真实客户问法样本（从broker logs收集）  
- 试点一周后各类型出现频率  

**下一步最该做什么：**  
从真实客户消息中补充2–3个常见问法，跑一周试点，用处理矩阵统计各类型出现频率。

---

## 13. COPY/PASTE DECISION BLOCK

**Selected top question groups:**  
new_car_quote, cancellation_warning, payment_failed, missing_document, already_sent_followup, notice_confusion, premium_too_high, claim_intake, remove_car

**Best FAST candidates:**  
already_sent_followup, what_to_send, add_car_field_followup, handoff_confirmation

**Biggest human-confirmation categories:**  
cancellation_warning, payment_failed, missing_document (customer_says_sent), add_car (VIN, primary_driver)

**Strongest scenario additions:**  
FAQ-RM1 (remove car), FAQ-SR1 (SR-22/DMV), FAQ-W1 (what to send), FAQ-AS1 (already sent)

**What to do next:**  
Add 2–3 real-customer phrasings from broker logs; run pilot week with handling matrix; measure type frequency in queue.

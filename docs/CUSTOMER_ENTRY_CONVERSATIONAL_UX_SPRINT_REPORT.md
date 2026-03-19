# Customer Entry Conversational UX Sprint Report

**Sprint:** Customer Entry Conversational UX Sprint  
**Date:** 2026-03-10  
**Status:** Complete

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| Stage 1 — Define what good front-end conversational UX means | ✅ | Target UX defined below |
| Stage 2 — First-pass real-user UX simulation | ✅ | Simulated 5 flows; identified form-checklist, no-acknowledgement, abrupt handoff |
| Stage 3 — Classify UX problems by type | ✅ | Too much form feeling, robotic next question, weak acknowledgement |
| Stage 4 — Prioritize highest-value UX fixes | ✅ | Add-car progressive ask + acknowledgement; claim empathy; handoff warmth |
| Stage 5 — Improvement loop 1 | ✅ | Implemented all fixes |
| Stage 6 — Improvement loop 2 | ✅ | Fixed scenario phrase expectations (报价); guardrail pass |
| Stage 7 — Optional loop 3 | ⏭️ | Skipped — loop 2 sufficient |
| Stage 8 — Front-end product proof | ✅ | 5 flow walkthroughs below |
| Stage 9 — Regression + safety protection | ✅ | Guardrail PASS; CUSTOMER_ENTRY_REPLY_STRATEGY updated |
| Stage 10 — Audit | ✅ | Accept |

---

## 2. UX target

**What “good” front-end conversational UX means:**

| Dimension | Bad (before) | Good (target) |
|-----------|--------------|---------------|
| **Helpful vs robotic** | Generic checklist; no acknowledgement | Acknowledge what customer said; ask 1–2 next things |
| **Next question** | "把年份、车型、VIN、提车日期、地址邮编和主要驾驶人发我" (6 items) | "好的，宝马X5。可以把年份和地址邮编发我，我先帮你算报价。" |
| **Handoff** | "办公室会尽快处理" (abrupt) | "您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。" |
| **Explanation before handoff** | Push to handoff without reinforcing progression | Brief "您说的情况已收到" or "报价资料已整理" |
| **Issue progression** | Customer feels like filling a form | Each turn moves the case forward; customer feels heard |
| **Emotional reassurance** | Claim: bare first-step guidance | "刚出事故一定很着急，先别慌。先确保人没事..." |

**Why it matters:** Customers should feel the system is helping them move their issue forward, not routing them through a disguised form. Chen Kui’s office should receive cases where the customer already feels prepared.

---

## 3. Product / logic / wording changes made

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Add-car: progressive first-turn reply (acknowledge + ask 1–2 items); `_get_add_car_acknowledgement()` for turn 2+; `_get_next_ask_for_add_car()` now prefixes with acknowledgement |
| `configs/industries/insurance/reply_templates.json` | Claim intake: added brief empathy ("刚出事故一定很着急，先别慌" / "Accidents can be stressful—first make sure everyone is okay") |
| `configs/clients/chen_kui/handoff_phrases.json` | Add-car: "您说的报价资料已整理好了，办公室会尽快出价"; Other: "您说的情况已收到，办公室会尽快处理" |
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Added conversational UX notes and examples for add-car; claim tone update |

---

## 4. Simulation and improvement loops

### First pass (baseline)
- Add-car T1 "我买了台宝马X5": reply listed 6 items, no acknowledgement
- Add-car T2 "2024年的": reply "把地址邮编发我" with no acknowledgement
- Claim: no emotional reassurance
- Handoff: generic "办公室会尽快处理"

### Fixes (loop 1)
1. Add-car first turn: progressive ask based on fields; acknowledge model/year when present
2. Add-car turn 2+: `_get_add_car_acknowledgement()` prefixes next ask (e.g. "好的，2024年的。")
3. Claim: empathy prefix in reply template
4. Handoff: warmer phrasing in config

### Loop 2
- Scenario pack expected ["报价", "VIN", "车型"] in add-car drafts; progressive reply sometimes omitted 报价
- Added "算报价" to add-car ask strings so 报价 appears

### After rerun
- Inbox scenarios: 49/49 ✅
- Multi-turn: 19/19 ✅
- Expression robustness: 41/41 ✅
- Adversarial: 27/27 ✅
- Complex: 22 strong, 1 acceptable (LC-AC3) ✅
- Guardrail: PASS ✅

---

## 5. Product proof strength

| Flow | Before | After |
|------|--------|-------|
| Add car / quote | Form checklist; no acknowledgement | "好的，宝马X5。可以把年份和地址邮编发我，我先帮你算报价。" |
| Renewal / premium | Good | Unchanged |
| Claim first response | Bare guidance | "刚出事故一定很着急，先别慌。先确保人没事..." |
| Notice / payment | Good | Unchanged |
| Missing document | Good | Unchanged |
| Handoff | Generic | "您说的报价资料已整理好了，办公室会尽快出价" |

The front-end now feels more like a capable office front desk: it acknowledges what the customer said, asks the next most useful thing, and reinforces progression at handoff.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 49/49 pass |
| `run_multi_turn_simulations.py` | 19/19 pass |
| `run_expression_robustness.py` | 41/41 strong |
| `run_adversarial_simulation.py` | 27/27 strong |
| `run_complex_adversarial_simulation.py` | 22 strong, 1 acceptable |
| `guardrail_inbox_triage.sh` | PASS |
| `npm run build` (ui/) | Success |

---

## 7. Business / platform value

- **User trust:** Acknowledgement and progressive ask make customers feel heard; less repetition.
- **Office workload:** Customers arrive with clearer context; broker sees "您说的报价资料已整理好了" reinforcing what was collected.
- **Platform story:** Front-end carries more load; feels more advanced than a generic chatbot; handoff feels less abrupt.

---

## 8. Remaining blocker(s)

1. **LC-AC3:** Handoff at turn 2 when driver correction in turn 3 (known edge case).
2. **Add-car English:** Model extraction could cover more makes (Honda CR-V, Toyota Camry) for acknowledgement.
3. **Premium/renewal:** No acknowledgement on follow-up turns (lower priority).

---

## 9. Recommended next step

**One clear next step:** Add 1–2 conversational UX examples to the founder demo queue (e.g. add-car with acknowledgement, claim with empathy) so Chen Kui can see the improved flow live.

---

## 10. 中文或中英混合宏观总结

**前端对话体验这次具体变好了什么：**
- 加车流程：不再一次问6个字段，改为先确认车型/年份，再问1–2项（如"好的，宝马X5。可以把年份和地址邮编发我"）
- 多轮对话：客户说"2024年的"后，系统会先回"好的，2024年的。"再问邮编，不再生硬
- 事故首次响应：增加"刚出事故一定很着急，先别慌"的共情，再给第一步指引
- 转交话术：从"办公室会尽快处理"改为"您说的报价资料已整理好了，办公室会尽快出价"，让客户感到有进展

**哪些地方更像真人前台：**
- 有确认、有下一步、有转交时的收尾感
- 不再像填表机器人

**哪些地方还不够自然：**
- 英文加车对部分车型的确认语还不够丰富
- 续保/保费多轮暂无确认语

**修了哪些最值钱的问题：**
- 加车首轮不再一次问6项
- 加车多轮有确认语
- 事故有共情
- 转交话术更温暖

**对用户和陈奎办公室有什么帮助：**
- 用户感觉系统在帮忙推进，而不是机械收集
- 办公室收到的案件更有上下文，客户更易配合

---

## 11. Practical conversational UX cheat sheet

| What improved | Before | After |
|---------------|--------|-------|
| Add-car first turn | 6-item checklist | Acknowledge + ask 1–2 (year+zip or zip only) |
| Add-car turn 2+ | "把地址邮编发我" | "好的，2024年的。把地址邮编发我，我先帮你算报价。" |
| Claim first turn | Bare guidance | "刚出事故一定很着急，先别慌。" + guidance |
| Handoff (add-car) | "报价资料已收集" | "您说的报价资料已整理好了，办公室会尽快出价" |
| Handoff (other) | "办公室会尽快处理" | "您说的情况已收到，办公室会尽快处理" |
| Still weaker | — | Premium/renewal follow-up no acknowledgement; LC-AC3 edge case |

---

## 12. UX problem summary

| Category | Strong | Acceptable | Weak | Fixes |
|----------|--------|------------|------|-------|
| Add car | First-turn progressive ask; turn 2+ acknowledgement | — | — | Progressive ask; acknowledgement helper |
| Renewal / premium | Policy/bill ask | — | — | — |
| Claim intake | Empathy + guidance | — | — | Empathy prefix |
| Notice / payment | Urgency + ask | — | — | — |
| Missing document | Item naming + resend | — | — | — |
| Handoff | Warmer phrasing | — | — | Config update |

**Repeated problem patterns addressed:** Form checklist (add-car), no acknowledgement (add-car turn 2+), abrupt handoff, claim without empathy.

---

## 13. Front-end proof walkthroughs

### 1. Add car / quote
- **Customer:** 我买了台宝马X5，想问下保费多少钱
- **System T1:** 好的，宝马X5。可以把年份和地址邮编发我，我先帮你算报价。
- **Customer:** 2024年的
- **System T2:** 好的，2024年的。把地址邮编发我，我先帮你算报价。
- **Explanation:** Acknowledgement at each turn; asks 1–2 items; handoff when year+model+zip.
- **Handoff:** 您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。
- **Result:** Strong

### 2. Renewal / premium
- **Customer:** 保费太高了，能不能便宜一点
- **System:** 我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我，我先帮你核对。
- **Explanation:** Explains review path; asks for policy/bill.
- **Handoff:** 您说的情况已收到，办公室会尽快处理，有结果会联系您。
- **Result:** Strong

### 3. Claim first response
- **Customer:** 刚出事故了，要收集什么？
- **System:** 刚出事故一定很着急，先别慌。先确保人没事，再拍现场照片、记下对方车牌和保险信息。把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。
- **Explanation:** Empathy first; then first-step guidance; then ask.
- **Handoff:** 您说的情况已收到，办公室会尽快处理，有结果会联系您。
- **Result:** Strong

### 4. Notice confusion
- **Customer:** 客户问：这个英文 notice 说 payment failed，我现在怎么办？
- **System:** 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
- **Explanation:** Conclusion first; urgency; next step.
- **Handoff:** 您说的情况已收到，办公室会尽快处理，有结果会联系您。
- **Result:** Strong

### 5. Missing document follow-up
- **Customer:** UW follow up - need dec page + garaging proof. 客户说上周发过了
- **System:** 现在文件里还缺 declaration page（保单首页） 和 garaging proof（车辆停放地址证明）。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。
- **Explanation:** Names items; offers to verify if already sent.
- **Handoff:** 您说的情况已收到，办公室会尽快处理，有结果会联系您。
- **Result:** Strong

### Graceful limitation
- **Case:** Customer sends three intents in one message.
- **Behavior:** System picks primary intent; may not fully address all three. Handoff with summary.
- **Result:** Acceptable — fails gracefully.

### Retrieval adds value
- **Case:** "garaging proof 是什么" + add-car.
- **Behavior:** Brief explanation of garaging proof, then add-car ask.
- **Result:** Strong — retrieval augments without making reply worse.

---

*End of sprint report*

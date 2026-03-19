# Customer Entry Next-Step Guidance Sprint Report

**Sprint:** Customer Entry Next-Step Guidance Sprint  
**Date:** 2026-03-11  
**Status:** Complete

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| Stage 1 — Define what good next-step guidance looks like | ✅ | Target defined below |
| Stage 2 — First-pass next-step guidance simulation | ✅ | Simulated 5 flows; identified multi-item friction, passive ask phrasing |
| Stage 3 — Classify next-step guidance weaknesses | ✅ | Multi-item no "先发其中一个也行"; add-car "可以把" not "先把"; claim no "先"; payment no "现在最关键的是" |
| Stage 4 — Prioritize highest-value fixes | ✅ | Add-car "先把"; renewal "先发其中一个也行"; claim "先把"; missing-doc multi "先发其中一个也行"; payment/cancel "现在最关键的是" |
| Stage 5 — Improvement loop 1 | ✅ | All fixes implemented |
| Stage 6 — Improvement loop 2 | ✅ | Payment/cancellation "现在最关键的是" |
| Stage 7 — Optional loop 3 | ⏭️ | Skipped — loop 2 sufficient |
| Stage 8 — Front-end product proof | ✅ | 5 flow walkthroughs below |
| Stage 9 — Regression + safety protection | ✅ | Guardrail PASS; CUSTOMER_ENTRY_REPLY_STRATEGY updated |
| Stage 10 — Audit | ✅ | Accept |

---

## 2. Next-step-guidance target

**What "good" next-step guidance means:**

| Dimension | Weak (before) | Strong (target) |
|-----------|---------------|-----------------|
| **Next step feels clear** | "把资料发我" (vague) | "先把年份和地址邮编发我" (specific, prioritized) |
| **User knows what to send first** | "保单和账单" (both?) | "保单和账单（先发其中一个也行）" |
| **User understands why** | Ask without cause-effect | "发我，我就能帮你算报价" (send this → I can do that) |
| **Multi-item manageable** | "请再发我一次" (2 items) | "请再发我一次（先发其中一个也行）" |
| **Urgent flows prioritized** | "请把通知发我" | "现在最关键的是把通知或截图发我" |
| **Action-oriented phrasing** | "可以把...发我" | "先把...发我" |

**Why it matters:** A strong office front desk does not only reply and ask questions—it makes the next step obvious and useful. Users should feel: I know what I should do next; I understand why this matters; I am not just being asked random questions.

---

## 3. Product / logic / wording changes made

| File | Change |
|------|--------|
| `configs/industries/insurance/reply_templates.json` | premium_review + "（先发其中一个也行）"; premium_review_reassurance same; claim_intake "先把事故经过..."; payment_lapse_expiration "现在最关键的是把..."; cancellation_warning "现在最关键的是把..." |
| `services/fiqa_api/inbox_triage/triage.py` | Add-car: "先把...发我，我就能帮你算"; _get_next_ask_for_add_car same; missing_document when len(items)>1: "（先发其中一个也行）"; premium fallbacks updated |
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Next-step guidance notes for add-car, renewal, claim, missing-doc, payment |

---

## 4. Simulation and improvement loops

### First pass (baseline)
- Add-car: "可以把年份和地址邮编发我" — less action-oriented
- Renewal: "把保单和账单发我" — user might not have both
- Claim: "把事故经过、对方信息和照片发我" — no "先"
- Missing doc multi: "请再发我一次" — 2 items, no "先发其中一个也行"
- Payment/cancel: "请把通知发我" — no prioritization

### Fixes (loop 1)
1. Add-car: "先把...发我，我就能帮你算报价"
2. Renewal: "（先发其中一个也行）"
3. Claim: "先把事故经过、对方信息和照片发我"
4. Missing doc multi: "（先发其中一个也行）"

### Loop 2
5. Payment/cancellation: "现在最关键的是把..."

### After rerun
- Guardrail: PASS
- Multi-turn: 29/29 strong
- Adversarial: 27/27 strong
- Complex: 22 strong, 1 acceptable

---

## 5. Product proof strength

| Flow | Before | After |
|------|--------|-------|
| Add car | "可以把...发我" | "先把...发我，我就能帮你算报价" |
| Renewal | "把保单和账单发我" | "把保单和账单发我（先发其中一个也行）" |
| Claim | "把事故经过...发我" | "先把事故经过、对方信息和照片发我" |
| Notice / payment | "请把通知发我" | "现在最关键的是把最新通知或付款截图发我" |
| Missing doc (multi) | "请再发我一次" | "请再发我一次（先发其中一个也行）" |

The front-end now makes the next step clearer: "先" signals priority; "我就能" shows cause-effect; "先发其中一个也行" reduces friction; "现在最关键的是" prioritizes urgent flows.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | Pass |
| `run_multi_turn_simulations.py` | 29/29 strong |
| `run_adversarial_simulation.py` | 27/27 strong |
| `run_complex_adversarial_simulation.py` | 22 strong, 1 acceptable |
| `guardrail_inbox_triage.sh` | PASS |
| `npm run build` (ui/) | Success |

---

## 7. Business / platform value

- **User trust:** Users know what to send first and why; less confusion.
- **Office workload:** Customers arrive more prepared; fewer "what do I send?" follow-ups.
- **Platform story:** Front-end feels more like a front desk that leads, not just asks.

---

## 8. Remaining blocker(s)

1. **LC-AC3:** Handoff at turn 2 when driver correction in turn 3 (known edge case).
2. **Premium/renewal:** No acknowledgement on follow-up turns (lower priority).

---

## 9. Recommended next step

**One clear next step:** Add 1–2 next-step-guidance examples to the founder demo queue (e.g. add-car "先把...发我"，renewal "先发其中一个也行"，payment "现在最关键的是") so Chen Kui can see the improved flow live.

---

## 10. 中文或中英混合宏观总结

**前端「下一步怎么做」这次具体变好了什么：**
- 加车：从「可以把...发我」改为「先把...发我，我就能帮你算报价」— 用户知道发什么、发完会怎样
- 续保：增加「（先发其中一个也行）」— 保单或账单先发一个就行，降低门槛
- 事故：增加「先把事故经过、对方信息和照片发我」— 明确先发什么
- 付款/取消：增加「现在最关键的是把...发我」— 紧急时下一步更清晰
- 缺材料（多项）：增加「（先发其中一个也行）」— 多项时先发一个即可

**哪几条主线最清楚地告诉用户下一步：**
- 加车（先把...发我，我就能算报价）
- 事故（先把...发我；对方跑了时「最关键的是」）
- 付款/取消（现在最关键的是）
- 缺材料（先发其中一个也行；核对好后就能往下推）

**哪几条还不够强：**
- 续保多轮暂无确认语
- LC-AC3 边缘情况

**修了哪些最值钱的问题：**
- 「先」字强化行动导向
- 「先发其中一个也行」降低多选摩擦
- 「现在最关键的是」强化紧急流程优先级
- 「我就能帮你算」强化因果感

**对用户和陈奎办公室有什么帮助：**
- 用户更清楚下一步做什么、为什么
- 办公室收到的客户更易配合，减少重复澄清

---

## 11. Practical next-step guidance cheat sheet

| Flow | Clearer "do this next" | Clearer "why this matters" | Still weaker |
|------|------------------------|----------------------------|--------------|
| Add car | "先把年份和地址邮编发我" | "我就能帮你算报价" | — |
| Renewal | "把保单和账单发我（先发其中一个也行）" | "我先帮你核对" | Follow-up no ack |
| Claim | "先把事故经过、对方信息和照片发我" | "我帮你确认下一步怎么报案" | — |
| Notice / payment | "现在最关键的是把通知或截图发我" | "我先帮你确认；今天尽快处理" | — |
| Missing doc | "请再发我一次（先发其中一个也行）" | "核对好后就能往下推" | — |

---

## 12. Next-step guidance problem summary

| Category | Strong | Acceptable | Weak | Fixes |
|----------|--------|------------|------|-------|
| Add car | "先把...发我，我就能算" | — | — | 先 + 我就能 |
| Renewal | 先发其中一个也行 | — | — | Template + fallback |
| Claim | 先把...发我 | — | — | 先 |
| Notice / payment | 现在最关键的是 | — | — | Template |
| Missing doc | 先发其中一个也行 + 核对好后 | — | — | Multi-item logic |

**Repeated patterns addressed:** Passive "可以把"; multi-item without "先发其中一个也行"; urgent without "现在最关键的是".

---

## 13. Front-end proof walkthroughs

### 1. Add car / quote
- **Customer T1:** 我买了台宝马X5，想问下保费多少钱
- **System T1:** 好的，宝马X5。先把年份和地址邮编发我，我就能帮你算报价。
- **Customer T2:** 2024年的，zip 90210，下周提车
- **System T2:** 您说的报价资料已整理好了，办公室会尽快出价，有结果会联系您。
- **User knows to do next:** Send year and zip first → get quote.
- **Result:** Strong

### 2. Renewal / premium
- **Customer T1:** 保费太高了，能不能便宜一点
- **System T1:** 我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。
- **User knows to do next:** Send policy or bill (either one) → we check.
- **Result:** Strong

### 3. Claim first response
- **Customer T1:** 刚出事故了，要收集什么？
- **System T1:** 刚出事故一定很着急，先别慌。先确保人没事，再拍现场照片、记下对方车牌和保险信息。先把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。
- **User knows to do next:** Send accident details, other driver info, photos → we confirm next steps.
- **Result:** Strong

### 4. Notice confusion
- **Customer T1:** 客户问：这个英文 notice 说 payment failed，我现在怎么办？
- **System T1:** 这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
- **User knows to do next:** Send notice or screenshot first → we confirm; if unpaid, fix today.
- **Result:** Strong

### 5. Missing document follow-up (multi-item)
- **Customer T1:** UW follow up - need dec page + garaging proof. 客户说上周发过了
- **System T1:** 现在文件里还缺 declaration page（保单首页） 和 garaging proof（车辆停放地址证明）。请再发我一次（先发其中一个也行）；如果你之前已经发过，也跟我说一声，我这边帮你核对，核对好后就能往下推。
- **User knows to do next:** Resend one or both; if already sent, tell us → we verify → move forward.
- **Result:** Strong

### Graceful limitation
- **Case:** LC-AC3 — driver correction in turn 3.
- **Result:** Acceptable — known edge case.

---

*End of sprint report*

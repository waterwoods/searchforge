# Customer Conversational Intake Quality Sprint Report

**Sprint:** Customer Conversational Intake Quality Sprint  
**Date:** 2026-03-09  
**Target:** Upgrade same-page customer conversation to behave like a useful insurance front desk

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Lock 6 highest-value intents | **Completed** | Updated `CUSTOMER_ENTRY_REPLY_STRATEGY.md` with Chinese markers (买了, 保费多少钱, 删车, 英文 notice); locked response plan for all 6 |
| Stage 2 — Fix generic fallback problem | **Completed** | Chinese BMW X5 quote no longer gets "不够完整"; add-car, remove-car, premium, notice, payment all get intent-specific replies |
| Stage 3 — Make conversation feel natural | **Completed** | English notice confusion gets reassuring "英文通知有些术语看不懂很正常"; wording tightened per Chen Kui proxy |
| Stage 4 — Improve broker handoff quality | **Completed** | `_build_conversation_summary` now includes intent hint (Add-car, Payment risk, etc.) for broker context |
| Stage 5 — Audit + validate + demo check | **Completed** | All checks pass: scenarios 32/32, proxy 14/14, guardrail, smoke check, npm build |

**Skipped:** None.

---

## 2. Response quality improvements

| Pattern | Before | After |
|---------|--------|-------|
| 我刚刚买了2026年的宝马X5，我想问一下保费多少钱 | `unclear` → "这段内容还不够完整..." | `customer_question` → "可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）..." |
| 这个英文 notice 看不懂 | Generic "把完整通知发我" | "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我..." |
| 他想把一辆车删掉 | Already worked | Added "删车" marker for robustness |
| 他说 payment failed，现在怎么办 | Already worked | No change; payment_lapse_expiration path correct |

**Categories covered:** Add car (Chinese + English), remove car, premium review, payment risk, English notice confusion, missing document, DMV/SR-22.

**Why it matters:** Chen Kui’s customers no longer hit generic "内容不够完整" when intent is obvious. The system asks the right next 1–2 fields and sounds like a front desk.

---

## 3. Product/design changes made

### Stage 1 + 2 (intent detection, generic fallback)

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | `ADD_VEHICLE_MARKERS`: added "买了", "保费多少钱", "保费多少" |
| `services/fiqa_api/inbox_triage/triage.py` | `VEHICLE_CONTEXT_MARKERS`: added "宝马" |
| `services/fiqa_api/inbox_triage/triage.py` | `REMOVE_VEHICLE_MARKERS`: added "删车" |
| `services/fiqa_api/inbox_triage/triage.py` | `_is_english_notice_confusion()`: new helper for English notice confusion |
| `services/fiqa_api/inbox_triage/triage.py` | `_build_client_reply_draft`: English notice confusion gets reassuring phrase |

### Stage 3 (conversation feel)

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Chinese draft for notice confusion: "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我..." |
| `services/fiqa_api/inbox_triage/triage.py` | English draft for notice confusion: "English notices can be confusing. Send me the full notice..." |

### Stage 4 (broker handoff)

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | `_build_conversation_summary()`: intent hint (Add-car, Payment risk, etc.) + message count + latest snippet |

### Regression + proxy

| File | Change |
|------|--------|
| `configs/inbox_triage_scenarios.json` | R18: Chinese BMW X5 quote; R19: English notice confusion; R20: payment failed relay |
| `configs/chen_kui_proxy_calibration_cases.json` | CK14: Chinese BMW X5 quote |

### Docs + UI

| File | Change |
|------|--------|
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Add-car: added 买了, 保费多少钱; Remove: 删车; English notice: 英文 notice, reassuring example |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Chinese add-car example |
| `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` | Add-car note for Chinese markers |
| `ui/src/pages/UnifiedIntakePage.tsx` | CUSTOMER_ENTRY_EXAMPLES: "BMW X5 quote (Chinese)"; inferCaseFocusFromText: 买了, 宝马, x5 |

---

## 4. Before vs after

**Where the conversation previously felt generic:**
- "我刚刚买了2026年的宝马X5，我想问一下保费多少钱" → "这段内容还不够完整。把完整通知或前后内容再发我一下..."
- "这个英文 notice 看不懂" → Generic "把完整通知发我" without reassurance

**What now feels more like a real office intake:**
- BMW X5 (Chinese): "可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。"
- English notice: "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。"

**BMW X5 / add-car / premium-review:** All get intent-specific follow-up. Chinese "买了" + vehicle context now triggers add-car path.

**Broker handoff:** `conversation_summary` now includes intent hint (e.g. "Add-car / new vehicle quote. 2 customer message(s). Latest: ...") so broker sees likely issue type at a glance.

---

## 5. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` (ui/) | **Pass** | UI compiles |
| `run_inbox_triage_scenarios.py` | **32/32 pass** | Category, urgency, draft quality |
| `run_chen_kui_proxy_calibration.py` | **14/14 pass** | Draft tone, proxy style |
| `guardrail_inbox_triage.sh` | **Pass** | Scenario pack, API, persistence |
| `unified_intake_smoke_check.sh` | **Pass** | Full guardrail + manual checklist |

---

## 6. Business value impact

- **Customer experience:** Obvious intents (BMW X5 quote, payment failed, notice confusion) get specific next-step questions instead of generic "send more context."
- **Broker work reduction:** Fewer repeated WeChat/call explanations; broker receives cleaner cases with intent hint in summary.
- **Product sellability:** Demo path "我刚刚买了2026年的宝马X5，我想问一下保费多少钱" now shows front-desk-style intake.

---

## 7. Remaining blocker(s)

1. **Progressive logic is heuristic:** "Enough info" is rule-based (2nd message or manual_followup_needed=false). No NLP extraction of collected fields yet.
2. **No structured progressive_answers:** Broker sees conversation text and intent hint, but not key-value pairs (e.g. year=2026, model=BMW X5). Deferred.
3. **Conversation memory is session-only:** No user identity; each "提交新问题" starts fresh.

---

## 8. Recommended next step

**One clear next step:** Add a lightweight "Collected from conversation" summary on the broker case card when `source_text` contains multiple turns and intent is add-car/premium/remove-car — e.g. "Vehicle: 2026 BMW X5 (from customer message)." Keep it heuristic and narrow.

---

## 9. 中文或中英混合宏观总结

**这次主要把哪些客户对话回复做对了：**
- 中文新车报价（如「我刚刚买了2026年的宝马X5，我想问一下保费多少钱」）不再回「内容不够完整」，而是直接问年份、车型、VIN、提车日期、地址、驾驶人。
- 英文通知看不懂：加了「英文通知有些术语看不懂很正常」的安抚语，再请客户发完整通知。
- 加车、删车、保费太高、付款失败、缺件、DMV/SR-22：沿用既有意图逻辑，无回归。

**BMW X5 / 加车 / 保费太高 这些场景现在怎么接：**
- BMW X5（中/英）：识别为加车报价，问年份、车型、VIN、提车日期、邮编、驾驶人。
- 加车：同上。
- 保费太高：问保单和最新账单，说明会帮看为什么变高、有没有调整空间。

**有没有困难或限制：**
- 「够不够」仍是启发式（第二轮或 manual_followup=false 即交办），没有字段级提取。
- 对话记忆只在当前 session，没有用户身份。

**现在最适合演示哪几个问题：**
1. 「我刚刚买了2026年的宝马X5，我想问一下保费多少钱」
2. 「客户问：这个英文 notice 说 payment failed，我现在怎么办？」
3. 「这个英文 notice 看不懂」
4. 「客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价」

---

## 10. 如何打开前端 / 后端

| Item | Command / URL |
|------|---------------|
| **Start demo** | `bash scripts/run_demo_local.sh` |
| **Frontend** | http://localhost:5173/workbench/unified-intake |
| **Backend** | http://localhost:8001 (default) |
| **First tab** | 客户入口 (Customer Entry) |
| **Port caveats** | If 8001 busy, use `restore_8001_readiness.sh`. If 5173 bumps to 5174, use the URL shown in Vite. Isolated path: backend 8002 + frontend 5174 with `VITE_API_PROXY_TARGET=http://127.0.0.1:8002`. |

---

## 11. Runtime walkthrough

### Example 1: BMW X5 / 新车报价

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 我刚刚买了2026年的宝马X5，我想问一下保费多少钱 |
| 2 | System | 可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。 |
| 3 | Customer | 90210，下周提车 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Broker | Case shows: Add-car / new vehicle quote. 2 customer message(s). Latest: 90210，下周提车... broker_next_step: "Collect the new vehicle details, confirm the delivery date and primary driver, then quote or add it the same day if possible." |

**Why better than old generic fallback:** Old path returned "这段内容还不够完整。把完整通知或前后内容再发我一下..." despite clear add-car intent. New path recognizes 买了 + 宝马X5 + 保费多少钱 and asks for the concrete fields a broker needs.

---

### Example 2: Payment failed / cancellation risk

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 客户问：这个英文 notice 说 payment failed，我现在怎么办？ |
| 2 | System | 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。 |
| 3 | Customer | 我发了截图在微信 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Broker | Case shows: Payment failed / lapse risk. 2 customer message(s). broker_next_step: "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today." |

**Why better than old:** Same intent-specific first reply as before; handoff now includes intent hint in conversation_summary so broker sees "Payment failed / lapse risk" at a glance.

---

### Example 3: English notice confusion

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 这个英文 notice 看不懂 |
| 2 | System | 英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。 |
| 3 | Customer | [sends photo] |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Broker | Case shows: English notice confusion. 2 customer message(s). broker_next_step: "Read the notice in plain language, confirm whether there is any deadline or payment risk, and tell the client the next step clearly." |

**Why better than old:** Old reply was generic "把完整通知或更清楚的照片发我。我先帮你看一下..." New reply adds "英文通知有些术语看不懂很正常" so the client feels reassured before sending.

---

*End of sprint report*

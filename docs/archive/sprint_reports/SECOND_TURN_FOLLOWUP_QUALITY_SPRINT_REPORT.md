# Second-Turn Follow-up Quality Sprint Report

**Sprint:** Second-Turn Follow-up Quality Sprint  
**Date:** 2026-03-09  
**Target:** Improve second-turn follow-up so the system does not hand off too early and can gather the next most useful information before passing the case to the broker workbench.

---

## 1. Stages Completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Define second-turn follow-up rules | **Completed** | Added §4 to `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` with per-category rules, handoff thresholds, third-turn continuation |
| Stage 2 — Fix early handoff / premature stopping | **Completed** | Add-car: content-aware handoff; ask for zip/delivery/driver when missing; extract from customer messages only |
| Stage 3 — Allow light third-turn continuation | **Completed** | MT13 regression: turn 2 only year → ask for zip; turn 3 zip → hand off |
| Stage 4 — Improve broker handoff | **Completed** | `conversation_summary` includes "Collected: year, model, zip, delivery, driver"; add-car handoff message: "报价资料已收集，办公室会尽快出价"; `conversation_summary` persisted to case |
| Stage 5 — Audit + validate + spot-check | **Completed** | All validation scripts pass |

**Skipped:** None.

---

## 2. Second-Turn Strategy Improvements

| Pattern | Before | After |
|---------|--------|-------|
| Add-car, turn 2 only year | Hand off ("办公室会尽快处理") | Ask for zip ("把地址邮编发我，我先帮你算。") |
| Add-car, turn 2 year+zip+delivery | Hand off | Hand off with clearer message ("报价资料已收集，办公室会尽快出价") |
| Add-car handoff message | Generic "办公室会尽快处理" | Quote-specific "报价资料已收集，办公室会尽快出价，有结果会联系您。" |
| Broker summary | Intent + message count + latest snippet | + "Collected: year, model, zip, delivery, driver" when add-car |

**Categories covered:** Add-car / new vehicle quote (primary focus). Other categories hand off after 2 turns to avoid repeating the same ask.

---

## 3. Product / Logic Changes Made

| File | Change |
|------|--------|
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Added §4 Second-Turn Follow-Up Rules: per-category decision table, handoff thresholds, third-turn continuation |
| `services/fiqa_api/inbox_triage/triage.py` | `_extract_add_car_fields()` (customer messages only), `_add_car_enough_for_handoff()`, `_get_next_ask_for_add_car()`, `_get_next_ask_draft()`; `_build_conversation_summary()` adds "Collected:" for add-car; add-car handoff reply; triage_conversation wires next-ask vs handoff |
| `services/fiqa_api/inbox_triage/case_store.py` | Persist `conversation_summary` when present in triage result |
| `configs/customer_entry_multi_turn_simulations.json` | Added MT13: add-car partial (year only) → ask zip → turn 3 zip → handoff |
| `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md` | Handoff trigger note; second-turn quality reference |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Multi-turn intake description updated |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Customer flow description updated |

---

## 4. Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Add-car turn 2 with only year | Hand off immediately | Ask for zip; hand off at turn 3 when zip provided |
| Add-car handoff message | "办公室会尽快处理，有结果会联系您。" | "报价资料已收集，办公室会尽快出价，有结果会联系您。" |
| Broker conversation summary | Intent + count + latest snippet | + "Collected: year, model, zip, delivery, driver" for add-car |
| Third-turn continuation | Always hand off after 2 turns | Add-car: one more ask when zip/delivery/driver missing |
| Extraction source | Full merged text (incl. system reply) | Customer messages only (avoids false "zip" from system question) |

---

## 5. Validation Summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` (ui/) | **Pass** | UI compiles |
| `run_inbox_triage_scenarios.py` | **Pass** (32/32) | Category, urgency, escalation |
| `run_chen_kui_proxy_calibration.py` | **Pass** (14/14) | Draft tone, proxy style |
| `run_multi_turn_simulations.py` | **Pass** (13/13 Strong) | Multi-turn intake including MT13 |
| `verify_inbox_case_persistence.py` | **Pass** | Case store, follow-up, notes |
| `guardrail_inbox_triage.sh` | **Pass** | Full guardrail |

---

## 6. Business Value Impact

- **Reduces repetitive broker intake:** Customer can add zip in turn 3 instead of broker chasing; add-car cases arrive with year+model+zip more often.
- **Improves customer experience:** System feels like a practical front desk—asks for the next useful thing instead of stopping early.
- **More sellable:** Chen Kui can show that the intake collects more useful info before handoff; broker receives cleaner cases with "Collected:" summary.

---

## 7. Remaining Blocker(s)

1. **Add-car only:** Second-turn "ask one more" is implemented for add-car quote only. Payment, missing-doc, premium-review still hand off after 2 turns.
2. **Extraction is heuristic:** Year/zip/model/delivery/driver use regex and keyword matching; no structured NLP.
3. **No `what_still_needed` field:** Broker infers from `source_text` and `conversation_summary`; no explicit "still need: driver" in API response.

---

## 8. Recommended Next Step

Extend `_get_next_ask_draft` to payment-risk and missing-document when customer gives vague second-turn (e.g. "我看看", "等一下")—one targeted ask before handoff. Keep scope narrow.

---

## 9. 中文或中英混合宏观总结

**这次主要修正了哪些第二轮跟进问题：**
- 加车报价：客户第二轮只给年份时，系统不再过早交办，会再问「把地址邮编发我」；第三轮给邮编后交办。
- 加车交办语：从「办公室会尽快处理」改为「报价资料已收集，办公室会尽快出价，有结果会联系您。」
- Broker 摘要：加车 case 会显示「Collected: year, model, zip, delivery, driver」，方便快速判断已收集内容。

**哪些场景现在不会太早结束：**
- 加车报价：当客户只提供年份或部分信息时，系统会再问邮编或提车日期/驾驶人，不会立刻交办。

**第三轮在什么情况下允许继续：**
- 加车：第二轮缺 zip 时，第三轮可补 zip 后交办；或第二轮缺 delivery/driver 时，第三轮可补后交办。

**有没有困难或限制：**
- 目前只对加车做了「再问一次」逻辑；付款失败、缺材料等仍是两轮后交办。
- 字段提取是启发式，没有做完整 NLP。

**现在最适合演示哪几个场景：**
1. BMW X5 加车 → 第一轮要年份/车型/zip → 第二轮只给「2024年的」→ 系统问邮编 → 第三轮「90210」→ 交办
2. BMW X5 加车 → 第一轮要字段 → 第二轮「2024, 90210, 下周提车」→ 直接交办（报价资料已收集）
3. 付款失败 → 两轮交办（维持原逻辑）
4. 缺材料 → 两轮交办（维持原逻辑）

---

## 10. 如何打开前端 / 后端

| Item | Command / URL |
|------|---------------|
| **Start demo** | `bash scripts/run_demo_local.sh` |
| **Frontend** | http://localhost:5173/workbench/unified-intake |
| **Backend** | http://localhost:8001 (default) |
| **First tab** | 客户入口 (Customer Entry) |
| **Port caveats** | If 8001 busy, use `restore_8001_readiness.sh`. If 5173 bumps to 5174, use the URL shown in Vite. |

---

## 11. Runtime Spot-Check Walkthroughs

### 1. BMW X5 / 新车报价

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 我买了台宝马X5，想问下保费多少钱 |
| 2 | System | 可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。 |
| 3 | Customer | 2024年的，zip 90210，下周提车 |
| 4 | System | 报价资料已收集，办公室会尽快出价，有结果会联系您。 |
| 5 | Third turn? | No |
| 6 | Handoff? | Yes |
| 7 | Broker receives | Full conversation; conversation_summary: "Add-car / new vehicle quote. Collected: year, model, zip, delivery. 2 customer message(s). Latest: 2024年的，zip 90210，下周提车..." |
| 8 | Result | **Strong** |

### 2. 加车 partial (ask one more)

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 我买了台宝马X5，想问下保费多少钱 |
| 2 | System | 可以把车子的年份、车型、VIN、提车日期、地址邮编和主要驾驶人发我 |
| 3 | Customer | 2024年的 |
| 4 | System | 把地址邮编发我，我先帮你算。 |
| 5 | Third turn? | Yes (customer can send "90210") |
| 6 | Handoff? | After turn 3 when zip provided |
| 7 | Broker receives | Full conversation; broker sees year+zip collected |
| 8 | Result | **Strong** (MT13 regression) |

### 3. 保费太高

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 保费太高了，能不能便宜一点 |
| 2 | System | 我先帮你看这次保费为什么变高...把现在保单和最新账单发我 |
| 3 | Customer | 续保通知和账单我发你微信了 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Third turn? | No |
| 6 | Handoff? | Yes |
| 7 | Broker receives | Full conversation; category=customer_question |
| 8 | Result | **Strong** |

### 4. Payment Failed / Cancellation Risk

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 客户问：这个英文 notice 说 payment failed，我现在怎么办？ |
| 2 | System | 这看起来是付款出了问题。请把最新通知或付款截图发我... |
| 3 | Customer | 我发了截图在微信 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Third turn? | No |
| 6 | Handoff? | Yes |
| 7 | Broker receives | Full conversation; category=payment_lapse_expiration; urgency=high |
| 8 | Result | **Strong** |

### 5. English Notice Confusion

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 客户发来一张DMV的信，问「这是什么意思？我需要做什么？」 |
| 2 | System | 把完整通知或更清楚的照片发我。我先帮你看一下，再告诉你重点和下一步怎么处理。 |
| 3 | Customer | 他说是suspension clearance，要带什么去DMV |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Third turn? | No |
| 6 | Handoff? | Yes |
| 7 | Broker receives | Full conversation; category=customer_question |
| 8 | Result | **Strong** |

---

*End of sprint report*

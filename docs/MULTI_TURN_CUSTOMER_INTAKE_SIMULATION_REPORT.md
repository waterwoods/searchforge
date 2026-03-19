# Multi-Turn Customer Intake Simulation Sprint Report

**Sprint:** Multi-Turn Customer Intake Simulation  
**Date:** 2026-03-09  
**Target:** Stress-test the current customer-facing conversational intake by simulating realistic 2–3 turn conversations for the highest-frequency Chen Kui insurance customer cases.

---

## 1. Stages Completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Define high-frequency multi-turn test pack | **Completed** | Created `configs/customer_entry_multi_turn_simulations.json` with 12 scenarios across 6 categories |
| Stage 2 — Run multi-turn simulations | **Completed** | All 12 scenarios pass; created `scripts/run_multi_turn_simulations.py` |
| Stage 3 — Fix highest-value failures | **Skipped** | No failures found; all flows classified Strong |
| Stage 4 — Verify broker handoff quality | **Completed** | Full conversation in `source_text`; broker receives actionable context |
| Stage 5 — Audit + validate + report | **Completed** | Guardrail, scenarios, proxy calibration, smoke check all pass |

---

## 2. Simulation Pack

| Metric | Value |
|--------|-------|
| Scenarios created | 12 |
| Categories covered | 6 |
| Turn structure | 2-turn (customer → system → customer → handoff) |

**Categories:**

1. **新车 / 加车报价** — MT1 (BMW X5 中文), MT2 (BMW X5 English), MT11 (Tesla shorthand)
2. **删车 / 保单变更** — MT3 (卖车)
3. **保费太高 / 续保 review** — MT4
4. **付款失败 / 取消风险** — MT5, MT6, MT12
5. **英文通知看不懂** — MT7 (DMV), MT8 (payment notice)
6. **缺材料 / declaration page / DL / garaging proof** — MT9, MT10

**Why they matter:** These are the highest-frequency inbound types for a California auto insurance broker office. Multi-turn intake reduces repeated broker intake work when customers provide partial info first and then add details.

---

## 3. Product / Logic Changes Made

| File | Change |
|------|--------|
| `configs/customer_entry_multi_turn_simulations.json` | **Created.** 12 multi-turn scenarios with realistic customer styles (short Chinese, mixed, shorthand). |
| `scripts/run_multi_turn_simulations.py` | **Created.** Runs simulation pack against triage engine; classifies Strong / Acceptable / Weak. |
| `scripts/guardrail_inbox_triage.sh` | **Updated.** Added step [5] Multi-turn intake simulations. |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | **Updated.** Documented multi-turn simulation pack and commands. |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | **Updated.** Added multi-turn intake note. |

**No triage logic changes.** The existing `triage_conversation` and intent-specific reply logic already handle multi-turn flows correctly.

---

## 4. Simulation Results

| Classification | Count | Notes |
|-----------------|-------|-------|
| **Strong** | 12 | First reply intent-specific; second turn triggers handoff; broker receives full conversation |
| **Acceptable with friction** | 0 | — |
| **Weak / broken** | 0 | — |

**Repeated failure patterns found:** None.

**Flow behavior:**
- First reply: Intent-specific (add car → ask year/model/VIN/zip; payment failed → ask notice/screenshot; missing doc → name item and ask resend).
- Second reply: Handoff message ("办公室会尽快处理，有结果会联系您.") when customer provides follow-up.
- Broker receives: Full `[客户]` / `[系统]` conversation in `source_text`; actionable `broker_next_step`; category and urgency correct.

---

## 5. Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Multi-turn regression coverage | None | 12 scenarios in guardrail |
| Simulation pack | N/A | `configs/customer_entry_multi_turn_simulations.json` |
| Guardrail | 4 steps | 5 steps (includes multi-turn) |
| Documentation | Single-turn focus | Multi-turn documented in runbook and demo readiness |

**Where multi-turn intake used to break:** Not observed in this sprint. The Continuous Conversational Intake sprint (previous) had already implemented `triage_conversation`, same-page flow, and handoff logic.

**What now feels more natural:** The simulation pack validates that common 2-turn flows (add car, payment risk, notice confusion, missing doc) work end-to-end. Broker handoff receives full conversation context.

---

## 6. Validation Summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` | **Pass** | UI compiles |
| `run_inbox_triage_scenarios.py` | **Pass** (32/32) | Category, urgency, escalation |
| `run_chen_kui_proxy_calibration.py` | **Pass** | Draft tone, proxy style |
| `run_multi_turn_simulations.py` | **Pass** (12/12 Strong) | Multi-turn intake quality |
| `guardrail_inbox_triage.sh` | **Pass** | Full guardrail including multi-turn |
| `unified_intake_smoke_check.sh` | **Pass** | Manual UI checklist |

---

## 7. Business Value Impact

- **Reduces repeated broker intake work:** Customer can add year, zip, delivery date, or "I sent the screenshot" in a second turn instead of starting over. Broker receives the full exchange.
- **Improves customer experience:** Same-page continuation feels natural; no "please provide more context" for obvious intents.
- **More sellable:** Multi-turn intake is a differentiator; Chen Kui office can show that the system guides customers across 2–3 turns before handoff.

---

## 8. Remaining Blocker(s)

1. **Progressive logic is heuristic:** Handoff after 2nd message or when `manual_followup_needed=false`. No structured extraction of collected fields (e.g. year=2024, zip=90210) into `progressive_answers`.
2. **Conversation memory is session-only:** No user identity; each "提交新问题" starts fresh.
3. **broker_next_step is template-based:** Does not dynamically include "client already provided X" in the guidance text; broker infers from `source_text`.

---

## 9. Recommended Next Step

Add optional "Collected from conversation" summary to the broker case card when `source_text` contains multiple turns and intent is add-car or remove-car (e.g. "Year: 2024, Zip: 90210, Delivery: next week"). Keep it lightweight.

---

## 10. 中文或中英混合宏观总结

**这次主要测了哪些多轮对话场景：**
- 新车/加车报价（BMW X5、Tesla Model Y）
- 删车/卖车
- 保费太高/续保
- 付款失败/取消风险（中英混合、AutoPay failed、保单要停）
- 英文通知看不懂（DMV、payment notice）
- 缺材料（declaration page、garaging proof、驾照）

**哪些场景已经比较顺：**
- 全部 12 个场景都通过。第一轮回复意图明确（加车问年份车型、付款问题要通知、缺材料点名要什么），第二轮客户补充后正常交办。

**哪些场景还会卡住：**
- 本次未发现卡住场景。

**修掉了哪些最值钱的问题：**
- 本次无失败，未做逻辑修改。新增了多轮回归测试和 guardrail 覆盖，防止后续改动破坏多轮流程。

**现在最适合演示哪几条对话路径：**
1. BMW X5 新车报价（中或英）→ 系统要年份/zip/提车日期 → 客户补「2024, 90210, 下周提车」→ 交办
2. 付款失败 → 系统要通知/截图 → 客户补「我发了截图在微信」→ 交办
3. 英文 notice 看不懂 → 系统要完整通知 → 客户补「他说是 suspension clearance，要带什么去 DMV」→ 交办
4. 缺材料 → 系统点名 dec page + garaging proof → 客户补「dec page 他又发了一次，garaging proof 还没弄」→ 交办

---

## 11. 如何打开前端 / 后端

| Item | Command / URL |
|------|---------------|
| **Start demo** | `bash scripts/run_demo_local.sh` |
| **Frontend** | http://localhost:5173/workbench/unified-intake |
| **Backend** | http://localhost:8001 (default) |
| **First tab** | 客户入口 (Customer Entry) |
| **Port caveats** | If 8001 busy, use `restore_8001_readiness.sh`. If 5173 bumps to 5174, use the URL shown in Vite. |

---

## 12. Multi-Turn Walkthroughs

### Walkthrough 1: BMW X5 / 新车报价

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 我买了台宝马X5，想问下保费多少钱 |
| 2 | System | 可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。 |
| 3 | Customer | 2024年的，zip 90210，下周提车 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Handoff | Yes |
| 6 | Broker receives | Full conversation in source_text; category=customer_question; broker_next_step: "Collect the new vehicle details, confirm the delivery date and primary driver, then quote or add it the same day if possible." |

**Flow:** Strong.

---

### Walkthrough 2: Payment Failed / Cancellation Risk

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 客户问：这个英文 notice 说 payment failed，我现在怎么办？ |
| 2 | System | 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。 |
| 3 | Customer | 我发了截图在微信 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Handoff | Yes |
| 6 | Broker receives | Full conversation; category=payment_lapse_expiration; urgency=high; broker_next_step: "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today." |

**Flow:** Strong.

---

### Walkthrough 3: English Notice Confusion

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | 客户发来一张DMV的信，问「这是什么意思？我需要做什么？」 |
| 2 | System | 把完整通知或更清楚的照片发我。我先帮你看一下，再告诉你重点和下一步怎么处理。 |
| 3 | Customer | 他说是suspension clearance，要带什么去DMV |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Handoff | Yes |
| 6 | Broker receives | Full conversation; category=customer_question; broker_next_step: "Confirm whether DMV wants SR-22 filing proof, check any deadline, and tell the client exactly what to bring." |

**Flow:** Strong.

---

### Walkthrough 4: Missing Document Follow-Up

| Step | Actor | Message |
|------|-------|---------|
| 1 | Customer | UW follow up - need dec page + garaging proof. 客户说上周发过了 |
| 2 | System | 现在文件里还缺 declaration page（保单首页） 和 garaging proof（车辆停放地址证明）。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。 |
| 3 | Customer | declaration page 他又发了一次，garaging proof 还没弄 |
| 4 | System | 办公室会尽快处理，有结果会联系您。 |
| 5 | Handoff | Yes |
| 6 | Broker receives | Full conversation; category=missing_document; broker_next_step: "Confirm exactly which item is still missing, check whether underwriting or the carrier already received it, and resend or chase it before the file stalls." |

**Flow:** Strong.

---

## Demo Honesty

| Area | Status |
|------|--------|
| Multi-turn same-page conversation | **Real** |
| Progressive follow-up logic | **Real** (rule-based; heuristic handoff) |
| Full conversation in broker case | **Real** |
| Structured progressive_answers | **Deferred** |
| User identity / session memory | **Demo-only** (local; no auth) |
| Full chat memory across users | **Deferred** |

---

*End of sprint report*

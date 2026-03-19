# Broker Handoff Clarity + Daily Case Expansion Sprint Report

**Sprint:** Broker Handoff Clarity + Daily Case Expansion  
**Date:** 2026-03-09  
**Scope:** Unified Intake / Customer Entry / Broker Workbench mainline

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|------|
| Stage 1 — Define broker handoff clarity target | **Completed** | Created `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` |
| Stage 2 — Improve broker handoff clarity | **Completed** | Extended conversation_summary, Collected/Still needed for add-car, remove-car, premium review, missing doc, payment risk; UI improvements |
| Stage 3 — Expand daily-use case maturity | **Completed** | Premium review before renewal_reminder; "renewal premium too high" / "续保保费太高" correctly routed |
| Stage 4 — Add regression protection for daily cases | **Completed** | Added D1–D4 scenarios to inbox_triage_scenarios.json |
| Stage 5 — Audit + validate + product judgment | **Completed** | All validation scripts pass |

**Skipped:** None.

---

## 2. Handoff clarity target

**What "clean enough broker handoff" now means:**

| Element | Content |
|---------|---------|
| **Case focus** | Tag: Add car quote, Premium review, Payment risk, etc. |
| **Your next move** | One operational sentence (check/confirm/resend/quote/remove) |
| **Collected** | When extractable: year, model, zip (add-car); vehicle, sale date, transfer (remove-car); policy/bill mentioned (premium); items resent (missing doc); notice/screenshot (payment risk) |
| **Still needed** | When safe: add-car delivery/driver when year+model+zip present; missing doc items not yet resent |
| **Full conversation** | Label changes to "Full conversation" when multi-turn; raw [客户] / [系统] turns below fold |

**What changed:** Backend now produces Collected for remove-car, premium review, missing document, payment risk. Add-car gets "Still needed: delivery date, main driver" when those are missing. UI shows both Collected and Still needed; multi-turn cases show "Full conversation" label.

---

## 3. Product / logic changes made

### Stage 1
| File | Change |
|------|--------|
| `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` | **Created.** Defines broker handoff target: what broker sees first, Collected/Still needed, broker_next_step style, conversation_summary format, visual hierarchy. |

### Stage 2
| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Added `_extract_remove_car_fields()`, `_extract_missing_doc_status()`. Extended `_build_conversation_summary()`: Collected for remove-car, premium review, missing document, payment risk; Still needed for add-car (delivery/driver) and missing doc (items not resent). |
| `ui/src/pages/UnifiedIntakePage.tsx` | Display Collected and Still needed from conversation_summary; "Message that opened this case" → "Full conversation" when multi-turn. |

### Stage 3
| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Added "renewal review", "renewal premium" to PREMIUM_REVIEW_MARKERS. Premium review check before renewal_reminder so "续保保费太高" and "renewal premium too high" route to customer_question (premium review), not renewal_reminder. |

### Stage 4
| File | Change |
|------|--------|
| `configs/inbox_triage_scenarios.json` | Added D1 (renewal premium too high EN), D2 (续保保费太高 ZH), D3 (missing doc shorthand), D4 (add car shorthand). |

### Docs
| File | Change |
|------|--------|
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Added broker handoff clarity note; reference to BROKER_HANDOFF_CLARITY_GUIDE. |
| `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` | Added reference to BROKER_HANDOFF_CLARITY_GUIDE. |

---

## 4. Daily-use case improvements

| Case | Improvement |
|------|-------------|
| **Add car / vehicle change** | Already strong; Collected/Still needed now visible in broker case card. |
| **Premium review** | "续保保费太高" and "renewal premium too high" now correctly route to premium review (not renewal_reminder). Collected: "policy/bill mentioned" when customer says they sent. |
| **Missing document** | Collected: items resent; Still needed: items not yet resent. Broker sees clearer status. |
| **Remove car** | Collected: vehicle, sale date, transfer when detectable from customer messages. |
| **Payment failed** | Collected: "client says sent notice/screenshot" when present. |

---

## 5. Before vs after

| Aspect | Before | After |
|--------|--------|-------|
| Broker handoff | "Collected:" only for add-car; raw conversation dominant | Collected for add-car, remove-car, premium, missing doc, payment risk; Still needed when safe |
| Case focus | Category tag only | Same; category tag now more accurate (premium vs renewal) |
| Multi-turn label | "Message that opened this case" | "Full conversation" when multi-turn |
| Premium vs renewal | "续保" could match renewal_reminder | Premium review checked first; "续保保费太高" → premium review |
| Daily-use regression | 32 scenarios | 36 scenarios (D1–D4 for premium, missing doc, add car) |

---

## 6. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` | **Pass** | UI compiles |
| `run_inbox_triage_scenarios.py` | **Pass** (36/36) | Category, urgency, draft quality |
| `run_chen_kui_proxy_calibration.py` | **Pass** (14/14) | Draft tone, proxy style |
| `run_multi_turn_simulations.py` | **Pass** (14/14 Strong) | Multi-turn intake quality |
| `verify_inbox_case_persistence.py` | **Pass** | Case store, follow-up, notes |
| `guardrail_inbox_triage.sh` | **Pass** | Full guardrail |
| `unified_intake_smoke_check.sh` | **Pass** | Manual UI checklist |

---

## 7. Business value impact

- **Broker handoff:** Broker can understand the case faster; Collected and Still needed reduce mental reconstruction.
- **Daily-use cases:** Premium review, add car, missing doc, remove car all now have clearer broker-side summaries.
- **Repetitive office work:** Chen Kui can see at a glance what was collected and what remains; less re-reading and re-asking.

---

## 8. Remaining blocker(s)

1. **Extraction is heuristic:** Year/zip/model/delivery/driver use regex and keyword matching; no structured NLP.
2. **Still needed is conservative:** Only add-car and missing-document get it; other categories defer to broker inference.
3. **No `what_still_needed` API field:** Broker infers from conversation_summary; no explicit structured field.

---

## 9. Recommended next step

1. **Demo:** Run the 5 walkthroughs in UI for founder demo; verify broker handoff clarity in practice.
2. **Optional:** Add one more multi-turn simulation for "premium review" with second-turn "policy sent" to validate Collected display.
3. **Defer:** Full structured progressive_answers, NLP extraction, workbench redesign.

---

## 10. 中文或中英混合宏观总结

**这次 broker handoff 清晰了哪些：**
- Broker 打开 case 能看到 Collected（已收集：年份、车型、zip、保单/账单等）和 Still needed（还缺：delivery date、main driver 等）。
- 多轮对话的 case 会显示 "Full conversation" 标签，方便区分单条消息 vs 完整对话。
- 加车、删车、保费 review、缺材料、付款风险都有更清晰的 intent 和 collected 摘要。

**哪些 daily-use case 现在更顺了：**
- 保费太高 / 续保 review：续保保费太高、renewal premium too high 不会再误判成 renewal_reminder，会正确走 premium review。
- 缺材料：会显示哪些已补、哪些还缺。
- 加车、删车：Collected 会显示已收集的 vehicle 信息。

**哪些场景最能帮陈奎省时间：**
- 加车报价：一眼看到 year、model、zip、delivery。
- 缺材料：看到 dec page 已补、garaging proof 还缺。
- 保费 review：看到 policy/bill 已提到。
- 付款失败：看到客户说已发截图。

**有没有困难或限制：**
- 提取是启发式，没有做完整 NLP。
- Still needed 只在 add-car 和 missing-doc 时安全显示，其他情况 broker 需从 source_text 推断。

**现在最适合演示哪几条链路：**
1. BMW X5 / 新车报价
2. add car / vehicle change
3. premium too high / renewal review
4. missing document / declaration page
5. payment failed / cancellation risk

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

## 12. Handoff + daily-case walkthroughs

### 1. BMW X5 / 新车报价

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | I bought a new BMW X5, how much is insurance? |
| 1 | System | I can start a quote for the new car. Send me the year, make/model, VIN if you have it, delivery date, zip or address, and main driver and I will check it. |
| 2 | Customer | 2024, 90210, picking up next week |
| 2 | System | Quote details received. Our office will review and follow up with you. |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `conversation_summary`: "Add-car / new vehicle quote. Collected: year, model, zip, delivery. Still needed: main driver. 2 customer message(s). Latest: 2024, 90210, picking up next week..."  
**Result:** Strong.

---

### 2. Add car / vehicle change

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | 想加一台车，2025 Honda CR-V |
| 1 | System | 可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。 |
| 2 | Customer | 90210 |
| 2 | System | 报价资料已收集，办公室会尽快出价，有结果会联系您。 |

**Handoff:** Yes, after turn 2.  
**Broker receives:** Collected: year, model, zip. Still needed: delivery date, main driver.  
**Result:** Strong.

---

### 3. Premium too high / renewal review

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | 续保保费太高了，能不能看看怎么降 |
| 1 | System | 我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我，我先帮你核对。 |
| 2 | Customer | 续保通知和账单我发你微信了 |
| 2 | System | 办公室会尽快处理，有结果会联系您。 |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `conversation_summary`: "Premium review / too high. Collected: policy/bill mentioned. 2 customer message(s)..."  
**Result:** Strong.

---

### 4. Missing document / declaration page

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | UW follow up - need dec page + garaging proof. 客户说上周发过了 |
| 1 | System | 现在文件里还缺 declaration page（保单首页） 和 garaging proof（车辆停放地址证明）。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。 |
| 2 | Customer | declaration page 他又发了一次，garaging proof 还没弄 |
| 2 | System | 办公室会尽快处理，有结果会联系您。 |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `conversation_summary`: "Missing document follow-up. Collected: dec page resent. Still needed: garaging proof. 2 customer message(s)..."  
**Result:** Strong.

---

### 5. Payment failed / cancellation risk

| Turn | Role | Content |
|------|------|---------|
| 1 | Customer | 客户问：这个英文 notice 说 payment failed，我现在怎么办？ |
| 1 | System | 这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。 |
| 2 | Customer | 我发了截图在微信 |
| 2 | System | 办公室会尽快处理，有结果会联系您。 |

**Handoff:** Yes, after turn 2.  
**Broker receives:** `conversation_summary`: "Payment failed / lapse risk. Collected: client says sent notice/screenshot. 2 customer message(s)..."  
**Result:** Strong.

---

## Demo honesty

| Area | Status |
|------|--------|
| Broker handoff clarity | **Real** — Collected/Still needed from heuristic extraction |
| Daily-use case routing | **Real** — premium vs renewal, add car, missing doc, remove car |
| Conversation summary | **Real** — intent + Collected + Still needed + msg count |
| Structured progressive_answers | **Deferred** |
| NLP extraction | **Heuristic** — regex and keyword matching |

---

*End of sprint report*

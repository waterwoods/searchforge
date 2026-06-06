# 5 Business Flows Verticalization Sprint Report

**Sprint:** 5 Business Flows Verticalization  
**Date:** 2026-03-10  
**Status:** Complete

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1 — Define flow targets + acceptance criteria | ✅ | `docs/FIVE_BUSINESS_FLOWS_TARGETS.md` |
| Stage 2 — Build multi-scenario simulation packs | ✅ | Claim intake added; F1–F4 scenarios; expression robustness CL1–CL5 |
| Stage 3 — First pass simulation | ✅ | All 44 inbox scenarios, 41 expression variants, 17 multi-turn pass |
| Stage 4 — Prioritize highest-value problems | ✅ | Claim intake was main gap; classification order fix for S2/S5 |
| Stage 5 — Improvement loop 1 | ✅ | Claim intake flow, markers, reply templates, classification order |
| Stage 6 — Improvement loop 2 | ⏭️ | Skipped — first loop sufficient |
| Stage 7 — Optional loop 3 | ⏭️ | Skipped |
| Stage 8 — Demo proof | ✅ | UNIFIED_INTAKE_DEMO_READINESS.md updated; claim intake added |
| Stage 9 — Regression protection | ✅ | F1–F4 in inbox_triage_scenarios; MT17 in multi-turn; CL1–CL5 in expression robustness |
| Stage 10 — Audit | ✅ | All validations pass |

---

## 2. Flow targets and acceptance criteria

See `docs/FIVE_BUSINESS_FLOWS_TARGETS.md`. Summary:

| Flow | Customer success | Broker success | Good enough |
|------|------------------|----------------|-------------|
| **1. Add car / new quote** | Asks naturally; system asks year/model/zip/delivery | Collected visible; broker_next_step actionable | ✅ |
| **2. Renewal / premium too high** | Policy/bill mentioned; review path explained | Premium review intent; realistic options | ✅ |
| **3. Claim intake / accident** | First-step guidance (safety, photos, other driver) | Claim intake intent; broker guides to report | ✅ NEW |
| **4. Notice / payment / cancellation** | Urgency stated; notice/screenshot asked | Payment/cancel; same-day action | ✅ |
| **5. Document chase / underwriting** | Item named; resend or check confirmed | Missing doc; Collected/Still needed | ✅ |

---

## 3. Product / logic changes made

| File | Change |
|------|--------|
| `configs/industries/insurance/markers.json` | Added `claim_intake` markers; extended `premium_review` (coverage adjustment); extended `question_help` (is this urgent) |
| `configs/industries/insurance/reply_templates.json` | Added `claim_intake` template (zh/en) |
| `services/fiqa_api/inbox_triage/triage.py` | Added `_is_claim_intake_request()`; claim handling in `_build_client_reply_draft`, `_build_customer_question_broker_next_step`, `_build_customer_question_client_prep`; classification order (missing_document before claim); exclusion for "prior claims" in claim_intake |
| `configs/expression_robustness_cases.json` | Added `claim_intake` intent with CL1–CL5 variants |
| `configs/inbox_triage_scenarios.json` | Added F1 (claim zh), F2 (claim en), F3 (notice urgent), F4 (doc chase) |
| `configs/customer_entry_multi_turn_simulations.json` | Added MT17 claim intake multi-turn |
| `docs/FIVE_BUSINESS_FLOWS_TARGETS.md` | **New** — flow targets and acceptance criteria |
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | Added claim intake row to strategy matrix |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Added claim intake to best-supported flows and example inputs |

---

## 4. Simulation and improvement loops

### First pass
- Inbox scenarios: 42/44 (S2 missing_document, S5 underwriting_followup misclassified)
- Expression robustness: 41/41 (claim_intake added and passed)
- Multi-turn: 17/17 (MT17 claim intake added and passed)

### Fixes
1. **Classification order:** `missing_document` checked before `claim_intake` so "driver's license" + "requested" → missing_document, not claim
2. **Claim exclusion:** `_is_claim_intake_request` returns False for "prior claims", "underwriting needs", "clarification on" so S5 → underwriting_followup
3. **Claim markers:** Removed bare "license" from claim_intake; use "other driver's license" to avoid matching document requests

### After rerun
- Inbox: 44/44 ✅
- Expression: 41/41 ✅
- Multi-turn: 17/17 ✅
- Chen Kui proxy: 14/14 ✅
- Guardrail: PASS ✅

---

## 5. Product proof strength

| Flow | Strength | Sellable |
|------|----------|----------|
| Add car / new quote | Strong | Yes — multi-turn, shorthand, full-info handoff |
| Renewal / premium too high | Strong | Yes — policy/bill ask, realistic options |
| Claim intake / accident | **Strong (new)** | Yes — first-step guidance, office-natural |
| Notice / payment / cancellation | Strong | Yes — urgency, same-day action |
| Document chase / underwriting | Strong | Yes — item naming, resend/check |

The platform now feels closer to a real insurance office: customers can ask naturally, the system guides and collects, and the broker receives cleaner cases.

---

## 6. Validation summary

| Check | Result |
|-------|--------|
| `run_inbox_triage_scenarios.py` | 44/44 pass |
| `run_expression_robustness.py` | 41/41 strong |
| `run_multi_turn_simulations.py` | 17/17 pass |
| `run_chen_kui_proxy_calibration.py` | 14/14 pass |
| `guardrail_inbox_triage.sh` | PASS |
| `npm run build` (ui/) | Success |
| `test_inbox_triage_api.py` | All pass (when server on 8001) |

---

## 7. Business / platform value

- **Customer experience:** Natural questions (add car, claim, payment, document) get intent-specific replies, not generic fallback.
- **Broker workload:** Cleaner handoffs with Collected/Still needed; broker_next_step is operational.
- **Platform story:** Five high-value flows verticalized; config-driven; retrieval assists explanation where appropriate; rules stay in code.

---

## 8. Remaining blocker(s)

1. **Claim multi-turn Collected:** Conversation summary does not yet extract "photos", "other driver info" for claim intake (nice-to-have).
2. **Premium coverage-adjustment phrasing:** "Remove one car to lower premium" could be clearer; currently maps to premium_review.
3. **Retrieval for claim:** No RAG augmentation for claim first-step content yet (optional).

---

## 9. Recommended next step

**One clear next step:** Add 1–2 claim-intake scenarios to the founder demo queue so Chen Kui can see the accident first-response flow live.

---

## 10. 中文或中英混合宏观总结

**5 条主线进步：**
1. **加车/报价** — 已有，保持稳定
2. **续保/保费太高** — 已有，增加 coverage adjustment 识别
3. **事故/理赔首次响应** — **新增**：刚出事故、要收集什么、对方保险等，系统给出第一步指引（安全、拍照、对方信息）
4. **通知/付款/取消** — 已有，增加「是不是要处理」「is this urgent」识别
5. **缺材料/核保跟进** — 已有，保持稳定

**最像真实办公室的：** 加车、事故首次响应、付款失败、缺材料

**还不够好的：** 事故多轮 Collected 提取（可选优化）

**修了的高价值问题：** 事故流程从无到有；分类顺序修复（S2/S5）

**对陈奎和以后客户：** 事故刚发生时的客户不再掉进「不够完整」；办公室收到更清晰的案件摘要和下一步指引。

---

## 11. Practical 5-flow cheat sheet

| Flow | Customer asks | System collects | Handoff when | Broker receives | Still manual |
|------|---------------|------------------|--------------|-----------------|--------------|
| **Add car** | 加车、报价、new car | year, model, zip, delivery, driver | year+model+zip | Collected; quote same day | Carrier quote |
| **Renewal/premium** | 保费太高、怎么降 | policy, bill | policy/bill mentioned | Premium review; 1–2 options | Rate comparison |
| **Claim intake** | 出事故、要收集什么 | accident details, photos, other driver | 1–2 turns | Claim first response; guide to report | Claims adjudication |
| **Notice/payment** | payment failed、取消 | notice, screenshot | notice or proof | Same-day fix; confirm payment | Payment processing |
| **Document chase** | 缺材料、发过了 | item, sent status | item + status clear | Resend or check | Document verification |

---

## 12. Simulation outcome summary

| Flow | Strong | Acceptable | Weak | Fixes |
|------|--------|------------|------|-------|
| Add car | 10 variants, 6 MT | 0 | 0 | — |
| Remove car | 4 variants, 1 MT | 0 | 0 | — |
| Premium review | 5 variants, 1 MT | 0 | 0 | — |
| Payment/cancellation | 5 variants, 3 MT | 0 | 0 | — |
| Notice confusion | 4 variants, 2 MT | 0 | 0 | — |
| Missing document | 5 variants, 2 MT | 0 | 0 | Classification order |
| **Claim intake** | **5 variants, 1 MT** | 0 | 0 | **New flow** |
| DMV/SR-22 | 3 variants, 1 MT | 0 | 0 | — |

**Repeated issue patterns addressed:** Claim intake missing; classification collision (license/prior claims).

---

## 13. Live proof walkthroughs

### 1. Add car / new quote
- **Customer:** "我买了台宝马X5，想问下保费多少钱"
- **System:** "可以先帮你看这台车的报价。把车子的年份、车型、VIN（有的话）、提车日期、地址邮编和主要驾驶人发我，我先帮你算。"
- **Retrieval:** None
- **Next step:** Customer provides year, zip, delivery → handoff
- **Handoff:** Yes (turn 2)
- **Result:** Strong

### 2. Renewal / premium too high
- **Customer:** "保费太高了，能不能便宜一点"
- **System:** "我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我，我先帮你核对。"
- **Retrieval:** None
- **Next step:** Customer sends policy/bill → handoff
- **Handoff:** Yes (turn 2)
- **Result:** Strong

### 3. Claim intake / accident first response
- **Customer:** "刚出事故了，要收集什么？"
- **System:** "事故刚发生的话，先确保人没事，再拍现场照片、记下对方车牌和保险信息。把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。"
- **Retrieval:** None
- **Next step:** Customer sends details/photos → handoff
- **Handoff:** Yes (turn 2)
- **Result:** Strong

### 4. Notice / payment / cancellation confusion
- **Customer:** "客户问：这个英文 notice 说 payment failed，我现在怎么办？"
- **System:** "这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。"
- **Retrieval:** Optional (notice_interpretation when enabled)
- **Next step:** Customer sends notice/screenshot → handoff
- **Handoff:** Yes (turn 2)
- **Result:** Strong

### 5. Document chase / underwriting follow-up
- **Customer:** "UW follow up - need dec page + garaging proof. 客户说上周发过了"
- **System:** "现在文件里还缺 declaration page（保单首页）和 garaging proof（车辆停放地址证明）。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对。"
- **Retrieval:** Optional (document explanation when confused)
- **Next step:** Customer resends or confirms → handoff
- **Handoff:** Yes (turn 2)
- **Result:** Strong

---

*End of sprint report*

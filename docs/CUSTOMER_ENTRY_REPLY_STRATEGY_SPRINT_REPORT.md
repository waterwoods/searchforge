# Customer Entry Reply Strategy Sprint Report

**Sprint:** Customer Entry Reply Strategy Sprint  
**Date:** 2026-03-09  
**Scope:** Unified Intake / Customer Entry mainline only

---

## 1. Stages completed

| Stage | Status | Notes |
|-------|--------|-------|
| Stage 1: Define response strategies | **Completed** | Created `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` with 8-category matrix |
| Stage 2: Implement intent-specific first response | **Completed** | Extended add-car detection for English ("I bought a new BMW X5, how much is insurance?"); improved broker-natural replies |
| Stage 3: Improve customer-side wording | **Completed** | Added zip/address to add-car client_prep and drafts (Chinese + English) |
| Stage 4: Broker-side continuity | **Completed** | Verified case creation, category/urgency, broker_next_step, saved-case flow; no regressions |
| Stage 5: Optional polish | **Completed** | Added R17 scenario, CK13 proxy case, doc updates |

---

## 2. Response strategy design

**Created:** `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md`

**Categories covered:**

1. Add car / new car quote — ask for year, model, VIN, delivery date, zip, driver
2. Remove car / policy change — ask for sale date, vehicle details, transfer status
3. Premium too high / renewal review — ask for policy, renewal notice, bill
4. Payment failed / cancellation risk / lapse risk — state urgency, ask for notice/payment
5. English notice confusion — explain likely meaning, ask for full notice
6. Missing document — name the missing item, ask for resend or confirm already sent
7. DMV / SR-22 help — explain workflow, what to prepare
8. Generic vague help — light clarification fallback

**Why it matters:** The customer entry no longer responds to all incomplete inputs the same way. High-frequency requests (add car, premium review, payment risk, notice confusion, missing document, DMV/SR-22) now get broker-natural next-step requests instead of generic "please provide more context."

---

## 3. Product changes made

### Stage 1

| File | Change |
|------|--------|
| `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` | **New.** 8-category response matrix, per-category strategy detail, anti-patterns |

### Stage 2

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Extended `ADD_VEHICLE_MARKERS`: "new car", "bought a", "bought", "how much is insurance", "how much for insurance", "insurance for", "quote for", "how much" |
| `services/fiqa_api/inbox_triage/triage.py` | Extended `VEHICLE_CONTEXT_MARKERS`: "bmw", "mercedes", "lexus", "x5", "accord", "camry" |

### Stage 3

| File | Change |
|------|--------|
| `services/fiqa_api/inbox_triage/triage.py` | Add-car `client_prep`: added "zip or address" |
| `services/fiqa_api/inbox_triage/triage.py` | Add-car English draft: added "zip or address" |
| `services/fiqa_api/inbox_triage/triage.py` | Add-car Chinese draft: added "地址邮编" |

### Stage 5

| File | Change |
|------|--------|
| `configs/inbox_triage_scenarios.json` | Added R17: "I bought a new BMW X5, how much is insurance?" |
| `configs/chen_kui_proxy_calibration_cases.json` | Added CK13: English add-car quote |
| `docs/UNIFIED_INTAKE_DEMO_READINESS.md` | Section 3: Customer Entry Reply Strategy; R17 example in Best Example Inputs |
| `docs/UNIFIED_INTAKE_MVP_SCENARIOS.md` | R17 scenario; Fragmented Demo Cases; Category Coverage |
| `docs/CHEN_KUI_FOUNDER_DEMO_SCRIPT.md` | Step 1: English add-car example and intent-specific response note |

---

## 4. Before vs after

**Before:** A customer asking "I bought a new BMW X5, how much is insurance?" could fall into `unclear` or a generic `customer_question` with a vague "send me more context" reply.

**After:** Same input is classified as `customer_question` with add-vehicle intent. The reply asks for: year, make/model, VIN if available, delivery date, zip or address, and main driver — like a real broker office intake.

**Other improvements:**

- Add-car (Chinese and English): now explicitly asks for zip/address for rating
- Payment risk, cancellation, notice confusion, missing document, DMV/SR-22: already had intent-specific logic; no regressions
- Generic vague: only used when no clear intent; lighter clarification fallback

**Broker continuity:** Case creation, category, urgency, broker_next_step, client_prep, saved-case flow, reopen, status, follow-up, notes — all intact.

---

## 5. Validation summary

| Check | Result | Protects |
|-------|--------|----------|
| `npm run build` (ui/) | **Pass** | Frontend builds |
| `run_inbox_triage_scenarios.py` | **29/29 pass** | Category, urgency, escalation, draft quality |
| `run_chen_kui_proxy_calibration.py` | **13/13 pass** | Proxy-style drafts, language fit |
| `test_inbox_triage_api.py` | **Pass** | API triage + persistence |
| `guardrail_inbox_triage.sh` | **Pass** | Scenario pack, output shape, persistence |
| `verify_inbox_case_persistence.py` | **Pass** | Save/list/status/follow-up/note/activity |

---

## 6. Business value impact

- **Customer experience:** First reply feels like a real office intake, not a generic AI response.
- **Broker work:** Fewer "please provide more context" loops; clearer next-step requests.
- **Demo:** Stronger story: "I bought a new BMW X5, how much is insurance?" → broker-natural reply asking for vehicle details.

---

## 7. Remaining blocker(s)

1. None. Sprint goals met.
2. (Optional) Broader English add-car phrasing ("just got a Tesla", "need a quote for my new car") — current markers cover common patterns.
3. (Optional) LLM path: `_merge_with_rule_guardrails` always uses rule-based drafts; LLM wording is not used for client_reply_draft. Intentional for demo-safe behavior.

---

## 8. Recommended next step

**One clear next step:** Run a live demo with Customer Entry first — paste "I bought a new BMW X5, how much is insurance?" and show the intent-specific reply, then switch to Broker Workbench to show the case.

---

## 9. 中文或中英混合宏观总结

**这次主要做对了什么：**

- 客户入口的回复策略更清晰：加车/报价、保费审核、付款风险、通知困惑、缺件、DMV/SR-22、模糊求助 — 每种都有对应的回复模式。
- 英文加车/报价请求（如 "I bought a new BMW X5, how much is insurance?"）现在会得到具体的车辆信息请求，而不是「请提供更多信息」。
- 加车场景的客户准备清单增加了邮编/地址，更贴近实际报价流程。

**哪些类型更像保险办公室会怎么接：**

- 加车/报价：直接问年份、车型、VIN、提车日期、地址、驾驶人。
- 付款/停保风险：说明 urgency，请客户发通知和付款截图，今天尽快处理。
- 缺件：点名缺什么，请客户再发或确认已发。
- DMV/SR-22：说明流程，请客户发 DMV 信，再告诉要带什么。

**有没有遇到困难或限制：**

- 无。现有 rule-based 逻辑已覆盖主要场景；LLM 路径被 guardrail 覆盖，始终用 rule-based draft，保证 demo 稳定。

**现在最适合演示哪几个客户问题：**

1. **高险：** "客户问：这个英文 notice 说 payment failed，我现在怎么办？" — 付款风险，urgency 清晰。
2. **日常：** "I bought a new BMW X5, how much is insurance?" — 加车报价，具体信息请求。
3. **日常：** "客户要加一台2021 Tesla Model Y，下周提车，问今天能不能先出报价" — 中文加车。
4. **缺件：** "UW follow up - need dec page + garaging proof. 客户说上周发过了" — 缺件跟进。

---

## 10. 如何打开前端 / 后端

**Local run:**

```bash
bash scripts/run_demo_local.sh
```

**URLs:**

- Frontend: http://localhost:5173/workbench/unified-intake
- Backend: http://localhost:8001 (default)

**Which tab first:** 客户入口 (Customer Entry) — default tab.

**Port caveats:**

- If 5173 is taken, Vite may use 5174.
- If 8001 is stale, use isolated path: backend 8002, frontend 5174 with `VITE_API_PROXY_TARGET=http://127.0.0.1:8002`.

---

## 11. Customer-side simulation

### Example 1: High-risk (payment failed / cancellation risk)

**Customer types:**
```
客户问：这个英文 notice 说 payment failed，我现在怎么办？
```

**System replies:**
```
这看起来是付款出了问题。请把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。
```

**Urgency tag:** "This needs urgent attention."  
**Follow-up:** "Chen Kui's office will review this and follow up with you."

**Broker-side case:** `payment_lapse_expiration`, `high`, `manual_followup_needed=true`. Broker next step: "Confirm whether the payment actually failed, check whether the carrier still shows the balance due, and help the client fix it today."

**Why better than old:** Old generic fallback might say "please provide more context." New reply names the issue (付款), asks for notice and payment proof, and states urgency (今天尽快处理，避免停保).

---

### Example 2: Daily-use (add car / premium review)

**Customer types:**
```
I bought a new BMW X5, how much is insurance?
```

**System replies:**
```
I can start a quote for the new car. Send me the year, make/model, VIN if you have it, delivery date, zip or address, and main driver and I will check it.
```

**Follow-up:** "Chen Kui's office will review this and follow up with you."

**Broker-side case:** `customer_question`, `medium`, `manual_followup_needed=true`. Broker next step: "Collect the new vehicle details, confirm the delivery date and primary driver, then quote or add it the same day if possible."

**Why better than old:** Old path could classify as `unclear` or return "please provide more context" or "send me the full notice." New reply recognizes add-car/quote intent and asks for the concrete fields a broker needs: year, model, VIN, delivery date, zip, driver.

---

*End of sprint report*

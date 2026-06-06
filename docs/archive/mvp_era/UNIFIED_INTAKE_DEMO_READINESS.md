# Unified Intake Demo Readiness

**Purpose:** One practical page Andy can use before showing Unified Intake to his father.

---

## 0. Founder Demo Story (Business-First)

| Version | Content |
|--------|---------|
| **One sentence** | A broker assistant that turns messy inbound messages into one structured case with urgency, next step, and a draft reply — so the office moves faster without losing control. |
| **30 seconds** | When a customer sends a text, pasted notice, or screenshot — the system classifies it, asks for what’s missing, and hands off a clean case to the broker. The broker sees one dominant next move, what the client should prepare, and a draft response. No manual triage. |
| **2 minutes** | Customer Entry: paste once, get intent-specific replies (add car, payment risk, notice confusion, missing document, claim intake). Multi-turn: ask for year/model/zip, then hand off. Broker Workbench: structured case card, urgency, Collected/Still needed, client draft. Cases stay saved. Broker stays in control. |
| **Why Chen Kui** | 减少重复解释、减少intake工作量、处理真实客户发来的messy消息、比通用chatbot强、规则+检索+人工把关。 |

---

## 1. What Will Be Shown

Unified Intake has **two surfaces**:

- **Customer Entry (客户入口)** — default tab. Simple customer front door: one input box, one CTA. Customer gets a useful first-pass response; the case is saved to the broker workbench. Click "查看工作台" to switch to broker view.
- **Broker Workbench** — internal triage and case management.

**Best demo order:** Show Customer Entry first (customer submits a messy message), then switch to Broker Workbench.

**Chen Kui trial pack:** See `docs/CHEN_KUI_TRIAL_PACK.md` for trial purpose, scenarios, order, value validation questions, and pilot offer.

**Visual Simulation Assistant:** On the Customer Entry tab, click **Simulation Assistant** to open a side panel. Run scripted multi-turn scenarios (Notice/cancellation, Missing document, Add car, Claim, Renewal) to quickly see how the system responds. Useful for internal QA and demo prep. See `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md` §5b.

**Broker handoff clarity:** When a case is handed off, the broker sees: (1) **Case focus** (dedicated line at top: Add car quote, Premium review, Claim intake, Missing document, Payment / cancellation risk), (2) Your next move (operational, action-oriented), (3) Collected / Still needed (structured chips for add-car, renewal, claim, missing-document; free-text fallback for others), (4) **Human confirmation recommended** badge when AI collected from conversation (payment risk, customer_says_sent, VIN/driver). Unified workflow language: Case focus → Your next move → Collected → Still needed → Human confirmation (when applicable) → Full conversation. See `docs/BROKER_HANDOFF_CLARITY_GUIDE.md`.

**Queue triage at a glance:** The Recent cases list helps the broker decide which case to open first. Each queue card shows: **case focus tag first** (when inferable from structured fields), attention label (Action now, Your move, Due today), readiness (Ready to act / Needs more info / Verify receipt), urgency, compact flow-specific preview, and tracking summary. Work now vs Waiting or parked grouping. See `docs/BROKER_HANDOFF_CLARITY_GUIDE.md` §0a. Trial walkthroughs: `docs/STRUCTURED_OUTPUT_VISIBILITY_BUG_HARVEST_TRIAL_READINESS_SPRINT_REPORT.md` §12.

**Multi-turn intake:** The Customer Entry tab supports 2–3 turn conversations. After the first reply, the customer can continue in the same input. The system acknowledges what the customer said (e.g. "好的，2024年的。") before asking the next most useful missing field (e.g. add-car: year only → ask for zip). It asks 1–2 items per turn, not a 6-item checklist. It hands off when enough info is collected or after 2–3 turns. Handoff phrasing: "好的，收到了。" when customer says they sent something; "好的，明白了。" when customer corrects; "您说的卖车信息已整理好了" for remove-car; "您说的报价资料已整理好了" for add-car. See `configs/customer_entry_multi_turn_simulations.json` and `scripts/run_multi_turn_simulations.py` for regression coverage (38 variants including 3–4 turn scenarios). Consolidation: `docs/FRONT_END_CONSOLIDATION_TARGET.md`; `docs/FRONT_END_NATURALNESS_PROGRESSION_CONSOLIDATION_SPRINT_REPORT.md`.

The broker-facing flow:

1. Paste inbound text
2. Run triage
3. Review a structured case card
4. See broker action guidance
5. Copy a client-facing draft
6. Confirm whether manual follow-up is required
7. Reopen the saved case from Recent cases
8. Mark a lightweight case status
9. Set who or what the case is waiting on
10. Save a tiny next-contact timing memory
11. Add or review a tiny broker note / activity trail
12. Use the founder-demo-safe starter queue and snapshot counts when you need a repeatable live-looking workbench

Route: `https://ui-smoky-beta.vercel.app/workbench/unified-intake` (production) or `http://localhost:5173/workbench/unified-intake` (local)

Repeatable local prep:

```bash
PYTHONPATH=. python3 scripts/prepare_unified_intake_founder_demo.py
```

---

## 2. What Is Real vs Demo-Assisted

| Area | Status | Notes |
|------|--------|-------|
| Customer Entry tab | **Real** | Customer-facing input, first-pass response, case saved to broker workbench |
| Text input | **Real** | Broker pastes text directly |
| Triage result | **Real** | API returns structured output |
| Case card rendering | **Real** | UI shows urgency, category, next step, prep, client draft |
| Lightweight local case persistence | **Real** | Saved case appears in Recent cases |
| Simple case status | **Real** | `new`, `reviewing`, `waiting_client`, `done` |
| Follow-up target + timing | **Real** | Local-only `waiting_on` + `next_contact_by` on saved cases |
| Broker note / activity trail | **Real** | Local-only follow-up context on saved cases |
| Copy draft | **Real** | Browser copy action |
| Founder demo snapshot counts | **Real** | Derived from the current local saved-case queue |
| Founder demo starter queue | **Demo-assisted** | Demo-safe seeded input messages run through the real local triage + saved-case flow |
| Showcase examples | **Demo-assisted** | Seeded messages for repeatable demo, hidden behind **Need an example?** so the main entry stays paste-first |
| OCR upload / inbox sync / CRM collaboration | **Deferred** | Not part of v1 |

---

## 3. Customer Entry — Same-Page Conversational Intake

The Customer Entry tab now uses a **same-page conversational flow** (see `docs/CONTINUOUS_CUSTOMER_INTAKE_MVP.md`):

- Customer types first message → system replies inline
- If key info is missing, system asks 1–2 focused follow-up questions
- Customer can continue in the same conversation
- Once enough info or after 2nd message, system hands off to broker
- Customer sees "办公室会尽快处理" and can click 查看工作台

Intent-specific first responses follow `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md`. All high-value scenarios align to the mature intake skeleton (`docs/MATURE_INTAKE_SKELETON.md`): detect → ask → enough? → hand off. High-frequency requests (add car, premium review, payment risk, notice confusion, missing document, DMV/SR-22) receive broker-natural next-step requests instead of generic "provide more context."

**Expression robustness:** The system handles multiple realistic phrasings of the same intent (short Chinese, mixed language, WeChat-style fragments). See `configs/expression_robustness_cases.json` and `scripts/run_expression_robustness.py`. Regression cases ER1–ER4 protect shorthand add-car, fragment add-car, mixed-English remove-car, and English notice confusion.

**Adversarial real-user:** Messy, imperfect inputs (e.g. 刚撞了对方跑了、续保涨了好多、都发过了怎么还要) are stress-tested. See `configs/adversarial_real_user_scenarios.json` and `scripts/run_adversarial_simulation.py`. Guardrail includes adversarial pack.

**Complex adversarial (mixed-intent + long-context):** Two harder packs stress-test (1) mixed-intent messages (e.g. 保费太贵了+英文notice没看懂, 出事了要拍什么+payment failed什么意思) and (2) vague follow-ups / corrections (e.g. 不是这个，是另一辆车; 就是上次那个材料，我又发了). See `configs/mixed_intent_scenarios.json`, `configs/long_context_memory_shift_simulations.json`, and `scripts/run_complex_adversarial_simulation.py`. Guardrail includes complex pack.

## 4. Supported Demo Flows

**Today's 3 focus chains (Chen Kui founder demo):**

1. **BMW X5 / new car quote** — Customer Entry: "I bought a new BMW X5, how much is insurance?" → system asks year/model/zip/delivery → customer provides → handoff with "Quote details received" (EN) or "报价资料已收集" (ZH). Broker sees Collected: year, model, zip.
2. **Payment failed / cancellation risk** — "这个英文 notice 说 payment failed，我现在怎么办？" → system asks for notice/screenshot, states urgency → "我发了截图" → handoff. Broker sees payment_lapse_expiration, same-day action.
3. **English notice confusion / DMV-SR22** — "客户发来一张DMV的信，问这是什么意思？" or "DMV信说要 SR-22 proof 才能 clear suspension，这个要带什么？" → system asks for full notice → customer provides → handoff. Broker sees customer_question with DMV/SR-22 guidance.

Best-supported flows in v1:

- Cancellation warning
- Missing document follow-up
- Payment / lapse concern
- Mixed shorthand document chase
- Broken AutoPay / interruption wording
- Mixed overdue / policy-stop question
- DMV / SR-22 help wording
- Premium-too-high review request
- Add-car quote request
- **Claim intake / accident first response** — "刚出事故了，要收集什么？" or "Car accident just happened, what should I collect?" → first-step guidance (safety, photos, other driver info) → handoff
- Vague customer question
- Fragmented mixed-language notice text
- English notice with Chinese client question
- English cancellation notice with Chinese broker/customer summary

Weak or deferred flows:

- Raw image upload
- Attachment parsing
- Multi-message thread context
- Full customer/case history
- Automatic outbound communication

---

## 5. Strongest Father-Demo Order

### A. Best 3-case founder demo (time is short)

1. **Load founder demo queue** — seeds 13 demo-safe cases; cancellation-risk case auto-opens.
2. **Cancellation risk (opens first)** — proves urgency, same-day action, manual follow-up. Best first impression.
3. **Reopen missing-document follow-up** — proves operational follow-up, `waiting_on`, `next_contact_by`, note-taking.
4. **Reopen add-car quote or premium review** — proves everyday broker work, revenue/retention value.

If you only show one flow, show **Cancellation risk**.

### B. Best 5-case founder demo (stronger proof)

1. Cancellation risk (urgency, same-day)
2. Missing document (operational, "already sent")
3. Add-car quote (revenue, multi-turn, Collected)
4. **English notice + Chinese confusion** (retrieval-assisted explanation)
5. **Claim intake** or **messy-user hit-and-run** (robustness proof)

### C. Full tour (someone wants to see more)

1. Cancellation risk
2. Missing document
3. Add-car quote
4. Premium review
5. English notice + Chinese confusion (retrieval)
6. Declaration page missing (retrieval)
7. DMV / SR-22 help
8. Claim intake
9. Messy-user: 刚撞了，对方跑了，我现在先干嘛
10. Mixed-intent: 出事了要拍什么，还有payment failed什么意思

---

## 6. Best Example Inputs

Use these first:

### Urgent cancellation

```text
Notice: Policy will be cancelled in 7 days due to non-payment. Last notice.
```

### Missing document

```text
Underwriting requested driver's license copy. Client says "I already sent it last week."
```

### Mixed shorthand document chase

```text
UW follow up - need dec page + garaging proof. 客户说上周发过了
```

### Broken payment wording

```text
AutoPay failed again, please update card to avoid interruption in coverage
```

### Vague customer question

```text
客户发来一张DMV的信，问「这是什么意思？我需要做什么？」
```

### English add-car quote (Customer Entry)

```text
I bought a new BMW X5, how much is insurance?
```

Shows intent-specific reply: asks for year, make/model, VIN, delivery date, zip, and main driver — not generic "provide more context."

### Claim intake / accident first response (Customer Entry)

```text
刚出事故了，要收集什么？
```

or

```text
Car accident just happened, what should I collect?
```

Shows first-step guidance: ensure safety, take photos, get other driver's license and insurance info. Asks for accident details and photos to help with next steps to report the claim.

### Chinese add-car quote (Customer Entry)

```text
我刚刚买了2026年的宝马X5，我想问一下保费多少钱
```

Shows intent-specific reply in Chinese: asks for 年份、车型、VIN、提车日期、地址邮编、主要驾驶人 — not generic "这段内容还不够完整" fallback.

---

## 7. What To Say During Walkthrough

Suggested talk track:

- "This is the one unified intake surface for the kinds of inbound messages a broker already gets."
- "I can drop the raw message here without cleaning it up first."
- "I can paste a customer text, forwarded notice, or OCR text from a screenshot."
- "The system turns that into one current case with the broker's next move, client prep, and a draft reply."
- "The client draft is proxy-calibrated toward how a Chinese-speaking SoCal broker office would usually send a short reply, but it still needs real broker review."
- "The case is saved locally so it does not disappear after one paste, and I can see who I'm waiting on plus when I want to check again when I reopen it."
- "Recent cases stay lightweight so I can quickly tell what needs attention now versus what is waiting."
- "The founder-demo queue is demo-safe input data, but the triage, saved-case behavior, and local snapshot counts are real in this workbench."
- "It helps the broker move faster, but the broker still stays in control."

---

## 8. What Not To Overclaim

Do not say:

- "It is connected directly to email or WeChat."
- "It reads image uploads in the product."
- "It automatically sends replies."
- "It already manages full CRM cases, assignments, collaboration, or customer identity."
- "It perfectly handles every multilingual insurance message." The current strength is better short Chinese-vs-English draft fit on common broker cases, not full translation coverage.

---

## 9. Strongest Supported Demo Story

The clearest supported product story today is:

1. One inbound message comes in as pasted text
2. Unified Intake turns it into one structured broker case
3. The broker sees one dominant next move first, then client prep and a client draft
4. The case is saved locally and remains visible in Recent cases
5. The broker can reopen it, update lightweight follow-up context, and keep a tiny note/activity trail
6. The top-of-page snapshot makes the business value legible: what needs attention now, what is waiting on the client, and how many cases were triaged first

That is the strongest believable story to tell today. Do not stretch beyond it.

---

## 10a. Demo Readiness Note (Manual Smoke Sprint)

**Real-human demo readiness:** The product is ready to show when:
- First impression: Customer Entry feels like a real broker front door, not a chatbot toy
- Multi-turn: 5 flows (add-car, renewal, claim, notice/payment, missing doc) handle natural wording and hand off cleanly
- Handoff: "好的，收到了" when customer says they sent something; "您说的情况已整理好了" when they describe situation
- Document confusion: "garaging proof 是什么意思" → lead with definition first, then ask for notice
- Broker workbench: Case focus, Your next move, Collected/Still needed chips visible for all 4 structured flows

**Best case to show first:** Cancellation risk (urgency, same-day action). **Best workbench proof:** Missing document + add-car (Collected/Still needed chips).

---

## 10. Next Logical Step After Demo

The next product step is **slightly stronger broker memory without crossing into CRM**:

- tighten the saved-case reopen surface around lightweight follow-up context already present
- consider one tiny helper such as better due-state labeling or a safer clear/reset interaction
- do not broaden into assignments, automation, notifications, or CRM workflows

The product should keep feeling like a believable broker workbench, not a case-management platform.

**Lightweight ticket / follow-up (2026-03-11):** Reopen now shows "Resume here" with waiting on + next contact + latest note. Due-state: Overdue, Due today, Due tomorrow, No due date. "Last meaningful update" in case card; queue shows "Last update" when broker note exists. See `docs/LIGHTWEIGHT_TICKET_FOLLOWUP_UX_SPRINT_REPORT.md`.

**Paste new customer follow-up (2026-03-11):** When reopening a case, broker can paste a new customer message in "Paste new customer follow-up" and click "Update with new customer message." The case refreshes with updated next step, collected/still needed, and source_text. No inbox sync; broker pastes manually. See `docs/PASTE_NEW_MESSAGE_INTO_EXISTING_CASE_SPRINT_REPORT.md`.

---

## 11. Best Local Run Path

Use this order:

1. **Preferred default path:** `bash scripts/run_demo_local.sh`
   - Backend default: `8001`
   - Frontend default: `5173`
2. **If the default path looks stale or is already occupied, use the isolated stronger demo pair already supported by this repo:**

- backend: `python3 -m uvicorn services.fiqa_api.app_main:app --host 0.0.0.0 --port 8002`
- frontend: `VITE_API_PROXY_TARGET=http://127.0.0.1:8002 npm run dev -- --host 0.0.0.0 --port 5174`

This keeps the stronger Unified Intake demo path separate from any older local session already running on `8001`.

Warning:

- If `5173` auto-bumps to `5174`, use the actual Vite URL shown in the terminal
- If `8001` serves older output than expected, do not over-explain it live; switch to the isolated `8002` + `5174` path instead

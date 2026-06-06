# Unified Intake Product Audit — March 2026

**Auditor role:** Senior product auditor, conversation UX designer, SaaS workflow reviewer  
**Scope:** California auto insurance broker assistant — Unified Intake / Customer Entry  
**Benchmark:** Amazon / Shopify / Stripe style support systems  
**Date:** 2026-03-15

---

## PART 1 — EXECUTIVE SUMMARY

### What This Product Currently Is

SearchForge’s Unified Intake is a hybrid customer entry and broker triage system for a small auto insurance business. It combines:

1. **Customer Entry** — A conversational intake surface with 5 quick-action buttons (报价, 变更, 事故, 付款, 材料), free-text input, and multi-turn conversation that progressively collects structured fields (year, model, zip, etc.) and hands off to the broker when enough info is gathered.
2. **Broker Workbench** — A paste-box triage tool where the broker pastes inbound messages and receives structured output (category, urgency, broker_next_step, client_reply_draft, collected/still_needed fields).
3. **Backend triage** — Rule-based intent detection with optional LLM, slot-filling for add-car/quote, missing-document, cancellation, renewal, and claim flows, plus a lightweight state layer (follow_up_type, collection_stage, human_confirmation_required).

The system is designed for Chen Kui’s Chinese-speaking clients and office. It lives at `/workbench/unified-intake`, with the left nav hidden for a focused product feel.

### Single Biggest Strength

**Progressive slot-filling and handoff logic.** The add-car flow correctly asks for year+model first, then zip, then delivery/driver. It acknowledges partial info (“好的，宝马X5。”) and asks 1–2 things at a time instead of a long checklist. Handoff thresholds are defined per category (MATURE_INTAKE_SKELETON, LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT). This is exactly what a Shopify-style intake should do.

### Single Biggest Weakness

**No clear “talk to an agent” path.** Users who want to speak to a human have no dedicated quick action. “上传材料 / 联系客服” is the closest, but it routes to missing-document, not “I want to talk to someone.” For a small business, this is a trust gap: customers who are confused or urgent may bounce.

### What It Feels Like Today

**D) A partial prototype** — with strong intake bones.

- It has the right structure: quick actions, free text, multi-turn, case summary, handoff.
- But it feels more like a lab tool than a polished product: Case Summary shows raw field names (year, make_model, zip); “需要示例？” is tucked away; no agent path; entry is buried under `/workbench/unified-intake`.
- It is not yet a “strong intake tool” because discoverability, trust, and agent handoff clarity are incomplete.
- It is not a “basic chatbot” because it does structured slot-filling and handoff, not open-ended chat.
- It is not a full “support case builder” because the broker view is paste-based, not a live queue with real-time case creation from the customer flow.

### Maturity Scores (1–10)

| Dimension | Score | Notes |
|-----------|-------|------|
| **UX clarity** | 6 | Welcome and buttons are clear; Case Summary and field labels are technical. |
| **Conversation quality** | 7 | Good templates, acknowledgment, 1–2 asks per turn; some edge cases weak. |
| **Routing / intake logic** | 7 | Intent detection works for common cases; free-text fallback can misroute. |
| **Structured case capture** | 7 | collected/still_needed per flow; add-car strongest; renewal/claim thinner. |
| **Agent usability** | 6 | broker_next_step and client_reply_draft are useful; case card could be denser. |
| **Startup-readiness** | 6 | Right scope; needs polish for “feels professional” and “talk to agent.” |

---

## PART 2 — IDEAL PRODUCT STANDARD

### First Screen / First Impression

- One clear headline: “How can we help?” or equivalent.
- 5–7 quick actions covering: quote, policy change, claim, payment, documents, **talk to agent**.
- Free-text input visible and inviting.
- No jargon. No “Unified Intake” or “Workbench” in customer view.
- Light, calm, professional — not dark/corporate unless brand requires it.

### Quick Actions / Routing

- Buttons map to real intents; click = start flow with a starter message.
- Labels are customer language (“Get a quote,” “Payment help”), not internal terms.
- “Talk to agent” is always visible.
- Routing is visible: user sees their choice reflected (e.g., “We’re helping with your quote”).

### Free-Text Intent Detection

- “I just bought a 2026 Toyota Corolla, how much is insurance for half a year?” → quote intent, year=2026, model=Corolla, make=Toyota.
- “Payment failed” / “cancelled” → payment/cancellation.
- “I need to add a car” vs “I need to remove a car” → distinct intents.
- Ambiguous input gets a clarifying question, not a random category.

### Conversation Flow

- One main question per turn (or 2 closely related).
- Acknowledge what the user said before asking.
- No “please provide more context” when intent is obvious.
- Calm, office-natural tone — not formal, not robotic.
- User feels “I’m being helped,” not “I’m filling a form.”

### Asking for Missing Info

- System knows collected vs still needed.
- Asks only for missing fields.
- Order: most impactful first (e.g., year+model before zip for quote).
- Stops when enough; does not over-ask.

### Case Summary Generation

- Real-time: collected vs still needed, human-readable labels.
- Broker sees: intent, key facts, next step, draft reply.
- Not raw field names; not technical jargon.
- Enough for a human to continue without re-asking everything.

### Agent Handoff

- Clear “Office will follow up” message.
- Case appears in broker queue with full context.
- broker_next_step is one concrete sentence.
- client_reply_draft is editable, professional, ready to send.

### User Trust / Reassurance

- Urgent cases get “same-day” or “today” language.
- “Already sent” gets “We’ll check on our side.”
- No false promises (e.g., no premium numbers without broker).
- “Talk to agent” available when user is stuck.

### Error Handling

- Network/API errors: clear, non-technical message.
- Unclear input: light clarification, not “error.”
- Fallback path when backend is down (e.g., offline mode).

### Speed / Startup Practicality

- Fast to complete: 2–3 turns for most flows.
- No heavy CRM, no multi-tenant auth for v1.
- Config-driven where possible; code changes for new intents.

---

## PART 3 — CURRENT SYSTEM AUDIT

### 1. ENTRY EXPERIENCE

**Working:**
- “今天有什么可以帮您？” is warm and clear.
- 5 quick buttons cover main intents.
- Free text is prominent; user can type without clicking first.
- Left nav hidden on Unified Intake; page feels focused.
- “您可以选择下面的主题，或直接在下方输入您的问题” explains both paths.

**Weak:**
- URL `/workbench/unified-intake` is internal; “Unified Intake” in header is broker jargon.
- No “talk to agent” button.
- “需要示例？” is secondary; new users may not find it.
- Dark theme may feel corporate for some customers.

**Why it matters:** First impression sets trust. Missing “talk to agent” can make users feel trapped.

**What good companies do:** Shopify/Stripe put “Contact support” or “Talk to us” in the first screen.

**Recommendation:** Add a 6th button “联系客服 / Talk to agent” that routes to a handoff with note “Customer requested human contact.” Surface “需要示例？” more prominently (e.g., “Not sure what to say? See examples”).

---

### 2. ROUTING / QUICK ACTIONS

**Working:**
- 5 buttons map to add_car, remove_car, claim_intake, cancellation_warning, missing_document.
- Click with empty input sends starter message and begins flow.
- soft_route overrides when text conflicts; reroute message shown.
- SOFT_ROUTE_STARTER_REPLIES give intent-specific first replies when triage returns unclear.

**Weak:**
- “上传材料 / 联系客服” conflates documents and “contact us”; not a true agent path.
- No quote vs policy-change vs claim distinction in labels (partially covered by 报价/变更/事故).
- “当前主题” tag with × to clear is good but could be more visible.

**Why it matters:** Quick actions reduce friction; wrong or missing options increase bounce.

**What good companies do:** Amazon uses clear issue trees; Shopify uses “Get help” with sub-options.

**Recommendation:** Split “上传材料” and “联系客服” into two buttons, or add “联系客服” as a 6th. Ensure “联系客服” always hands off with “Customer requested human contact.”

---

### 3. FREE TEXT UNDERSTANDING

**Working:**
- “客户要加一台2021 Tesla Model Y，下周提车” → add_car, year, model, delivery.
- “我刚刚买了2026年的宝马X5，我想问一下保费多少钱” → add_car.
- “刚出事故了” → claim_intake.
- “付款有问题” → cancellation_warning.
- Markers cover common Chinese and English phrases.

**Weak:**
- “I just bought a 2026 Toyota Corolla, how much is insurance for half a year?” — Should work (add_vehicle + vehicle_context + year). “Half a year” is not explicitly captured (6-month policy vs delivery).
- Unusual phrasings (“I need to insure my new car”) may hit customer_question or unclear.
- Rule-based only when LLM off; no semantic understanding of near-miss intents.
- Mixed intents (e.g., payment + document) can be tricky.

**Why it matters:** Users type naturally; misrouting causes confusion and rework.

**What good companies do:** Stripe/Shopify use intent classification that tolerates paraphrasing.

**Recommendation:** Add “half a year,” “6 months,” “six months” to delivery/coverage markers if relevant. Consider LLM for ambiguous single-turn when available. Add test cases for “I need to insure my new car” and similar.

---

### 4. CONVERSATION UX

**Working:**
- One main ask per turn for add-car (e.g., “先把年份和地址邮编发我”).
- Acknowledgment: “好的，宝马X5。” / “好的，2024年的。”
- Templates avoid “please provide more context” for obvious intents.
- follow_up_type drives strategy: clarification_question → answer first; already_sent → warmer handoff.
- “（先发其中一个也行）” reduces friction for multi-item requests.

**Weak:**
- Some replies can feel long (e.g., document confusion + garaging explanation).
- Case Summary shows during collection but uses raw field names (year, make_model, zip).
- Tags like “Follow-up: clarification_question” and “Human confirmation recommended” are broker-facing; customers may not need them.

**Why it matters:** Conversation quality drives completion and trust.

**What good companies do:** Intercom/Drift keep replies short; Zendesk uses templated, scannable responses.

**Recommendation:** Humanize Case Summary labels for customers (e.g., “Year” instead of “year,” “Address/ZIP” instead of “zip”). Consider hiding technical tags from customer view.

---

### 5. SLOT FILLING / MISSING INFO COLLECTION

**Working:**
- Add-car: year, model, zip, delivery, driver; VIN optional. Threshold: (year+model or VIN) + (zip or delivery or driver).
- _extract_add_car_fields parses customer messages only.
- _get_next_ask_for_add_car returns the next 1–2 asks.
- Missing-doc: requested items, customer_says_sent; enough when item + sent status clear.
- Cancellation: notice, screenshot, already_paid; enough when one present.
- Renewal: policy_bill_sent, premium_concern, etc.
- Claim: accident_reported, photos, other_driver_info.

**Weak:**
- Add-car model list is hardcoded (Tesla, BMW, Honda, Toyota, etc.); unknown makes may miss.
- ZIP regex `9[0-9]{4}` is California-centric; other states need different patterns.
- Renewal/claim structured fields are thinner than add-car.
- No explicit “policy number” or “effective date” for some flows.

**Why it matters:** Incomplete slot-filling forces broker to re-ask.

**What good companies do:** Progressive asks with validation; optional fields clearly marked.

**Recommendation:** Expand model regex or use a looser pattern (e.g., “year + any word sequence”). Document ZIP assumption. Add policy_number to renewal when mentioned.

---

### 6. REAL-TIME CASE SUMMARY

**Working:**
- Case Summary card shows: issue_category, collected_fields, still_needed_fields.
- Updates per turn.
- Hidden when handoff_ready (replaced by handoff card).
- Broker Workbench shows full triage: broker_next_step, client_reply_draft, collected, still_needed, conversation_summary.

**Weak:**
- Field names are technical: “year,” “make_model,” “zip,” “delivery_date,” “primary_driver.”
- No humanized labels in Customer Entry (Broker Workbench has ADD_CAR_FIELD_LABELS etc., but Customer Entry does not use them).
- conversation_summary exists but is not always surfaced in the same place as collected/still_needed.

**Why it matters:** Broker needs to scan quickly; raw names slow comprehension.

**What good companies do:** Shopify/Stripe use plain-language summaries.

**Recommendation:** Use humanizeStructuredField or equivalent in Customer Entry Case Summary. Show “Year,” “Make/Model,” “ZIP,” etc.

---

### 7. AGENT FOLLOW-UP READINESS

**Working:**
- broker_next_step is one actionable sentence.
- client_reply_draft is editable, professional.
- client_prep tells broker what client should prepare.
- human_confirmation_required and human_confirmation_fields flag VIN, payment status, customer_says_sent.
- Case card has status, waiting_on, next_contact_by, notes.
- Append message flow: paste new customer message → re-triage → update case.

**Weak:**
- conversation_summary could be more prominent on the case card.
- “What would broker still need to ask?” is implicit in still_needed_fields; no explicit “Broker should confirm X.”
- No link from Customer Entry handoff to the specific case in Broker Workbench (case_id exists but UX could be clearer).
- Founder demo queue is loaded manually; not a live queue from real customer submissions.

**Why it matters:** Chen Kui needs to pick up and act without re-reading everything.

**What good companies do:** Zendesk/Intercom show “Suggested next step” and “What’s missing” clearly.

**Recommendation:** Add “Broker should confirm” for human_confirmation_fields. Ensure “查看工作台” opens the right case when case_id is present. Consider a “What’s still needed” one-liner on the case card.

---

### 8. TRUST / PROFESSIONALISM

**Working:**
- Tone is calm, office-natural.
- Urgent cases get “今天尽快处理” / “same-day.”
- “Already sent” gets “我这边帮你核对.”
- No premium promises; human_confirmation for VIN, payment.
- Copy avoids robotic phrases (“Thank you for reaching out,” etc.).

**Weak:**
- “Unified Intake” in header feels internal.
- “模拟演示” and “需要示例？” can suggest “this is a demo.”
- No explicit “We’re a real insurance office” or “Your message goes to Chen Kui’s team.”
- Dark theme may feel less warm than a light, consumer-style page.

**Why it matters:** Trust drives completion and retention.

**What good companies do:** Stripe/Shopify use clear branding and “We’re here to help.”

**Recommendation:** Replace “Unified Intake” with “客户服务” or broker name. Add one line: “您的消息会直接转给办公室，我们会尽快处理.” Consider a light theme option for customer-facing view.

---

### 9. MVP FOCUS

**Working:**
- Scope is right: single broker, no multi-tenant, no Stripe.
- Config-driven markers and templates.
- Lightweight state machine; no heavy workflow engine.
- 53+ scenarios in guardrail; run_inbox_triage_scenarios, guardrail_inbox_triage.sh.
- Simulation Assistant for demos.

**Weak:**
- Some overkill: many sprint reports, multiple similar docs.
- Demo flow (/demo) is separate from Customer Entry; two different UIs for related use cases.
- JobHunter, Mortgage, etc., still in app; scope creep risk.

**Why it matters:** Startup must ship fast; distractions slow progress.

**What good companies do:** Focus on one workflow; cut or hide the rest.

**Recommendation:** Keep Unified Intake as the main product surface. Archive or hide non-broker routes. Consolidate docs; keep one source of truth per area.

---

## PART 4 — GAP ANALYSIS VS AMAZON / SHOPIFY / STRIPE

### A. Amazon-Style Strengths Relevant Here

- Guided routing: issue trees, predictable paths.
- Structured issue selection: user picks category, then sub-options.
- Confidence-building: “We’re on it,” “Expected by X.”
- Escalation visible when needed.

**Gap:** We have quick actions but no explicit issue tree. User can type freely, which is good, but we lack Amazon’s “Choose your issue” drill-down for users who prefer structure.

**Verdict:** Our hybrid (buttons + free text) is reasonable for a small business. Full issue tree is overkill for MVP.

---

### B. Shopify-Style Strengths Relevant Here

- Lightweight support entry: simple form or chat.
- Quick actions: “Get help with order,” “Payment,” “Account.”
- Conversational but structured: collect what’s needed, then hand off.
- Small-business practicality: fast, minimal setup.

**Gap:** We are close. Missing: “Contact support” as a first-class option; slightly more polished labels and Case Summary.

**Verdict:** We are aligned with Shopify’s philosophy. A few UX tweaks would close the gap.

---

### C. Stripe-Style Strengths Relevant Here

- Clarity: minimal copy, clear next steps.
- Self-service first: help before human.
- Clean support logic: category → collect → resolve or escalate.
- High trust: professional, no confusion.

**Gap:** Our UI has more moving parts (tabs, Case Summary, tags). Stripe is more minimal. Our copy is good but could be tighter.

**Verdict:** We are more feature-rich than Stripe’s support entry; that’s fine for insurance. Focus on clarity and trust.

---

### Where We Are Strong

- Progressive slot-filling (add-car).
- Acknowledgment before ask.
- Handoff thresholds per category.
- broker_next_step and client_reply_draft quality.
- Reassure-first for “already sent.”
- follow_up_type and collection_stage logic.
- Human confirmation boundaries.

### Where We Are Weaker

- No “talk to agent” path.
- Case Summary field labels too technical.
- Entry discoverability (/workbench/unified-intake).
- Some edge cases in free-text intent.

### Gaps That Matter Most for MVP

1. **Talk to agent** — High impact, low effort.
2. **Humanized Case Summary** — Medium impact, low effort.
3. **Entry URL/branding** — Medium impact, medium effort (e.g., /support or /help).

### Big-Company Features to Skip for Now

- Full issue tree (Amazon).
- Multi-channel routing (email, SMS, chat).
- CRM integration.
- Automated outbound.
- Complex SLA dashboards.

---

### Gap Table

| Area | Current Level | Benchmark | Gap Severity | Recommended Action |
|------|---------------|-----------|--------------|---------------------|
| First screen | Good | Strong | Low | Add “联系客服”; surface examples |
| Quick actions | Good | Strong | Medium | Add talk-to-agent; split materials/contact |
| Free-text intent | Good | Strong | Medium | Add edge-case tests; consider LLM for ambiguous |
| Conversation flow | Strong | Strong | Low | Humanize Case Summary labels |
| Slot filling | Strong | Strong | Low | Expand model regex; document ZIP |
| Case summary | Fair | Strong | Medium | Humanize labels in Customer Entry |
| Agent handoff | Good | Strong | Low | Add “Broker should confirm” for human_confirmation |
| Trust | Good | Strong | Medium | Replace “Unified Intake”; add “real office” line |
| MVP focus | Good | Strong | Low | Consolidate; hide non-broker routes |

---

## PART 5 — WHAT WE ARE ALREADY DOING BETTER

1. **Progressive, not monolithic** — We ask 1–2 things per turn and acknowledge first. Many chatbots dump a long form or “please provide more context.”

2. **Reassure-first for “already sent”** — When the customer says they sent documents, we lead with “我这边帮你核对” instead of repeating “please send.” That reduces frustration.

3. **Human confirmation boundaries** — We flag VIN, payment status, customer_says_sent as “broker must verify.” We avoid promising premiums or carrier receipt. That’s more careful than many AI support tools.

4. **Bilingual from the start** — Markers and templates support Chinese and English. For Chen Kui’s clients, that’s a real advantage.

5. **Lightweight state, not heavy workflow** — follow_up_type and collection_stage improve replies without a big workflow engine. Startup-practical.

6. **Config-driven** — Markers and templates in config; new intents can be added without large code changes.

---

## PART 6 — TOP RISKS / FAILURE MODES

### Risk 1: User Confusion — “I Just Want to Talk to Someone”

**User experience:** Clicks around, no clear “talk to agent” option, leaves.

**Broker experience:** Loses leads or urgent cases.

**Seriousness:** High for trust; medium for volume if most users have clear intents.

**Fix:** Add “联系客服 / Talk to agent” button; route to handoff with “Customer requested human contact.”

---

### Risk 2: Weak Intent Understanding for Edge Cases

**User experience:** Types “I need to insure my new car” → gets “unclear” or wrong category.

**Broker experience:** Case arrives with wrong category; rework.

**Seriousness:** Medium; common phrasings work, but edge cases exist.

**Fix:** Add markers for “insure,” “new car,” “need coverage”; add test cases; consider LLM for ambiguous single-turn.

---

### Risk 3: Chatbot Feeling Instead of Intake Tool

**User experience:** Long back-and-forth; feels like chat, not “I’m getting help.”

**Broker experience:** Unclear when to take over; case summary not actionable.

**Seriousness:** Medium; current design limits turns, but UX could reinforce “intake” more.

**Fix:** Emphasize “Case Summary” and “Ready for handoff” in UI. Use “办公室会尽快处理” consistently. Consider a progress indicator (e.g., “Step 2 of 3”).

---

### Risk 4: Poor Case Handoff

**User experience:** Submits, sees “办公室会尽快处理,” but unclear what happens next.

**Broker experience:** Case in queue but key info missing; has to re-ask.

**Seriousness:** Medium; structured fields help, but handoff clarity could improve.

**Fix:** Ensure “查看工作台” opens the right case. Add “Broker should confirm” for human_confirmation_fields. Make conversation_summary prominent on case card.

---

### Risk 5: Asking Wrong Follow-Up Questions

**User experience:** System asks for something already provided or irrelevant.

**Broker experience:** Client frustrated; case quality drops.

**Seriousness:** Medium; add-car logic is solid; other flows less tested.

**Fix:** Audit renewal, claim, missing-doc for duplicate asks. Ensure _extract_* functions parse all customer turns, not just the last.

---

### Risk 6: Missing Critical Quote Fields

**User experience:** Provides year, model, zip; system hands off; broker still needs driver or lienholder.

**Broker experience:** Extra round-trip.

**Seriousness:** Low–medium; add-car threshold is defined; optional fields are documented.

**Fix:** Document “Broker may still ask: primary driver, lienholder” in broker_next_step when those are missing. Consider one more ask when only driver is missing and it’s a new car.

---

### Risk 7: Over-Reliance on Vague AI Replies

**User experience:** Gets generic “please provide more context” when intent is obvious.

**Broker experience:** Client gives up; case never completes.

**Seriousness:** Low; templates and SOFT_ROUTE_STARTER_REPLIES reduce this.

**Fix:** Audit unclear/informational paths. Ensure button-starter fallback always fires when soft_route is set and triage returns generic.

---

## PART 7 — TOP 10 IMPROVEMENTS IN PRIORITY ORDER

| # | Title | Why It Matters | User Impact | Broker Impact | Difficulty | When |
|---|-------|----------------|-------------|---------------|-------------|------|
| 1 | Add “联系客服 / Talk to agent” button | Trust; users who want human contact | High | Medium | Low | Now |
| 2 | Humanize Case Summary field labels | Readability; professionalism | Medium | High | Low | Now |
| 3 | Replace “Unified Intake” with customer-facing label | Trust; clarity | Medium | Low | Low | Now |
| 4 | Add “您的消息会直接转给办公室” reassurance line | Trust | Medium | Low | Low | Now |
| 5 | Surface “需要示例？” more prominently | Discoverability | Medium | Low | Low | Now |
| 6 | Add “Broker should confirm” for human_confirmation_fields | Agent usability | Low | High | Medium | Next |
| 7 | Ensure “查看工作台” opens specific case when case_id present | Handoff clarity | Medium | High | Low | Next |
| 8 | Add test cases for “I need to insure my new car” and similar | Intent robustness | Medium | Medium | Low | Next |
| 9 | Expand add-car model regex for more makes | Slot filling | Medium | Medium | Low | Later |
| 10 | Consider /support or /help as customer entry URL | Discoverability | Medium | Low | Medium | Later |

---

## PART 8 — MVP RECOMMENDED TARGET STATE

### First Screen

- Headline: “今天有什么可以帮您？” (keep).
- Subhead: “选择下面的主题，或直接输入您的问题。您的消息会直接转给办公室，我们会尽快处理.”
- 6 buttons: 报价, 变更, 事故, 付款, 材料, **联系客服**.
- Large text area; placeholder: “请在此输入或粘贴您的问题、通知内容...”
- “需要示例？” as a clear link or secondary button.

### Quick Action Buttons

- Each maps to intent; click = start flow.
- “联系客服” = immediate handoff with “Customer requested human contact.”
- Selected button highlighted; user can clear and type something else.

### Free-Text Fallback

- User can type without clicking.
- System infers intent; may reroute if they clicked one thing but typed another.
- Unclear → light clarification, not generic error.

### Conversation Pattern

- Turn 1: Acknowledge + ask 1–2 next things.
- Turn 2+: Acknowledge new info + ask next missing OR hand off.
- Max 2–3 customer turns for most flows.
- Handoff when threshold met or user says “先这样” / “你先看.”

### Missing Info Collection

- System knows collected vs still needed.
- Asks only for missing; one main question per turn.
- Case Summary shows “已收集: Year, Make/Model, ZIP” (humanized).

### Live Case Summary

- Visible during collection.
- Labels: “Year,” “Make/Model,” “ZIP,” “Delivery date,” “Primary driver.”
- Hidden when handoff_ready.

### Submit / Handoff Pattern

- “办公室会尽快处理，有结果会联系您.”
- “已整理成 case，办公室会尽快跟进.”
- “查看工作台” opens Broker Workbench, ideally with this case selected.

### Agent Review View

- Case card: source_text, conversation_summary, broker_next_step, client_reply_draft.
- Collected (humanized) and still needed.
- human_confirmation_fields → “Broker should confirm: VIN, payment status.”
- Status, waiting_on, next_contact_by, notes.
- Append message for new customer follow-up.

---

## PART 9 — ACCEPTANCE CHECKLIST

Use this for the next version review.

### Entry & Routing

- [ ] User can type without selecting a category first.
- [ ] User can click a quick action to start a flow.
- [ ] “联系客服” or “Talk to agent” is visible and routes to handoff.
- [ ] System auto-detects likely intent from first message for common phrasings.
- [ ] Reroute message appears when user’s text conflicts with selected button.
- [ ] “需要示例？” or equivalent is easy to find.

### Conversation

- [ ] System asks only one main question at a time (or 2 closely related).
- [ ] System acknowledges what user said before asking (e.g., “好的，宝马X5.”).
- [ ] No “please provide more context” when intent is obvious (add-car, payment, missing-doc).
- [ ] Handoff occurs when threshold met (add-car: year+model + zip/delivery/driver).
- [ ] Max 2–3 customer turns for most flows before handoff.

### Case Summary

- [ ] Case summary shows collected vs missing fields during collection.
- [ ] Field labels are human-readable (Year, Make/Model, ZIP), not raw (year, make_model, zip).
- [ ] Case summary is hidden when handoff_ready.
- [ ] Handoff card shows “办公室会尽快处理” and “查看工作台.”

### Quote Flow

- [ ] Quote flow captures ZIP + vehicle (year + model or VIN) + at least one of delivery/driver.
- [ ] Add-car asks for year+model first when missing, then zip, then delivery/driver.
- [ ] “I just bought a 2026 Toyota Corolla, how much is insurance” routes to add-car and extracts year, model.

### Agent Handoff

- [ ] Agent can read summary and continue without re-asking everything for typical cases.
- [ ] broker_next_step is one concrete sentence.
- [ ] client_reply_draft is professional and editable.
- [ ] human_confirmation_fields are flagged when present (e.g., VIN, customer_says_sent).
- [ ] “查看工作台” opens the case when case_id is available.

### Trust & Polish

- [ ] No “Unified Intake” or internal jargon in customer-facing view.
- [ ] One line reassures that messages go to the office (e.g., “您的消息会直接转给办公室”).
- [ ] Urgent cases (cancellation, payment) get “今天” or “same-day” language.
- [ ] “Already sent” gets “我这边帮你核对” or equivalent.

---

## PART 10 — FINAL VERDICT

### Brutally Honest Verdict

You have built a **solid intake skeleton** with the right ideas: quick actions, free text, progressive slot-filling, handoff thresholds, and a lightweight state layer. The add-car flow, acknowledgment pattern, and reassure-first logic are strong. The gap is not architecture—it’s **polish and one critical missing path**.

The system feels like a **partial prototype** because: (1) there is no “talk to agent” option, which hurts trust; (2) the Case Summary uses technical field names; (3) the entry is under `/workbench/unified-intake` with “Unified Intake” in the header. Fix those, and it will feel much closer to a real product.

### Demoable Today?

**Yes.** For a founder demo to Chen Kui or a partner, you can show: Customer Entry → click 报价 → type “2024 BMW X5, 下周提车” → see progressive ask → handoff → Broker Workbench. The flow works. Use Simulation Assistant for SIM1–SIM3 if needed. Run `guardrail_inbox_triage.sh` before demo.

### Useful Today?

**Partly.** For a broker who pastes messages into Broker Workbench, it is useful: triage, draft, next step. For a customer who lands on Customer Entry, it works if their intent is clear. It is less useful for “I just want to talk to someone” or for users who need more reassurance that this is a real office.

### Feels Like a Real Intake Tool Yet?

**Almost.** The logic is there. The UX needs a few targeted changes: “联系客服,” humanized labels, and clearer branding. With those, it will cross the line.

### 3 Biggest Next Moves for “Professional” Feel

1. **Add “联系客服 / Talk to agent”** — One button, immediate handoff. Signals “we’re here if you need us.”
2. **Humanize Case Summary labels** — Use “Year,” “Make/Model,” “ZIP” instead of “year,” “make_model,” “zip.” Small change, big clarity gain.
3. **Replace “Unified Intake” and add reassurance** — Customer-facing header: “客户服务” or broker name. One line: “您的消息会直接转给办公室，我们会尽快处理.”

These three moves are low-effort, high-impact. Do them before the next demo.

---

*End of audit*

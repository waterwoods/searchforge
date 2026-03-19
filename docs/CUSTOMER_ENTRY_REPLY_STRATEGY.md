# Customer Entry Reply Strategy

**Purpose:** Define the intended first-response strategy for major customer-entry request types. The customer-facing entry should react differently depending on likely customer intent, not fall back to generic "please provide more context" for all incomplete inputs.

**Scope:** Chen Kui Insurance Unified Intake — Customer Entry tab only.

---

## 1. Response Strategy Matrix

| Category | What to recognize | Tone | Reply action | Info to request next | Urgency feel | Chen Kui office mention |
|----------|-------------------|------|--------------|----------------------|--------------|-------------------------|
| **Add car / new car quote** | New vehicle, quote request, "how much for X car" | Calm, operational | Ask for key fields to estimate | Year, model, VIN, zip/address, driver if relevant, delivery date | Routine | Yes — "我先帮你算" |
| **Remove car / policy change** | Sold vehicle, want to drop from policy | Calm, operational | Confirm removal path | Sale date, vehicle details, transfer status | Routine | Yes — "可以处理" |
| **Premium too high / renewal review** | Premium increase concern, want to lower | Calm, reassuring | Explain review path | Current policy, renewal notice, recent changes | Routine | Yes — "我先帮你看" |
| **Payment failed / cancellation risk / lapse risk** | Payment declined, cancel notice, overdue | Urgent, clear | State urgency, ask for notice/payment | Notice, payment screenshot, callback number | Urgent | Yes — "今天尽快处理" |
| **English notice confusion** | "What does this mean?" re: English notice | Reassuring, explanatory | Explain likely meaning, ask for notice | Full notice or clearer photo | Medium | Yes — "我先帮你看" |
| **Missing document / declaration page / DL / garaging proof** | Carrier/UW requested item; client confused or says sent | Operational, clear | Name the missing item, ask for resend | Exact item, whether already sent | Medium | Yes — "我这边帮你核对" |
| **DMV / SR-22 help** | DMV letter, suspension, what to bring | Operational, explanatory | Explain workflow, what to prepare | DMV notice, suspension letter, SR-22 proof if any | Medium | Yes — "再告诉你要带什么" |
| **Claim intake / accident first response** | Accident just happened, what to collect | Calm, reassuring | Brief empathy, then first-step guidance: safety, photos, other driver info | Accident details, photos, other driver info, policy number | Medium | Yes — "刚出事故一定很着急，先别慌" + first-step guidance |
| **Generic vague help request** | Unclear, fragmented, no obvious intent | Light, clarifying | Light clarification fallback | Full notice or more context | Low | Yes — "我帮你确认下一步" |

---

## 2. Per-Category Strategy Detail

### Add car / new car quote

- **Recognize:** "加一台", "新车", "提车", "拿车", "先出报价", "报价", "多少钱", "买了", "保费多少钱", "add car", "new car", "how much is insurance", "quote for [vehicle]", "刚买车", "保险大概", "picking up"
- **Tone:** Calm, operational. Not "send more context."
- **Reply:** Ask for year, model, VIN (if available), delivery date, primary driver, zip/address.
- **Ask order (multi-turn):** When vehicle (year+model or VIN) is missing → ask year and model first. When zip is missing → ask zip. When delivery and driver both missing → ask delivery and driver. Do not ask a giant checklist; ask the next most useful thing.
- **Do NOT:** Overload with too many fields at once. Keep short.
- **Conversational UX:** Acknowledge what the customer said (e.g. "好的，宝马X5。") before asking. Ask 1–2 next things, not a 6-item checklist. On follow-up turns, acknowledge their reply (e.g. "好的，2024年的。") before the next ask.
- **Next-step guidance:** Use "先把...发我，我就能帮你算报价" so user knows: send this → I can do that.
- **Example (Chinese):** When customer says "我买了台宝马X5，想问下保费多少钱" → "好的，宝马X5。先把年份和地址邮编发我，我就能帮你算报价。" When customer says "2024年的" → "好的，2024年的。先把地址邮编发我，我就能帮你算报价。"

### Remove car / policy change

- **Recognize:** "拿掉", "删掉", "删车", "卖掉", "卖车", "remove car", "drop vehicle", "sold"
- **Tone:** Calm, operational.
- **Reply:** Acknowledge ("好的，可以处理。") then ask for sale date, vehicle details, whether title/registration transferred.
- **Handoff:** "您说的卖车信息已整理好了，办公室会尽快处理，有结果会联系您。"
- **Example (Chinese):** "好的，可以处理。把卖车日期、车辆信息和是否已经过户发我，我先帮你确认。"

### Premium too high / renewal review

- **Recognize:** "保费太高", "怎么降", "premium too high", "rate too high"
- **Tone:** Reassuring, practical.
- **Reply:** Ask for current policy or renewal notice, latest bill.
- **"有办法吗" reassurance:** When customer asks "有办法吗" or "有办法", add "一般有办法的" to reassure that options exist before the ask.
- **Next-step guidance:** Add "（先发其中一个也行）" so user knows they can send one item first—reduces friction.
- **Example (Chinese):** "我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。"
- **Example (有办法):** "一般有办法的。我先帮你看这次保费为什么变高，再看看有没有能调整的地方。把现在保单和最新账单发我（先发其中一个也行），我先帮你核对。"

### Payment failed / cancellation risk / lapse risk

- **Recognize:** "payment failed", "cancelled", "non-payment", "AutoPay failed", "保单要停", "overdue"
- **Tone:** Urgent, clear. State that it needs same-day attention.
- **Reply:** Ask for notice, payment confirmation, callback number.
- **Next-step guidance:** Use "现在最关键的是" to make the next step feel prioritized and actionable.
- **Example (Chinese):** "这看起来是付款出了问题。现在最关键的是把最新通知或付款截图发我，我先帮你确认；如果还没付，今天尽快处理，避免停保。"

### English notice confusion

- **Recognize:** "什么意思", "what does this mean", "what does", "我需要做什么", "怎么办", "看不懂", "英文 notice"
- **Tone:** Reassuring. Explain that English notices can be confusing; ask for full notice.
- **Reply:** Brief reassurance, then ask for full notice or clearer photo.
- **Example (Chinese):** "英文通知有些术语看不懂很正常。把完整通知或更清楚的照片发我，我先帮你看一下，再告诉你重点和下一步怎么处理。"

### Missing document

- **Recognize:** "declaration page missing", "need driver's license", "garaging proof", "dec page", "缺", "发过了"
- **Tone:** Operational. Name the missing item if detectable.
- **Reply:** Ask for the exact item; if client says already sent, ask them to confirm and we will check.
- **Progress phrase:** Add "核对好后就能往下推" so the user feels the next step is concrete.
- **Multi-item guidance:** When 2+ items, add "（先发其中一个也行）" so user knows they can send one first.
- **Example (Chinese):** "现在文件里还缺 declaration page（保单首页）。请再发我一次；如果你之前已经发过，也跟我说一声，我这边帮你核对，核对好后就能往下推。"
- **Example (multi-item):** "现在文件里还缺 X 和 Y。请再发我一次（先发其中一个也行）；..."

### DMV / SR-22 help

- **Recognize:** "DMV", "SR-22", "suspension", "clearance", "带什么", "what to bring"
- **Tone:** Operational, explanatory.
- **Reply:** Explain likely workflow; ask for DMV notice, suspension letter; tell client what to prepare.
- **Example (Chinese):** "把 DMV 信件发我，我先帮你确认是不是要 SR-22 filing proof（SR-22备案证明），再告诉你要带什么。"

### Claim intake / accident first response

- **Recognize:** "刚出事故", "car accident just happened", "what should i collect", "对方跑了"
- **Tone:** Calm, reassuring. Brief empathy, then first-step guidance.
- **Reply:** Brief empathy, then first-step guidance: safety, photos, other driver info.
- **Next-step guidance:** Use "先把...发我" so user knows what to send first.
- **Hit-and-run variant:** When customer says "对方跑了" / "hit and run", tailor reply to emphasize license plate, photos, and what happened (since other-driver info is unavailable).
- **Example (Chinese):** "刚出事故一定很着急，先别慌。先确保人没事，再拍现场照片、记下对方车牌和保险信息。先把事故经过、对方信息和照片发我，我帮你确认下一步怎么报案。"
- **Example (hit-and-run):** "刚出事故一定很着急，先别慌。对方跑了的话，最关键的是车牌号、现场照片和事故经过。先把这些发我，我帮你确认下一步怎么报案和报保险。"

### Generic vague help request

- **Recognize:** Ambiguous, fragmented, no clear category.
- **Tone:** Light, clarifying. Only then use a lighter fallback.
- **Reply:** Ask for full notice or more context.
- **Example (Chinese):** "这段内容还不够完整。把完整通知或前后内容再发我一下，我帮你确认下一步。"

---

## 3. Anti-Patterns to Avoid

| Anti-pattern | Instead |
|--------------|---------|
| "Please provide more context" for obvious add-car/quote | Ask for year, model, VIN, delivery date |
| "Please provide more context" for payment failed | State urgency, ask for notice and payment proof |
| "Please provide more context" for notice confusion | Explain likely meaning, ask for full notice |
| "Please provide more context" for missing document | Name the missing item, ask for resend |
| Generic AI empathy ("Thank you for reaching out") | Short, conclusion-first, next-step-second |
| Overloading with too many fields | 1–3 key items per reply |
| Formal letter tone | Office-natural, short |

---

## 4. Second-Turn Follow-Up Rules

**Purpose:** After the customer answers the first follow-up, the system should either ask the next most useful missing field(s) or hand off cleanly. Do not stop too early; do not over-ask.

### 4.1 Per-Category Second-Turn Decision Rules

| Category | First-turn typically collected | Second-turn: ask one more when | Second-turn: hand off when | What not to over-ask |
|----------|-------------------------------|--------------------------------|----------------------------|----------------------|
| **新车 / 加车报价** | Year, model, VIN hint | Missing zip, delivery, or main driver | Year+model+zip present; or year+model+delivery | Do not ask for VIN if model+year clear; do not ask for lienholder in first 2 turns |
| **删车 / 保单变更** | Vehicle, sale intent | Sale date or transfer status missing | Vehicle + sale date; or vehicle + "already transferred" | Do not ask for replacement vehicle unless client mentions it |
| **保费太高 / renewal** | Policy/bill mention | No policy or bill yet | Policy or bill mentioned/sent | Do not ask for full claims history |
| **付款失败 / cancellation risk** | Notice or payment proof | No notice/screenshot/confirmation | Notice, screenshot, or "I sent it" / "I paid" | Do not ask for callback number if they said they sent proof |
| **英文 notice confusion** | Full notice or clearer photo | No notice text yet | Full notice or "I sent it" / summary of notice | Do not ask for translation of every term |
| **缺材料 / dec page / DL / garaging** | Which item missing, whether sent | Unclear which item still missing | Item identified + sent status clear | Do not chase multiple items in one turn |

### 4.2 Handoff-Readiness Thresholds

- **Add-car:** Enough when (year + model or VIN) + zip. Delivery and main driver are nice-to-have; one more ask only if both missing and case would materially improve.
- **Remove-car:** Enough when vehicle + sale date, or vehicle + transfer status.
- **Premium review:** Enough when policy or bill mentioned.
- **Payment risk:** Enough when notice, screenshot, or "I sent it" / "I paid" mentioned.
- **Notice confusion:** Enough when full notice or clear summary provided.
- **Missing document:** Enough when which item(s) and sent status are clear.

### 4.3 Third-Turn Continuation

- Allow one more turn only when one critical field would materially improve the case.
- If the case is already clean enough, hand off.
- If the customer clearly cannot provide more (e.g. "我不知道", "你先看"), hand off cleanly.
- Max 2–3 customer turns before handoff; do not become a long-form chatbot.

### 4.4 Handoff Acknowledgement (Multi-Turn UX)

When the customer says they sent something (发, sent, 发了, 发你, 截图, etc.) in turn 2, use the warmer handoff: "好的，收到了。办公室会尽快处理，有结果会联系您。" instead of the generic "您说的情况已收到". This makes renewal, payment, missing-document, and claim handoffs feel more conversational.

---

## 5. Mature Intake Skeleton

All high-value scenarios follow the same flow shape: **detect → ask → enough? → hand off**. See `docs/MATURE_INTAKE_SKELETON.md` for the shared design.

---

## 6. Implementation Notes

- **Triage module:** `services/fiqa_api/inbox_triage/triage.py`
- **Second-turn logic:** `_get_next_ask_draft()`, `_extract_add_car_fields()`, `_add_car_enough_for_handoff()` in triage.py
- **Intent detection:** `_is_add_vehicle_request`, `_is_remove_vehicle_request`, `_is_premium_review_request`, `_is_sr22_help_request`, etc.
- **Client draft builder:** `_build_client_reply_draft()` — already has category- and intent-specific logic.
- **Classification:** Rule-based guardrails ensure consistent category/urgency; client draft comes from rule-based templates for demo-safe behavior.
- **English add-car:** Add markers for "new car", "bought", "how much", "insurance" + vehicle make/model to catch "I bought a new BMW X5, how much is insurance?"

---

*End of strategy doc*

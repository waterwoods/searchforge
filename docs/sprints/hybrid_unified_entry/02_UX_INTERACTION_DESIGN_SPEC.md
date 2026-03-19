# Hybrid Unified Entry — UX / Interaction Design Spec

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15

---

## 1. First Screen Experience

### 1.1 Layout (Above the fold)

```
┌─────────────────────────────────────────────────────────────┐
│  [Welcome message — friendly, one line]                      │
│  How can I help today?                                       │
├─────────────────────────────────────────────────────────────┤
│  [5 quick-start buttons — horizontal wrap, equal weight]      │
│  [Get a Quote] [Policy Change] [File a Claim] [Payment] [Other] │
├─────────────────────────────────────────────────────────────┤
│  [Free-text input — always visible, prominent]               │
│  Or type your question here...                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│  [Submit / Send]                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Welcome Message

**Primary**: "How can I help today?" (or 今天有什么可以帮您？)  
**Secondary** (optional, smaller): "You can choose a topic above or type your question below."

- Tone: Friendly, not formal
- Length: One short line
- No long paragraphs

---

## 2. The 5-Button Model

| Button | Intent / Soft Route | Example user message if they type instead |
|--------|---------------------|-------------------------------------------|
| **Get a Quote** | add_car, new_vehicle_quote | "我想加一台2021 Tesla Model Y" |
| **Policy Change** | remove_car, policy_update | "我卖掉旧车了，想从保单拿掉" |
| **File a Claim** | claim_intake | "刚出事故了，要收集什么？" |
| **Payment / Billing** | cancellation_warning, payment_lapse | "Notice说payment failed，怎么办？" |
| **Upload Documents / Talk to Agent** | missing_document, unclear, human_handoff | "UW要dec page，我发过了" / "我想跟人聊" |

**Rationale**: Covers the 5 core flows from MATURE_INTAKE_SKELETON and LIGHTWEIGHT_STATE_MACHINE. "Upload Documents / Talk to Agent" catches missing-doc and unclear/human-preference cases.

**Display labels** (customer-facing, short):
- 获取报价
- 保单变更
- 报事故
- 付款 / 账单
- 上传材料 / 联系客服

---

## 3. How Buttons and Free Text Coexist

| State | Behavior |
|-------|----------|
| **No selection** | User can type freely; triage infers intent from text only |
| **Button selected** | Soft context stored; triage can use it as hint, but text overrides |
| **User types after button** | If text clearly indicates different intent → reroute and acknowledge |
| **User types without button** | Same as today: triage from text only |

**Visual**: Selected button shows active state (filled/highlighted). User can deselect by clicking again or by typing something that triggers reroute.

---

## 4. Selected Button State

- **Default**: All buttons neutral (outline or ghost style)
- **Selected**: One button highlighted (e.g., primary color, filled)
- **Deselect**: Click same button again, or system reroutes and clears selection
- **No lock**: Selection is soft context only; never blocks free-text intent

---

## 5. Rerouting — Visual and Behavioral

### 5.1 When Rerouting Occurs

- User clicked "Get a Quote" but types "我保单要cancel了怎么办" (payment/cancellation)
- User clicked "Payment" but types "我想加一台新车" (add-car)
- System detects intent from latest message differs from button context

### 5.2 Rerouting Acknowledgment

**System says** (in reply or inline):  
"It looks like this is actually a [X] issue — I'll help with that first."  
(看起来这是 [X] 相关的问题，我先帮您处理这个。)

- Shown as a brief inline note or as part of the first system reply
- Clears the previous button selection
- Proceeds with the new intent

### 5.3 When NOT to Reroute

- User message is ambiguous — stay with button context
- User message reinforces button context — no need to acknowledge
- User message is a follow-up (e.g., "我发了ZIP 90210") — stay in flow

---

## 6. Customer-Side Flow vs Office-Side Flow

| Area | Customer Entry | Broker Workbench |
|------|----------------|------------------|
| **Who** | Customer / prospect | Broker / office |
| **Purpose** | Intake, get help, submit question | Triage, follow-up, case management |
| **Tone** | Welcoming, reassuring | Operational, structured |
| **Visibility** | Default tab; first thing user sees | Secondary tab; "办公室" |
| **Entry** | Welcome + buttons + free text | Paste message, load queue, reopen cases |

**Separation**: Tabs already exist. This sprint strengthens the *customer* side with welcome + buttons. Broker Workbench remains office-focused.

---

## 7. What Happens After Enough Information Is Collected

1. System shows handoff message: "办公室会尽快处理，有结果会联系您。"
2. **Case creation suggestion** (new): "Would you like me to organize this into a case so our office can follow up?" (是否要整理成 case 让办公室跟进？)
3. User can: "查看工作台" (switch to Broker tab) or "提交新问题" (new conversation)

---

## 8. What Happens When User Is Unsure / Emotional / Vague

| Scenario | Behavior |
|----------|----------|
| **Unsure** | "我不太确定" → Reassure first: "没关系，您先说说大概情况，我们帮您看看。" |
| **Emotional** | "急死了" / "怎么办" → Reassure first, then route |
| **Vague** | "有个问题" → Ask one focused question; do not overload |
| **Wrong button** | User clicked wrong button → Free text overrides; reroute if clear |

**Principle**: Answer first, reassure first, then collect. Do not force structure when user is confused.

---

## 9. Simulation Assistant

- Remains available as "模拟演示" link/button
- Does not compete with main entry; secondary for demo/walkthrough
- Same placement as today (top-right of Customer Entry header)

---

*See also: Structured Intake Flow Spec, Routing/State Logic Spec*

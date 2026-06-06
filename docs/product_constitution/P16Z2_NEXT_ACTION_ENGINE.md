# P16-Z2 Phase 5 — Next Action Engine Research

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Question:** How do Zendesk, Intercom, and Salesforce determine what happens next?

---

## The three audiences

Every next-action system answers **three questions simultaneously:**

| Audience | Question | Example |
|----------|----------|---------|
| **Office (broker)** | What do I do now? | "Call Mercury re: UW; deadline Friday" |
| **Customer** | What do I send/wait for? | "请发驾照正反面照片" |
| **System** | What state is this case in? | waiting_on: customer, urgency: high |

**SearchForge fields today:** `broker_next_step`, `client_prep`, `waiting_on`, `urgency`, `lifecycle_status`

**P16-Y gap:** Office Actionability stuck at **25/25 ceiling** — technically scored but wording often generic.

---

## Zendesk — Triggers, Macros, and Copilot

### Architecture

```
Ticket event (create, update, comment, SLA breach)
        ↓
   Triggers (if/then rules)
        ↓
   Actions: assign, tag, email, webhook, macro apply
        +
   Copilot (2026): suggests next reply + next action to agent
        ↓
   Resolution verification → close or escalate
```

### Next action mechanics

| Mechanic | Purpose |
|----------|---------|
| **Triggers** | Event-driven automation ("if priority=urgent → notify manager") |
| **Macros** | Pre-built action bundles ("request screenshot" = tag + reply + status) |
| **Views** | Agent's "what to work now" queue |
| **SLA timers** | Time-based next action ("respond in 4h or escalate") |
| **Copilot suggestions** | AI drafts reply + recommends macro |

### What creates value

- **One-click macros** — agent doesn't compose from scratch
- **SLA-driven urgency** — system tells you what's late
- **Suggested reply** — reduces cognitive load

### Steal for Chen Kui

| Zendesk pattern | Our implementation |
|-----------------|-------------------|
| Macro | `client_prep` + copy button (exists) |
| View: "urgent today" | Filter queue by urgency + deadline (missing in product_only) |
| Copilot draft | `broker_next_step` + WeChat draft (exists; EN/ZH mix breaks trust) |
| Trigger on SLA | `deadline_mentioned` → urgency bump (partial) |

---

## Intercom — Fin resolution path + handoff

### Architecture

```
Customer message
        ↓
   Fin AI: can I resolve from KB + tools?
        ↓
   YES → answer + close conversation
   NO  → handoff to human with context summary
        ↓
   Operator: snooze, assign, tag, convert to ticket
        ↓
   Ticket typed attributes + ticket_state
```

### Next action mechanics

| Mechanic | Purpose |
|----------|---------|
| **Fin confidence threshold** | Low confidence → human handoff |
| **Handoff summary** | Human gets structured context, not raw chat |
| **Snooze** | "Follow up Tuesday" — case disappears until then |
| **Assignment** | Route to right team member |
| **Ticket state machine** | submitted → in_progress → resolved |

### What creates value

- **Clear handoff moment** — customer knows human is coming
- **Operator inbox** — only items needing human action
- **Snooze/follow-up** — nothing falls through cracks

### Steal for Chen Kui

| Intercom pattern | Our implementation |
|------------------|-------------------|
| Handoff summary | `conversation_summary` (exists) |
| Low confidence → human | Risk scores v4/v5 (computed, not shown) |
| Snooze | `next_contact_by` + follow-up editor (hidden on trial) |
| Customer "what's next" | Post-handoff confirmation (over-built, unclear CTA) |

---

## Salesforce — Einstein Next Best Action (NBA)

### Architecture

```
Case record opened
        ↓
   Strategy Builder runs:
     - Eligibility filters (case type, account tier)
     - Business rules
     - Einstein prediction scores
        ↓
   NBA component shows top recommendation(s)
        ↓
   Agent clicks action → Flow executes
        ↓
   Outcome logged → model improves
```

### Next action mechanics

| Mechanic | Purpose |
|----------|---------|
| **Strategy Builder** | Define when recommendations appear |
| **Eligibility filters** | Only show relevant actions per case type |
| **Prediction ranking** | AI ranks actions by likelihood of success |
| **One-click Flow** | Action button executes multi-step workflow |
| **Case Wrap-Up** | At close: summarize + suggest final fields |

### NBA use cases in service

- Suggest knowledge article
- Offer discount/retention (not our domain)
- Create task for specialist
- Escalate to Tier 2
- Request specific document

### What creates value

- **Context-aware** — different actions for cancel vs add-car vs claim
- **One operational sentence** — not a paragraph of options
- **Executable** — button does something, not just text

### Steal for Chen Kui

| Salesforce pattern | Our implementation |
|--------------------|-------------------|
| Category → action template | Rules in `case_draft_engine.py` (exists) |
| Confidence-gated auto vs suggest | v4/v5 risk scores (surface in UI) |
| Wrap-Up at handoff | `broker_next_step` generation (wording weak) |
| One-click Flow | Copy-to-WeChat button (exists — killer feature) |

---

## Unified next-action model (proposed)

```
┌─────────────────────────────────────────────────────────────┐
│                    NEXT ACTION ENGINE                          │
│                                                              │
│  Inputs:                                                     │
│    issue_category, urgency, collected_fields,               │
│    still_needed_fields, deadline_mentioned, waiting_on,       │
│    message_count, risk_scores                                 │
│                                                              │
│  Outputs:                                                    │
│    broker_next_step    → one operational sentence (ZH)       │
│    client_prep         → copy-paste WeChat message (ZH)      │
│    waiting_on          → office | customer | carrier         │
│    office_action_type  → call | email | quote | verify       │
│    customer_action_type → send_doc | confirm | wait          │
│    follow_up_by        → date if deadline-driven             │
└─────────────────────────────────────────────────────────────┘
```

**This engine already exists** in `case_draft_engine.py` + `triage.py`. The sprint finding: **don't rebuild — improve templates and surface outputs.**

---

## Next action by insurance category (target copy)

### Cancellation / UW

| Audience | Next action |
|----------|-------------|
| **Office** | 今天联系 {carrier} 确认取消原因；截止 {deadline} |
| **Customer** | 请发最新保单页或取消通知截图，我们帮您确认 |
| **System** | waiting_on: customer (if notice_image missing) else office |

### Add car quote

| Audience | Next action |
|----------|-------------|
| **Office** | 用 {year} {make} {model} 询价；缺 {still_needed} |
| **Customer** | 请补充：{still_needed 中文清单} |
| **System** | waiting_on: customer until fields complete |

### Payment / bill

| Audience | Next action |
|----------|-------------|
| **Office** | 确认 {amount} 是否在截止 {date} 前已付 |
| **Customer** | 请发付款截图或说明是否已付 |
| **System** | urgency: high if deadline ≤ 3 days |

### Claim (FNOL)

| Audience | Next action |
|----------|-------------|
| **Office** | 记录事故详情；联系 {carrier} 报案 |
| **Customer** | 请描述事故时间、地点、是否报警 |
| **System** | waiting_on: customer for details |

---

## What makes next action fail (our current failures)

| Failure | Evidence | Fix |
|---------|----------|-----|
| Generic fallback wording | P16-Y Office Actionability ceiling | Category-specific templates |
| English in Chinese office | P16-X F-005 | ui_copy + template locale |
| No post-copy state | Chen Kui simulation 38/100 | "等客户回复" after copy |
| Append not taught | Continuity 41/100 | Post-copy CTA |
| Risk not visible | v4/v5 hidden | Glance badge |
| Too many actions at once | P16-N confirmation screen | One primary CTA |

---

## Next action UI patterns (steal, don't build platform)

| Pattern | Source | Pilot implementation |
|---------|--------|---------------------|
| **Single hero action** | Linear | One broker CTA per case state |
| **Copy button** | Intercom saved replies | Already have — promote |
| **"Waiting on" pill** | Salesforce Case status | Show in glance header |
| **Deadline countdown** | Zendesk SLA | "还有3天" from deadline_mentioned |
| **Snooze/follow-up** | Intercom | Expose follow-up editor on trial |
| **Macro library** | Zendesk | 5 templates per category in ui_copy.json |

---

## 2-week next-action priorities

| Rank | Item | Cap | Effort |
|------|------|-----|--------|
| 1 | Chinese-only `broker_next_step` templates per category | 2, 3 | S |
| 2 | Post-copy: "已发送？标记等客户回复" | 5 | S |
| 3 | Deadline → visible countdown in glance | 2 | S |
| 4 | Surface v4 risk as "需核实" badge | 3 | S |
| 5 | `waiting_on` pill in broker glance | 5 | S |
| 6 | Urgent-today queue filter | 1, 5 | M |
| 7 | 5 macro templates in Chen Kui ui_copy | 1 | S |

**Do NOT build:** Strategy Builder, Flow automation, Einstein ML, trigger engine.

---

*End of P16-Z2 Phase 5 — Next Action Engine Research*

# Page / Flow / State / Handoff Backbone Spec

**Sprint:** Mature Skeleton / Commercial Intake Backbone Sprint  
**Purpose:** Core product structure reference — the 4 backbones that all future work should align to.

---

## 1. Page Backbone

### Structure (Stripe-inspired hierarchy)

| Layer | Name | Purpose | Placement |
|-------|------|---------|-----------|
| **1** | **Trust / Hero** | Explain what this page helps with; that the office will follow up; that info is handled and reviewed | Top of page, above the fold |
| **2** | **Primary Action Area** | Main business actions as intentional service entry points (获取报价, 保单变更, 报事故, 上传材料, 联系人工) | Immediately below hero; primary visual focus |
| **3** | **Free Input Area** | Secondary path for "not sure which to choose"; paste box + submit | Below primary actions; subordinate |
| **4** | **Supporting / Helper Area** | Examples, hints, "how this works"; collapsible or subtle | Tertiary; does not compete with primary |

### Visual Containment and Hierarchy

- **Card boundaries** — Each major block in a contained card; clear section gaps (24–32px)
- **Primary vs secondary** — Primary actions dominate; free input is fallback, not hero
- **Max content width** — 720–800px centered; professional, not full-bleed
- **Background** — Soft light gray (#f5f5f5 or #f8f9fa); business-like, not playful

### Rules

- Trust/hero must be visible without scroll
- Primary actions must be the main interaction surface
- Free input must NOT dominate page identity
- No "lab" or "workbench" framing on customer-facing entry

---

## 2. Flow Backbone

### Stages (Amazon-style service pathing + our detect→ask→enough?→handoff)

| Stage | Name | What Happens |
|-------|------|--------------|
| **1** | **Entry** | Customer lands on page; chooses primary action (quick-start) or pastes free text |
| **2** | **Triage / Routing** | System detects intent (add-car, missing doc, payment risk, etc.); routes to correct flow |
| **3** | **Information Collection** | Ask 1–2 next things per turn; do not overload; apply per-category thresholds |
| **4** | **Confirmation** | System confirms enough collected; may send handoff message to customer |
| **5** | **Handoff** | Case persisted to workbench; broker sees structured case with next step, collected, still needed |
| **6** | **Broker Follow-up** | Broker acts; may paste follow-up; case re-triaged; status updated; reopen context preserved |

### Flow Rules

- **Entry:** Primary actions = service entry points; free input = fallback
- **Triage:** One dominant intent per case; mixed intent → primary + secondary handling
- **Collection:** Max 2–3 customer turns for most categories; add-car may need 3
- **Handoff:** When threshold met OR customer says "先这样" / "你先看"
- **Follow-up:** Reopen shows waiting_on, next_contact_by, latest note

---

## 3. State Backbone

### Product States That Matter

| State | Meaning | Where Used |
|-------|---------|------------|
| **need_more** | Not enough info for handoff; still collecting | Triage result; case card |
| **almost_ready** | One critical field away; e.g. add-car has year+model, needs zip | Triage; quote-ready visibility |
| **quote_ready** | Add-car: (year+model OR VIN) + (zip OR delivery OR driver) | Case card; broker_next_step |
| **attachment_received** | Customer uploaded/sent attachment; visible to broker | Case card; optional, non-blocking |
| **contact_missing** | Quote-ready but customer_name or customer_phone still needed | Still needed chips |
| **escalation / urgent** | Same-day action; cancellation risk; payment failed | Queue; urgency badge |
| **closed** | Broker marked done | Status |
| **follow_up_pending** | Waiting on client/carrier; next_contact_by set | Queue; reopen context |

### State Rules (Zendesk-inspired + our field progress)

- **Status:** new, reviewing, waiting_client, done
- **Due-state:** Overdue, Due today, Due tomorrow, No due date
- **Collection stage:** collecting, enough_for_handoff, handed_off
- **Follow-up type:** new_info, correction, already_sent, clarification_question, urgency_question, next_step_question

### Human Confirmation States

- **human_confirmation_recommended** — When VIN, payment status, customer_says_sent in collected; broker must verify

---

## 4. Handoff Backbone

### What Broker Receives (Intercom-style context + our structure)

| Element | Content | Priority |
|---------|---------|----------|
| **Case focus** | Add car quote · Premium review · Missing document · Payment risk · Claim intake | 1 |
| **Your next move** | One operational sentence: check, confirm, resend, quote, remove, tell client what to bring | 2 |
| **Collected** | Green chips: what customer already provided | 3 |
| **Still needed** | Orange chips: what to ask or verify next | 4 |
| **Urgency** | Same-day vs routine | 5 |
| **Human confirmation** | Badge when AI extracted sensitive data; broker should verify | 6 |

### Context Visibility

| Context Type | What Broker Needs | Where |
|--------------|-------------------|-------|
| **Correction** | Customer corrected earlier info | Badge or chip |
| **Already sent** | Customer says "I already sent it" | "Verify receipt" badge |
| **Attachment** | Case has attachment(s) | Attachment block; download link |
| **Secondary issue** | Mixed intent; second issue in same message | Secondary case or note |

### Handoff Rules

- **Prominence:** broker_next_step bold, top of case card
- **Style:** Operational; concrete (mention document, deadline, vehicle when known)
- **One sentence:** Not a paragraph
- **Draft editable:** client_reply_draft; broker confirms before sending; no auto-send
- **Reopen context:** "Resume here" with waiting_on + latest note

---

## 5. Backbone Alignment Checklist

Future sprints should verify:

- [ ] Page: Trust/hero above fold; primary actions dominate; free input subordinate
- [ ] Flow: Entry → triage → collect → confirm → handoff → follow-up
- [ ] State: need_more, almost_ready, quote_ready, escalation, etc. used consistently
- [ ] Handoff: Case focus, next move, collected, still needed, urgency, correction/already_sent visible

---

*End of Page / Flow / State / Handoff Backbone Spec*

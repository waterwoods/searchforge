# Broker Inbox Triage Assistant — Master Goal

**Created**: 2026-03-07  
**Scope**: SearchForge → Broker Inbox Triage (new product direction)  
**Phase**: MVP Definition & First Prototype

---

## 1. Mission

Create one unified intake point where inbound broker messages can be triaged by AI first, then routed into broker workflow—inspired by Amazon-style service triage: one entry point → AI triage → easy cases handled quickly → harder cases escalated to a human.

---

## 2. Target User

- **Primary**: California auto insurance brokers (e.g., 陈奎)
- **Profile**: Receives fragmented inbound messages from clients, carriers, underwriting, escrow, mortgage, HOA
- **Pain**: Too many messages, missed issues, delayed follow-up, customer trust damage, policy cancellation risk, manual reading/sorting, repetitive explanation work

---

## 3. Business Goal

- **First useful MVP** that takes pasted message/screenshot text and produces structured triage output
- **No automation of actions** in v1—broker decides and acts
- **Single broker** pilot; no auth, billing, multi-tenant
- **Testimonial / feedback** as success metric for next phase

---

## 4. What This Product Does

| Area | What |
|------|------|
| **Input** | Pasted message text (from screenshot, email, SMS, notice, client description) |
| **Output** | 1) Issue category 2) Urgency level 3) Broker next step 4) What client should prepare 5) Client-ready reply draft 6) Whether manual broker follow-up is needed |
| **Flow** | Intake → Classify → Urgency → Broker next step → Client draft → Escalation flag |

---

## 5. What This Product Does NOT Do

| Area | What |
|------|------|
| **CRM** | No full CRM |
| **Communication platform** | No email/SMS/WeChat integration |
| **Auto-send** | No auto-actuation in v1 |
| **Auth / billing / multi-tenant** | Not in scope |
| **Other verticals** | Auto insurance broker only |

---

## 6. MVP Success Criteria

1. Takes realistic inbound message text as input
2. Produces all six output fields in consistent shape
3. Scenario pack (8–12 cases) passes with expected categories and urgency
4. Client-ready draft is professional, safe, and editable
5. Escalation flag is reasonable for each scenario

---

## 7. Constraints

- Document first, then code
- Narrow MVP over broad ambition
- Practical broker value over AI sophistication
- No unbounded autonomous expansion

---

*End of goal document*

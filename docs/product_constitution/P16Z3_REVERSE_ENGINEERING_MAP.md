# P16-Z3 Reverse Engineering Map

**Date:** 2026-06-01  
**Sprint:** P16-Z3 Case Intelligence Maturity Model Sprint  
**Sources:** P16-Z2 company teardown, P16-Z2_CASE_INTELLIGENCE_COMPARISON.md, maturity model L0–L9  
**Question:** Which maturity levels correspond to which company strengths — and where does SearchForge sit?

---

## Universal pipeline (all companies)

```
Inbound chaos → Normalize/classify → Extract fields → Structured record → Next action → Continuity → Outcome
```

Every company implements this. None skip the structured record step. The 2026 shift (verified resolution, context-first agents, credit-per-resolution) confirms: **outcomes on structured cases**, not activity on messages.

---

## Maturity level × company strength matrix

| Level | Name | Zendesk | Intercom | Salesforce | Stripe | Linear | HubSpot | **SearchForge** |
|-------|------|---------|----------|------------|--------|--------|---------|-----------------|
| **L0** | Raw Intake | Omnichannel ticket create | Messenger session | Email/Web/Chat-to-Case | Dispute + evidence upload | Issue from Slack/API | Ticket from chat/email | **Text paste ✅** |
| **L1** | Classification | AI intent + sentiment | Fin reads conversation | Einstein Case Classification | Dispute reason codes | Auto-label + priority | Ticket categorization | **Rules strong ✅** |
| **L2** | Field Intelligence | Custom fields + tags | Ticket attributes API | Auto-fill picklists (85% gate) | recommended_evidence[] | Issue properties | Contact/deal fields | **collected/still_needed ✅** |
| **L3** | Case Distillation | Ticket object unified | Convert conversation→ticket | Case + Wrap-Up summary | Evidence packet assembly | Context→Issue creation | Ticket + timeline | **summary + draft ✅** |
| **L4** | Office Action | Copilot draft + macros | Fin reply + macros | Next Best Action + Wrap-Up | Dispute response templates | Agent suggested actions | Sequences + tasks | **broker_next_step ✅** |
| **L5** | Continuity | Ticket comments thread | Conversation primary | Case Feed + field history | Evidence append on dispute | Comment thread = truth | Conversation→ticket link | **Backend ✅ UX ❌** |
| **L6** | Document Intel | Attachment + optional AI | Attachments on conv | Files on Case + Einstein | Receipt/screenshot OCR merge | N/A (code context) | Attachments on ticket | **API ✅ UI ❌** |
| **L7** | Confidence/Risk | AI confidence on fields | Fin confidence | 3-tier: auto/suggest/show | Evidence quality scoring | N/A | Lead scoring | **Backend ✅ UI ❌** |
| **L8** | Lifecycle | Status + SLA + groups | Snooze + assign | Status + Owner + milestones | Dispute stage machine | State + assignee | Pipeline stages | **Partial ⚠️** |
| **L9** | Outcome | Verified resolution 2026 | Resolution reporting | Case closed + CSAT | Win/loss + learning | Cycle analytics | CSAT→KB gap | **Missing ❌** |

---

## Company profiles mapped to maturity

### Zendesk — L1, L3, L8, L9 strength

**Core strength:** Omnichannel normalization into one ticket object + outcome verification.

| Steal | Maps to | SearchForge action |
|-------|---------|-------------------|
| One ticket regardless of channel | L0–L3 | Case = one object; paste simulates channel |
| AI classification on create | L1 | Maintain rules; don't rebuild ML |
| Verified resolution mindset | L9 | Observation log → outcome (process) |
| SLA/deadline visibility | L2/L8 | Promote deadline_mentioned to countdown |

| Skip | Why |
|------|-----|
| 20B ticket corpus training | Not our data |
| Voice AI | Out of scope |
| Seat pricing model | Manual invoice pilot |

**SearchForge gap vs Zendesk:** L8 SLA views, L9 verified resolution.

---

### Intercom — L0, L5, L4 strength

**Core strength:** Conversation-first; structure emerges at handoff.

| Steal | Maps to | SearchForge action |
|-------|---------|-------------------|
| Don't ask category first | L1 | Infer from paste — already done |
| Conversation → typed record at handoff | L3–L4 | handoff_ready moment |
| Continuity as primary UX | L5 | **Post-copy append CTA — P0** |
| Custom Helpdesk API pattern | L3 | We own case; engine owns intelligence |

| Skip | Why |
|------|-----|
| Messenger widget PLG | Broker paste wedge |
| Fin as primary UX | Paste-and-copy soul |

**SearchForge gap vs Intercom:** L5 discoverability — Intercom lives in the thread; we hide append.

---

### Salesforce — L2, L3, L4, L7 strength

**Core strength:** CRM-native case with auto-fill and Next Best Action.

| Steal | Maps to | SearchForge action |
|-------|---------|-------------------|
| collected/still_needed = picklist auto-fill | L2 | Maintain extractors |
| Wrap-Up distills conversation → fields | L3 | conversation_summary + case_draft |
| broker_next_step = NBA output | L4 | Tune Chinese templates |
| 3-tier confidence (auto/suggest/show) | L7 | Surface v4 as「需核实」|

| Skip | Why |
|------|-----|
| Full CRM | Offices have AMS |
| Flow Builder | Over-engineering |
| Einstein platform | Rules at 88.6 sufficient |

**SearchForge gap vs Salesforce:** L7 UI surfacing, L8 owner/queue assignment.

---

### Stripe — L2, L6, L3 strength

**Core strength:** Evidence packet assembly for disputes — merge auto-extracted + manual.

| Steal | Maps to | SearchForge action |
|-------|---------|-------------------|
| recommended_evidence[] | L2 | still_needed_fields |
| Merge OCR + manual fields | L6 | ocr_case_fusion.py — wire UI |
| Structured dispute object | L3 | case_draft bundle |
| Win/loss learning | L9 | Observation log (manual) |

| Skip | Why |
|------|-----|
| Payments | Not our vertical |
| Radar fraud ML | Irrelevant |

**SearchForge gap vs Stripe:** L6 product UI for evidence merge.

---

### Linear — L3, L5 strength

**Core strength:** Context is source of truth; inbound automations create issues from context.

| Steal | Maps to | SearchForge action |
|-------|---------|-------------------|
| Context → record (not form-first) | L3 | Paste-first intake |
| Thread as canonical state | L5 | Append without new case |
| Minimal UI, maximum context | L4 | Glance over dashboards |

| Skip | Why |
|------|-----|
| Git/PR workflow | Not insurance |
| Agent platform | P17 blocked |

**SearchForge gap vs Linear:** L5 UX — Linear makes thread continuity obvious; we bury append.

---

### HubSpot — L4, L8, L9 strength (portal)

**Core strength:** Customer portal status + pipeline visibility.

| Steal | Maps to | SearchForge action |
|-------|---------|-------------------|
| Portal status view | L8/L4 | MyRequestsTab — week 3 |
| Pipeline stages | L8 | case_status + waiting_on |
| KB deflection loop | L9 | Future; not pilot |
| Localization | L4 | Chinese throughout |

| Skip | Why |
|------|-----|
| Marketing bundle | Not CRM |
| IVR | Out of scope |

**SearchForge gap vs HubSpot:** L8 customer-visible status (Cap 4 hidden).

---

## SearchForge position on the map

```
                    L9 Outcome
                         ▲
                    HubSpot · Zendesk
                         │
              L8 Lifecycle ◄── Zendesk · HubSpot · Salesforce
                         │
         L7 Risk ◄── Salesforce
                         │
              L6 Docs ◄── Stripe
                         │
    L5 Continuity ◄── Intercom · Linear  ◄── [SearchForge backend here]
                         │
         L4 Action ◄── All ◄── [SearchForge engine here]
                         │
         L3 Distill ◄── All
                         │
         L2 Fields ◄── Salesforce · Stripe
                         │
         L1 Classify ◄── Zendesk · Salesforce
                         │
         L0 Intake ◄── Intercom
                         │
                    [SearchForge deployed UX here — below L4]
```

**Diagnosis:** Engine competes at L4; deployed experience sits at L3.5; continuity backend at L5 with UX at L2.

---

## Steal vs skip summary

| Company | Steal (maturity levels) | Skip |
|---------|-------------------------|------|
| **Zendesk** | L9 outcome focus, L8 SLA/deadline | Corpus, voice, enterprise |
| **Intercom** | L5 continuity UX, L0 conversation-first | Widget, PLG, Fin-primary |
| **Salesforce** | L2 auto-fill, L4 NBA, L7 confidence tiers | CRM, Flow, Einstein platform |
| **Stripe** | L6 evidence merge, L2 recommended_evidence | Payments, fraud ML |
| **Linear** | L5 context-as-truth, L3 minimal record | Dev workflow |
| **HubSpot** | L8 portal status, L4 localized action | Marketing, IVR |

---

## Modality coverage vs benchmarks

| Modality | Best-in-class | SearchForge | Gap level |
|----------|---------------|-------------|-----------|
| Chat/paste | Intercom | ✅ Primary | — |
| Email | Zendesk | ✅ Simulated via paste | — |
| Multi-turn | Intercom | ⚠️ Backend only | **L5** |
| Image/screenshot | Stripe | ⚠️ API only | **L6** |
| PDF | Salesforce | ❌ Stub | Defer |
| Voice | Zendesk | ❌ N/A | Never |
| Portal status | HubSpot | ❌ Hidden tab | L8 week 3 |

---

## One-line per company for Chen Kui

| Company | One-line steal |
|---------|----------------|
| Zendesk | "One case object, deadline visible, outcome tracked" |
| Intercom | "Thread grows; you never start over" |
| Salesforce | "Fields fill themselves; office knows next step" |
| Stripe | "Screenshot becomes evidence on the case" |
| Linear | "Paste is enough; context is the case" |
| HubSpot | "Customer can check status without calling you" |

**SearchForge pitch:** "Linear's paste speed + Salesforce's field fill + Intercom's thread — for WeChat insurance chaos."

---

*End of P16-Z3 Reverse Engineering Map*

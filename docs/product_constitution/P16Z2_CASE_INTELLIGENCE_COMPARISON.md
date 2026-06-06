# P16-Z2 Phase 2 — Case Intelligence Comparison

**Date:** 2026-06-01  
**Sprint:** P16-Z2 Case Intelligence Strategic Reverse Engineering  
**Question:** How do world-class systems transform Conversation → Structured Record?

---

## Universal pipeline (abstracted)

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  Inbound    │ →  │  Normalize   │ →  │  Extract    │ →  │  Record      │
│  (any mod.) │    │  + classify  │    │  + validate │    │  + route     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
     chaos              understanding        facts           case + next action
```

Every company implements this pipeline differently. None skip it.

---

## Modality → Record mapping matrix

| Modality | Zendesk | Intercom | Salesforce | Stripe | Linear | HubSpot | **SearchForge (today)** |
|----------|---------|----------|------------|--------|--------|---------|-------------------------|
| **Conversation (chat)** | Ticket + comments | Conversation → optional Ticket | Case + Live Chat transcript | N/A | Comment thread → Issue | Conversation → Ticket | `conversation_turns` → case |
| **Email** | Ticket (email channel) | Email in inbox | Email-to-Case | Dispute email notices | N/A | Ticket thread | Paste simulates email |
| **Chat (sync)** | Messaging ticket | Messenger session | Embedded chat → Case | N/A | Slack/Teams → Agent | Live chat → Ticket | CustomerEntryTab (dev) |
| **Voice** | Voice AI → ticket | Limited | Service Cloud Voice | N/A | N/A | IVR → Ticket | ❌ Not in scope |
| **Image** | Attachment + optional AI | Attachment on conversation | Files on Case | Receipt/screenshot evidence | N/A | Attachments on ticket | OCR sidecar (API, no UI) |
| **PDF** | Attachment indexing | Attachment | Content document | Dispute docs | N/A | KB PDFs | `pdf_skipped` stub |

---

## Company-by-company: Conversation → Structured Record

### Zendesk

```
Email / Chat / Voice / Social / API
        ↓
   Ticket (unified object)
        ↓
   AI Classification (intent, sentiment, language)
        ↓
   Custom fields + Tags + Priority + Group
        ↓
   Agent Copilot draft + Suggested macros
        ↓
   Resolution (verified) → Knowledge gap signal
```

**Key mechanics:**
- **One ticket object** regardless of channel — omnichannel is normalization layer
- **Triggers on create** — auto-tag, auto-route, auto-reply
- **Side conversations** — internal threads without polluting customer view
- **2026:** Resolution Platform trains on ticket corpus; auto-fills resolution path

**Structured record shape:** Ticket ID, Requester, Subject, Description, Status, Priority, Type, Tags, Custom Fields[], Comments[], SLA timers

---

### Intercom

```
Messenger / Email / Custom Helpdesk API
        ↓
   Conversation (primary object)
        ↓
   Fin AI reads conversation + user attributes
        ↓
   [Optional] POST /conversations/{id}/convert
        ↓
   Ticket with ticket_type_id + typed attributes
```

**Key mechanics:**
- **Conversation is first-class** — ticket is escalation artifact, not starting point
- **Ticket types** — schema per issue type (bug, billing, access) with required attributes
- **Attributes API** — `_default_title_`, `_default_description_`, custom list fields
- **Custom Helpdesk** — Fin pulls from your system; you own the record; Fin owns intelligence

**Structured record shape:** Conversation → Ticket with `ticket_attributes`, `ticket_state`, `ticket_parts[]`, linked contacts

**Steal for Chen Kui:** Don't ask "what category?" first. Let conversation infer type; structure emerges at handoff.

---

### Salesforce Service Cloud

```
Email-to-Case / Web-to-Case / Chat / API
        ↓
   Case object created
        ↓
   Einstein Case Classification (ML on historical Cases)
        ↓
   Auto-set or Suggest: Type, Reason, Priority, custom picklists
        ↓
   Assignment Rules → Queue or Agent
        ↓
   [On close] Einstein Case Wrap-Up → summary + field suggestions
```

**Key mechanics:**
- **Case is CRM-native** — linked to Account, Contact, Asset, Entitlement
- **85% accept-rate gate** before auto-set (trust building)
- **Three-tier confidence:** auto-fill → preselect → show top 3
- **Wrap-Up at end** — distills conversation into case fields

**Structured record shape:** Case Number, AccountId, ContactId, Subject, Description, Type, Reason, Priority, Status, Owner, SLA milestones

**Steal for Chen Kui:** `collected_fields` / `still_needed_fields` = our picklist auto-fill. `broker_next_step` = Wrap-Up output.

---

### Stripe (Dispute-as-Case pattern)

```
Dispute webhook / Dashboard alert
        ↓
   Dispute object (reason code, amount, deadline)
        ↓
   Smart Disputes AI rules engine
        ↓
   Pull: transaction, customer, shipping, receipt, IP, metadata
        ↓
   Evidence packet (structured hash) + recommended_evidence[]
        ↓
   Merge manual evidence + auto → submit before due_by
```

**Key mechanics:**
- **Reason code drives extraction template** — different fields per dispute type
- **Status machine:** `requires_evidence` → `available` → submitted
- **`intended_submission_method`** — prefer_smart_disputes merges human + AI
- **Deadline is first-class** — auto-submit before timeout

**Structured record shape:** Dispute ID, reason, amount, evidence{...}, smart_disputes.status, due_by, submission_count

**Steal for Chen Kui:** Cancellation notice = dispute. Reason (cancel/UW/payment) drives which fields to extract. Deadline from notice → `still_needed_fields` if missing.

---

### Linear

```
Slack / Comment / @Linear mention / GitHub PR
        ↓
   Context interpreted by Linear Agent
        ↓
   Issue created or updated (not user-created ticket)
        ↓
   Automations refine on inbound
        ↓
   Agent Plan (checklist evolves during session)
        ↓
   Status synced from external events (PR merged → Done)
```

**Key mechanics:**
- **Context → issue** (inverse of traditional ticket-first)
- **AgentSession** — pending, active, awaitingInput, complete
- **Inbound automations** — triage/synthesize on arrival
- **Linkbacks** — external artifacts attached to issue without leaving Linear

**Structured record shape:** Issue ID, Title, Description, Status, Priority, Labels, Assignee, Project, linked PRs, AgentSession.plan[]

**Steal for Chen Kui:** Broker paste is "inbound context." Case should materialize from paste, not require broker to fill form first.

---

### HubSpot Service Hub

```
Chat / Email / Portal / Form
        ↓
   Ticket in Help Desk
        ↓
   Breeze AI: categorize, prioritize, suggest reply
        ↓
   CRM enrichment (contact tier, deal stage, prior tickets)
        ↓
   [Deflection path] KB article suggested → portal self-serve
        ↓
   Ticket closed → knowledge gap flagged
```

**Key mechanics:**
- **Ticket + Contact unified** — every ticket has CRM context
- **Customer portal** — customer sees same ticket record
- **KB deflection loop** — ticket content feeds article creation
- **Credit-based AI** — pay per resolution delivered

**Structured record shape:** Ticket ID, Subject, Pipeline stage, Priority, Owner, Contact properties, thread, KB articles cited

**Steal for Chen Kui:** Customer status tab (我的办理) = portal. Broker workbench = help desk. Same case, two views.

---

## SearchForge current state vs best-in-class

| Stage | Best-in-class | SearchForge today | Gap |
|-------|---------------|-------------------|-----|
| **Normalize** | Channel-agnostic ticket/case object | Text paste (+ dev chat) | No WeChat webhook; paste wedge OK for pilot |
| **Classify** | ML + rules hybrid | `triage.py` rules + categories | Strong (~85 Cap 2) |
| **Extract** | Typed fields per case type | `collected_fields`, extractors | Good single-turn; weak multi-turn merge |
| **Validate** | Confidence thresholds, HITL | P16-Y battery rubric | Engine scored; UI doesn't show confidence |
| **Record** | Persistent case with thread | Postgres case + `case_messages` on append | Backend complete; UI shows `source_text` mainly |
| **Route** | Queue + assignment rules | Demo queue + manual reopen | No "urgent today" filter in product_only |
| **Next action** | NBA / Wrap-Up / Copilot | `broker_next_step`, `client_prep` | Office Actionability 25/25 ceiling — generic wording |
| **Document** | IDP pipeline | OCR sidecar (hidden) | Text-only on trial; PDF stub |

---

## Insurance-specific record schema (target)

What a Chen Kui office **actually needs** in the structured record:

| Field group | Examples | Source modality |
|-------------|----------|-----------------|
| **Identity** | Named insured, driver, VIN, plate | Text, DL photo, reg photo |
| **Policy** | Carrier, policy #, effective dates | Dec page, cancel notice, email |
| **Intent** | Add car, remove car, cancel, claim, payment | Conversation |
| **Urgency** | Deadline, lapse risk, UW pending | Notice text, emoji dates |
| **Evidence** | Notice image, payment screenshot | Image, PDF |
| **Gaps** | Missing DL, missing garaging proof | Engine inference |
| **Office action** | Call carrier, send quote, verify payment | Engine + rules |
| **Customer action** | Send photo, confirm VIN, sign form | client_prep |
| **Lifecycle** | waiting_on, next_contact_by, status | Broker update |

**North Star record test:** Can Chen Kui act on the case **without re-reading the WeChat paste**? P16-Y rubric already measures this.

---

## Modality priority for 2–3 week pilot

| Priority | Modality | Why |
|----------|----------|-----|
| **P0** | WeChat text paste | 90% of Chen Kui inbound today |
| **P1** | Screenshot paste (text describing image) | Customer says "发你了" without attachment |
| **P2** | Image upload on broker workbench | OCR exists; wire UI only |
| **P3** | Customer chat multi-turn | CustomerEntryTab exists; hidden |
| **Defer** | PDF, voice, email auto-ingest | Infrastructure cost > pilot value |

---

## Conversion flow comparison (visual)

### Intercom (conversation-first) — **closest model for customer intake**

```
Customer message ──→ Fin understands ──→ [handoff] ──→ Typed ticket
                         ↑                              ↓
                    no category pick              office queue
```

### Salesforce (record-first) — **closest model for broker workbench**

```
Inbound ──→ Case created ──→ ML fills fields ──→ Agent sees complete record
                                    ↓
                              Route to queue
```

### SearchForge (hybrid target)

```
WeChat paste ──→ Triage ──→ Case glance ──→ Copy to WeChat
     ↑              ↓              ↓
Customer chat   Append merge   broker_next_step
 (dev/hidden)   (backend OK)   (wording weak)
```

---

*End of P16-Z2 Phase 2 — Case Intelligence Comparison*

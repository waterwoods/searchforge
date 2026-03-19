# Trusted Assistant Platform Blueprint

**Purpose:** High-level blueprint for a trusted assistant platform tailored to California Chinese-speaking insurance office context. Defines product shape, 3-layer architecture, trust boundaries, and monetization path.

**Scope:** Chen Kui pilot → repeatable small-client product. Blueprinting only; not a coding spec.

**Created:** 2026-03-12 — Trusted Assistant Platform Blueprint Sprint

---

## 1. Product Definition

### One-sentence definition

A trusted assistant that turns messy inbound customer messages into structured broker cases with clear next steps, collected data, and draft replies — so the office moves faster without losing control.

### One-paragraph definition

When a customer sends a text, pasted notice, or screenshot, the system classifies it, asks for what’s missing, and hands off a clean case to the broker. The broker sees one dominant next move, what the client should prepare, and a draft response. No manual triage. The assistant is narrow (insurance intake + broker workbench), traceable (full conversation + structured output), and human-backed (broker confirms before any external action). It is not a general AI chatbot; it is a practical, lightweight tool for daily office work.

### What the product is NOT

- A general-purpose AI chatbot
- A full CRM or case-management platform
- An automated outbound communication system
- A system that makes binding decisions (quotes, policy changes, carrier submissions)
- A replacement for broker judgment
- A large enterprise platform

### Who it is for

- **Primary:** California auto insurance brokers serving Chinese-speaking clients (e.g., Chen Kui)
- **Profile:** Small office; needs quick triage, structured intake, and client-ready drafts; values traceability and control

### What painful problem it solves first

- **Manual triage:** Broker spends time reading messy messages, figuring out intent, and deciding what to ask next.
- **Scattered context:** Customer info lives in WeChat/email; no single structured case.
- **Repetitive explanation:** Same notice questions, add-car flows, missing-document chases — the assistant handles the first pass.
- **Lost follow-up:** Cases slip; no lightweight “waiting on” / “next contact” memory.

---

## 2. The 3-Layer Architecture

### Overview

| Layer | Name | Purpose |
|-------|------|---------|
| **1** | Customer conversation / intake | Collect intent and key data from messy inbound messages |
| **2** | Structured case / workbench | Turn conversations into actionable broker cases |
| **3** | Knowledge / rules / human-confirmation / execution | What informs decisions; what gets executed; who confirms |

---

### Layer 1: Customer Conversation / Intake

**Purpose:** Receive messy inbound messages, classify intent, ask for missing info, and hand off when enough is collected.

**Inputs:** Pasted text (customer message, notice, screenshot text, forwarded content).

**Outputs:** Structured triage result (category, urgency, collected_fields, still_needed_fields, broker_next_step, client_reply_draft); persisted case when handoff occurs.

**What belongs here:**
- Intent detection (add-car, payment risk, notice confusion, missing document, claim intake, etc.)
- Multi-turn ask logic (1–2 items per turn)
- Handoff thresholds (enough when year+model+zip for add-car, etc.)
- Conversation memory within a single case
- Client-facing reply drafts (conclusion first, next step second)

**What does NOT belong here:**
- Final premium quotes or policy decisions
- Carrier submission or external API calls
- Broker identity or CRM assignment
- Long-term customer history across cases

**Connects to Layer 2:** Handoff produces a case with `source_text`, `conversation_summary`, `broker_next_step`, `collected_fields`, `still_needed_fields`, `client_reply_draft`. Case is saved to workbench.

---

### Layer 2: Structured Case / Workbench

**Purpose:** Present broker-ready cases with clear next steps, collected data, and follow-up context.

**Inputs:** Cases from Layer 1; broker updates (status, notes, waiting_on, next_contact_by); pasted follow-up messages.

**Outputs:** Queue view (urgency, case focus, readiness); case card (next move, collected, still needed, draft); reopen context (waiting on, next contact, latest note).

**What belongs here:**
- Case focus / type
- Collected fields (chips)
- Still needed fields (chips)
- Broker next step (one operational sentence)
- Status (new, reviewing, waiting_client, done)
- Due-state (Overdue, Due today, Due tomorrow, No due date)
- Last meaningful update
- Waiting on (client, broker, carrier, underwriting)
- Full conversation (for verification)
- Client reply draft (editable)

**What does NOT belong here:**
- Premium calculation logic
- Carrier API integration
- Automated outbound sending
- Multi-user assignment or collaboration

**Connects to Layer 3:** Broker uses workbench to decide what to do. Human confirmation happens before any Layer 3 execution (e.g., sending a reply, changing a policy). Knowledge and rules inform the drafts and next steps shown here.

---

### Layer 3: Knowledge / Rules / Human-Confirmation / Execution

**Purpose:** Provide the knowledge and rules that inform Layer 1 and 2; define what AI can do automatically vs what requires human confirmation; execute only what is explicitly human-approved.

**Inputs:** RAG corpus (DMV, CDI, insurer pages); workflow rules (handoff thresholds, urgency mapping); client-specific phrasing; broker confirmation.

**Outputs:** Retrieved explanations for notice confusion; draft content; suggested next steps. No automatic execution of binding actions.

**What belongs here:**
- Common domain knowledge (DMV, SR-22, notice interpretation) — RAG
- Workflow rules (detect → ask → enough? → hand off) — code/config
- Client-specific phrasing (Chen Kui tone) — config
- Human confirmation gate for any external or binding action
- Audit trail (what was suggested vs what was confirmed)

**What does NOT belong here:**
- Raw case state (→ Layer 2 persistence)
- Conversation turns (→ Layer 1)
- Automated premium quotes, policy changes, carrier submissions

**Connects to Layer 1 & 2:** Rules and knowledge drive triage and drafts. Human confirms before sending, quoting, or changing anything external.

---

## 3. Trusted Assistant Principles

| Principle | Meaning |
|-----------|---------|
| **Human-in-the-loop** | Broker confirms before any binding or external action. AI suggests; human decides. |
| **Traceability** | Full conversation and structured output are visible. Broker can verify what was extracted and why. |
| **Explicit next-step guidance** | One clear “Your next move” per case. No vague “review and follow up.” |
| **Conservative automation** | Automate only intake, classification, and drafting. Do not automate quotes, policy changes, or outbound sending. |
| **Structured outputs over vague chat** | Prefer collected/still_needed chips and broker_next_step over long free-text summaries. |
| **Safe escalation** | When uncertain, hand off to broker with “needs review” signal rather than guessing. |
| **Least necessary data** | Collect only what is needed for the next step. Do not over-ask. |
| **Clear risk boundaries** | Document what AI can do, what it can suggest, and what it must not do. |

---

## 4. Automation Boundaries

### A. AI can do automatically

- Classify inbound message intent (add-car, payment risk, notice confusion, etc.)
- Ask for 1–2 next missing fields per turn
- Decide when enough info is collected for handoff (per category thresholds)
- Build conversation summary and broker_next_step
- Generate client reply draft (conclusion first, next step second)
- Retrieve and cite DMV/CDI/insurer content for notice explanation
- Persist case to workbench with structured fields
- Update case when broker pastes follow-up message (re-triage in context)

### B. AI can draft/suggest, but human confirms

- Client reply draft — broker edits before sending
- Broker next step — broker may override
- Collected / still needed — broker verifies before acting
- Notice explanation — broker confirms before sharing with client

### C. AI must not do without explicit human control

- Send any message to customer (WeChat, email, SMS)
- Decide or display a premium quote as final
- Change a policy or coverage
- Submit to carrier or underwriting
- Make binding commitments to the customer
- Interpret incomplete or ambiguous customer language as fact without flagging uncertainty

---

## 5. Minimum Structured Outputs That Matter

| Output | Why it matters | Where it appears |
|--------|----------------|-------------------|
| **Case focus / type** | Triage at a glance | Queue card, case card top |
| **Collected fields** | Avoid re-asking; broker proceeds faster | Case card chips |
| **Still needed fields** | Next ask clarity | Case card chips |
| **Broker next step** | One operational sentence | Case card, bold |
| **Status** | new, reviewing, waiting_client, done | Case card, queue |
| **Due-state** | Overdue, Due today, Due tomorrow | Queue, case card |
| **Last meaningful update** | Continuity when reopening | Case card, queue |
| **Waiting on** | client, broker, carrier, underwriting | Case card, reopen |
| **Full conversation** | Verification, context | Case card, collapsible |
| **Client reply draft** | Editable before send | Case card |
| **Needs-review signal** (optional) | When extraction uncertain | Case card badge |

---

## 6. Trust / Compliance Risk Model

| Risk | Why it matters | Cheap reduction |
|------|----------------|------------------|
| **Wrong extraction** | Broker acts on bad data (wrong year, wrong vehicle) | Only show collected when safely derived; defer to broker inference when uncertain |
| **Wrong flow classification** | Case routed to wrong handling | Guardrail scenarios; expression robustness tests; safe fallback to “unclear” |
| **Overconfident answer** | Broker shares wrong notice explanation | Cite sources; “needs review” when retrieval confidence low |
| **Hidden ambiguity** | Customer said “last week” — which item? | Preserve raw conversation; broker sees full context |
| **Sensitive data leakage** | Customer SSN, DOB in logs or external call | No external API with PII; local persistence only for pilot |
| **Acting too automatically** | System sends without broker approval | No outbound automation; draft only |
| **Missing audit trail** | Can’t reconstruct what happened | source_text + conversation_summary + case updates persisted |
| **Mistaken external action** | Wrong policy change, wrong carrier submit | No carrier/policy integration in pilot |
| **Hallucinated business logic** | AI invents rules (e.g., “SR-22 not needed”) | RAG for explanations; rules in code/config, not LLM |

---

## 7. Monetization Path

### First pilot offer

- **What:** Narrow paid pilot for Chen Kui — Unified Intake + Broker Workbench.
- **What you are really selling:** Faster triage, structured cases, draft replies, and lightweight follow-up memory. Not a full CRM. Not automation of external systems.
- **Value to Chen Kui:** Less manual triage, fewer repetitive explanations, clearer next steps, no lost follow-ups. Office moves faster; broker stays in control.
- **Why different from big generic platforms:** Built for this niche (Chinese-speaking CA auto insurance). Rules + retrieval + human-backed. No enterprise bloat. Fast to pilot.
- **What NOT to sell too early:** Full CRM, inbox sync, carrier integration, multi-tenant, Stripe billing.
- **Payment:** Manual invoice (Zelle/Venmo/WeChat) acceptable for v1.

### Repeatable small-client offer (later)

- Same core: intake skeleton + workbench + knowledge layer.
- Per client: industry pack (insurance markers, templates) + client pack (phrasing, tone).
- Pricing: flat monthly for single-office pilot; testimonial as success metric.

---

## 8. Adaptation Strategy

| What | Reusable? | Client-specific? |
|------|-----------|-------------------|
| **Intake skeleton** (detect → ask → enough? → hand off) | Yes (core) | No |
| **Workbench UI** (queue, case card, reopen) | Yes (core) | No |
| **Case store interface** | Yes (core) | No |
| **Industry pack** (insurance markers, categories, handoff thresholds) | Yes (swap for other industries) | No |
| **Client pack** (phrasing, tone, handoff phrases) | No | Yes |
| **RAG corpus** (DMV, CDI, insurers) | Yes (insurance) | Optional client FAQ |
| **Test packs** (scenarios, calibration) | Yes (framework) | Client calibration cases |

**Portability:** New client = new `configs/clients/<id>/` folder. New industry = new `configs/industries/<id>/` folder. Core platform stays the same.

---

## 9. Platform Blueprint Summary

The trusted assistant platform is:

- **Narrow:** Insurance intake + broker workbench. Not a general chatbot.
- **Practical:** Structured outputs, clear next steps, draft replies. Supports real office work.
- **Traceable:** Full conversation + structured fields. Broker can verify.
- **Human-backed:** No binding action without broker confirmation.
- **Lightweight:** No CRM, no carrier integration, no multi-tenant in pilot.
- **Fast to pilot:** Chen Kui first; manual payment; single broker.
- **Adaptable:** Industry pack + client pack model for similar small clients later.

---

*See also: `docs/PROJECT_DOC_SYSTEM_MAP.md`, `docs/KNOWLEDGE_ARCHITECTURE_AND_CONFIG_LAYER.md`, `docs/MATURE_INTAKE_SKELETON.md`, `docs/BROKER_HANDOFF_CLARITY_GUIDE.md`*

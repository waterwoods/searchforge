# Unified Intake MVP — Master Goal

**Created**: 2026-03-07  
**Scope**: SearchForge → California Auto Insurance Broker Assistant  
**Phase**: Product Definition Sprint — First Useful Version

---

## 1. Problem This Product Solves

Insurance brokers like 陈奎 receive **fragmented inbound information**:

- Screenshots (OCR text)
- Pasted email text
- Forwarded notices
- Customer messages
- Underwriting / carrier / mortgage / escrow communications

This causes:

- **Missed issues** — urgent items buried in noise
- **Slow response** — manual reading and sorting
- **Repetitive explanation work** — same answers over and over
- **Customer trust damage** — delayed or inconsistent follow-up
- **Manual overload** — broker spends time triaging instead of advising
- **Weak prioritization** — hard to know what to do first

---

## 2. Primary User

- **Who**: California auto insurance brokers (e.g., 陈奎)
- **Profile**: Serves Chinese-speaking clients; receives mixed English/Chinese inbound; needs quick triage and client-ready drafts
- **Context**: One broker at a time; no CRM; manual workflow; copy-paste to WeChat/email

---

## 3. What the MVP Does

| Area | What |
|------|------|
| **Input** | Pasted message text (from screenshot OCR, email, SMS, notice, client description) |
| **Output** | Structured triage: issue category, urgency, broker next step, client prep, client-ready reply draft, manual-followup flag |
| **Flow** | Receive text → Normalize → Classify → Urgency → Broker next step → Client draft → Escalation flag |
| **Broker role** | Broker reviews output, edits draft if needed, decides and acts; no auto-send |

---

## 4. What the MVP Does NOT Do

| Area | What |
|------|------|
| **CRM** | No full CRM, no case history |
| **Communication platform** | No email/SMS/WeChat integration |
| **Auto-send** | No automatic outbound messaging |
| **Auth / billing / multi-tenant** | Not in scope |
| **Customer identification** | No case/customer linking in v1 |
| **Other verticals** | Auto insurance broker only |

---

## 5. Why This Is Valuable

- **One entry point** — broker pastes any inbound text; gets structured triage
- **Prioritization** — urgency and category surface what matters first
- **Less repetition** — client-ready draft reduces copy-paste and re-explanation
- **Fewer misses** — structured output makes follow-up explicit
- **Low friction** — paste → triage → edit → send; no new tools to learn

---

## 6. Demo Promise (Father-Demo Standard)

For demo purposes, this MVP should feel like a **broker-facing unified service entry point**:

1. One obvious place to paste incoming text
2. One structured case card that appears immediately after triage
3. One clear broker next step
4. One client-facing reply draft that can be copied
5. One visible signal for whether manual broker action is required

If the demo cannot make those five things obvious in under 60 seconds, it is not presentation-ready.

---

## 7. "Good Enough for Next Stage"

The MVP is ready for the next phase when:

1. Takes realistic inbound message text as input
2. Produces all six output fields in consistent shape
3. Scenario pack (8–12 cases) passes with expected categories and urgency
4. Client-ready draft is professional, safe, and editable
5. Escalation flag is reasonable for each scenario
6. A broker can use it in a real workflow (paste → review → act) without confusion

---

## 8. Constraints

- Document first, then code
- Narrow MVP over broad ambition
- Practical broker value over AI sophistication
- No unbounded autonomous expansion
- Broker always decides and acts; system advises only

---

## 9. Operator Clarity Requirement

By the end of this MVP cycle, Andy should be able to answer these questions quickly:

- What the system does now
- What inputs it supports now
- What outputs are real and generated now
- What parts are demo-safe framing rather than integrated production workflow
- Which example messages are strongest for a walkthrough
- What the next product step is after this demo

This clarity is part of the product goal, not a separate documentation nice-to-have.

---

## 10. Input Model (v1)

| Input Type | In Scope | Notes |
|------------|----------|-------|
| Pasted message text | **Yes** | Primary path; broker copies from WeChat, email, SMS |
| Pasted email text | **Yes** | Same as message; body text only |
| OCR-extracted screenshot text | **Yes** | Broker pastes OCR output; no built-in OCR in v1 |
| Short broker-provided context | **Optional** | e.g. "Client: 张先生" — not required for v1 |

**Out of scope for v1:**

- Raw image/file upload (no OCR in product)
- Case/customer identification (no linking)
- Identity or policy number extraction (deferred)
- Structured API from email/WeChat (no integration)

**v1 assumption:** Broker provides text only. No automatic ingestion.

---

## 11. Output Model (v1)

| Field | Required | Broker-only / Client-facing |
|-------|----------|-----------------------------|
| `issue_category` | Yes | Broker-only |
| `urgency` | Yes | Broker-only |
| `manual_followup_needed` | Yes | Broker-only |
| `broker_next_step` | Yes | Broker-only |
| `client_prep` | Yes | Broker-only |
| `client_reply_draft` | Yes | **Client-facing** (broker edits before sending) |

**Wording principles:** Professional, courteous; no legal/financial advice; no promises broker cannot keep. See `UNIFIED_INTAKE_MVP_STANDARD.md`.

---

## 12. Implementation Path

- **Code:** `services/fiqa_api/inbox_triage/`
- **API:** `POST /api/inbox/triage`
- **UI:** `ui/src/pages/UnifiedIntakePage.tsx` at `/workbench/unified-intake`
- **Boundaries:** `docs/UNIFIED_INTAKE_MVP_BOUNDARIES.md`
- **Scenarios:** `configs/inbox_triage_scenarios.json`
- **Demo readiness:** `docs/UNIFIED_INTAKE_DEMO_READINESS.md`

---

*End of goal document*

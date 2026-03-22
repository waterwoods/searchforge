# Add-Car Submission / Confirmation / Office Handoff Blueprint

**Sprint:** Add-Car Clear Submission + Confirmation + Office Handoff  
**Product:** SearchForge → Chen Kui Insurance Unified Entry  
**Principle:** One Add-Car thread = one business event. Optimize for formal intake, not more chat.

## Goal

Move the flagship Add-Car line from “the assistant replied” to:

1. **Clear submission** — Customer believes they have *submitted* an Add-Car request, not merely sent a message.
2. **Clear confirmation** — Customer sees *what the system recorded* and can judge completeness / accuracy.
3. **Clear office handoff / waiting** — Customer believes the *office has the request* and understands *what happens next* and *roughly when*, without overpromising.

## Non-goals

OCR, carrier API, multi-tenant auth, broad redesign, LLM replacement of rules, full ticketing.

## Current architecture (baseline)

| Layer | Responsibility |
|--------|----------------|
| **Rules** | `services/fiqa_api/inbox_triage/triage.py` — handoff gates, `collected_fields`, `still_needed_fields`, `quote_ready_status`, `client_reply_draft` at handoff |
| **Phrases** | `configs/clients/chen_kui/handoff_phrases.json` — canned handoff lines per flow key (`add_car`, etc.) |
| **UI copy** | `configs/clients/chen_kui/ui_copy.json` — customer ribbons, closure headlines, toasts (served via `get_ui_copy`) |
| **Customer UI** | `ui/src/pages/UnifiedIntakePage.tsx` — progress card pre-handoff; closure card post-handoff |

## Baseline gap (pre-sprint)

- Pre-handoff progress card shows structured tags; **post-handoff closure card removed that structure**, so confirmation weakened at the exact moment of “done.”
- Follow-up timing was mostly “尽快,” light on **business-day realism**.
- Primary CTA on first screen remained generic “提交,” weak for Add-Car **submission framing**.

## Target end state

- Closure card includes a **received-information snapshot** for Add-Car (same semantics as progress card).
- Dedicated **office follow-up expectation** line (config-driven, believable SLA wording).
- **Handoff reply** (`handoff_phrases` + `client_reply_draft`) stresses **formal submission** in ≤2 short sentences.
- First-turn submit label **Add-Car-specific** when intent is Add-Car.

## Success signals (founder / broker)

- Customer can answer: “What did they record?” without re-reading the whole chat.
- Customer can answer: “Is the office working on this?” and “When might I hear back?” at a high level.
- Assistant/broker see unchanged structured fields in workbench; customer side **mirrors** that discipline.

# Lightweight Production Case Record — Product / System Blueprint

**Sprint**: Lightweight Production Case Record Sprint  
**Created**: 2026-03-15  
**Scope**: Chen Kui Insurance Unified Entry — Case persistence, Broker Workbench

---

## 1. Why Lightweight Formal Case Records Matter Now

The front door and Talk-to-Agent path are now much stronger. The next major product gap is not "can it talk," but:

**Can it remember, track, and operate cases in a more formal, durable way?**

Right now the founder has validated that:
- users can ask questions
- the system can route and summarize
- the office can see a workbench

But to move toward paid pilot / small-client real use, the system needs a more formal case record model. The biggest lightweight production gaps are:

| Gap | Current State | Impact |
|-----|---------------|--------|
| Message history | Merged blob (`source_text`) | No per-turn audit, hard to replay, append overwrites context |
| Customer linkage | None | Cannot associate case with a person; no follow-up continuity |
| Workflow state | Partial (status, waiting_on) | collected/still_needed/topic not formal; implicit |
| Lifecycle status | case_status exists | Acceptable but not formal enough for office follow-up |
| Office continuity | case_activity, notes | Good; needs message-level support |

---

## 2. Current Limitations (Baseline)

| Dimension | Status | Detail |
|-----------|--------|--------|
| **Case storage** | JSON file | `data/unified_intake_cases.json`; single file, no schema version |
| **Message representation** | Merged string | `source_text` = `[客户] msg1\n\n[系统] reply1\n\n[客户] msg2` |
| **Message-level history** | **Weak** | No `case_messages` table; append merges into blob |
| **Customer identity** | **Blocking** | No customer_id, name, phone, email, policy_number |
| **Workflow state** | **Weak** | issue_category, collected_fields, still_needed in triage output; not always persisted explicitly |
| **Lifecycle status** | **Acceptable** | case_status: new/reviewing/waiting_client/done; waiting_on |
| **Event history** | **Acceptable** | case_activity for status/follow-up/note; no message-level events |

---

## 3. Target Minimum Improvement

| Dimension | Target |
|-----------|--------|
| **Message-level history** | Each user/assistant turn as its own record; `source_text` derived or deprecated |
| **Customer linkage** | Minimal: customer_id (optional), name, phone, email, policy_number when known |
| **Workflow state** | Explicit: issue_category, collected_fields, still_needed_fields, handoff_ready, case_creation_suggested, human_confirmation_required |
| **Lifecycle status** | Formal: New, Waiting for customer, Agent follow-up, Closed |
| **Office continuity** | Case list/detail shows lifecycle; follow-up target clear |

---

## 4. What This Sprint Will Do

- Add `case_messages` (or equivalent) for message-level history
- Persist explicit workflow state (collected, still_needed, topic, handoff flags)
- Add lightweight customer linkage (minimal fields)
- Formalize minimal lifecycle status
- Preserve compatibility: existing cases readable; `source_text` derived from messages when needed

---

## 5. What This Sprint Will NOT Do

- Full enterprise CRM or ticketing system
- Auth, multi-tenant, or assignment systems
- Front-door UX redesign
- Migration to Postgres/SQLite (unless clearly justified)
- Broad refactor of triage or routing

---

## 6. Success Criteria (High Level)

At the end of this sprint:

1. A case has message-level history (each turn persisted)
2. A case can link to a minimal customer identity when available
3. Workflow state is explicit and persisted
4. Lifecycle status is formal and office-visible
5. The system remains startup-practical and demo-friendly

---

*See also: `02_CASE_RECORD_DESIGN_SPEC.md`, `03_DATA_MODEL_SPEC.md`*

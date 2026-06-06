# State/Workflow Backbone — Product System Blueprint

**Sprint**: State Workflow Backbone  
**Purpose**: Why this backbone matters now, current weaknesses, what this sprint strengthens, and what it will NOT do.  
**Audience**: Founder, product, engineering.

---

## 1. Why State/Workflow Backbone Matters Now

| Driver | Impact |
|--------|--------|
| **Multi-turn continuity** | Customer Entry must remember where the conversation is. Without explicit state, Turn 3 can forget Turn 1–2 context. |
| **Broker handoff clarity** | Office needs to see: collected vs still needed, what stage we're in, when to act. Fuzzy state → broker confusion. |
| **Pilot readiness** | Real office use requires predictable progression: detect → ask → enough? → hand off. No backbone = ad-hoc behavior. |
| **Reply quality** | Follow-up type (already_sent vs clarification vs new_info) drives reply strategy. State enables correct phrasing. |
| **Case vs conversation** | A case is a persisted workflow unit. A conversation is the message thread. We need both, clearly separated. |

**Bottom line**: The system already has triage, handoff logic, and case persistence. What's missing is a **consistent, explicit state/workflow layer** that ties them together and makes progression predictable.

---

## 2. Current Weaknesses

| Weakness | Where it shows | Consequence |
|----------|----------------|--------------|
| **State is implicit** | `collection_stage`, `follow_up_type` exist in triage output but are not consistently persisted or enforced | Broker can't reliably see "collecting" vs "enough_for_handoff" |
| **Conversation vs case identity blur** | No explicit `conversation_id` or `session_id`; case is created at handoff, not at first message | Hard to track "same customer, same thread" before case exists |
| **Transition rules scattered** | `_should_handoff`, `_get_next_ask_draft`, `_add_car_enough_for_handoff` live in triage.py; no single guardrail | Edge cases slip through; regression risk |
| **Handoff timing inconsistency** | Persist only when `handoff_ready`; append always hands off | Append flow treats every follow-up as handoff-ready; no "still collecting" append path |
| **Lifecycle status underused** | `case_status`, `waiting_on` exist in case_store but UI and flows don't consistently drive them | Office can't reliably triage by status |
| **No formal transition validation** | Status changes accepted without checking validity (e.g., closed → new) | Invalid states possible |

---

## 3. What This Sprint Strengthens

| Area | Strengthening |
|------|---------------|
| **Conversation lifecycle** | Explicit stages: collecting → enough_for_handoff → handed_off. Persisted and visible. |
| **Workflow progression** | Per-flow field progress (collected, still_needed) as first-class contract; handoff threshold rules codified. |
| **Handoff progression** | Clear rules: when to persist case, when append updates vs creates, when broker receives. |
| **Message thread vs case** | Message thread = ordered turns; case = persisted workflow unit with identity. Document the relationship. |
| **Case vs office workflow** | Case lifecycle (new → reviewing → waiting_customer → agent_followup → closed) aligned with office use. |
| **Transition guardrails** | Valid/invalid state transitions documented and enforced where practical. |
| **Data contract** | Schema for conversation identity, case identity, message record, workflow_state, frontend/backend response. |

---

## 4. What This Sprint Will NOT Do

| Out of scope | Reason |
|--------------|--------|
| **Full workflow engine** | No BPMN, no complex branching. Lightweight state layer only. |
| **Multi-tenant / CRM** | Single-broker pilot. No customer deduplication, no assignment. |
| **SQLite/Postgres migration** | Stay with JSON file storage. Schema improvements within existing store. |
| **Auth / permissions** | Out of scope. |
| **Automated binding decisions** | Human confirmation boundaries remain. No auto-commit. |
| **New business flows** | Focus on strengthening the 5 core flows (add-car, missing doc, cancellation, claim, renewal). |
| **Giant refactor** | Incremental improvements to triage, case_store, routes. No rewrite. |

---

## 5. Success in One Sentence

**After this sprint**: The system has a documented, consistent state/workflow backbone: conversation lifecycle, workflow progression, handoff rules, and case lifecycle are explicit, persisted, and founder-inspectable.

---

*See also: `02_STATE_WORKFLOW_ARCHITECTURE_SPEC.md`, `docs/LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`, `docs/MATURE_INTAKE_SKELETON.md`*

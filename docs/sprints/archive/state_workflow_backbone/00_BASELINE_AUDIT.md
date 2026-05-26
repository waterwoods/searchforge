# State/Workflow Backbone — Baseline Audit

**Sprint**: State Workflow Backbone  
**Purpose**: Honest audit of current backbone before implementation.  
**Date**: 2026-03-16

---

## 1. Current Backbone Components

| Component | Location | Role |
|-----------|----------|------|
| **Conversation entry** | `routes/inbox_triage.py` POST /triage | Uses `triage_conversation(text, turns)` for first and follow-up |
| **First-turn logic** | `triage.py` triage_conversation | `turns=[]` → first turn; add-car Turn 1 enough → hand off |
| **Follow-up logic** | `triage.py` triage_conversation | `_should_handoff(count, manual_followup, category)`; next_ask when add-car needs more |
| **Append path** | `triage_for_append()` + `append_follow_up_message()` | Always handoff_ready=True; broker paste into existing case |
| **Case creation** | `save_case()` | Only when handoff_ready + persist_case |
| **State fields** | triage result | collection_stage, follow_up_type, collected_fields, still_needed_fields, handoff_ready |
| **Lifecycle** | case_store | case_status, waiting_on, next_contact_by |
| **Persistence** | case_store | JSON file; case_messages, source_text |
| **Frontend** | UnifiedIntakePage.tsx, inboxTriage.ts | Turns in React state; no conversation_id; persist_case when handoff_ready |

---

## 2. Classification

| Area | Rating | Notes |
|------|--------|------|
| **Unified entry path** | Strong | First message goes through triage_conversation (MULTI_TURN_CONTINUITY_GUARDRAIL) |
| **First-turn logic** | Strong | Add-car Turn 1 enough → hand off; others ask |
| **Follow-up logic** | Acceptable | _should_handoff(count≥2) + next_ask for add-car |
| **Append path** | Weak | Always handoff_ready; no "still collecting" append |
| **Case creation timing** | Strong | Only when handoff_ready |
| **State field usage** | Acceptable | collection_stage, follow_up_type, collected, still_needed in triage; persisted in case |
| **Lifecycle status** | Weak | case_status exists but UI doesn't drive it strongly |
| **Persistence timing** | Strong | save_case only when handoff; append updates case |
| **Frontend/backend coupling** | Acceptable | TriageResult has handoff_ready, collection_stage; UI shows them |
| **Guardrails** | Acceptable | MULTI_TURN_CONTINUITY; persist only handoff |
| **conversation_id** | Blocking | None; in-progress session is ephemeral |
| **Append handoff_ready** | Risky | Append always hands off; broker paste = handoff by design |
| **Legacy/demo shortcut** | Acceptable | talk_to_agent bypass; soft_route button-starter |

---

## 3. Biggest Weaknesses

| # | Weakness | Impact |
|---|----------|--------|
| 1 | **No conversation_id before case** | In-progress sessions (Turn 1–2, not handoff) have no identity; refresh loses state |
| 2 | **Append always handoff_ready** | Append flow assumes broker paste = handoff; no "still collecting" append path |
| 3 | **State fields not consistently persisted** | collection_stage, follow_up_type in triage result; case_store persists them but not all paths |
| 4 | **Lifecycle underused** | case_status, waiting_on exist but office workflow doesn't drive them strongly |

---

## 4. Biggest Source of Confusion

- **Message thread vs case**: Before handoff, thread is in-memory. After handoff, case = thread. No explicit "conversation" entity.
- **When to persist**: Only handoff_ready. But append always hands off, so append path is different from first/follow-up.

---

## 5. Biggest Source of Fragility

- **Scattered transition logic**: _should_handoff, _get_next_ask_draft, _add_car_enough_for_handoff live in triage.py; no single guardrail doc.
- **case_creation_suggested** logic: `handoff and (collected>0 or category in high-value)` — can be inconsistent across flows.

---

## 6. What Is Strong

- Unified entry: triage_conversation for first and follow-up.
- Persist only when handoff_ready.
- Per-flow field extractors (add-car, missing_doc, cancellation, claim, renewal).
- follow_up_type and collection_stage derived and returned.
- case_messages with sequence; source_text derived.

---

*See: 01_PRODUCT_SYSTEM_BLUEPRINT.md, 02_STATE_WORKFLOW_ARCHITECTURE_SPEC.md*

# Minimal Production Backbone Architecture Spec

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. Intended Backbone Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER ENTRY (Layer 1)                          │
│  session_id (client UUID) → turns + workflow_state → triage → handoff?   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ handoff_ready → persist case
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     STRUCTURED CASE / WORKBENCH (Layer 2)                │
│  case_id → case_messages, workflow_state, lifecycle_status, status      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Entity Relationships

| Entity | When Created | When Updated | Links To |
|--------|--------------|--------------|----------|
| **session** | First triage with session_id, no case | Each turn until handoff | — |
| **case** | handoff_ready + persist_case | Status, notes, follow-up, append | — |
| **message** | In session (turns) or case (case_messages) | — | session or case |

**Key rule:** When case is created from session, session is deleted. No session_id → case_id linkage stored (by design: session is ephemeral pre-handoff).

---

## 2. How Messages, workflow_state, Sessions, Cases Relate

| Phase | Messages | workflow_state | Session | Case |
|-------|----------|----------------|---------|------|
| **Pre-handoff** | In session.turns | In session.workflow_state | Exists | None |
| **Handoff** | Persisted as case_messages | Persisted on case | Deleted | Created |
| **Office follow-up** | case_messages appended | Updated from triage_for_append | — | Updated |

---

## 3. Office Follow-Up in Same Backbone

- **Reopen case** → Load case by case_id
- **Paste follow-up** → POST /cases/{case_id}/append-message
- **Re-triage** → triage_for_append(existing_source_text, new_message)
- **Update** → append_follow_up_message updates case_messages, source_text, workflow_state

---

## 4. Where Current Architecture Is Too Loose

| Area | Current | Target |
|------|---------|--------|
| lifecycle_status on case | Derived from case_status (handed_off if new, else office_followup) | Explicit from triage; persist as-is |
| session_id → case_id | Not stored | Optional: store origin_session_id on case for traceability |
| workflow_state keys | Extracted in session_store; case_store copies subset | Single WORKFLOW_STATE_KEYS contract |
| source_text vs case_messages | Both; source_text built from messages | case_messages source of truth; source_text derived |

---

## 5. What This Sprint Will Tighten

1. **Single workflow_state contract** — Same keys in triage, session, case
2. **lifecycle_status** — Persist from triage; do not override with case_status-derived value for new cases
3. **Schema documentation** — Formal field list for message, session, case
4. **Demo/prod boundary** — Env or flag for demo-only behavior

---

*See also: `04_DATA_CONTRACT_SCHEMA_SPEC.md`, `05_DEMO_VS_PRODUCTION_BOUNDARY_SPEC.md`*

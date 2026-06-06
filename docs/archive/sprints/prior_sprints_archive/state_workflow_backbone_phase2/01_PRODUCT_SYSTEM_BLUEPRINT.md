# State / Workflow Backbone Phase 2 — Product / System Blueprint

**Sprint**: State Workflow Backbone Phase 2  
**Date**: 2026-03-16  
**Scope**: Chen Kui Insurance Unified Entry

---

## 1. Why Backbone Phase 2 Matters Now

Phase 1 strengthened:
- Mixed-message handling (follow_up_type order)
- Workflow state schema (WORKFLOW_STATE_KEYS)
- Transition guardrails (closed terminal)
- Basic backbone regression coverage

The founder correctly observed: **the backbone is still incomplete.**

The biggest remaining architecture weakness is not model quality. It is:
- **Incomplete continuity** — no formal conversation_id before case; in-progress sessions ephemeral
- **Incomplete visibility** — workflow_state not fully exposed; UI does not show lifecycle clearly
- **Incomplete contract** — some fields implicit; office users lack clear state interpretation

---

## 2. What Phase 1 Solved

| Area | Phase 1 Outcome |
|------|-----------------|
| Mixed messages | follow_up_type order fixed (clarification before already_sent) |
| Workflow schema | WORKFLOW_STATE_KEYS constant; explicit keys in triage |
| Transition guardrails | closed is terminal; update_case_status rejects closed→other |
| Regression | test_state_workflow_backbone in guardrail_inbox_triage.sh |

---

## 3. What Remains Unsolved

| Gap | Impact |
|-----|--------|
| **No conversation_id before case** | In-progress (Turn 1–2) sessions have no identity; refresh loses state |
| **Workflow_state shape incomplete** | next_best_question not exposed; lifecycle_status not formalized |
| **UI visibility weak** | Founder/office cannot easily see: collecting vs handoff vs office-follow-up |

---

## 4. What This Sprint Will Strengthen

1. **Conversation/session continuity** — Optional `conversation_id` / `session_id` for in-progress threads (localStorage + API)
2. **Workflow_state contract** — Complete shape: next_best_question, lifecycle_status, summary contract
3. **UI state visibility** — Clearer display of: collecting / handoff / office status; collected / still_needed; lifecycle

---

## 5. What We Intentionally Will NOT Do

- Enterprise workflow engine
- SQL migration or new persistence layer
- Multi-tenant auth
- Full append "still collecting" path (broker paste = handoff by design)
- Giant infrastructure rewrite

---

*See: 02_PHASE2_BACKBONE_DESIGN_SPEC.md, 03_CONVERSATION_SESSION_CONTINUITY_SPEC.md*

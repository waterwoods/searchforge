# State / Workflow Backbone Phase 2 — Baseline Audit

**Purpose**: Honest audit of Phase 2 gaps before implementation.

---

## 1. Current State (Post Phase 1)

| Area | Status | Notes |
|------|--------|------|
| conversation_id / session_id | **Blocking** | None; in-progress session ephemeral |
| workflow_state shape | **Acceptable** | WORKFLOW_STATE_KEYS; missing next_best_question, lifecycle_status |
| UI state visibility | **Weak** | collection_stage, collected, still_needed shown but lifecycle underused |
| First-turn continuity | **Strong** | triage_conversation for all |
| Append path | **Acceptable** | Always handoff by design |
| Transition guardrails | **Strong** | closed terminal |

---

## 2. Biggest Current Weakness

**No conversation_id before case.** In-progress sessions (Turn 1–2) have no identity; refresh loses state.

---

## 3. Biggest Source of Ambiguity

**Workflow_state vs lifecycle.** collection_stage = collecting|enough_for_handoff; but "lifecycle" (collecting vs handed off vs office) not formalized.

---

## 4. Biggest Source of User/Business Confusion

**Office users cannot easily see**: Is this still collecting? Handed off? In office follow-up? UI shows case_status but not a unified "lifecycle" view.

---

## 5. Classification

| Item | Rating |
|------|--------|
| conversation_id | Blocking |
| next_best_question | Weak (not exposed) |
| lifecycle_status | Weak (not formalized) |
| UI lifecycle display | Weak |
| session_id in API | None |

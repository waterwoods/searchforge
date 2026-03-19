# Founder Cross-Window Summary Notes — Phase 2.5

**Purpose**: Notes for the founder to paste into another ChatGPT window for evaluation and advice.

---

## What the State / Workflow Work Now Does

1. **Session continuity**: Client generates session_id (UUID), stores in localStorage, sends with triage requests. When no case is persisted, backend echoes it as conversation_id. Enables in-progress thread identity before case creation.

2. **workflow_state contract**: Triage always returns next_best_question (what to ask when still collecting) and lifecycle_status (collecting | handoff_pending | handed_off | office_followup).

3. **UI visibility**: Customer Entry shows "下一步建议" when collecting; "Collecting" / "Ready to save" tag. Broker Workbench case detail shows "Handed off" / "Office follow-up".

4. **Case persistence**: New cases get lifecycle_status = handed_off; cases with status updates get office_followup.

---

## What Was Improved in Phase 2.5

- **talk_to_agent** now returns next_best_question and lifecycle_status (workflow_state contract consistency)
- **Queue cards** in Broker Workbench now show lifecycle_status ("Handed off" / "Office follow-up")
- Deployment of backend (Cloud Run) and frontend (Vercel)

---

## What Remains Weak

- No server-side persistence of in-progress turns; refresh loses state
- Optional: localStorage persistence of turns by session_id for refresh recovery

---

## Whether the Architecture Direction Is Correct

Yes. Formal session identity, complete state contract, clearer visibility. Reusable small-business intake backbone.

---

## Best Next Step

Optional: persist in-progress turns in localStorage keyed by session_id for refresh recovery. Or: lightweight server-side in-progress session storage.

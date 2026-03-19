# State / Workflow Backbone Phase 2 — Acceptance / SLA Criteria

---

## Continuity

- [ ] session_id accepted by POST /api/inbox/triage
- [ ] Frontend sends session_id when available (localStorage)
- [ ] conversation_id echoed in response when session_id provided (optional)

---

## State Clarity

- [ ] next_best_question present in triage result when handoff_ready=false and next ask exists
- [ ] lifecycle_status derived for case (handed_off, office_followup from case_status)
- [ ] All WORKFLOW_STATE_KEYS present in triage result

---

## Visibility

- [ ] UI shows "Collecting" vs "Ready for handoff" clearly
- [ ] Collected / Still needed visible when present
- [ ] Lifecycle/office status visible for persisted cases

---

## No Premature Completion

- [ ] First turn still uses triage_conversation; handoff only when threshold met
- [ ] Append still handoff_ready=true by design

---

## Office Usability

- [ ] Founder can inspect: what state, what collected, what missing
- [ ] No regression in existing flows

---

## Deferred

- Server-side persistence of in-progress turns
- Full append "still collecting" path
- SQL migration

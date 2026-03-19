# Execution Outline — Customer Entry Multi-Turn Continuity Audit

| Step | Task | Owner | Output |
|------|------|-------|--------|
| 1 | Create control docs | Planner | Blueprint, Outline, Acceptance Criteria |
| 2 | Reproduce founder-observed behavior | QA | Documented UI flow for example input |
| 3 | Frontend state audit | Frontend | How thread/handoff/continuation work; where continuity breaks |
| 4 | Backend / routing audit | Backend | handoff_ready, case_creation_suggested, workflow logic |
| 5 | Session / persistence audit | Session | conversation id, case id, thread model, append-message path |
| 6 | UX / product intent audit | UX | Intentional vs bug; design docs alignment |
| 7 | Optional probe | QA | Logging/inspection to confirm thread/case continuity |
| 8 | Final judgment | Planner | Root cause, fix direction, next sprint recommendation |

## Investigation Loops

Each loop: inspect code → reproduce behavior → trace state transitions → identify root cause → compare expected vs actual.

## Key Files

| Area | Path |
|------|------|
| Customer Entry UI | `ui/src/pages/UnifiedIntakePage.tsx` (CustomerEntryTab) |
| Inbox triage API | `services/fiqa_api/routes/inbox_triage.py` |
| Triage logic | `services/fiqa_api/inbox_triage/triage.py` |
| Case store | `services/fiqa_api/inbox_triage/case_store.py` |
| Design intent | `docs/MATURE_INTAKE_SKELETON.md`, `docs/CUSTOMER_ENTRY_REPLY_STRATEGY.md` |

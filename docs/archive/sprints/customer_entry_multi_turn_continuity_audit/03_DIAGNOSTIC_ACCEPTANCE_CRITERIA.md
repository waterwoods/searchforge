# Diagnostic / Acceptance Criteria — Customer Entry Multi-Turn Continuity Audit

## Must Answer Explicitly

- [ ] After the first user message, why does the UI look "finished"?
- [ ] Why is there no obvious next-turn continuation path in the same conversation?
- [ ] Is `handoff_ready` being triggered too early?
- [ ] Is `case_creation_suggested` or case persistence causing the UI to switch to end-state too soon?
- [ ] Is the frontend reusing a conversation/session/thread id across turns, or not?
- [ ] Is Customer Entry intentionally designed as "single-turn intake then handoff"?
- [ ] If the user wants to continue the same case, what currently happens?
- [ ] What should happen instead if we want true multi-turn continuity?

## Trace Requirements

- Trace first-message path: frontend submit → API payload → backend branch → handoff_ready
- Trace second-message path: conversation_turns sent? triage_conversation used?
- Trace UI state: when input hidden, when handoff card shown, when "提交新问题" clears thread

## Pass Criteria

- Root cause identified (primary + secondary)
- Minimum fix direction specified
- Next sprint recommendation (frontend / backend / session / combination)

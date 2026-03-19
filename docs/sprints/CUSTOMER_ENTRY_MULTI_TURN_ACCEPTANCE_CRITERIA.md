# Customer Entry Multi-Turn — Acceptance / SLA Criteria

**Sprint:** Customer Entry True Multi-Turn Repair + Guardrail Sprint

---

## 1. What Counts as True Multi-Turn

- First user message goes through `triage_conversation` (or equivalent conversation logic)
- `handoff_ready` is derived from `_should_handoff()` / collection thresholds, not forced
- System asks for the next missing field when info is incomplete
- Same thread/case is preserved across turns until handoff
- Handoff occurs when intake has reached a meaningful point (threshold met or customer turn count ≥ 2)

---

## 2. What Counts as Premature Handoff

- `handoff_ready=True` on first turn when `manual_followup_needed=True` and only one customer message
- Handoff before asking for at least one critical missing field (e.g. add-car without year/model)
- Case creation before handoff when conversation should continue

---

## 3. What Counts as Incorrect First-Turn Completion

- First reply is generic handoff message ("办公室会尽快处理") when more info is needed
- Frontend shows "done" or handoff card when system should ask for more
- Input hidden or disabled when conversation should continue

---

## 4. What Counts as Continuity Preserved

- Same conversation context used for subsequent turns
- `conversation_turns` passed correctly to API
- Frontend keeps input available when `handoff_ready=False`
- No hidden resets of conversation context

---

## 5. Acceptable Edge Behavior

| Edge | Acceptable |
|------|------------|
| **Talk to Agent** | Explicit human-handoff; `handoff_ready=True` on first turn is correct |
| **Add-car with full info** | First turn with year+model+zip → hand off immediately (MATURE_INTAKE_SKELETON) |
| **Informational / renewal reminder** | `manual_followup_needed=False` → hand off |
| **triage_for_append** | Broker pastes into existing case; always handoff-ready (broker receives update) |

---

*End of acceptance criteria*

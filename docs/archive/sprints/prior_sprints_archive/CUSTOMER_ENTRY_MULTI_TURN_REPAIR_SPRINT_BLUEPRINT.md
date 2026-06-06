# Customer Entry True Multi-Turn Repair — Sprint Blueprint

**Sprint:** Customer Entry True Multi-Turn Repair + Guardrail Sprint  
**Created:** 2026-03-15  
**Status:** In progress

---

## 1. Why This Continuity Repair Matters Now

The founder discovered that Customer Entry behaves like **one-shot intake** instead of **true multi-turn intake**:

- First user message → immediate case/handoff
- No real ongoing conversation
- System does not ask for the next missing thing before handing off

The intended product is **human-first, answer-first, next-missing-info, true multi-turn intake**, with case creation / handoff at the appropriate moment—not immediately.

---

## 2. What Was Wrong in the Old Design

| Issue | Location | Behavior |
|-------|----------|----------|
| **First-turn bypass** | `routes/inbox_triage.py` | When `conversation_turns` is empty, route uses `triage_message()` instead of `triage_conversation()`, then **forces** `handoff_ready=True` |
| **Forced completion** | Same | First message never goes through `_should_handoff()` logic; handoff is assumed |
| **Single-turn demo shortcut** | Legacy | Route was built for one-shot demo; multi-turn path added later but first-turn kept the shortcut |

The audit identified: first message bypasses `triage_conversation`, `handoff_ready=true` is forced, frontend treats the flow as complete and shows handoff card.

---

## 3. Intended Multi-Turn Model

From `docs/MATURE_INTAKE_SKELETON.md`:

1. **Detect** likely intent
2. **Ask** the next most useful thing (1–2 focused questions)
3. **Decide** if enough info is collected (`_should_handoff`)
4. **Hand off** with summary/context when appropriate

`_should_handoff()` in `triage.py`:
- `manual_followup_needed=False` → hand off
- `customer_turn_count >= 2` → hand off
- Otherwise → **do not** hand off (ask for more)

First turn with `manual_followup_needed=True` should return `handoff_ready=False` and ask for the next missing field.

---

## 4. What Success Looks Like

| Scenario | Before | After |
|----------|--------|-------|
| Quote / add-car first turn | handoff_ready=True, done | handoff_ready=False, asks for year/model/zip |
| Payment first turn | handoff_ready=True | handoff_ready=False if more info needed |
| Missing-doc first turn | handoff_ready=True | handoff_ready=False if item/sent status unclear |
| Button starter | Same forced handoff | Preserves continuity; asks next thing |
| Talk to Agent | handoff_ready=True (correct) | Unchanged (explicit human-handoff exception) |

---

## 5. Implementation Summary

**Primary fix:** Route always uses `triage_conversation(text, turns)`—including first message with `turns=[]`. Remove the branch that uses `triage_message()` and forces `handoff_ready=True`.

**Persistence:** Only persist when `handoff_ready=True` to avoid creating premature cases and duplicate cases across turns.

**Guardrail:** Document the rule so future workers do not reintroduce single-turn demo behavior.

---

*End of blueprint*

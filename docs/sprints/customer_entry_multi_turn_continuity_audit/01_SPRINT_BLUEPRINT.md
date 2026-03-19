# Sprint Blueprint — Customer Entry Multi-Turn Continuity Audit

**Sprint name:** Customer Entry Multi-Turn Continuity Audit Sprint  
**Execution mode:** Structured diagnostic / investigation  
**Target budget:** 20–40 minutes  
**Scope:** Chen Kui Insurance Unified Entry — Customer Entry tab

---

## Mission

Investigate why Customer Entry currently feels like single-turn intake + case handoff, instead of a true continuous multi-turn conversation.

## Founder Observation

After asking one question, the UI appears to generate a case/handoff card and shows buttons like:
- 查看工作台
- 提交新问题

This makes the experience feel like:
- one-shot intake
- not a continuous multi-turn thread
- user must ask a new question instead of continuing naturally

## Key Questions

1. Is Customer Entry currently designed as single-turn-by-default?
2. Where exactly does continuity break?
3. Is the break caused by frontend state, backend handoff logic, session/conversation persistence, or UX design?
4. What is the minimum fix direction?

## Working Method

- **Phase A:** Control docs (Blueprint, Execution Outline, Diagnostic Criteria)
- **Phase B:** Multi-agent investigation (frontend, backend, session, UX)
- **Phase C:** Inspect → trace → verify → explain loops
- **Phase D:** Final convergence — root cause, fix direction

## Success Criteria

- Explicit answer to each key question
- Root cause identified (primary + secondary)
- Minimum high-value fix direction recommended
- Founder-readable summary block

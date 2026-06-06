# Handoff Timing Audit Blueprint

**Sprint:** Broker Trial Simulation + Handoff Timing Audit  
**Created:** 2026-03-19  
**Scope:** SearchForge → Chen Kui Insurance Unified Entry

---

## 1. Why Handoff Timing Matters Now

The product is strong in scenario package, client-aware wiring, trial preparation, workbench, mixed-intent visibility, broker-style simulation, and scenario logic center. **One likely remaining weakness:** handoff may happen before the customer has fully finished saying what matters.

This can create:
- Incomplete cases
- Broker extra work
- Customer frustration
- Lower trust during real trial

Before real broker trial, the team needs a focused audit of handoff timing.

---

## 2. Why This Is the Right Move Before Real Broker Trial

- All existing simulation packs pass (64 inbox, 41 multi-turn, 27 adversarial, 23 complex, 27 sim assistant, 5 append, 8 broker stress).
- **But:** passing scenarios does not prove handoff timing is correct.
- The current rule: `customer_turn_count >= 2` → handoff for non-add-car. Add-car uses field-based thresholds.
- Risk: customer adds "还有一个问题" or "对了" or "顺便问一下" in turn 3 — we never see it because we handed off at turn 2.

---

## 3. What This Sprint Will Strengthen

- Realistic simulation set focused on handoff timing
- Clear evidence of where handoff is too early / acceptable / too late
- Practical classification of handoff timing risks
- 1–2 small fixes applied if justified
- Stronger confidence before real broker-style use

---

## 4. What This Sprint Intentionally Will NOT Do

- Broad new feature development
- Redesign of the whole workflow engine
- Advanced state machine frameworks
- Broad platform refactors
- Optimization for "fast handoff" alone

---

## 5. Core Principle

**Do NOT assume current handoff timing is correct just because scenarios pass.**

The correct goal: **handoff at the right time, with enough useful information, without making the user feel cut off.**

---

*End of Blueprint*

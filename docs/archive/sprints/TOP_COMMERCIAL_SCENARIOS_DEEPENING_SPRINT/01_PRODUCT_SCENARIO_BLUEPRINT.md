# Top Commercial Scenarios Deepening — Product / Scenario Blueprint

**Sprint:** Top Commercial Scenarios Deepening Sprint  
**Date:** 2026-03-17  
**Execution:** Cursor Composer

---

## 1. Why Deeper-Turn Scenario Hardening Matters Now

The founder correctly identified that the system is much better than before, but still sometimes feels simulated because:
- Turn 1 is okay
- Turn 2 is okay
- **Turn 3 / 4 can still feel shallow, generic, or too eager to hand off**

That means the next highest-value move is: **deepen the most commercially important scenarios into more natural later-turn flows**. This is where real product trust is won or lost.

## 2. Why This Is the Correct Move Before Real Pilot

If the product can survive 3rd–4th turn business interactions naturally, it becomes much more credible for paid pilot use. The sprint targets:
- Better follow-up after partial user answers
- Better correction handling
- More natural confirmation language
- Less robotic "I already know you" behavior
- Better handoff timing after enough useful information is collected
- Better case summary value for broker handoff
- Fewer points where broker must manually re-ask obvious questions

## 3. What This Sprint Will Strengthen

| Area | Target |
|------|--------|
| Add-car driver correction | LC-AC3: "我刚才说错了，是我老婆开那辆" — capture driver at T3 |
| Add-car driver ask | When zip+delivery at T2, ask for driver before handoff |
| Billing multi-turn | T2 "我发你了" → already_sent handoff |
| Summary | Capture "说错了" corrections in context_hint |
| Driver extraction | "我老婆开", "老公开", "我开" → driver=True |

## 4. What This Sprint Intentionally Will Not Do

- Add lots of new scenarios
- Improve only first-turn classification
- Spread effort evenly across too many things
- Add random new features
- LC-AC3 was the only friction case; billing multi-turn was deferred in Phase 2 — now addressed

---

*Aligned with MATURE_INTAKE_SKELETON, DEEP_MULTI_TURN_TARGET, LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.*

# Hybrid Unified Entry — Structured Intake Flow Spec

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15

---

## 1. Button-Guided Flow Behavior

When user selects a button before typing:

| Step | Behavior |
|------|----------|
| 1 | Store `soft_route` = button intent (e.g., add_car, claim_intake) |
| 2 | User types message |
| 3 | Triage receives: `text` + optional `soft_route` |
| 4 | If text intent matches soft_route → proceed normally |
| 5 | If text intent conflicts with soft_route → reroute, acknowledge, clear soft_route |
| 6 | If text is ambiguous → use soft_route as tiebreaker |

**Important**: Button does not force the flow. It only provides a hint. Text is truth.

---

## 2. Free-Text-First Behavior

When user types without selecting a button:

| Step | Behavior |
|------|----------|
| 1 | No soft_route |
| 2 | Triage infers intent from text only |
| 3 | Same detect → ask → enough? → handoff flow as today |

No change to existing triage logic when soft_route is absent.

---

## 3. One-Question-at-a-Time Principle

| Rule | Meaning |
|------|---------|
| Per turn | Ask for 1–2 next useful things only |
| No overload | Do not list 6 items at once |
| Focused | "请提供ZIP码" not "请提供ZIP、提车日期、驾驶人..." in one breath |

Already in MATURE_INTAKE_SKELETON. Preserved.

---

## 4. Answer-First / Reassure-First Behavior

| Scenario | Action |
|----------|--------|
| User asks "什么意思" | Answer the question first, then hand off or collect |
| User says "急死了" | Reassure first ("别着急，我们先帮您看看") then route |
| User asks "最要紧做什么" | Answer next step first, then hand off |
| User says "发过了" | Acknowledge ("好的，收到了") then hand off |

From LIGHTWEIGHT_STATE_MACHINE follow_up_type strategy. Preserved.

---

## 5. Missing Info Collection Rules

| Stage | Behavior |
|-------|----------|
| Collecting | Ask for next critical field |
| Enough | Hand off; do not over-question |
| Partial | If one critical field would materially improve case, ask for it |

From MATURE_INTAKE_SKELETON handoff thresholds. Preserved.

---

## 6. Uncertainty / Human Confirmation Rules

| Case | Behavior |
|------|----------|
| VIN, payment status, customer_says_sent | Mark "Human confirmation recommended" |
| Never commit to premium number | Broker must verify |
| Never say "carrier received" when customer said they sent | Broker must verify |

From LIGHTWEIGHT_STATE_MACHINE. Preserved.

---

## 7. Flow Summary

```
[User arrives]
    → See welcome + 5 buttons + free-text input
    → Option A: Click button (soft_route set) then type
    → Option B: Type only (no soft_route)
[User sends message]
    → Triage(text, soft_route?)
    → If conflict: reroute, acknowledge
    → If match or no route: proceed
[Detect → Ask → Enough? → Hand off]
    → Same as today
[Hand off]
    → Suggest case creation
    → User can view workbench or start new
```

---

*See also: MATURE_INTAKE_SKELETON.md, LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md*

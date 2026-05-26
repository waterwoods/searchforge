# Add-Car Quote Excellence — Execution Outline

**Sprint:** Add-Car Quote Excellence  
**Purpose:** Workstreams, implementation order, loop plan, validation.

---

## 1. Workstreams

| WS | Area | Scope |
|----|------|-------|
| WS1 | Field collection / ask-next | add_car_rules ask_driver_only; ask order verification |
| WS2 | Handoff / broker actionability | broker_next_step with concrete vehicle; conversation_summary enhancement |
| WS3 | Add-car excellence simulations | New simulation pack; correction, ZIP change, coverage side question |
| WS4 | Mixed-intent coverage | "顺便 coverage 可以调吗" — brief answer, hand off |

---

## 2. Implementation Order

1. **Baseline audit** — Document current strengths/weaknesses
2. **Loop 1** — WS1: ask_driver_only in config; verify ask-next quality
3. **Loop 2** — WS2: broker_next_step + conversation_summary with concrete vehicle
4. **Loop 3** — WS3 + WS4: add-car simulations; coverage side-question handling

---

## 3. Loop Plan

| Loop | Focus | Validation |
|------|-------|------------|
| 1 | Field collection / ask-next | guardrail_inbox_triage.sh, run_multi_turn_simulations.py |
| 2 | Handoff / broker actionability | Same + manual broker_next_step check |
| 3 | Add-car excellence simulations | New add_car_excellence_simulations.json + runner |

---

## 4. Validation / Deployment Approach

- **Pre-loop:** Run guardrail_inbox_triage.sh, run_multi_turn_simulations.py, run_handoff_timing_simulations.py
- **Post-loop:** Same; add run_add_car_excellence_simulations.py if new pack
- **Deploy:** Backend only if triage.py changed; no frontend changes expected

---

*See also: 06_ACCEPTANCE_CRITERIA.md, 07_FOUNDER_INSPECTION_NOTES.md*

# Top Scenarios Hardening — Product / Scenario Blueprint

**Sprint:** Top Scenarios Hardening Master Sprint  
**Created:** 2026-03-17  
**Scope:** Chen Kui Insurance Unified Entry

---

## 1. Why Top Scenarios Hardening Matters Now

The product has a solid backbone:
- Customer entry, workbench, multi-turn continuity
- workflow_state, lifecycle visibility, in-progress persistence
- Case creation and follow-up backbone

The founder correctly observes: **the system can still feel "too simple" or "too wrong" when users ask real-world questions outside narrow demo phrasing.**

The next most valuable move is not more generic platform work. It is: **hardening the top scenarios that actually drive merchant value.**

## 2. Why the Backbone Is Now Sufficient

- 53/53 inbox triage scenarios pass
- 38/38 multi-turn simulations pass (all Strong)
- State/field accuracy audit: 7/7 passed
- Speed routing verified
- Full guardrail passes (adversarial, complex adversarial, simulation assistant)

The backbone can support scenario hardening without structural changes.

## 3. What This Sprint Will Strengthen

1. **Phrasing coverage** — Add driver, bundling, premium-vs-payment disambiguation
2. **Next-best-question** — More robust field extraction for edge phrasings
3. **Answer-first / reassure-first** — Reduce generic "这段内容还不够完整" for clear intents
4. **Routing clarity** — Premium + "我发你账单了" must not route to payment_lapse_expiration
5. **Handoff timing** — LC-AC3 (driver correction) edge case
6. **Case summary quality** — Already strong; minor refinements

## 4. What This Sprint Intentionally Will NOT Do

- No new platform features
- No UI polish unrelated to scenario handling
- No multi-tenant, auth, Stripe
- No broad refactor
- No coverage of every possible edge case — focus on highest-value gaps

---

*See: 02_TOP_SCENARIOS_SELECTION_SPEC.md*

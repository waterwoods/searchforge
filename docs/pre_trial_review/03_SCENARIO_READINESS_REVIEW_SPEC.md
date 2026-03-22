# Scenario Readiness Review Spec

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18

---

## 1. Scenarios to Assess

| Scenario | SIM IDs | Maturity (Logic Center) | Assess |
|----------|---------|-------------------------|--------|
| Add-car / Quote | SIM3, SIM4, SIM15, ER1–2, AC-ULTRA | strong | Route, ask-next, handoff, broker_next_step |
| Remove vehicle / Policy change | SIM8, ER3, FAQ-RM1, TSH2-RV1 | medium | Route correctness; handoff timing |
| Material collection / Already sent | SIM2, SIM8, D3, F4, FAQ-AS1, R7 | strong | Verify receipt; already_sent visibility |
| Payment / Cancellation risk | SIM1, SIM7, SIM9, R3–12 | strong | Urgency; same-day action |
| Renewal increase / Premium review | SIM6, D1–2, R13, TSH2-RN1 | strong | Retention follow-up |
| Billing clarification | TSH2-BC1–2, TSH-PR1 | medium, fix_next | Route vs payment_lapse |
| Claim first notice | SIM5, F1–2, TSH2-CL1 | strong | First-response; collected/still-needed |
| Talk to Agent | R3b | strong | Client config; immediate handoff |

---

## 2. Assessment Dimensions

| Dimension | What to check |
|-----------|---------------|
| **Route correctness** | Does message route to right scenario? |
| **Ask-next quality** | Does system ask 1–2 useful things, not overload? |
| **Handoff timing** | Does handoff occur when enough info collected? |
| **broker_next_step usefulness** | Is it operational, actionable, not generic? |
| **Trial risk** | Trust-breaking? High friction? |

---

## 3. Guardrail Evidence (2026-03-18)

| Check | Result |
|-------|--------|
| Scenario pack | OK |
| Rule-based (64 scenarios) | 64/64 passed |
| Multi-turn (41 simulations) | 41/41 passed |
| Simulation Assistant (27 SIM) | 27 Normal, 0 Needs review, 0 Off-flow |
| Client-aware handoff | PASS |
| Client identity persistence | PASS |
| API test (append) | 1 fail when server not on 8001 (route may need restart) |

---

## 4. Per-Scenario Judgment Template

For each scenario:

- **Strong enough for trial:** Route correct; ask-next good; handoff timing right; broker_next_step useful; low trial risk
- **Usable with caution:** Minor gaps; broker should verify; watch during first 3–5 conversations
- **Weak / defer:** Route unreliable; handoff wrong; broker_next_step generic; do not include in first trial

---

*End of Scenario Readiness Review Spec*

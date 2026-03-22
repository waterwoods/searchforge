# Trial Scope Review Spec

**Sprint:** Pre-Trial Review Sprint  
**Created:** 2026-03-18

---

## 1. Purpose

Define what is included and excluded in the first real broker trial, based on current system readiness.

---

## 2. Included Product Surfaces (Confirmed)

| Surface | Status | Notes |
|--------|--------|-------|
| Customer Entry (paste box) | ✅ | Primary entry; multi-turn conversation |
| Case handoff card | ✅ | Case focus, next move, Collected, Still needed |
| Broker Workbench | ✅ | Queue, status, follow-up, reopen |
| Load founder demo queue | ✅ | Seeds 13 demo cases |
| Simulation Assistant | ✅ | 15 trial scenarios |
| Copy to client | ✅ | Copy draft to clipboard |

---

## 3. Included Scenario Types (From Trial Scope Definition)

| # | Scenario | Trial order | Why included |
|---|----------|-------------|--------------|
| 1 | Cancellation risk / payment failed | 1 | Urgency, same-day action |
| 2 | Missing document / already sent | 2 | Operational pain; verification |
| 3 | Add-car quote | 3 | Revenue; multi-turn; Collected |
| 4 | Premium review / renewal | 4 | Retention |
| 5 | Claim intake | 5 | First-response guidance |
| 6 | Billing clarification | Extended | Payment risk; fix_next |
| 7 | Talk to Agent | Always available | Customer wants human |

---

## 4. Excluded / Deferred

- Email/WeChat/SMS integration
- OCR upload
- Full CRM
- Multi-tenant
- Stripe billing
- Carrier API integration
- DMV/SR-22 deep-dive (unless broker asks)
- Bundling (weak; defer)

---

## 5. First Trial Scope Decision (Pre-Review)

**Recommended:** 3–5 flows for first trial.

- **Must include:** SIM1 (cancellation), SIM2 (missing doc), SIM3 (add-car)
- **Include if time:** SIM6 (premium review), SIM5 (claim)
- **Exclude from first trial:** Billing clarification (fix_next); Talk to Agent (available but watch closely)

---

*End of Trial Scope Review Spec*

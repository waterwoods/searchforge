# Acceptance / Sellability Criteria

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17

---

## 1. Talk to Agent Usefulness

| Criterion | Pass |
|-----------|------|
| Button always visible | Yes |
| Free-text "联系人工" routes to handoff | Yes |
| Reassuring reply: "已帮您转给办公室，他们会尽快联系您" | Yes |
| No "Are you sure?" friction | Yes |
| Office sees "Customer requested human contact" | Yes |

---

## 2. Customer Reassurance

| Criterion | Pass |
|-----------|------|
| Handoff reply feels formal, not generic | Yes |
| Customer knows request was received | Yes |
| No sense of "escape hatch" — feels like upgrade path | Yes |

---

## 3. Office Usability

| Criterion | Pass |
|-----------|------|
| Case focus shows "联系人工" for customer_requested_human | Yes |
| broker_next_step actionable | Yes |
| Recent customer messages visible | Yes |
| Correction / already_sent badges when applicable | Yes |

---

## 4. Edge-Case Handling Quality

| Criterion | Pass |
|-----------|------|
| Billing "我发你了" → already_sent handoff | Yes |
| Talk to Agent mid-flow (free-text) → handoff | Yes |
| Late correction visible in workbench | Yes (verify) |

---

## 5. Reduced Trust-Breaking Moments

| Criterion | Pass |
|-----------|------|
| No re-asking after "我发你了" when already_sent | Yes |
| No ignoring "联系人工" when typed | Yes |
| Correction survives handoff | Yes |

---

## 6. Pilot-Readiness

| Criterion | Pass |
|-----------|------|
| All guardrail scripts PASS | Yes |
| Inbox triage scenarios pass | Yes |
| Multi-turn simulations pass | Yes |
| UI build succeeds | Yes |

---

## 7. What Remains Acceptable to Defer

- Mixed-intent + human escalation (e.g. "加车报价，但我想跟人说")
- Inbox/WeChat integration
- Full CRM, multi-tenant, Stripe

---

*End of Acceptance / Sellability Criteria*

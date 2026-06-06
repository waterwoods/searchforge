# Hybrid Unified Entry — Acceptance / SLA Criteria

**Sprint**: Hybrid Unified Entry System  
**Created**: 2026-03-15

---

## 1. What Must Be True for This Sprint to Count as Success

| Criterion | Required |
|-----------|----------|
| Welcome message visible on first load | Yes |
| 5 quick-start buttons visible and clickable | Yes |
| Free-text input always visible and prominent | Yes |
| Selected button shows active state | Yes |
| User can type without selecting a button | Yes |
| User can select button then type | Yes |
| Customer Entry feels more welcoming than before | Yes |
| Broker Workbench remains clearly office-side | Yes |

---

## 2. UX Improvement Required

| Before | After |
|--------|-------|
| Single text area, "需要示例？" | Welcome + 5 buttons + free text |
| No guided start | Buttons provide guided start |
| Feels like paste-only lab | Feels like product intake surface |

**Founder test**: "Does this feel more like a real SaaS intake than a lab tool?" → Must be Yes.

---

## 3. Routing/State Behavior That Must Work

| Scenario | Expected |
|----------|----------|
| User clicks "Get a Quote", types add-car message | Proceeds in add_car flow |
| User clicks "Payment", types add-car message | Reroute to add_car (when implemented); or at least no forced payment flow |
| User types only, no button | Same as today; triage from text |
| User deselects button | Soft context cleared |

**Loop 1**: Buttons set soft context; rerouting can be Loop 2.

---

## 4. What Would Count as Too Confusing

| Anti-pattern | Avoid |
|--------------|-------|
| Buttons lock the user into a flow | Buttons must be soft only |
| Free text hidden or de-emphasized | Free text must remain prominent |
| Too many buttons or options | 5 is the limit |
| Long welcome paragraph | One short line |
| Case creation forced without user awareness | Suggest, don't auto-create without context |

---

## 5. What Would Count as Too Much Scope

| Out of scope | Do not implement |
|--------------|-------------------|
| Full rerouting backend logic | Can defer to Loop 2 |
| Multi-language toggle | Chinese + English labels sufficient |
| A/B testing infrastructure | Not needed |
| Full case-creation confirmation flow | Simple suggestion is enough |
| New triage categories | Use existing |

---

## 6. SLA Summary

- **Must have**: Welcome + 5 buttons + free text + selected state + customer-friendly feel
- **Should have**: Soft-route sent to API when button selected
- **Nice to have**: Rerouting acknowledgment (Loop 2)
- **Out of scope**: Hard routing, new categories, A/B testing

---

*See also: Founder Demo/Inspection Notes*

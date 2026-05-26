# Add-Car Identity + Contact Lite — Execution Outline

**Sprint:** Add-Car Identity + Contact Lite  
**Purpose:** Workstreams, implementation order, simulation/validation, deployment.

---

## 1. Workstreams

| # | Workstream | Owner | Scope |
|---|------------|-------|-------|
| 1 | Contact extraction | Backend | Extract name/phone from customer messages; add to collected/still_needed |
| 2 | Case persistence | Backend | Populate customer_name/phone when triage extracts them |
| 3 | broker_next_step | Backend | Add contact hint when quote-ready but contact missing |
| 4 | Workbench contact block | Frontend | Display name/phone; show "needed" when missing |
| 5 | Add-car simulations | Config | Add contact-lite scenarios (name/phone in chat, missing, etc.) |

---

## 2. Implementation Order

1. **Loop 1:** Contact extraction + collected/still_needed for add-car; case save with extracted contact
2. **Loop 2:** broker_next_step contact hint; Workbench contact block UI
3. **Loop 3:** Add-car contact simulations; harden scenarios

---

## 3. Simulation / Validation Plan

- **guardrail_inbox_triage.sh** — must pass
- **run_multi_turn_simulations.py** — add MT46–MT50 for contact-lite (name in chat, phone in chat, both missing, etc.)
- **ui build** — `cd ui && npm run build`

---

## 4. Deployment Approach

- Backend: redeploy if triage/case_store changed
- Frontend: redeploy if UnifiedIntakePage changed
- No database migration; JSON case store already has customer_name, customer_phone

---

*See also: 06_ACCEPTANCE_IDENTITY_CONTACT_CRITERIA.md, 07_FOUNDER_INSPECTION_NOTES.md*

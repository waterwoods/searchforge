# Add-Car Quote 80% Completion Deploy Sprint — Blueprint

**Sprint:** Add-Car Quote 80% Completion Deploy Sprint  
**Date:** 2025-03-16  
**Mode:** Deployment-only, no new feature scope

---

## 1. Why Deployment Is Needed Now

The Add-Car Quote 80% Completion sprint improved the default add-car quote flow:

- **Handoff is no longer too early** — zip alone is not enough; office needs delivery or driver context for quote
- **Richer extraction** — insurance_status (add_to_existing, new_customer), additional_drivers
- **Flow continues** — after ZIP, system asks for delivery/driver before handoff

This is only valuable if it is **live in production**. The founder needs to inspect the improved flow on Vercel.

---

## 2. What Must Be Live

| Component | What |
|-----------|------|
| **Backend** | `_add_car_enough_for_handoff` = vehicle + zip + (delivery or driver); `_get_next_ask_for_add_car` asks delivery/driver when zip-only |
| **Config** | `configs/simulation_assistant_scenarios.json`, `configs/customer_entry_multi_turn_simulations.json` aligned with 80% completion |
| **Frontend** | `ui/src/config/simulation_assistant_scenarios.json` in sync; Simulation Assistant + Broker Workbench pointing at production backend |

---

## 3. What Counts as Success

- Backend deployed to Cloud Run; health/readyz OK
- Add-car first turn ("我想加一台X5") → asks for ZIP or next missing thing, NOT immediate handoff
- Add-car second turn ("90210") → asks delivery/driver if still missing, NOT immediate handoff
- Add-car third turn (delivery or driver) → then handoff
- Founder can go to Vercel and inspect the new behavior

---

*See: EXECUTION_OUTLINE.md, ACCEPTANCE_CRITERIA.md*

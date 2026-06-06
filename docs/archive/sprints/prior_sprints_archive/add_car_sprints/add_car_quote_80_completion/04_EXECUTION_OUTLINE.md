# Add-Car Quote 80% Completion — Execution Outline

**Sprint:** Add-Car Quote 80% Completion  
**Purpose:** Workstreams, implementation order, test plan, loop count.

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| **WS1: Slot extraction** | Backend | Add insurance_status, additional_drivers to _extract_add_car_fields |
| **WS2: Handoff threshold** | Backend | Require zip + (delivery or driver) — no zip-only handoff |
| **WS3: Next-ask logic** | Backend | Extend _get_next_ask_for_add_car with insurance_status, additional_drivers |
| **WS4: First-turn template** | Config | Softer first ask: 1–2 items, not 6 at once |
| **WS5: Structured fields** | Backend | Add new slots to collected/still_needed output |
| **WS6: Scenarios** | QA | Add Add-Car scenarios for new branches |

---

## 2. Implementation Order

**Loop 1 (highest value):**
1. WS2 — Stricter handoff (zip required; delivery or driver required)
2. WS3 — Richer next-ask (ask delivery when zip+vehicle but no delivery/driver)
3. WS1 — Add insurance_status, additional_drivers extraction (detect only, no ask yet)
4. Run validation

**Loop 2 (refinement):**
1. WS3 — Add "additional drivers?" ask when vehicle+zip+delivery present
2. WS4 — Improve first-turn template (ask year+zip first, not 6 items)
3. WS5 — Wire new slots to collected/still_needed
4. Run validation

**Loop 3 (optional):**
1. WS3 — Add insurance_status ask when ambiguous
2. WS6 — Add regression scenarios
3. Final validation

---

## 3. Test Plan

| Test | When | Command |
|------|------|---------|
| Inbox triage | After each loop | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` |
| Multi-turn sims | After each loop | `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` |
| State field accuracy | After loop 2 | `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` |
| Speed routing | After loop 2 | `PYTHONPATH=. python3 scripts/verify_speed_routing.py` |
| Guardrail | After loop 2 | `bash scripts/guardrail_inbox_triage.sh` |
| Smoke check | Final | `bash scripts/unified_intake_smoke_check.sh` |

---

## 4. Likely Loop Count

- **Loop 1:** Must run — core flow depth + handoff
- **Loop 2:** Must run — business quality + first-turn
- **Loop 3:** Optional — insurance_status ask, edge cases

---

*See also: 05_ACCEPTANCE_SLA_CRITERIA.md*

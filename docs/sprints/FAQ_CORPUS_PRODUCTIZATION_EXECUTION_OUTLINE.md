# FAQ Corpus Productization — Execution Outline

**Sprint:** FAQ Corpus Productization  
**Target budget:** 45–90 minutes

---

## Selection Process

1. **Score corpus items** on: frequency, business relevance, pilot/demo usefulness, routing clarity, scenario usefulness, small-client understanding.
2. **Apply filters:** Exclude purely informational (renewal_reminder, policy_delay, informational_done) from "productization" — they are already FAST and low-value for scenario depth.
3. **Select 5–8** with mix of:
   - High-frequency (new_car_quote, payment_failed, cancellation_warning, missing_document)
   - High-urgency (cancellation_warning, payment_failed, underwriting_followup)
   - Scenario-rich (claim_intake, notice_confusion, premium_too_high)
   - FAST candidates (already_sent_followup, what_to_send, add_car_field_followup)

---

## Productization Targets

| Target | Deliverable |
|--------|-------------|
| **Simulation Assistant** | 5–8 scenarios (new or improved) with realistic phrasing, 2–3 turn structure |
| **FAST path** | Strengthen triage.py for already_sent, what_to_send, add_car_field where rule-safe |
| **FAQ handling matrix** | configs/docs/faq_handling_matrix.md — customer asks → office says → still need → route |
| **Founder examples** | One block per selected type in final report |

---

## Routing / Handling Work

- **FAST:** already_sent_followup (Q07), what_to_send (Q12), add_car_field_followup (Q11), handoff_confirmation (Q18)
- **LLM:** new_car_quote (Q01), payment_failed (Q04), cancellation_warning (Q05), missing_document (Q06), notice_confusion (Q08), premium_too_high (Q03), claim_intake (Q10), remove_car (Q02)
- **Human confirmation:** moving_zip_change (Q21), adding_driver (Q22) — policy changes affecting rate

---

## Simulation / Testing Plan

1. **run_inbox_triage_scenarios.py** — single-turn inbox triage
2. **run_multi_turn_simulations.py** — customer_entry_multi_turn_simulations.json
3. **run_simulation_assistant_scenarios.py** — simulation_assistant_scenarios.json
4. **audit_state_field_accuracy.py** — structured field accuracy
5. **verify_speed_routing.py** — FAST vs LLM path
6. **guardrail_inbox_triage.sh** — full guardrail
7. **unified_intake_smoke_check.sh** — smoke flow (if server running)

---

## Likely Loop Count

- **Loop 1:** Select 5–8, implement first slice, run validation
- **Loop 2:** Improve weak scenarios, tighten routing, sharpen founder examples
- **Loop 3:** Optional — only if clear high-value, low-risk refinement remains

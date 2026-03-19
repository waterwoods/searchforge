# Scenario Inventory Spec

**Sprint:** Scenario Logic Center Sprint  
**Created:** 2026-03-18  
**Purpose:** Define the important scenarios to include in the center and what each scenario card/section should show.

---

## 1. Scenarios to Include (Minimum)

| # | Scenario | Business goal | Standard package |
|---|----------|---------------|------------------|
| 1 | **Add-car / Quote** | New vehicle quote; revenue; high-frequency | ✓ #1 |
| 2 | **Remove vehicle / Policy change** | Add/remove vehicle; routine | ✓ #2 |
| 3 | **Add driver** | Add household driver; routine | (extended) |
| 4 | **Material collection / Already sent** | Missing document; client says already sent; common pain | ✓ #3 |
| 5 | **Payment / Already paid** | Payment failed; cancellation risk; same-day action | ✓ #5 (billing) |
| 6 | **Billing clarification** | Bill confusion; distinct from payment failure | (extended) |
| 7 | **Renewal increase / Premium review** | Premium too high; retention | ✓ #4 |
| 8 | **Claim first notice** | Accident; hit-and-run; first-response guidance | ✓ #6 |
| 9 | **Talk to Agent / Human handoff** | Customer wants human; broker takes over | ✓ #7 |
| 10 | **Cancellation warning** | Policy will cancel; critical urgency | (core) |
| 11 | **English notice confusion** | Client can't read English notice; ask for full notice | (core) |
| 12 | **DMV / SR-22 help** | DMV notice; suspension; SR-22 filing | (extended) |
| 13 | **Bundling** | Home + auto discount; lower priority | (extended) |
| 14 | **Unclear** | Ambiguous; broker should clarify | (fallback) |

---

## 2. Per-Scenario Definition (What Each Card Shows)

For each scenario define:

| Field | Purpose |
|-------|---------|
| **scenario_name** | Display name (e.g. "Add-car / Quote") |
| **business_goal** | Why it matters (revenue, retention, urgency) |
| **common_customer_phrasing** | Example phrases that trigger this scenario |
| **main_route** | How it's detected (markers, LLM, rules) |
| **next_best_question** | What the system asks next (1–2 things) |
| **handoff_timing** | When enough info → hand off |
| **broker_next_step** | One operational sentence for broker |
| **current_maturity** | strong / medium / weak |
| **fix_now / fix_next / defer** | If applicable |
| **config_layer** | common / industry / client |

---

## 3. Mapping to Existing Sources

| Scenario | markers.json | category_templates | reply_templates | triage.py |
|----------|---------------|--------------------|-----------------|-----------|
| Add-car | add_vehicle, vehicle_context | (customer_question sub) | add_car | _add_car_enough_for_handoff |
| Remove vehicle | remove_vehicle | (customer_question sub) | remove_vehicle | _is_remove_vehicle_request |
| Add driver | add_driver | (customer_question sub) | (generic) | _is_add_driver_request |
| Missing document | missing_document_* | missing_document | missing_document | _build_customer_question_missing_doc |
| Payment / Cancellation | payment, strong_cancellation | payment_lapse_expiration, cancellation_warning | payment_lapse_expiration, cancellation_warning | _is_payment_* |
| Premium review | premium_review | (customer_question sub) | premium_review | _is_premium_review_request |
| Claim intake | claim_intake | (customer_question sub) | claim_intake | _is_claim_intake_request |
| Talk to Agent | talk_to_agent | customer_requested_human | (handoff) | _is_talk_to_agent_request |
| English notice | question_help + notice | (customer_question sub) | english_notice_confusion | _build_customer_question_* |
| DMV / SR-22 | dmv_help | (customer_question sub) | (generic) | _is_sr22_help_request |
| Bundling | bundling | (customer_question sub) | (generic) | _is_bundling_request |
| Unclear | (fallback) | unclear | (generic) | _classify_with_guardrails |

---

## 4. Why These Scenarios Were Selected

- **Standard package 7** — Canonical sellable set
- **Trial top 5** — SIM1–SIM5; highest trial value
- **Inbox triage categories** — What the system actually classifies to
- **Fix-now relevance** — Scenarios that appear in fix-now/fix-next/defer

---

*See also: `configs/inbox_triage_scenarios.json`, `configs/simulation_assistant_scenarios.json`, `docs/STANDARD_SCENARIO_PACKAGE.md`*

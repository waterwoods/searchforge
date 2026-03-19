# Eight-Question Integration Audit — Acceptance / Audit Criteria

**Sprint:** Eight-Question Integration Audit + Fix Sprint

---

## What Must Be True for "Truly Integrated"

For each of the 8 question types, ALL of the following must hold:

1. **Docs present** — In faq_handling_matrix.md and/or auto_insurance_faq_intake_corpus.json
2. **Handling matrix present** — Explicit handling framework (customer asks → office says → still need → route)
3. **Backend logic present** — triage.py classifies correctly (direct category or customer_question sub-type)
4. **Scenario present** — At least one inbox_triage or multi-turn scenario with expected_category
5. **Simulation Assistant visible** — At least one scenario with matching flow_type in recommended/real/edge
6. **Frontend-visible / demo-ready** — Founder can open Simulation Assistant and run a scenario for this type
7. **Realism quality** — Phrasing is realistic (strong / acceptable / weak)

---

## What Counts as Docs-Only

- In faq_handling_matrix or corpus but no inbox_triage scenario
- No Simulation Assistant scenario
- Backend may route to generic customer_question with no tailored reply

---

## What Counts as Config-Only

- In inbox_triage_scenarios.json but not in Simulation Assistant
- In customer_entry_multi_turn_simulations but different category naming (e.g. english_notice_confusion vs notice_confusion)
- Not visible in founder-facing UI

---

## What Counts as Frontend-Visible

- Scenario appears in Simulation Assistant scenario list (Recommended trial, Real customer, Edge cases)
- Founder can click scenario, run replay, see triage result with correct category/focus
- UnifiedIntakePage shows correct case focus label for the category

---

## What Counts as Demo-Ready

- Scenario passes run_simulation_assistant_scenarios.py or run_inbox_triage_scenarios.py
- Phrasing is realistic (not generic "provide more context")
- Handoff / Collected / Still needed / Human confirmation appear correctly when applicable

---

## Realism Quality Scale

| Level | Definition |
|-------|------------|
| **Strong** | Realistic broker-forwarded or customer phrasing; tailored reply; no generic fallback |
| **Acceptable** | Phrasing recognizable; reply adequate; minor wording could improve |
| **Weak** | Generic or vague; reply could apply to many types; "provide more context" risk |

---

## Non-Negotiable: Track All 8 Explicitly

Do NOT collapse into "mostly integrated." For each of the 8, report:

- docs present? yes/no  
- handling matrix present? yes/no  
- backend logic present? yes/no  
- scenario present? yes/no  
- Simulation Assistant visible? yes/no  
- frontend-visible/demo-ready? yes/no  
- realism quality: strong / acceptable / weak  
- integration level: fully / partially / weakly / not integrated  

---

*Used for: Eight-Question Integration Matrix*

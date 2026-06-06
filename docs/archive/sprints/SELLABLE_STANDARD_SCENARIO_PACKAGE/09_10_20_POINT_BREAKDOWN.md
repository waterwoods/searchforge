# 10–20 Point Breakdown — Sellable Standard Scenario Package

**Purpose:** Structured breakdown of concrete package-building points. Use for quick reference.

---

1. **Package name:** Broker Standard Package (Chen Kui Broker Standard Package for client-specific)
2. **Target broker/merchant profile:** Small CA auto broker; Chinese-speaking clients; 1–5 people
3. **Included scenarios:** Quote/add-car, policy change (add/remove), material collection/already sent, renewal/premium review, billing clarification, claim first notice, talk to agent
4. **Excluded/deferred:** Email/WeChat/SMS, OCR, full CRM, multi-tenant, Stripe, carrier API
5. **Why these scenarios belong together:** High-frequency broker work; revenue + retention + operational + urgency
6. **Customer-side value proposition:** Faster broker response; clearer what to send; less back-and-forth
7. **Broker-side value proposition:** Less manual triage; fewer repetitive explanations; clearer next steps; no lost follow-ups
8. **Office handoff value:** One next move; Collected/Still needed chips; client reply draft; follow-up memory
9. **Routing model:** FAST (turn 2+ simple); LLM (turn 1, mixed); Human (VIN, payment, customer_says_sent)
10. **Multi-turn expectations:** Add-car 2–3 turns; others 2 turns; handoff when threshold met
11. **Case summary expectations:** conversation_summary + broker_next_step + collected/still_needed
12. **Workbench expectations:** Case focus, Your next move, Collected, Still needed, queue triage, reopen context
13. **Strongest today:** Cancellation risk, missing document, add-car quote, premium review, claim intake
14. **Still need another round:** Talk to agent (lightweight); some edge cases
15. **Demo/prospect story:** "One paste → structured case. One next move. One draft. Workbench included. No auto-send."
16. **Pilot-ready enough:** Guardrail passes; 7 core scenarios; founder demo path; one-sentence offer
17. **Still not included:** Inbox sync, OCR, CRM, multi-tenant, Stripe
18. **Next packaging step:** Inbox integration; client pack customization; more verticals

---

*End of 10–20 Point Breakdown*

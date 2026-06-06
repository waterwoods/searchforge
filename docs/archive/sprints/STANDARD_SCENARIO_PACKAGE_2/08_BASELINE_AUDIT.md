# Baseline Audit — Standard Scenario Package

**Sprint:** Standard Scenario Package 2.0  
**Date:** 2026-03-18

---

## 1. Current Package Quality

| Area | Status |
|------|--------|
| **Inbox triage scenarios** | 64/64 pass (LLM disabled, rule path) |
| **Multi-turn simulations** | 41/41 pass (strong) |
| **Recognition** | Strong for add-car, missing_document, payment, renewal, claim, talk-to-agent |
| **First reply** | Strong; tailored per category |
| **Later-turn** | Good: follow_up_type, clarification-first, already_sent handoff |
| **Handoff** | Exists; phrases (add_car, other_received, other_corrected) |
| **Summary** | Basic: intent + collected + still_needed + context + msg_count + latest |
| **Workbench** | collected_fields, still_needed_fields, broker_next_step |

---

## 2. Classification: Strong vs Weak

| Scenario | Strong Core | Usable but Shallow | Weak in Later Turns | Weak in Office Handoff | High-Value to Improve |
|----------|-------------|--------------------|--------------------|------------------------|------------------------|
| Add-car | ✓ | | | Summary "Collected" could be clearer | ✓ |
| Material / already sent | ✓ | | | Summary when 2+ items; broker verify guidance | ✓ |
| Renewal premium | ✓ | | | Handoff when bill sent; summary | ✓ |
| Payment / cancellation | ✓ | | | "Already paid" broker guidance | ✓ |
| Talk to Agent | ✓ | | | Mid-flow detection | ✓ |

---

## 3. Biggest Current Package Weakness

**Summary and broker_next_step when "client says sent" or "client says paid"** — The system correctly uses warmer handoff phrases ("好的，收到了"), but the **conversation_summary** and **broker_next_step** do not always tell the broker to **verify receipt with the carrier**. The broker may still need to ask "did we get it?" — the improvement is to make this explicit in broker_next_step.

---

## 4. Biggest Current Broker Rework Source

When client says "发过了" or "我付了" — broker receives handoff but may not have clear guidance that **verification with carrier** is the next step. The case is "handed off" but the broker's next move is implicit.

---

## 5. Biggest "Still Feels Too MVP-Like" Issue

The workbench shows collected/still_needed chips, but when the flow is "client says sent" or "client says paid", the **broker_next_step** could be more actionable: "Verify dec page received with carrier; if not, request resend" vs generic "Review and follow up."

---

## 6. 10–20 Point Breakdown (Concrete)

1. **Scenarios in scope:** Add-car, Material/already sent, Renewal premium, Payment/cancellation, Talk to Agent
2. **Why selected:** Highest commercial value; reduce broker rework; pilot-ready
3. **Deferred:** Remove-car (strong), Claim (lower freq), Billing clarification standalone
4. **Biggest weakness each:** Add-car—summary clarity; Material—verify guidance; Renewal—handoff when bill sent; Payment—verify when paid; Talk to Agent—mid-flow
5. **Recognition improvements:** Minor; already strong
6. **Later-turn improvements:** Ensure clarification/urgency/next_step answer-first; already_sent warmer handoff
7. **Correction handling:** other_corrected + embedded question answer; exists
8. **Already-sent / material:** broker_next_step "verify receipt"; summary "Client says sent"
9. **Handoff timing:** Per MATURE_INTAKE_SKELETON; add-car 3–4 turns; others 2 turns
10. **Summary improvements:** "Client says sent" explicit; "verify receipt" in broker_next_step
11. **Workbench usefulness:** collected_fields include dec_page_sent, garaging_sent; still_needed include verify_receipt when client says sent
12. **Broker follow-up reduction:** Explicit verify guidance when client says sent/paid
13. **Simulation/test additions:** Add 1–2 scenarios for "client says sent" broker_next_step
14. **Guardrails:** Ensure broker_next_step includes verify when human_confirmation_required
15. **"Package 2.0 stronger":** Broker asks fewer manual follow-ups; summary + broker_next_step more actionable
16. **Out of scope:** New scenarios, platform features, docs-only
17. **More reusable:** Same skeleton; clearer handoff contract
18. **Next step after:** Package 2.1 — remove-car deepening, claim deepening, or config extraction

---

*End of Baseline Audit*

# Evaluation Criteria Spec

**Sprint:** Broker Trial Simulation + Fix Queue Hardening Sprint  
**Created:** 2026-03-19

---

## 1. Per-Simulation Judgment Dimensions

| Dimension | What to judge | Strong | Weak |
|-----------|--------------|--------|------|
| **Route correctness** | issue_category matches intent | Correct category | Wrong category (e.g. talk_to_agent → customer_question) |
| **Ask-next quality** | First reply asks right thing | Asks for year/zip, or policy/bill, or what to send | "Please provide more context" / generic |
| **Handoff timing** | handoff_ready when enough info | Turn 2–3 when enough; turn 1 never for vague | Handoff turn 1 for vague; no handoff when enough |
| **broker_next_step usefulness** | Operational one-liner | "Verify vehicle details and zip; run quote" | "Review and follow up" |
| **Summary usefulness** | conversation_summary | Captures key facts | Empty or wrong |
| **Append/follow-up correctness** | triage_for_append | Uses correction; updates collected | Ignores correction; wrong collected |
| **Client-aware continuity** | client_id in append | Preserved | Lost |
| **Trust/readability impact** | Draft tone; Human confirmation | Editable; badge when AI extracted | Robotic; no badge |

---

## 2. Classification Outcomes

| Outcome | Meaning |
|---------|---------|
| **Strong** | No notes; route correct; handoff timing correct; broker_next_step useful |
| **Acceptable with friction** | Minor notes (≤2); not trust-breaking |
| **Weak** | 3+ notes; or trust-breaking; or wrong route |

---

## 3. Commercial Impact Filter

For each issue found, ask:
- Will this cause **broker extra work**? → Prioritize higher
- Will this cause **customer confusion**? → Prioritize higher
- Will this cause **trust loss**? → Fix now
- Will this cause **slower case creation**? → Fix next
- Will this cause **worse trial confidence**? → Prioritize higher

---

*End of Evaluation Criteria Spec*

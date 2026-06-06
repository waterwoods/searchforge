# Auto Insurance FAQ Intake Corpus — Sprint Blueprint

**Sprint:** Auto Insurance FAQ Intake Corpus Sprint  
**Date:** 2026-03-14  
**Mode:** Research → structure → classify → refine (45–90 min)

---

## 1. Why This Corpus Matters Now

- **Founder feedback:** Product feels too designed; scenarios feel limited
- **Real customer pack:** Helps but still not enough breadth of real-world patterns
- **Routing depends on patterns:** FAST / LLM / human-confirm decisions need realistic question types
- **Demo quality:** More realistic questions → more convincing demo → easier pilot sell

---

## 2. Why Realism and Routing Depend on Real-World Question Patterns

| Dependency | Why |
|------------|-----|
| **Turn 1 routing** | Rule-first path needs high-confidence markers; real phrasing reveals which patterns are safe |
| **Handoff clarity** | Broker handoff needs real-world "what office actually needs" clarity |
| **Simulation Assistant** | Scenarios must feel like real customer traffic, not generic FAQ |
| **Trust boundaries** | Human-confirm items need real examples of what "could go wrong" |

---

## 3. What "Good Enough Corpus" Looks Like

- **20–30** question types (not 100+)
- **Realistic user phrasing** (1–3 examples per type)
- **Handling framework** per type (not just Q&A)
- **Routing classification** (FAST / LLM / human confirmation)
- **Product-usable** — feeds Simulation Assistant, Turn 1 routing, handoff docs

---

## 4. Scope

| In scope | Out of scope |
|----------|--------------|
| Common customer auto-insurance questions (CA, Chinese + English) | Full knowledge base |
| Handling framework: clarify, safe response, trust boundary | Hardcoded answers |
| Routing: FAST / LLM / human | New product features |
| 5–8 scenario recommendations for Simulation Assistant | Giant dataset |
| Integration recommendation for current product | Other verticals |

---

*See: Execution Outline, Acceptance Criteria*

---

## Appendix: Corpus Summary (25 Types)

| ID | Topic | Route |
|----|-------|-------|
| Q01 | new_car_quote | LLM |
| Q02 | remove_car | LLM |
| Q03 | premium_too_high | LLM |
| Q04 | payment_failed | LLM |
| Q05 | cancellation_warning | LLM |
| Q06 | missing_document | LLM |
| Q07 | already_sent_followup | FAST |
| Q08 | notice_confusion | LLM |
| Q09 | sr22_dmv_help | LLM |
| Q10 | claim_intake | LLM |
| Q11 | add_car_field_followup | FAST |
| Q12 | what_to_send | FAST |
| Q13 | renewal_reminder | FAST |
| Q14 | policy_delay | FAST |
| Q15 | missing_signature | LLM |
| Q16 | underwriting_followup | LLM |
| Q17 | escrow_lienholder | LLM |
| Q18 | handoff_confirmation | FAST |
| Q19 | bill_why_so_high | LLM |
| Q20 | quick_quote_request | LLM |
| Q21 | moving_zip_change | human |
| Q22 | adding_driver | human |
| Q23 | proof_of_insurance_dmv | LLM |
| Q24 | unclear_forwarded | LLM |
| Q25 | informational_done | FAST |
ndoff_confirmation | FAST | Short confirm |
| Q19 | bill_why_so_high | LLM | Overlaps Q03 |
| Q20 | quick_quote_request | LLM | Often add-car |
| Q21 | moving_zip_change | human | Policy change |
| Q22 | adding_driver | human | Policy change |
| Q23 | proof_of_insurance_dmv | LLM | DMV |
| Q24 | unclear_forwarded | LLM | Unclear |
| Q25 | informational_done | FAST | All set |

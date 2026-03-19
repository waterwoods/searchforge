# 10–20 Point Breakdown

**Sprint:** Sales Readiness Hardening Sprint  
**Created:** 2026-03-17

---

## Concrete Hardening Points

| # | Point | Decision |
|---|-------|----------|
| 1 | **Talk to Agent trigger conditions** | Button always; free-text: "联系人工", "联系陈奎", "联系办公室", "我要找人工", "talk to agent" |
| 2 | **Talk to Agent customer-facing wording** | "好的，已帮您转给陈奎办公室，他们会尽快联系您。" |
| 3 | **Talk to Agent reassurance copy** | Same as above; no "Are you sure?" |
| 4 | **Talk to Agent handoff payload** | issue_category=customer_requested_human; broker_next_step; client_reply_draft; lifecycle_status=handoff_pending |
| 5 | **What office sees immediately after Talk to Agent** | Case focus "联系人工"; broker_next_step; Recent customer messages |
| 6 | **Whether next office action is shown** | Yes — broker_next_step: "Customer requested human contact. Call or message back promptly." |
| 7 | **Which edge cases are in scope** | (1) Billing "我发你了", (2) Talk to Agent mid-flow, (3) Late correction (verify) |
| 8 | **Why those edge cases were selected** | Billing = high-frequency; Talk to Agent mid-flow = trust; Late correction = broker action quality |
| 9 | **How billing clarification should continue after "我发你了"** | already_sent handoff; broker_next_step: verify receipt; no re-ask |
| 10 | **How late correction should survive handoff** | follow_up_type=correction; badge visible; append preserves it |
| 11 | **How mixed-intent + human escalation should behave** | Deferred this sprint |
| 12 | **How corrections / already_sent / context hints should surface in workbench** | Badge when follow_up_type in (correction, already_sent); customer_requested_human badge |
| 13 | **How summary should reflect edge-case info** | conversation_summary; context hint in handoff |
| 14 | **What guardrails/tests are needed** | guardrail_inbox_triage.sh; run_inbox_triage_scenarios; run_multi_turn_simulations; test_inbox_triage_api |
| 15 | **What simulations are needed** | MT40 billing "我发你了"; free-text "联系人工" |
| 16 | **What is intentionally deferred** | Mixed-intent + human; inbox integration; multi-tenant |
| 17 | **What reduces broker rework** | already_sent handoff; correction badge; clear next move |
| 18 | **What makes this more sellable / more trustworthy** | Talk to Agent = real capability; edge cases handled; office gets usable context |

---

*End of 10–20 Point Breakdown*

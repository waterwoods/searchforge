# State/Workflow Backbone — Acceptance SLA Criteria

**Sprint**: State Workflow Backbone  
**Purpose**: Practical criteria for continuity, state correctness, workflow clarity, case progression, handoff timing, office usability, and what to defer.  
**Audience**: Founder, product, engineering.

---

## 1. Continuity

| Criterion | Pass | Fail |
|-----------|------|------|
| Multi-turn uses triage_conversation | Turn 1 and Turn 2+ both use triage_conversation with turns | Turn 1 uses triage_message |
| Append preserves context | append_follow_up_message keeps case_messages, source_text, workflow fields | Overwrites or drops context |
| No duplicate cases | persist only when handoff_ready | Case created on Turn 1 when still collecting |

---

## 2. State Correctness

| Criterion | Pass | Fail |
|-----------|------|------|
| collection_stage in triage result | collecting or enough_for_handoff present | Missing |
| follow_up_type in triage result | new_info, already_sent, clarification_question, etc. present | Missing |
| collection_stage on case | Persisted on save_case and append_follow_up_message | Not persisted |
| follow_up_type on case | Persisted on save and append | Not persisted |

---

## 3. Workflow Clarity

| Criterion | Pass | Fail |
|-----------|------|------|
| collected_fields per flow | Add-car, missing doc, cancellation, claim, renewal have correct extracted fields | Wrong or empty |
| still_needed_fields per flow | Correct still-needed list; verify_carrier_received when customer says sent | Wrong or missing |
| human_confirmation_fields | VIN, customer_says_sent_*, payment when applicable | Missing when high-risk |
| conversation_summary | Intent + collected + still needed + message count + snippet | Generic or empty |

---

## 4. Case Progression

| Criterion | Pass | Fail |
|-----------|------|------|
| Case created at handoff | Only when handoff_ready | Created when still collecting |
| Append updates workflow | collected, still_needed, broker_next_step, etc. updated from triage | Stale workflow fields |
| case_messages ordered | sequence ascending; source_text matches | Out of order or mismatch |
| case_status values | new, reviewing, waiting_customer, agent_followup, closed | Invalid values |

---

## 5. Handoff Timing

| Criterion | Pass | Fail |
|-----------|------|------|
| Add-car one-shot | Year+model+zip+delivery/driver → hand off Turn 1 | Asks again |
| Add-car progressive | Year only Turn 1 → ask zip; zip Turn 2 → hand off | Wrong ask or early handoff |
| Non-add-car Turn 2 | Hand off after 2 customer turns (or threshold) | Repeats same ask |
| next_ask overrides handoff | When next_ask returned, use it; don't hand off | Hands off when should ask |

---

## 6. Office Usability

| Criterion | Pass | Fail |
|-----------|------|------|
| Case list shows status | case_status visible | Not visible |
| Case detail shows workflow | collected, still_needed, broker_next_step | Not visible |
| Append works | Paste message → case updates | Fails or corrupts |
| Status update works | PATCH status accepted | Rejected |

---

## 7. What to Defer

| Item | Reason |
|------|--------|
| conversation_id / session_id persistence | Case = conversation after persist; pre-persist is UI-only |
| Strict case_status transition validation | Document in 04; enforce in future sprint |
| SQLite/Postgres | JSON file sufficient for pilot |
| Multi-thread cases | One case = one thread |
| Assignment/routing | Out of scope |
| Auth | Out of scope |

---

## 8. Regression Criteria

| Check | Must Pass |
|-------|-----------|
| verify_inbox_case_persistence.py | All assertions |
| guardrail_inbox_triage.sh | PASS |
| run_inbox_triage_scenarios.py | All scenarios |
| run_multi_turn_simulations.py | No new failures |
| audit_state_field_accuracy.py | All pass |
| verify_speed_routing.py | OK |
| unified_intake_smoke_check.sh | OK |

---

## 9. Founder Readiness

| Criterion | Pass |
|-----------|------|
| 07_FOUNDER_DEMO_INSPECTION_NOTES.md | Founder can follow and see value |
| API returns inspectable state | collection_stage, follow_up_type, collected, still_needed in response |
| Case object complete | All workflow fields present after save and append |

---

*See also: `07_FOUNDER_DEMO_INSPECTION_NOTES.md`, `docs/standards/UNIFIED_INTAKE_MVP_STANDARD.md`*

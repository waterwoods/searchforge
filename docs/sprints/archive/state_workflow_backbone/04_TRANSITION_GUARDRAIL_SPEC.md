# State/Workflow Backbone — Transition Guardrail Spec

**Sprint**: State Workflow Backbone  
**Purpose**: Valid/invalid state transitions, first-turn rules, follow-up rules, handoff rules, persistence rules, regression guardrails.  
**Base**: `triage.py`, `case_store.py`, `routes/inbox_triage.py`.

---

## 1. Valid / Invalid State Transitions

### 1.1 collection_stage

| From | To | When |
|------|-----|------|
| (none) | collecting | Turn 1, not enough for handoff |
| (none) | enough_for_handoff | Turn 1, enough for handoff (e.g. add-car one-shot) |
| collecting | enough_for_handoff | Turn 2+, threshold met |
| collecting | collecting | Turn 2+, next_ask returned |
| enough_for_handoff | handed_off | Case persisted (implicit) |

**Invalid**: enough_for_handoff → collecting (once ready, we don't go back). Handled by not re-triaging already-persisted case in same flow.

### 1.2 case_status (Office Workflow)

| From | Valid To |
|------|----------|
| new | reviewing, waiting_customer, agent_followup, closed |
| reviewing | waiting_customer, agent_followup, closed |
| waiting_customer | reviewing, agent_followup, closed |
| agent_followup | reviewing, waiting_customer, closed |
| done | closed (alias) |
| closed | (none; terminal) |

**Invalid**: closed → new, closed → reviewing. Implementation: `update_case_status` accepts any value in CASE_STATUS_VALUES; strict transition validation deferred to UI or future guardrail.

---

## 2. First-Turn Rules

| Rule | Implementation | Guardrail |
|------|----------------|----------|
| Use triage_conversation for Turn 1 | `triage_conversation(text, [])` not `triage_message` | MULTI_TURN_CONTINUITY_GUARDRAIL |
| Add-car one-shot handoff | When fields enough (year+model+zip+delivery/driver), hand off Turn 1 | `_add_car_enough_for_handoff` in triage |
| No persist when not handoff_ready | persist_case only when handoff_ready | routes/inbox_triage.py |
| Soft-route fallback | When unclear + soft_route, use intent-specific starter | SOFT_ROUTE_STARTER_REPLIES |

---

## 3. Follow-Up Rules

| Rule | Implementation | Guardrail |
|------|----------------|----------|
| follow_up_type drives reply | already_sent → other_received; clarification → other_clarification; correction → other_corrected | triage.py handoff phrase selection |
| Answer before handoff for clarification | "garaging 是什么意思" → explain first, then handoff suffix | triage.py document confusion path |
| Correction + embedded question | "其实已经付了...最要紧做什么" → answer urgency, then hand off | triage.py other_corrected + urgency_next_markers |
| Turn 2+ handoff | manual_followup_needed + customer_count≥2 → hand off | `_should_handoff` |
| Add-car ask one more | When not enough, return next_ask (zip, delivery/driver) | `_get_next_ask_for_add_car` |
| Other categories: hand off after 2 turns | No next_ask for non-add-car | `_get_next_ask_draft` returns None |

---

## 4. Handoff Rules

| Rule | Implementation | Guardrail |
|------|----------------|----------|
| Persist only when handoff_ready | save_case called only when handoff_ready | routes/inbox_triage.py |
| Append always handoff_ready | triage_for_append sets handoff_ready=True | triage.py |
| Add-car: next_ask overrides handoff | When would_handoff and next_ask, use next_ask; don't hand off yet | triage.py |
| case_creation_suggested | Set when handoff + (collected_fields or high-value category) | triage.py |

---

## 5. Persistence Rules

| Rule | Implementation | Guardrail |
|------|----------------|----------|
| Case has case_messages | save_case creates case_messages from source_text | case_store._parse_source_to_messages |
| Append adds to case_messages | append_follow_up_message appends customer + system | case_store.append_follow_up_message |
| source_text in sync | _build_source_from_messages after append | case_store |
| Workflow fields on persist | collected_fields, still_needed, collection_stage, follow_up_type | case_store.save_case, append_follow_up_message |
| Lazy migration | Case without case_messages: parse source_text on read | case_store._normalize_case |

---

## 6. Regression Guardrails

| Guardrail | Script / Location | Must Pass |
|-----------|-------------------|-----------|
| Persistence | `verify_inbox_case_persistence.py` | All assertions |
| Triage scenarios | `run_inbox_triage_scenarios.py` | All scenarios |
| Multi-turn | `run_multi_turn_simulations.py` | No new failures |
| State field accuracy | `audit_state_field_accuracy.py` | All pass |
| Speed routing | `verify_speed_routing.py` | OK |
| Full guardrail | `guardrail_inbox_triage.sh` | PASS |
| Smoke | `unified_intake_smoke_check.sh` | OK |

---

## 7. Documented but Not Yet Enforced

| Item | Current | Future |
|------|---------|--------|
| case_status transition validity | All values accepted | Reject invalid (e.g. closed→new) |
| conversation_id pre-persist | None | Optional session_id for UI |
| Append "still collecting" path | Append always handoff | Could support append without handoff for edge cases |

---

*See also: `05_EXECUTION_OUTLINE.md`, `docs/guardrails/MULTI_TURN_CONTINUITY_GUARDRAIL.md`*

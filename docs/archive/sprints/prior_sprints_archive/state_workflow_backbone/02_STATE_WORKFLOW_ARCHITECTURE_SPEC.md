# State/Workflow Backbone — Architecture Spec

**Sprint**: State Workflow Backbone  
**Purpose**: Target architecture for conversation lifecycle, workflow progression, handoff progression, message thread vs case, case vs office workflow.  
**Base**: `triage.py`, `case_store.py`, `LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT.md`, `MATURE_INTAKE_SKELETON.md`.

---

## 1. Conversation Lifecycle

Every customer intake follows the same shape:

```
detect → ask → enough? → hand off
```

### 1.1 Collection Stages

| Stage | Meaning | When |
|-------|---------|------|
| **collecting** | We're asking for more info | Not enough for handoff; next_ask returned |
| **enough_for_handoff** | Threshold met; ready to hand off | `_should_handoff` true OR per-flow enough (e.g. add-car year+model+zip+delivery) |
| **handed_off** | Case persisted; broker has it | Case exists in case_store |

**Implementation**: `_derive_collection_stage()` in triage.py returns `collecting` or `enough_for_handoff`. `handed_off` is implicit when case exists.

### 1.2 Flow Shape (MATURE_INTAKE_SKELETON)

| Step | Action |
|------|--------|
| 1 | Detect likely intent (add-car, missing doc, cancellation, claim, renewal, unclear) |
| 2 | Ask 1–2 next things (no overload) |
| 3 | Decide if enough: per-category handoff thresholds |
| 4 | Hand off with summary, broker_next_step, client_reply_draft |

---

## 2. Workflow Progression

### 2.1 Per-Flow State Dimensions

| Dimension | Source | Example |
|-----------|--------|---------|
| **issue_category / flow** | Triage | add_car, missing_document, cancellation_warning, claim_intake, renewal_premium |
| **collection_stage** | `_derive_collection_stage()` | collecting, enough_for_handoff |
| **collected_fields** | Per-flow extractors | year, model, zip, delivery_date |
| **still_needed_fields** | Per-flow logic | primary_driver, verify_carrier_received |
| **follow_up_type** | `_derive_follow_up_type()` | new_info, already_sent, clarification_question |
| **ready_for_handoff** | `handoff_ready` in triage result | true / false |
| **human_confirmation_required** | `_derive_human_confirmation_fields()` | true when VIN, payment, customer_says_sent |

### 2.2 Follow-Up Types (LIGHTWEIGHT_STATE_MACHINE_BLUEPRINT)

| Type | Detection | Reply action |
|------|-----------|-------------|
| new_info | New field values (year, zip, dec sent) | Acknowledge + ask next OR hand off |
| correction | "不是", "说错了", "是另一辆" | Acknowledge correction + hand off |
| already_sent | "发了", "发你", "sent", "截图" | Warmer handoff "好的，收到了" |
| clarification_question | "什么意思", "要发什么", "garaging 是什么意思" | Answer first + hand off |
| urgency_question | "最要紧", "是不是今天" | Answer urgency + hand off |
| next_step_question | "先看什么", "办公室先看什么" | Answer next step + hand off |

---

## 3. Handoff Progression

### 3.1 When Case Is Created

| Condition | Action |
|-----------|--------|
| `handoff_ready` true | Persist case via `save_case()` |
| `handoff_ready` false | Do NOT persist; return triage result only |
| `persist_case` true + handoff_ready | Save case; return case in response |

**Guardrail**: `MULTI_TURN_CONTINUITY_GUARDRAIL` — only persist when `handoff_ready` to avoid premature/duplicate cases.

### 3.2 Append Flow (Paste New Message)

| Step | Action |
|------|--------|
| 1 | Load case by case_id |
| 2 | `triage_for_append(existing_source_text, new_message)` — always returns `handoff_ready=True` |
| 3 | `append_follow_up_message()` — add customer + system message; update workflow fields |
| 4 | Preserve: case_status, waiting_on, next_contact_by, case_notes |

**Note**: Append is broker-initiated (paste into existing case). Every append is treated as handoff-ready because broker is actively reviewing.

### 3.3 First-Turn vs Follow-Up

| Turn | Path | Handoff |
|------|------|---------|
| Turn 1 | `triage_conversation(text, [])` | If add-car + enough fields → hand off immediately |
| Turn 2+ | `triage_conversation(text, turns)` | `_should_handoff()`: manual_followup + count≥2 → hand off; or next_ask if one more thing needed |
| Add-car Turn 1 | Special: `_add_car_enough_for_handoff(fields)` → hand off | One-shot when year+model+zip+delivery/driver |

---

## 4. Message Thread vs Case

### 4.1 Message Thread

- **Definition**: Ordered sequence of customer and system turns.
- **Format**: `[客户]` / `[系统]` in source_text; or `case_messages` with role, text, sequence.
- **Identity**: Before case exists, thread is ephemeral (in-memory in Customer Entry). After case exists, thread = case_messages.

### 4.2 Case

- **Definition**: Persisted workflow unit. Has case_id, workflow state, lifecycle status.
- **Created**: When handoff_ready and persist_case (or equivalent).
- **Contains**: source_text (derived from case_messages), triage fields, case_status, waiting_on, case_notes, case_activity.

### 4.3 Relationship

| Scenario | Message thread | Case |
|----------|----------------|------|
| Turn 1, not handoff_ready | In Customer Entry UI | None |
| Turn 1, handoff_ready, persist | Becomes case_messages | Created |
| Turn 2, same session, no case yet | In UI | None (or create if handoff) |
| Append to existing case | case_messages grows | Updated |

**Key**: One case = one conversation thread. No multi-thread cases in this sprint.

---

## 5. Case vs Office Workflow

### 5.1 Case Lifecycle (case_store.py)

| Status | Meaning |
|--------|---------|
| new | Just handed off; broker hasn't looked |
| reviewing | Broker is working it |
| waiting_client / waiting_customer | Waiting on customer response |
| agent_followup | Broker needs to follow up (carrier, UW, etc.) |
| done / closed | Resolved |

### 5.2 Waiting On

| Value | Meaning |
|-------|---------|
| none | No explicit wait |
| client | Waiting on customer |
| broker | Broker action needed |
| carrier | Waiting on carrier |
| underwriting | Waiting on UW |

### 5.3 Office Use

- Case list: sort by updated_at; filter by status (future).
- Case detail: show workflow state (collected, still_needed), broker_next_step, client_reply_draft.
- Broker actions: PATCH status, add note, set waiting_on, append message.

---

## 6. 10–20 Point Backbone Breakdown

| # | Point | Status | Notes |
|---|-------|--------|-------|
| 1 | **Unified conversation entry path** | ✓ | `triage_conversation(text, turns)` for first-turn and follow-up; no bypass |
| 2 | **First-turn vs follow-up vs append semantics** | ✓ | First: `triage_conversation(text, [])`; Follow-up: `triage_conversation(text, turns)`; Append: `triage_for_append(source, new_msg)` |
| 3 | **conversation_id / case_id / customer_id boundaries** | Partial | No conversation_id; case_id = canonical after persist; customer linkage on case |
| 4 | **Standard `workflow_state` structure** | ✓ | collection_stage, follow_up_type, handoff_ready, collected_fields, still_needed_fields |
| 5 | **Standard `collected` structure** | ✓ | Per-flow snake_case; add-car, missing_doc, cancellation, claim, renewal |
| 6 | **Standard `still_needed` structure** | ✓ | Per-flow; verify_carrier_received, primary_driver, etc. |
| 7 | **`next_best_question` / next-step logic** | ✓ | `_get_next_ask_draft()` for add-car; hand off when enough |
| 8 | **`handoff_ready` decision rules** | ✓ | `_should_handoff()` + per-flow enough (add-car); persist only when true |
| 9 | **`case_creation_suggested` decision rules** | ✓ | handoff + (collected>0 or high-value category) |
| 10 | **`human_confirmation_required` decision rules** | ✓ | `_derive_human_confirmation_fields()` for VIN, payment, customer_says_sent |
| 11 | **Lifecycle status model** | ✓ | new, reviewing, waiting_customer, agent_followup, done, closed |
| 12 | **Message history persistence model** | ✓ | case_messages with message_id, role, text, sequence, created_at |
| 13 | **Case persistence timing** | ✓ | Only when handoff_ready + persist_case |
| 14 | **Summary / office-readable handoff contract** | ✓ | conversation_summary, broker_next_step, client_reply_draft |
| 15 | **Frontend/backend contract for in-progress vs handoff** | ✓ | handoff_ready, case_creation_suggested, collection_stage in response |
| 16 | **Regression guardrails** | Partial | MULTI_TURN_CONTINUITY_GUARDRAIL; append always handoff_ready |
| 17 | **Testing matrix** | ✓ | run_inbox_triage_scenarios, run_multi_turn_simulations, audit_state_field_accuracy |
| 18 | **What remains intentionally deferred** | ✓ | conversation_id pre-persist; full transition validation; SQL migration |

---

## 7. Implementation Touchpoints

| Component | Role |
|-----------|------|
| `triage.py` | `_derive_collection_stage`, `_derive_follow_up_type`, `_should_handoff`, per-flow field extractors |
| `case_store.py` | save_case, append_follow_up_message, update_case_status, case_messages, workflow fields |
| `routes/inbox_triage.py` | POST /triage (persist_case), POST /cases/{id}/append-message, PATCH status |
| Config | Handoff phrases, add_car_rules, reply_templates |

---

*See also: `03_DATA_CONTRACT_SCHEMA_SPEC.md`, `04_TRANSITION_GUARDRAIL_SPEC.md`*

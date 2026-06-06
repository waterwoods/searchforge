# State / Workflow Backbone Phase 2 — Workflow State Contract Spec

**Purpose**: Define the intended `workflow_state` shape and semantics.

---

## 1. Standard Fields

| Field | Type | Semantics |
|-------|------|-----------|
| **topic / issue_category** | string | missing_document, cancellation_warning, customer_question, etc. |
| **stage** | string | collecting \| enough_for_handoff |
| **collected** | list[string] | Per-flow snake_case: year, make_model, zip, customer_says_sent_declaration_page |
| **still_needed** | list[string] | Per-flow: primary_driver, verify_carrier_received |
| **next_best_question** | string | When handoff_ready=false: what to ask next (optional; can be client_reply_draft) |
| **handoff_ready** | bool | Ready for broker handoff |
| **case_creation_suggested** | bool | Signal for UI: suggest persist |
| **human_confirmation_required** | bool | Broker must verify before acting |
| **human_confirmation_fields** | list[string] | VIN, customer_says_sent_*, etc. |
| **lifecycle_status** | string | collecting \| handoff_pending \| handed_off \| office_followup |
| **follow_up_type** | string | new_info, already_sent, clarification_question, etc. |

---

## 2. Field Semantics

### stage (collection_stage)
- **collecting**: Still gathering info; not ready for handoff
- **enough_for_handoff**: Threshold met; hand off

### collected
- Format: snake_case identifiers
- Per-flow: add_car (year, make_model, zip, delivery_date, primary_driver, vin), missing_doc (requested_*, customer_says_sent_*), cancellation (notice_present, screenshot_sent, already_paid_claimed), etc.

### still_needed
- What would materially improve the case or what broker must verify
- Examples: primary_driver, verify_carrier_received, renewal_notice_or_bill

### next_best_question
- When handoff_ready=false: the next thing to ask (can be derived from client_reply_draft or _get_next_ask_draft)
- Optional; improves UI "what to ask next" visibility

### handoff_ready
- true: Broker should receive case; persist when requested
- false: Continue collecting

### case_creation_suggested
- true when handoff_ready and (collected>0 or high-value category)
- UI uses for "Save case" prompt

### human_confirmation_required
- true when VIN, customer_says_sent_*, payment status, etc. in collected
- Broker must verify before acting

### lifecycle_status
- **collecting**: In-progress; no case yet or case not handed off
- **handoff_pending**: handoff_ready=true; case not yet persisted
- **handed_off**: Case persisted; case_status=new
- **office_followup**: case_status in (reviewing, waiting_client, agent_followup, done, closed)

---

## 3. WORKFLOW_STATE_KEYS (Extended)

```python
WORKFLOW_STATE_KEYS = (
    "collection_stage",
    "follow_up_type",
    "handoff_ready",
    "case_creation_suggested",
    "collected_fields",
    "still_needed_fields",
    "human_confirmation_required",
    "human_confirmation_fields",
    "next_best_question",      # Phase 2
    "lifecycle_status",        # Phase 2
)
```

---

## 4. Summary / Office-Readable Contract

- **conversation_summary**: Intent hint + "Collected:" + "Still needed:" + message count + latest snippet
- **broker_next_step**: One operational sentence
- **client_reply_draft**: Handoff or next-ask message

---

*See: 05_UI_STATE_VISIBILITY_SPEC.md*

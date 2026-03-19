# State/Workflow Backbone — Founder Demo Inspection Notes

**Sprint**: State Workflow Backbone  
**Purpose**: What the founder should inspect after the sprint, what behaviors should feel improved, and how to see the value of a stronger backbone.  
**Audience**: Founder (Chen Kui).

---

## 1. What to Inspect After the Sprint

### 1.1 API Response (Triage)

When you send a message to `/api/inbox/triage`, the response should include:

| Field | What to look for |
|-------|-------------------|
| **collection_stage** | `collecting` or `enough_for_handoff` — tells you if we're still asking or ready to hand off |
| **follow_up_type** | `new_info`, `already_sent`, `clarification_question`, etc. — drives reply tone |
| **collected_fields** | e.g. `["year", "model", "zip"]` — what we've extracted |
| **still_needed_fields** | e.g. `["primary_driver"]` — what would help or broker must verify |
| **handoff_ready** | `true` when office should receive the case |
| **conversation_summary** | Short broker-facing summary with intent + collected + still needed |

**How to check**: Use Customer Entry or curl. After Turn 1 "2024 BMW X5, 下周提车", you should see `handoff_ready: true`, `collected_fields` with year, model, delivery, and `collection_stage: enough_for_handoff`.

### 1.2 Case Object (Workbench)

When you open a case in the Workbench (or GET the case via API):

| Field | What to look for |
|-------|-------------------|
| **case_messages** | Each customer and system turn as separate messages, in order |
| **collected_fields** | Same as triage; visible so office knows what's in |
| **still_needed_fields** | What broker should check or ask |
| **collection_stage** | Was this handed off when "collecting" or "enough"? |
| **broker_next_step** | One actionable sentence for the broker |
| **case_status** | new, reviewing, waiting_customer, etc. |
| **human_confirmation_fields** | When present (VIN, payment, "customer says sent"), broker must verify |

### 1.3 Append Flow

Paste a new customer message into an existing case:

| Check | What to look for |
|-------|-------------------|
| **New message added** | case_messages grows by 2 (customer + system reply) |
| **Workflow updated** | collected_fields, still_needed_fields, broker_next_step reflect new triage |
| **Context preserved** | source_text includes full thread; conversation_summary updated |
| **Status preserved** | case_status, waiting_on, notes unchanged unless you change them |

---

## 2. What Behaviors Should Feel Improved

| Behavior | Before | After |
|----------|--------|-------|
| **Multi-turn continuity** | Turn 3 could forget Turn 1–2 | State (collected, still_needed) carried through; reply matches follow-up type |
| **Handoff clarity** | "Is this ready?" unclear | collection_stage + handoff_ready make it explicit |
| **Reply tone** | Generic | "发过了" → "好的，收到了"; "什么意思" → answer first, then hand off |
| **Broker visibility** | Raw text only | conversation_summary, collected, still_needed, broker_next_step |
| **Case progression** | Ad-hoc | Clear lifecycle: new → reviewing → waiting_customer → closed |
| **Append** | Could lose context | Full message history; workflow state updates |

---

## 3. How to See the Value of a Stronger Backbone

### 3.1 Quick Demo Path

1. **Customer Entry** — Type: "2024 BMW X5, 下周提车, zip 90210"
2. **Expect**: One-shot handoff. Reply: "报价资料已收集，办公室会尽快出价..."
3. **Workbench** — Find the case. Check: collected_fields has year, model, zip, delivery; still_needed may have primary_driver.
4. **Append** — Paste: "我老公开" (main driver)
5. **Expect**: New message added; workflow updates; still_needed shrinks or clears.

### 3.2 Multi-Turn Path

1. **Turn 1**: "缺dec page，我发过了"
2. **Expect**: Reassure-first reply ("您说发过了，我这边帮你核对..."); handoff_ready true.
3. **Turn 2** (if you simulate): "garaging 是什么意思"
4. **Expect**: Answer the question first ("garaging proof是证明车停哪里的..."), then hand off. follow_up_type = clarification_question.

### 3.3 What the Founder Should Notice

| Observation | Meaning |
|-------------|---------|
| Reply matches what customer said | follow_up_type drove the right phrase (already_sent vs clarification) |
| Office sees what's collected | collected_fields visible; no guessing |
| Office knows what to do | broker_next_step is actionable |
| Case doesn't appear too early | Only when handoff_ready |
| Append doesn't break anything | Message history and workflow stay consistent |

---

## 4. Quick Validation Commands

```bash
# Persistence
PYTHONPATH=. python3 scripts/verify_inbox_case_persistence.py

# Guardrail
bash scripts/guardrail_inbox_triage.sh

# Multi-turn
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py

# State audit
PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py

# Smoke
bash scripts/unified_intake_smoke_check.sh
```

---

## 5. If Something Feels Off

| Symptom | Check |
|---------|-------|
| Reply doesn't match follow-up type | follow_up_type in triage result; handoff phrase key (other_received, other_clarification) |
| Case created too early | handoff_ready; persist_case logic |
| Append loses workflow | append_follow_up_message updates collected, still_needed from triage |
| Office can't see state | API response and case object include collection_stage, collected_fields, still_needed_fields |
| Wrong collected/still_needed | Per-flow extractors in triage (_add_car_structured_fields, etc.) |

---

*See also: `docs/ANDY_QUICK_START.md`, `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md`, `06_ACCEPTANCE_SLA_CRITERIA.md`*

# Lightweight Production Case Record — Sprint Report

**Sprint**: Lightweight Production Case Record  
**Date**: 2026-03-15

## Summary

Upgraded the demo-grade case store into a lightweight production-ready case record foundation.

## What Was Done

### Loop 1: Message History + Workflow State
- Added `case_messages` array: each user/assistant turn is a record
- `_parse_source_to_messages()` and `_build_source_from_messages()` for parsing/sync
- `save_case` and `append_follow_up_message` create/update case_messages
- Persisted workflow fields: handoff_ready, case_creation_suggested, human_confirmation_required, collection_stage, follow_up_type
- Lazy migration: old cases get case_messages from source_text on read

### Loop 2: Customer Linkage + Lifecycle
- Added customer fields: customer_name, customer_phone, customer_email, policy_number, contact_note
- `update_case_customer()` and PATCH `/api/inbox/cases/{case_id}/customer`
- Extended CASE_STATUS_VALUES: waiting_customer, agent_followup, closed

## Validation

- verify_inbox_case_persistence.py: PASS
- run_inbox_triage_scenarios.py: 53/53
- run_multi_turn_simulations.py: 38/38
- audit_state_field_accuracy.py: 6/7 (M1 pre-existing)

## Founder Block

**Biggest improvement:** Message-level history + explicit workflow state. Each turn is a record; append adds messages.

**Biggest remaining weakness:** No extraction of customer info from conversation; UI may not surface case_messages/customer yet.

**Enough for pilot?** Yes. **Redeploy needed?** Yes (backend).

**Inspect next:** Create case, append follow-up, check case_messages in API response. PATCH /customer with name/phone.

# State/Workflow Backbone — Execution Outline

**Sprint**: State Workflow Backbone  
**Purpose**: Workstreams, implementation order, test plan, likely loop count.  
**Base**: Existing triage, case_store, routes; docs 01–04.

---

## 1. Workstreams

| ID | Workstream | Scope |
|----|------------|-------|
| W1 | **Documentation alignment** | Ensure 01–04 specs match current triage/case_store behavior; fix doc-code drift |
| W2 | **State persistence consistency** | collection_stage, follow_up_type always persisted on save and append |
| W3 | **Transition guardrail codification** | Add validation for case_status transitions where practical; document in 04 |
| W4 | **Regression suite** | Run and fix any failing guardrails; add state-workflow-specific assertions |
| W5 | **Founder-inspectable output** | Ensure workflow state visible in API response and case object |

---

## 2. Implementation Order

| Phase | Workstreams | Deliverable |
|-------|-------------|-------------|
| **Loop 1** | W1, W2 | Docs aligned; state fields consistently persisted |
| **Loop 2** | W3, W4 | Transition rules documented/enforced; all guardrails pass |
| **Loop 3** | W5 | Founder can inspect state in responses; 07 inspection notes validated |

---

## 3. Test Plan

### 3.1 Per-Loop Validation

| Script | Purpose |
|--------|---------|
| `verify_inbox_case_persistence.py` | Case creation, append, message history |
| `run_inbox_triage_scenarios.py` | Triage scenarios |
| `run_multi_turn_simulations.py` | Multi-turn continuity |
| `audit_state_field_accuracy.py` | collected/still_needed accuracy |
| `verify_speed_routing.py` | Fast path vs LLM routing |
| `guardrail_inbox_triage.sh` | Full guardrail |
| `unified_intake_smoke_check.sh` | End-to-end smoke |

### 3.2 State-Specific Checks

| Check | How |
|-------|-----|
| collection_stage present | Assert triage result has collection_stage; case has it after save/append |
| follow_up_type present | Assert triage result has follow_up_type |
| collected/still_needed on case | Assert case object has both after save and append |
| handoff_ready drives persist | Verify persist_case + handoff_ready=false → no case created |

### 3.3 Manual Smoke

1. Customer Entry: Turn 1 "2024 BMW X5, 下周提车" → handoff
2. Workbench: Find case; verify collection_stage, collected_fields, still_needed_fields
3. Append: Paste "zip 90210" → verify case_messages grows; workflow fields update
4. PATCH status: reviewing → waiting_customer → verify accepted

---

## 4. Likely Loop Count

| Phase | Estimate |
|-------|----------|
| Loop 1 (docs + persistence) | 1–2 hours |
| Loop 2 (transitions + guardrails) | 1–2 hours |
| Loop 3 (founder inspection) | 0.5–1 hour |
| **Total** | 2.5–5 hours |

---

## 5. Dependencies

| Dependency | Status |
|------------|--------|
| triage.py | Has _derive_collection_stage, _derive_follow_up_type, per-flow fields |
| case_store.py | Has case_messages, workflow fields, save_case, append_follow_up_message |
| routes/inbox_triage.py | Has persist_case, append-message, status PATCH |
| Config | Handoff phrases, add_car_rules |

---

## 6. Out of Scope (This Sprint)

- New storage backend
- conversation_id / session_id persistence
- Full case_status transition enforcement (document only)
- UI changes (beyond ensuring API returns inspectable state)

---

*See also: `06_ACCEPTANCE_SLA_CRITERIA.md`, `07_FOUNDER_DEMO_INSPECTION_NOTES.md`*

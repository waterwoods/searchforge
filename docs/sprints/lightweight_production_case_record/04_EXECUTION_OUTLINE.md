# Lightweight Production Case Record — Execution Outline

**Sprint**: Lightweight Production Case Record Sprint  
**Created**: 2026-03-15

---

## 1. Workstreams

| ID | Workstream | Scope |
|----|------------|-------|
| W1 | Message-level history | Add case_messages; persist each turn; derive/sync source_text |
| W2 | Workflow state persistence | Ensure collected, still_needed, handoff flags, etc. always persisted |
| W3 | Customer linkage | Add customer_name, customer_phone, customer_email, policy_number, contact_note |
| W4 | Lifecycle formalization | Align case_status values; ensure office visibility |
| W5 | Migration / compatibility | Handle existing cases; backward compat |

---

## 2. Implementation Order

| Phase | Workstreams | Deliverable |
|-------|-------------|-------------|
| **Loop 1** | W1, W2, W5 | Message history + workflow state; compat |
| **Loop 2** | W3, W4 | Customer linkage + lifecycle |
| **Loop 3** (optional) | W5 refinements, UI | One high-ROI polish |

---

## 3. Migration / Compatibility Strategy

| Case Type | Action |
|-----------|--------|
| **New case** | Create case_messages from initial turn(s); set workflow fields from triage |
| **Existing case (no case_messages)** | On first read/update: parse source_text → case_messages; or lazy migration |
| **Append** | Add message to case_messages; update source_text |
| **API response** | Include case_messages when present; source_text always present |

**Lazy migration**: When loading a case that has source_text but no case_messages, parse source_text into case_messages. One-time migration on read.

---

## 4. Likely Loop Count

- **Loop 1**: 1–2 hours (message history + workflow)
- **Loop 2**: 1–2 hours (customer + lifecycle)
- **Loop 3**: 0.5–1 hour (optional polish)
- **Total**: 2.5–5 hours implementation + validation

---

## 5. Validation After Each Loop

| Script | Purpose |
|--------|---------|
| `verify_inbox_case_persistence.py` | Persistence contract |
| `run_inbox_triage_scenarios.py` | Triage scenarios |
| `run_multi_turn_simulations.py` | Multi-turn |
| `audit_state_field_accuracy.py` | State fields |
| `verify_speed_routing.py` | Speed routing |
| `guardrail_inbox_triage.sh` | Full guardrail |
| `unified_intake_smoke_check.sh` | Smoke |

---

*See also: `05_ACCEPTANCE_SLA_CRITERIA.md`*

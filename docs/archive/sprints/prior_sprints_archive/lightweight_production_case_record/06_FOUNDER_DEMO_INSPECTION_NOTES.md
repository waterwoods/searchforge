# Lightweight Production Case Record — Founder Demo / Inspection Notes

**Sprint**: Lightweight Production Case Record Sprint  
**Created**: 2026-03-15

---

## 1. What the Founder Should Inspect After Implementation

### 1.1 Case Detail (Workbench)

| Check | What to look for |
|-------|------------------|
| **Message history** | Conversation shows as separate messages (customer / system turns), not one blob |
| **Workflow state** | Collected / Still needed chips visible; issue category clear |
| **Lifecycle** | Status (New, Waiting for customer, etc.) visible and meaningful |
| **Customer info** | If customer name/phone/email provided, they appear on the case |
| **Append** | Pasting a follow-up adds a new message; workflow state updates |

### 1.2 Case List

| Check | What to look for |
|-------|------------------|
| **Status** | Each case shows lifecycle status |
| **Recency** | Sorted by updated_at |
| **Preview** | Last message or summary visible |

### 1.3 API / Data File

| Check | What to look for |
|-------|------------------|
| **case_messages** | Each case has case_messages array with role, text, sequence |
| **Workflow fields** | collected_fields, still_needed_fields, handoff_ready, etc. present |
| **Customer fields** | customer_name, customer_phone, etc. when provided |
| **source_text** | Still present for backward compat |

---

## 2. What Product/Business Gain This Unlocks

| Gain | Impact |
|------|--------|
| **Audit trail** | Per-message history; can replay conversation |
| **Follow-up continuity** | Office knows what was said when; no lost context |
| **Customer association** | Case linked to person when known |
| **Formal lifecycle** | Clear status for queue management |
| **Pilot readiness** | Closer to real office use; not just demo |

---

## 3. Quick Validation Commands

```bash
# Persistence
PYTHONPATH=. python3 scripts/verify_inbox_case_persistence.py

# Guardrail
bash scripts/guardrail_inbox_triage.sh

# Multi-turn
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py

# State audit
PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py
```

---

## 4. Manual Smoke (If Server Running)

1. Open Customer Entry
2. Type: "2024 BMW X5, 下周提车"
3. Get reply; hand off
4. Open Workbench; find case
5. Verify: case_messages has 2+ entries (customer + system)
6. Paste follow-up: "zip 90210"
7. Verify: new message added; workflow updated

---

*See also: `docs/ANDY_QUICK_START.md`, `docs/runbooks/UNIFIED_INTAKE_MVP_RUNBOOK.md`*

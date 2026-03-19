# Founder Demo / Inspection Notes — Minimal Production Backbone

**Sprint:** Minimal Production Backbone Master Sprint  
**Created:** 2026-03-17

---

## 1. What Founder Should Inspect After This Sprint

1. **Refresh recovery** — Start conversation, add 1–2 turns, refresh page. Conversation should restore.
2. **Handoff** — Complete add-car or cancellation flow. Case should appear in Recent cases with correct lifecycle_status.
3. **Reopen** — Reopen case. Status, notes, follow-up, case_messages should persist.
4. **Append follow-up** — Paste new customer message. Case should update with new broker_next_step.

---

## 2. What Behaviors Should Clearly Feel More Formal

- **State display** — lifecycle_status tag (Collecting / Ready for handoff / Handed off / Office follow-up) should match reality
- **Persistence** — No lost turns on refresh; no duplicate cases
- **Case card** — workflow_state fields (collected, still needed) should be consistent

---

## 3. Evidence That Backbone Is More Reusable and Pilot-Ready

- Schema and contract documented
- workflow_state single source of truth
- lifecycle_status not overridden incorrectly
- All validation scripts pass

---

## 4. Quick Verification Steps

```bash
# 1. Guardrail
bash scripts/guardrail_inbox_triage.sh

# 2. Scenarios
PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py

# 3. Multi-turn
PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py

# 4. State audit
PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py

# 5. Smoke (with server on 8001)
bash scripts/unified_intake_smoke_check.sh
```

---

*See also: `docs/ANDY_QUICK_START.md`*

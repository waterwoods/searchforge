# State / Workflow Backbone Phase 2 — Founder Demo / Inspection Notes

---

## What Founder Should Inspect After This Sprint

1. **Session continuity**: Start Customer Entry, send message → check Network tab for session_id in request
2. **State visibility**: Add-car flow Turn 1 "我买了台宝马X5" → see "Collecting info", still_needed (year, zip, etc.)
3. **Handoff visibility**: Turn 2 "2024年，zip 90210" → see "Ready for handoff", collected fields
4. **Case lifecycle**: After persist → case_status, collected/still_needed in case detail

---

## What Should Visibly Feel Improved

- Clearer "Collecting" vs "Ready for handoff" at a glance
- Collected / Still needed always visible when relevant
- Session identity (session_id) in API for future continuity

---

## Tests That Prove Continuity and State Clarity

- `bash scripts/guardrail_inbox_triage.sh` → PASS
- `PYTHONPATH=. python3 scripts/test_state_workflow_backbone.py` → PASS
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` → PASS

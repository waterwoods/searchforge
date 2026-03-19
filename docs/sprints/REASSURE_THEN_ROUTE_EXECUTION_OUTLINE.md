# Reassure-Then-Route Intake Sprint — Execution Outline

**Sprint**: Reassure-Then-Route Intake  
**Target**: 2 loops, ~30–60 min total

---

## 1. Workstreams

| Workstream | Owner | Focus |
|------------|-------|-------|
| Reply strategy | triage.py | Answer-first phrasing, uncertainty language |
| Templates | reply_templates.json | Human wording, reassurance phrases |
| Handoff | triage.py, handoff_phrases | "Office will confirm" when uncertain |
| Case timing | triage.py, routes | `case_creation_suggested` when meaningful |
| Simulation | run_inbox_triage_scenarios | Validate no regressions |

---

## 2. Role Assignment

- **Planner**: Control docs, baseline audit
- **Reply-strategy worker**: `_build_client_reply_draft`, templates
- **Backend worker**: triage logic, handoff phrases
- **Simulation worker**: Run scenarios, guardrails, smoke checks

---

## 3. Simulation Plan

- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` (if exists)
- `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py`
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh`

---

## 4. Loop Count

- **Loop 1**: Reply strategy improvements (answer-first, uncertainty, human wording)
- **Loop 2**: Case-creation timing, safe-handoff polish
- **Loop 3**: Optional — one low-risk refinement if clearly worthwhile

---

*End of outline*

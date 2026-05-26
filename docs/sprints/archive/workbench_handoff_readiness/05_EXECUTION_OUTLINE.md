# Execution Outline

**Sprint:** Workbench Handoff Readiness

---

## 1. Workstreams

| Workstream | Owner | Scope |
|------------|-------|-------|
| Frontend workbench | Cursor | UnifiedIntakePage.tsx case card |
| API contract | Cursor | inboxTriage.ts SavedCase type |
| Backend | None | case_messages already returned |

---

## 2. Implementation Order

1. **Baseline audit** — Document current strengths/weaknesses
2. **Loop 1** — Recent customer messages + collected/still_needed prominence
3. **Loop 2** — Next action clarity + correction/context hints
4. **Loop 3** (optional) — One refinement if clearly valuable
5. **Validation** — Run guardrails, build, smoke check

---

## 3. Test Plan

- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py` (if exists)
- `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py` (if exists)
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh`
- `cd ui && npm run build`

---

## 4. Likely Loop Count

2–3 loops. Stop when handoff surface feels meaningfully more operational.

---

*End of execution outline*

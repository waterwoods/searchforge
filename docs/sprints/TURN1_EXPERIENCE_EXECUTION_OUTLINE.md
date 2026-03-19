# Turn 1 Experience — Execution Outline

**Sprint:** Controlled Multi-Agent Iteration Sprint  
**Theme:** Turn 1 Experience Optimization

---

## 1. Workstreams

| # | Workstream | Owner (Role) | Deliverable |
|---|------------|--------------|-------------|
| 1 | Customer Entry inline loading | Frontend worker | Inline "正在整理 case..." placeholder in conversation during Turn 1 |
| 2 | Broker Workbench loading polish | Frontend worker | Clearer loading wording; consistency with Customer Entry |
| 3 | Validation & simulation | QA worker | Run guardrail, scenario pack, smoke check; report pass/fail |
| 4 | Product critique | Product critic | Assess first-impression feel; flag regressions |

---

## 2. Sequence of Execution

1. **Planner:** Confirm blueprint and acceptance criteria (done).
2. **Backend worker:** No backend changes. Skip.
3. **Frontend worker:** Implement Customer Entry inline loading first; then Broker Workbench polish.
4. **QA worker:** Run `guardrail_inbox_triage.sh`, `run_inbox_triage_scenarios.py`, `unified_intake_smoke_check.sh` (or subset if backend not up).
5. **Product critic:** Review UX; compare before/after.
6. **Release reviewer:** Confirm no regression; approve or request refinement.

---

## 3. Testing / Simulation Plan

| Test | Command | Pass Criteria |
|------|---------|----------------|
| Guardrail | `bash scripts/guardrail_inbox_triage.sh` | Exit 0 |
| Scenario pack | `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` | All pass or documented skip |
| Smoke check | `bash scripts/unified_intake_smoke_check.sh` | Steps complete |
| Manual | Open /workbench/unified-intake, paste message, observe loading | Inline feedback visible in Customer Entry; Broker loading clear |

---

## 4. Rollback

If any regression: revert frontend changes; loading reverts to button-only (Customer Entry) or existing card (Broker Workbench).

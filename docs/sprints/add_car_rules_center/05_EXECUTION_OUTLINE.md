# Execution Outline

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Workstreams, implementation order, test plan.

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| Config | Backend | add_car_rules.json, config loader, triage integration |
| API | Backend | GET/PUT rules, preview endpoint |
| UI | Frontend | Rules Center page, edit, preview, publish |
| Safety | Both | Draft vs published, validation |

---

## 2. Implementation Order

1. **Baseline audit** — Document current state
2. **Config + backend** — add_car_rules.json, config_loader, triage uses config
3. **API** — GET /api/inbox/add-car-rules, PUT for draft, POST preview
4. **UI Loop 1** — Page, view rules, edit, preview
5. **UI Loop 2** — Draft, publish, restore

---

## 3. Test / Preview Plan

- `run_inbox_triage_scenarios.py` — add-car scenarios
- `run_multi_turn_simulations.py` — add-car multi-turn
- Manual: Rules Center → edit → preview → publish → Unified Intake → verify

---

## 4. Likely Loop Count

- Loop 1: Minimal shell (view, edit, preview)
- Loop 2: Draft/publish/restore
- Loop 3: Optional polish (e.g. better preview layout)

---

*See also: 06_ACCEPTANCE_CRITERIA.md*

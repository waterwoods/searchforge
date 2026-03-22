# Add-Car Commercial Flow Hardening — Execution Outline

**Sprint:** Add-Car Commercial Flow Hardening  
**Purpose:** Workstreams, loop plan, simulation approach, deployment.

---

## 1. Workstreams

| WS | Area | Scope |
|----|------|-------|
| WS1 | Fix-now weak points | broker_next_step quality; quote-ready/contact/correction on queue cards; no redundant ask |
| WS2 | Fix-next weak points | Concrete vehicle in summary; broker_next_step contact/attachment; side-question handling |
| WS3 | Readiness completeness | All combinations defined; contact + attachment interaction verified |
| WS4 | Simulation coverage | Add-car commercial flow scenarios; fix-queue validation |
| WS5 | Founder inspection | Vercel tests; "good enough to show as flagship" |

---

## 2. Implementation Order

1. **Baseline** — Document current state; align with 05_ADD_CAR_WEAK_POINT_FIX_QUEUE_SPEC
2. **Loop 1** — WS1: Fix-now items (broker_next_step, queue card signals, extraction)
3. **Loop 2** — WS2: Fix-next items (concrete vehicle, contact/attachment in next step)
4. **Loop 3** — WS3: Readiness combinations; edge cases
5. **Loop 4** — WS4: Simulations; regression
6. **Loop 5** — WS5: Founder inspection; Vercel validation

---

## 3. Loop Plan

| Loop | Focus | Validation |
|------|-------|------------|
| 1 | Fix-now | guardrail_inbox_triage.sh; run_handoff_timing_simulations.py; manual broker_next_step |
| 2 | Fix-next | Same + add-car excellence simulations |
| 3 | Readiness | All combination states; contact/attachment logic |
| 4 | Simulations | add_car_commercial_flow_simulations.json; full pack |
| 5 | Founder | 08_FOUNDER_INSPECTION_NOTES.md; Vercel manual tests |

---

## 4. Simulation Approach

| Pack | Scenarios |
|------|-----------|
| add_car_commercial_flow | Full T1 handoff; partial → complete; correction; garaging same turn; coverage side question; contact missing; attachment present |
| handoff_timing | HT1, HT5, HT8 (existing) |
| add_car_excellence | Quote-ready variants; contact variants; attachment variants |

**Runner:** `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py` (or dedicated add_car runner)

---

## 5. Deployment

| Component | When to Deploy |
|-----------|----------------|
| Backend (triage.py, case_store) | After WS1–WS3 changes |
| Frontend (workbench, queue cards) | After queue card signal changes |
| Config (add_car_rules) | With backend |

**Pre-deploy:**
- guardrail_inbox_triage.sh PASS
- run_handoff_timing_simulations.py PASS
- add_car commercial flow simulations PASS

**Post-deploy:**
- Vercel manual tests (08_FOUNDER_INSPECTION_NOTES.md)
- demo_quick_validate.sh PASS

---

## 6. Dependencies

| Dependency | Source |
|------------|--------|
| Quote-ready logic | triage.py _add_car_enough_for_handoff |
| Contact extraction | ADD_CAR_IDENTITY_CONTACT_LITE |
| Attachment storage | ADD_CAR_ATTACHMENT_READY_LITE |
| broker_next_step | WORKBENCH_HANDOFF_PROFESSIONALIZATION |
| Queue card UI | UnifiedIntakePage, workbench components |

---

*See also: 05_ADD_CAR_WEAK_POINT_FIX_QUEUE_SPEC.md, 07_ACCEPTANCE_COMMERCIAL_HARDENING_CRITERIA.md, 08_FOUNDER_INSPECTION_NOTES.md*

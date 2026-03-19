# Add-Car Rules Center Online Readiness — Execution Outline

**Sprint:** Add-Car Rules Center Online Readiness  
**Purpose:** Workstreams, implementation order, deployment plan.

---

## 1. Workstreams

| Workstream | Owner | Deliverables |
|------------|-------|--------------|
| Backend: publish capability | API worker | `publishable` in GET response; write test in config_loader |
| Frontend: safe publish mode | Frontend worker | Disable publish when `publishable: false`; badge + alert |
| Frontend: UX hardening | UX worker | Clearer copy, sample buttons, draft badge |
| Deployment | Release worker | Frontend redeploy (Vercel); backend redeploy if API changed |
| QA | QA worker | Guardrail scripts, build, smoke |

---

## 2. Implementation Order

1. **Backend:** Add `can_publish_add_car_rules()` to config_loader; include `publishable` in GET /api/inbox/add-car-rules response.
2. **Frontend:** Fetch `publishable`; conditionally disable publish; show "预览模式" badge and alert when false.
3. **Frontend:** Improve UX (intro copy, sample preview buttons, clearer labels).
4. **Deploy:** Frontend `npm run build` + `vercel --prod`; backend redeploy if needed.
5. **Verify:** Open page on Vercel; confirm publish disabled; run guardrail scripts.

---

## 3. Deployment Plan

| Component | Action |
|-----------|--------|
| Frontend | `cd ui && npm run build && vercel --prod` |
| Backend | Redeploy if config_loader or inbox_triage changed |
| Vercel | Ensure route `/workbench/add-car-rules` is live |

---

## 4. Test Plan

- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh`
- `cd ui && npm run build`
- Manual: Open Rules Center on Vercel; edit; preview; verify publish disabled when backend is Cloud Run

---

## 5. Likely Loop Count

- **Loop 1:** Online UX + preview hardening (copy, samples, draft badge)
- **Loop 2:** Safe publish mode (publishable detection, disabled publish, honest labels)
- **Loop 3:** Optional refinement (one label, one sample, or stop)

---

*See also: 05_ACCEPTANCE_CRITERIA.md*

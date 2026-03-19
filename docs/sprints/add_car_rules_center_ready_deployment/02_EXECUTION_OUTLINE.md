# Add-Car Rules Center Ready Deployment — Execution Outline

**Sprint:** Add-Car Rules Center Ready Deployment  
**Purpose:** Step-by-step deployment and verification.

---

## Phase A — Control Docs

1. Sprint Blueprint ✓
2. Execution Outline ✓
3. Acceptance / Operational Criteria ✓

---

## Phase B — Pre-Deploy Validation

**Inspect:**
- `ui/src/pages/AddCarRulesPage.tsx` — page, publishable support, preview mode
- `ui/src/api/inboxTriage.ts` — AddCarRules type, getAddCarRules
- `services/fiqa_api/inbox_triage/config_loader.py` — can_publish_add_car_rules
- `services/fiqa_api/routes/inbox_triage.py` — GET add-car-rules, publishable

**Confirm:**
- Frontend page exists at `/workbench/add-car-rules`
- Frontend supports `publishable`
- Backend GET returns `publishable`
- Safe publish/preview mode logic exists

**Run validation scripts (stop on failure):**
- `PYTHONPATH=. python3 scripts/run_inbox_triage_scenarios.py`
- `PYTHONPATH=. python3 scripts/run_multi_turn_simulations.py`
- `PYTHONPATH=. python3 scripts/audit_state_field_accuracy.py`
- `PYTHONPATH=. python3 scripts/verify_speed_routing.py`
- `bash scripts/guardrail_inbox_triage.sh`
- `bash scripts/unified_intake_smoke_check.sh`
- `cd ui && npm run build`

---

## Phase C — Backend Deploy

- `bash scripts/deploy_rag_demo.sh`
- Capture: success/failure, backend URL, revision, warnings/errors

---

## Phase D — Frontend Deploy

- `cd ui && npm run build && vercel --prod`
- Capture: success/failure, production URL, alias updated, warnings

---

## Phase E — Post-Deploy Verification

1. Production route `/workbench/add-car-rules` exists
2. Backend GET `/api/inbox/add-car-rules` returns `publishable`
3. UI shows correct behavior (preview mode badge when publishable=false)
4. Business user can see editable fields, click preview, understand mode
5. Page does not over-promise

---

## Phase F — Optional Second Loop

If one small, high-value, low-risk mismatch is revealed, fix and redeploy once.

---

## Likely Loop Count

1–2 loops (initial deploy + optional fix)

---

*See also: 03_ACCEPTANCE_CRITERIA.md*

---

## Sprint Report Summary (2026-03-16)

**Pre-deploy validation:** PASS (guardrail, build).  
**Backend deploy:** Manual — `bash scripts/deploy_rag_demo.sh`  
**Frontend deploy:** Manual — `cd ui && vercel --prod`  
**Production URL:** https://ui-smoky-beta.vercel.app/workbench/add-car-rules  
**Biggest limit:** Cloud Run read-only; publishable=false online; preview mode only.

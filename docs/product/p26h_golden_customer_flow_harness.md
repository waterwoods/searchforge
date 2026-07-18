# P26H — Golden Customer Flow Harness

## Status

**CONDITIONAL GO** — local + in-process QA path implemented; deployed HTTP QA gate
requires QA runtime flags + support key (not present in this workspace).

Companion UI journey: `docs/product/p26h_ui_golden_ui_journey.md`  
Unified release gate: `bash scripts/run_claim_release_gate.sh --local|--qa`

This is test infrastructure. It creates no product UI and never mutates Camry /
shared seeded cases.

## Architecture

```
run_claim_release_gate.sh --local
  → focused tests → build:gate → backend --local → UI --local
  → READY FOR QA DEPLOY

run_claim_release_gate.sh --qa
  → fixture preflight → backend --qa → UI --qa → cleanup
  → READY FOR FOUNDER QA   (HTTP transport only)

QA fixture runner (support-gated):
  /api/inbox/support/p26h-fixture/*
    → real Cap2 CreateClaim / evidence / Slice1 (or compat) contracts
    → tagged workbench_test + harness_run_id
    → scoped cleanup
```

Enablement (all required on the QA runtime):

- `ENABLE_P26H_FIXTURE_RUNNER=1`
- `UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1`
- `UNIFIED_INTAKE_SUPPORT_API_KEY` (required for prod-like + HTTP client auth)

Client:

- Deployed: `P26H_QA_BASE_URL=https://<qa-host>` + support key
- Local QA-path proof: `P26H_QA_TRANSPORT=inprocess` + the same enable flags  
  (proves the runner; does **not** emit READY FOR FOUNDER QA)

## Commands

```bash
# Local backend / UI
bash scripts/run_golden_customer_flow.sh --local
bash scripts/run_golden_customer_ui_flow.sh --local

# Unified local gate (pre-deploy)
bash scripts/run_claim_release_gate.sh --local

# QA backend / UI (deployed)
P26H_QA_BASE_URL=https://<qa-host> \
UNIFIED_INTAKE_SUPPORT_API_KEY=<key> \
  bash scripts/run_golden_customer_flow.sh --qa

P26H_QA_BASE_URL=https://<qa-host> \
UNIFIED_INTAKE_SUPPORT_API_KEY=<key> \
  bash scripts/run_golden_customer_ui_flow.sh --qa

bash scripts/run_claim_release_gate.sh --qa

# Local proof of QA path (not Founder-ready)
ENABLE_P26H_FIXTURE_RUNNER=1 UNIFIED_INTAKE_QA_FIXTURE_SURFACE=1 \
P26H_QA_TRANSPORT=inprocess \
  bash scripts/run_golden_customer_flow.sh --qa
```

## Scenarios (backend --qa)

| ID | Journey |
|---|---|
| A | Fresh zero-broker claim — collecting defaults, resume token, no false completion |
| B | Normal intake — vehicle + insurance/photo evidence; Timeline / Projection update |
| C | Resume — same case via signed token |
| D | Broker follow-up — one `broker_requested` task; defaults retained |
| E | Case isolation — Case B does not inherit Case A evidence/completion |
| F | Expired token — rejected; tokens masked |
| G | Idempotency — same idempotency key → same case_id |

## Sample PASS

```text
PASS
Golden Customer Flow: 36 assertions, 5 clean cases
harness_run_id: p26h_…
Cleanup: PASS
```

## Sample FAIL

```text
FAIL
harness_run_id: p26h_…
Cleanup: PASS

Step: Insurance page render
Task: insurance_card
Source: system_default
Expected: upload work surface visible
Actual: page shell only
Owning layer: WXML Render Gate
Smallest probable repair area: WXML Render Gate
```

## Security boundary

- Dual enable flags — impossible to turn on with a single accidental env
- Support export auth on every mutating route
- Prod-like runtime requires support key configured
- Cleanup only deletes `demo_name=p26h_ephemeral` + matching `harness_run_id` + `workbench_test`
- Camry / untagged records refused
- Cross-run inspect refused
- Raw tokens not logged; responses expose masked forms
- Mutating routes rate-limited (60/min/process)

## Release policy

**Before QA deploy:** focused tests + `build:gate` + local backend + local UI → `READY FOR QA DEPLOY`

**After QA deploy:** QA backend + QA UI + cleanup → `READY FOR FOUNDER QA`

## Reduced Founder checklist (~5 minutes)

1. Open a fresh claim  
2. Tap insurance / photos / story once  
3. Confirm visual quality  
4. Exit and reopen  
5. Confirm Broker follow-up UX  

Founder is **not** responsible for discovering wrong routes, blank pages, stale
case state, false completion, broken resume, or Projection mismatch.

## Scorecard

- Reliability: **CONDITIONAL** — local + inprocess PASS; deployed HTTP not run here
- Simplicity: **PASS** — one unified gate command per environment
- Smoothness: **PASS** — layer-owned diagnostics + cleanup always reported
- Business Value: **PASS** — broken journeys blocked before Founder device QA
- Scope Control: **PASS** — test infrastructure only

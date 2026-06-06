# Post Sprint Health Check

**Version:** V1 (P16-S)  
**Date:** 2026-06-01  
**Status:** Mandatory after every future sprint  
**Rule:** Sprint cannot close with overall **FAIL**. P0 section failures block GO verdict.

**Companion docs:** `FAILURE_PATTERN_LIBRARY.md`, `CONSTITUTION_ENFORCEMENT.md`, `REALITY_VALIDATION_CHECKLIST.md`

---

## How to run

1. Complete sprint work (code/docs).
2. Deploy to Preview (if applicable).
3. Fill every checkbox below with **Pass** or **Fail** + evidence link.
4. Run companion scripts where noted.
5. Record scores and overall verdict at bottom.
6. Attach to sprint FINAL_VERDICT doc.

**Evidence format:** curl transcript, bundle hash, screenshot path, or log file — not "looks fine."

---

## Deploy

### Local

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| L1 | Demo starts | `bash scripts/run_demo_local.sh` → UI + API on 8001 | ☐ Pass ☐ Fail | |
| L2 | Guardrail | `bash scripts/guardrail_inbox_triage.sh` → PASS | ☐ Pass ☐ Fail | |
| L3 | Quick validate | `bash scripts/demo_quick_validate.sh` → PASS | ☐ Pass ☐ Fail | |
| L4 | Product-only mode | Broker default tab; no Simulation on product path | ☐ Pass ☐ Fail | |
| L5 | Sprint-specific strings | New copy/features visible on localhost | ☐ Pass ☐ Fail | |

### Preview

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| P1 | Cold access | `curl -sI PREVIEW_URL` → **200** (not 401 SSO) | ☐ Pass ☐ Fail | |
| P2 | Bundle deployed | Sprint strings in JS bundle (grep) | ☐ Pass ☐ Fail | |
| P3 | Bundle hash | Hash matches post-deploy commit | ☐ Pass ☐ Fail | |
| P4 | CORS | OPTIONS from Preview origin → 200 | ☐ Pass ☐ Fail | |
| P5 | E2E paste loop | Paste → triage → draft → copy (browser) | ☐ Pass ☐ Fail | |

### Production

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| PR1 | Accessible | `curl -sI PROD_URL` → 200 | ☐ Pass ☐ Fail | |
| PR2 | Not stale | Bundle hash ≠ pre-sprint hash (if promoted) | ☐ Pass ☐ Fail ☐ N/A | |
| PR3 | Correct UI | product_only + broker default (if trial URL) | ☐ Pass ☐ Fail ☐ N/A | |
| PR4 | Promotion gate | If Preview PASS → prod deploy OR documented defer | ☐ Pass ☐ Fail ☐ N/A | |

### Parity

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| PA1 | Local ≈ Preview | Score delta ≤ 10 points | ☐ Pass ☐ Fail | |
| PA2 | Preview ≥ Production | Preview is canonical trial URL | ☐ Pass ☐ Fail | |
| PA3 | Git = Deploy | HEAD commit ≤ deployment timestamp | ☐ Pass ☐ Fail | |
| PA4 | Parity audit | No FP-001 symptoms (`FAILURE_PATTERN_LIBRARY.md`) | ☐ Pass ☐ Fail | |

**Deploy section:** ☐ Pass ☐ Fail  
*Fail if any of P1, P4, PA1, PA3 fail.*

---

## Environment

### Vercel

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| V1 | `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | Set in dashboard (Preview + Prod scopes) | ☐ Pass ☐ Fail | |
| V2 | `VITE_API_BASE_URL` | Set in dashboard; points to Cloud Run | ☐ Pass ☐ Fail | |
| V3 | Deployment Protection | Disabled for broker Preview OR bypass documented | ☐ Pass ☐ Fail | |
| V4 | Git link | Repo linked OR CLI deploy documented in verdict | ☐ Pass ☐ Fail | |

### Cloud Run

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| C1 | Preview origin in ALLOWED_ORIGINS | Current Preview URL allowlisted | ☐ Pass ☐ Fail | |
| C2 | `.env.cloudrun` synced | Matches Cloud Run live env | ☐ Pass ☐ Fail | |
| C3 | Pilot posture | `python3 scripts/validate_pilot_deploy_env.py` → exit 0 | ☐ Pass ☐ Fail | |

### GitHub

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| G1 | Branch pushed | Sprint commits on remote | ☐ Pass ☐ Fail | |
| G2 | Clean ui/ | No uncommitted deploy artifact drift | ☐ Pass ☐ Fail | |

### Feature flags

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| F1 | Build flags match intent | product_only on trial URLs | ☐ Pass ☐ Fail | |
| F2 | Backend flags | UNIFIED_INTAKE_PRODUCT_ONLY=1 on Cloud Run | ☐ Pass ☐ Fail | |
| F3 | No flag regression | Redeploy without manual `-b` still correct | ☐ Pass ☐ Fail | |

**Environment section:** ☐ Pass ☐ Fail  
*Fail if any of V1, V2, V3, C1, F1 fail.*

---

## Runtime

### Console errors

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| R1 | Browser console clean | No uncaught errors on Day 0 path (Preview) | ☐ Pass ☐ Fail | |
| R2 | No CORS errors | No "blocked by CORS policy" | ☐ Pass ☐ Fail | |

### Network errors

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| R3 | API reachable | `GET /api/inbox/cases` → 200 from Preview | ☐ Pass ☐ Fail | |
| R4 | Demo queue | 加载演示队列 completes (not Network Error) | ☐ Pass ☐ Fail | |
| R5 | Triage POST | Paste sample → structured response | ☐ Pass ☐ Fail | |

### API failures

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| R6 | Readiness | `/readyz` or readiness probe → ok | ☐ Pass ☐ Fail | |
| R7 | No 503 on warm path | After readiness, triage < 60s | ☐ Pass ☐ Fail | |
| R8 | Draft language | Chinese paste → acceptable draft language | ☐ Pass ☐ Fail ☐ N/A | |

**Runtime section:** ☐ Pass ☐ Fail  
*Fail if R2, R3, R5 fail.*

---

## Capability

Score each capability 0–100. Compare to pre-sprint baseline. Flag regression > 5 points.

| # | Capability | Contract | Pre | Post | Δ | Regression? | Evidence |
|---|------------|----------|-----|------|---|-------------|----------|
| 1 | Broker Front Door | `CAPABILITY_01_BROKER_FRONT_DOOR.md` | | | | ☐ Yes ☐ No | |
| 2 | Urgent Message Triage | `CAPABILITY_02_URGENT_TRIAGE.md` | | | | ☐ Yes ☐ No | |
| 3 | Structured Case Record | `CAPABILITY_03_CASE_RECORD.md` | | | | ☐ Yes ☐ No | |
| 4 | Customer Intake Collection | `CAPABILITY_04_INTAKE_COLLECTION.md` | | | | ☐ Yes ☐ No | |
| 5 | Case Lifecycle Management | `CAPABILITY_05_CASE_LIFECYCLE.md` | | | | ☐ Yes ☐ No | |
| 6 | Trial Conversion | `CAPABILITY_06_TRIAL_CONVERSION.md` | | | | ☐ Yes ☐ No | |
| 7 | Founder / Operator Control | `CAPABILITY_07_FOUNDER_OPERATOR.md` | | | | ☐ Yes ☐ No | |

### Regression detection

| # | Check | Pass criteria | Result |
|---|-------|---------------|--------|
| CP1 | No capability dropped > 5 pts without documented tradeoff | ☐ Pass ☐ Fail |
| CP2 | Sprint maps to exactly one primary capability | ☐ Pass ☐ Fail |
| CP3 | Deployed URL proves capability claim (not localhost only) | ☐ Pass ☐ Fail |

**Capability section:** ☐ Pass ☐ Fail  
*Fail if any regression unchecked or CP3 fail.*

**Baseline reference (P16-R):** Cap 1 ~45 deploy / 70 local · Cap 2 ~85 · Cap 3 ~72 · Cap 4 ~55 deploy / 70 local · Cap 5 ~55 · Cap 6 ~40 · Cap 7 ~65

---

## Reality

Validate on **deployed Preview URL** (not localhost). Use role simulations from P16-Q pattern.

| Role | Check | Pass criteria | Result | Notes |
|------|-------|---------------|--------|-------|
| **Founder** | Can open cold URL without Vercel login? | ☐ Pass ☐ Fail | |
| **Founder** | 15-min E2E log published? | ☐ Pass ☐ Fail ☐ N/A | |
| **Role C** | Lands broker workbench (not customer portal)? | ☐ Pass ☐ Fail | |
| **Role C** | No engineer chrome / Simulation tab? | ☐ Pass ☐ Fail | |
| **Broker** | Empty state guides to paste? | ☐ Pass ☐ Fail | |
| **Broker** | Paste → draft → copy in < 5 min unsupervised? | ☐ Pass ☐ Fail | |
| **Assistant** | Follow-up / append discoverable? | ☐ Pass ☐ Fail ☐ N/A | |
| **Customer** | Single-message entry (if customer path in scope)? | ☐ Pass ☐ Fail ☐ N/A | |

**Reality section:** ☐ Pass ☐ Fail  
*Fail if Founder cold URL or Broker 5-min loop fails.*

---

## Commercial

| # | Check | Pass criteria | Result | Evidence |
|---|-------|---------------|--------|----------|
| CM1 | Trial readiness | `bash scripts/trial_readiness_check.sh` → acceptable | ☐ Pass ☐ Fail ☐ N/A | |
| CM2 | Payment readiness | Invoice IDs filled (not placeholders) | ☐ Pass ☐ Fail ☐ N/A | |
| CM3 | Evidence readiness | Observation log has ≥1 real case OR sprint explicitly pre-trial | ☐ Pass ☐ Fail ☐ N/A | |
| CM4 | Pricing visible | Broker can answer "how much?" from product or one-pager | ☐ Pass ☐ Fail ☐ N/A | |
| CM5 | Launch check | `bash scripts/trial_launch_check.sh` if trial sprint | ☐ Pass ☐ Fail ☐ N/A | |

**Commercial section:** ☐ Pass ☐ Fail ☐ N/A  
*Required for trial/commercial sprints only.*

---

## Scores (optional quantitative)

| Dimension | Score (/100) | Notes |
|-----------|--------------|-------|
| Local | | |
| Preview (bundle) | | |
| Preview (cold access) | | |
| Production | | |
| Overall product | | |

---

## Output

### Section summary

| Section | Result |
|---------|--------|
| Deploy | ☐ Pass ☐ Fail |
| Environment | ☐ Pass ☐ Fail |
| Runtime | ☐ Pass ☐ Fail |
| Capability | ☐ Pass ☐ Fail |
| Reality | ☐ Pass ☐ Fail |
| Commercial | ☐ Pass ☐ Fail ☐ N/A |

### Overall verdict

| | |
|---|---|
| **Overall** | ☐ **Pass** ☐ **Fail** |
| Sprint ID | |
| Date | |
| Reviewer | |
| Preview URL tested | |
| Production URL tested | |

**Pass rules:**
- All sections Pass (Commercial N/A if non-commercial sprint)
- No P0 failure pattern open (`FAILURE_PATTERN_LIBRARY.md`)
- Constitution Enforcement completed (`CONSTITUTION_ENFORCEMENT.md`)
- Reality Validation Checklist completed (`REALITY_VALIDATION_CHECKLIST.md`)

**Fail actions:**
1. Do not publish GO verdict.
2. Map failures to FP-IDs.
3. Create fix plan before next sprint starts.

---

*End of Post Sprint Health Check V1 — mandatory after every sprint*

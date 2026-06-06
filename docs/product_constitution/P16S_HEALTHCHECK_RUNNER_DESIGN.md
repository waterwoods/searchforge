# P16-S Phase 8 — Health Check Runner Design

**Date:** 2026-06-01  
**Sprint:** P16-S Failure Pattern Library + Post Sprint Health Check  
**Status:** Design only — **do not implement in P16-S**

**Companion:** `P16S_AUTOMATION_REPORT.md`, `POST_SPRINT_HEALTH_CHECK.md`

---

## Objective

Design a single entry-point script — `scripts/post_sprint_check.sh` or `scripts/health_check_pilot.py` — that automates the Easy/Medium checks from POST_SPRINT_HEALTH_CHECK and outputs five scores plus overall Pass/Fail.

---

## Proposed entry points

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| `post_sprint_check.sh` | Matches bash operator surface; composes existing scripts | JSON output awkward | **Primary** for v1 |
| `health_check_pilot.py` | Structured JSON; extends `validate_pilot_deploy_env.py` | New dependency pattern | v2 if JSON consumers needed |

**Canonical name:** `scripts/post_sprint_check.sh`  
**Python helper:** `scripts/post_sprint_check_lib.py` (optional, for parity logic)

---

## CLI interface

```bash
# Minimal
bash scripts/post_sprint_check.sh \
  --preview https://ui-waterwoods.vercel.app \
  --branch sprint-a/broker-front-door

# Full
bash scripts/post_sprint_check.sh \
  --branch sprint-a/broker-front-door \
  --preview https://ui-iwnyo9ufa.vercel.app \
  --production https://ui-smoky-beta.vercel.app \
  --local http://127.0.0.1:5173 \
  --api https://YOUR-CLOUD-RUN.run.app \
  --markers "请把您的需求发给我们,product_only" \
  --sprint P16-R \
  --json /tmp/post_sprint_P16R.json \
  --verbose
```

### Arguments

| Flag | Required | Default | Purpose |
|------|----------|---------|---------|
| `--preview` | Yes* | — | Preview URL for cold access, CORS, bundle |
| `--production` | No | — | Production parity checks |
| `--local` | No | `http://127.0.0.1:5173` | Local parity (if demo running) |
| `--api` | No | from env / `.env.cloudrun` | Cloud Run base for CORS + smoke |
| `--branch` | Yes | — | Git branch for commit/deploy recency |
| `--markers` | No | — | Comma-separated sprint strings for bundle grep |
| `--sprint` | No | — | Sprint ID for evidence file lookup |
| `--json` | No | stdout summary | Write machine-readable report |
| `--verbose` | No | false | Print curl transcripts |
| `--skip-local` | No | false | Remote-only check (Andy common case) |

*Required unless `--skip-local` and all remote checks disabled (not recommended).

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Overall **Pass** |
| 1 | Overall **Fail** (one or more P0 checks) |
| 2 | Usage error / missing deps |
| 3 | Partial (Pass with warnings — optional v2) |

---

## Architecture

```
post_sprint_check.sh
├── parse_args
├── phase_local()      → reuse demo_pre_checklist, guardrail, quick_validate
├── phase_deploy()     → cold curl, bundle hash, hash parity
├── phase_environment()→ validate_pilot_deploy_env.py, CORS OPTIONS, chrome grep
├── phase_runtime()    → API smoke, demo queue endpoint
├── phase_capability() → optional score JSON diff
├── phase_commercial() → invoice grep, trial_readiness_check.sh
├── compute_scores()   → 5 dimension scores
└── emit_report()      → human table + optional JSON
```

---

## Check modules → POST_SPRINT_HEALTH_CHECK mapping

| Module | Health check section | Auto? | Weight in score |
|--------|---------------------|-------|-----------------|
| `check_cold_access` | Deploy P1 | Yes | deployment |
| `check_cors` | Deploy P4, Runtime R2 | Yes | deployment + runtime |
| `check_bundle_hash` | Deploy P2–P3, Parity PA1 | Yes | deployment |
| `check_bundle_markers` | Deploy P5, Parity | Yes | deployment |
| `check_engineer_chrome` | Reality Role C | Yes | reality |
| `check_local_stack` | Deploy L1–L3 | Yes | capability |
| `check_pilot_env` | Environment C3 | Yes | environment |
| `check_api_smoke` | Runtime R3–R5 | Yes | runtime |
| `check_git_clean` | Environment G2 | Yes | environment |
| `check_invoice_placeholders` | Commercial CM2 | Yes | commercial |
| `check_evidence_files` | Commercial CM3 | Partial | commercial |
| `check_vercel_env` | Environment V1–V2 | Medium | environment |
| `role_simulation` | Reality all | No | reality (manual override) |

---

## Output scores (0–100)

### 1. Health score (overall)

**Formula (weighted average):**

```
health = 0.25 × deployment
       + 0.15 × environment
       + 0.20 × runtime
       + 0.20 × capability
       + 0.20 × reality
       + 0.00 × commercial  # excluded unless --commercial flag
```

**Pass threshold:** health ≥ 70 **AND** no P0 submodule FAIL **AND** deployment ≥ 60

### 2. Deployment score

| Check | Points | Fail condition |
|-------|--------|----------------|
| Cold access 200 | 25 | 401 SSO |
| CORS OPTIONS 200 | 25 | 400 disallowed |
| Bundle hash matches git/deploy | 20 | missing marker |
| Preview ≠ stale (>7d without commit) | 15 | stale |
| Production parity (if `--production`) | 15 | hash mismatch >7d |

### 3. Capability score

| Check | Points | Source |
|-------|--------|--------|
| Guardrail PASS | 40 | existing script |
| Quick validate PASS | 30 | existing script |
| Demo queue API | 15 | runtime module |
| Score regression (if JSON) | 15 | cap diff |

**Default without score JSON:** guardrail + validate only → max 70 automated.

### 4. Reality score

| Check | Points | Notes |
|-------|--------|-------|
| Cold access | 30 | Same as deployment — double-weight reality impact |
| No engineer chrome | 20 | bundle grep |
| Sprint markers present | 20 | P16-O strings etc. |
| Manual override hook | 30 | `--reality-manual 85` for founder sign-off |

**Design choice:** Allow `--reality-manual SCORE` when Andy E2E log attached — prevents false Fail when automation cannot judge UX.

### 5. Environment score

| Check | Points |
|-------|--------|
| validate_pilot_deploy_env.py | 40 |
| CORS origin listed (inferred from OPTIONS) | 30 |
| git ui/ clean | 15 |
| Vercel env (if token) | 15 |

### 6. Risk score (inverse — lower is better)

**Formula:**

```
risk = Σ (pattern_weight × open_status)
```

| FP | Weight if FAIL |
|----|----------------|
| FP-004 Preview SSO | 25 |
| FP-001 Parity | 20 |
| FP-002 CORS | 20 |
| FP-003 Feature flags | 15 |
| FP-008 Reality gap | 15 |
| FP-009 Commercial | 10 |

**Output:** `risk_score` 0–100 where **0 = clean**, **100 = trial blocked**

Display: `Risk: 72 (HIGH) — FP-004, FP-013 open`

---

## Sample human output

```
POST SPRINT HEALTH CHECK — P16-R
Branch: sprint-a/broker-front-door
Preview: https://ui-iwnyo9ufa.vercel.app

DEPLOY
  cold_access .............. FAIL (401 SSO)
  cors_preflight ........... PASS
  bundle_hash .............. index-CKPYkrkL.js
  marker_grep .............. PASS (请把您的需求发给我们)
  prod_parity .............. FAIL (hash mismatch, 41d stale)

ENVIRONMENT
  pilot_env ................ PASS
  git_ui_clean ............. PASS

RUNTIME
  api_smoke ................ PASS (via curl, no browser)
  guardrail ................ PASS (local)

SCORES
  Deployment ............... 55/100
  Environment .............. 85/100
  Runtime .................. 90/100
  Capability ............... 85/100
  Reality .................. 45/100
  Risk ..................... 68/100 (HIGH)

OVERALL .................... FAIL
Blockers: FP-004 Preview SSO, FP-013 Production stale

Next: Disable Vercel Deployment Protection → re-run
```

---

## Sample JSON output

```json
{
  "sprint": "P16-R",
  "branch": "sprint-a/broker-front-door",
  "timestamp": "2026-06-01T12:00:00Z",
  "urls": {
    "preview": "https://ui-iwnyo9ufa.vercel.app",
    "production": "https://ui-smoky-beta.vercel.app"
  },
  "scores": {
    "health": 62,
    "deployment": 55,
    "environment": 85,
    "runtime": 90,
    "capability": 85,
    "reality": 45,
    "risk": 68
  },
  "overall": "FAIL",
  "blockers": ["FP-004", "FP-013"],
  "checks": [
    {"id": "cold_access", "section": "deploy", "pass": false, "detail": "HTTP 401"},
    {"id": "cors_preflight", "section": "deploy", "pass": true},
    {"id": "bundle_marker_请把您的需求发给我们", "section": "deploy", "pass": true}
  ]
}
```

---

## Dependencies

| Dependency | Required | Notes |
|------------|----------|-------|
| `curl` | Yes | Cold access, CORS, bundle fetch |
| `grep`, `jq` | Yes | Parsing |
| Python 3 | Yes | `validate_pilot_deploy_env.py` |
| Local demo running | Optional | `--skip-local` for remote-only |
| `VERCEL_TOKEN` | Optional | Vercel env audit (Medium) |
| `gcloud` | Optional | CORS auto-patch (future) |

---

## Integration with operator surface

| Existing script | Relationship |
|-----------------|--------------|
| `demo_pre_checklist.sh` | Called in `phase_local` |
| `guardrail_inbox_triage.sh` | Called in `phase_capability` |
| `trial_readiness_check.sh` | Called if `--commercial` |
| `summarize_readiness_posture.sh` | API readiness probe |
| `health_check.sh` | **Not** reused — lab 8011 stack; different purpose |

**AGENTS.md addition (future):**

```
Post-sprint validation: bash scripts/post_sprint_check.sh --preview URL
```

---

## Phased implementation plan (post P16-S)

| Version | Scope | Est. effort |
|---------|-------|-------------|
| v0.1 | E1–E8 from automation report | 4 hrs |
| v0.2 | Deployment + risk scoring | 4 hrs |
| v0.3 | JSON output + `--markers` | 2 hrs |
| v0.4 | Vercel env API | 1 day |
| v1.0 | Documented in AGENTS.md + mandatory gate | 0.5 day |

---

## Non-goals (explicit)

- Browser automation (Playwright) — defer to manual Reality checklist
- Automatic Production promote
- CORS auto-patch without human approve
- Replacing founder E2E judgment

---

*End of P16-S Phase 8 — Health Check Runner Design (design only)*

# P16-U Phase 2 — Failure Pattern Mapping

**Date:** 2026-06-01  
**Source:** `post_sprint_check.sh` baseline + supplementary curl evidence  
**Library:** `FAILURE_PATTERN_LIBRARY.md` V1

---

## Automated FAIL → Pattern map

### FAIL 1 — `preview_url_reachable` (HTTP 401)

| Field | Value |
|-------|-------|
| **Failure** | Cold curl to Preview alias returns HTTP 401 |
| **Pattern** | **FP-004** — Preview Protection (SSO Wall) |
| **Root cause** | Vercel Deployment Protection enabled on Preview; broker-facing alias documented as shareable but requires Vercel account or `vercel curl` |
| **Recommended fix** | Andy disables Deployment Protection for Preview in Vercel project settings **or** publishes a protection-disabled deployment URL for Chen Kui; re-run cold curl until HTTP 200 |

**Evidence:**
```
HTTP/2 401
set-cookie: _vercel_sso_nonce=...
```

---

### FAIL 2 — `preview_protection_absent` (SSO/401 detected)

| Field | Value |
|-------|-------|
| **Failure** | Same 401 — runner duplicate check for FP-004 |
| **Pattern** | **FP-004** — Preview Protection (SSO Wall) |
| **Root cause** | Same as above — not a separate defect |
| **Recommended fix** | Same as FAIL 1 |

---

## WARN → Pattern map

### WARN — `pilot_env_posture`

| Field | Value |
|-------|-------|
| **Failure** | Local `.env.cloudrun` failed `validate_pilot_deploy_env.py` |
| **Pattern** | **FP-011** — Environment Drift (local file ≠ pilot tuple) |
| **Root cause** | Missing `UNIFIED_INTAKE_PRODUCT_ONLY=1`, `UNIFIED_INTAKE_PG_DUAL_WRITE=0`, DB-primary flags; API keys stored in Secret Manager on Cloud Run but not in local file |
| **Recommended fix** | Sync pilot posture flags to `.env.cloudrun` (P16-U applied); API keys remain infra/founder task |

**Pre-fix errors (8):** product_only, DB flags, PG_DUAL_WRITE=1  
**Post-fix errors (2):** intake + support API keys only

---

## Informational parity (not runner FAIL, but mapped)

### Parity note — Preview ≠ Production bundle

| Field | Value |
|-------|-------|
| **Failure** | `index-CKPYkrkL.js` (Preview) vs `index-ctrXdUgj.js` (Production) |
| **Pattern** | **FP-001** Deployment Parity + **FP-013** Preview/Production Divergence |
| **Root cause** | Production not promoted since ~2026-04-21; intentional defer during P16-R |
| **Recommended fix** | After FP-004 cleared: `vercel deploy --prod` with `-b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` + P16-O bundle; verify Production markers |

**Production bundle grep:** P16-O marker `请把您的需求发给我们` — **0×**  
**Preview bundle grep:** P16-O marker — **1×** (vercel curl)

---

## Compound patterns (reality layer)

These are not separate runner FAILs but explain why trial remains blocked:

| Symptom | Pattern | Status |
|---------|---------|--------|
| Andy sends Preview link → broker sees login | FP-004 + **FP-010** Founder Assumption | Open |
| Local 80% health vs broker 12/100 cold | **FP-008** Reality Gap | Open |
| Production 200 but wrong UI | FP-013 + **FP-016** Wrong Default Tab | Open |
| No Andy E2E log on deployed URL | **FP-015** Missing Evidence | Open |
| Chen Kui Day 0 stops at link | **FP-014** Broken Trial Flow | Open (compound) |

---

## Pattern index for this run

| FP | Name | Mapped from | Severity |
|----|------|-------------|----------|
| FP-004 | Preview SSO | 2 FAIL checks | P0 |
| FP-011 | Environment drift | 1 WARN | P1 |
| FP-001 | Deployment parity | Parity note | P0 |
| FP-013 | Prod frozen | Parity note | P0 |
| FP-008 | Reality gap | Section summary | P0 |
| FP-010 | Founder assumption | Compound | P0 |
| FP-014 | Broken trial flow | Compound | P0 |
| FP-015 | Missing evidence | Compound | P1 |
| FP-016 | Wrong default tab | Production bundle | P0 |

**Patterns NOT triggered (would have been runner FAIL):** FP-002 CORS, FP-003 feature flags (Preview), FP-005 not deployed (Preview bundle current)

---

*End of P16-U Phase 2 — Failure Pattern Mapping*

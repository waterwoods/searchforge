# P16-S Phase 7 — Automation Report

**Date:** 2026-06-01  
**Sprint:** P16-S Failure Pattern Library + Post Sprint Health Check  
**Purpose:** Identify which failure patterns can be detected automatically; classify effort

**Reference:** `FAILURE_PATTERN_LIBRARY.md`, existing scripts in `scripts/`

---

## Executive summary

| Classification | Count | Patterns |
|----------------|-------|----------|
| **Easy** | 8 | CORS preflight, cold URL status, bundle hash, env vars (backend), guardrail, readiness, git clean, feature flag grep |
| **Medium** | 7 | Preview SSO, deployment parity, Vercel env, bundle string parity, capability regression diff, CORS auto-patch, production staleness |
| **Hard** | 5 | Reality role simulation, commercial evidence, draft language quality, founder E2E, UI 10-second test |

**Recommendation:** Ship Easy bundle first (~2–4 hrs implement); Medium in `post_sprint_check.sh` v1 (~1–2 days); Hard remains manual checklist.

---

## Pattern-by-pattern automation matrix

| FP | Pattern | Automatable? | Class | Detection method | Existing script |
|----|---------|--------------|-------|------------------|-----------------|
| FP-001 | Deployment Parity | **Partial** | Medium | Compare bundle hashes + string sets across 3 URLs | — |
| FP-002 | CORS | **Yes** | Easy | `curl OPTIONS -H Origin:URL` | Partial in manual audits |
| FP-003 | Feature Flag Drift | **Partial** | Medium | Grep bundle for Simulation/dev strings | — |
| FP-004 | Preview Protection | **Yes** | Easy | `curl -sI URL \| grep 401` | — |
| FP-005 | Not Deployed | **Partial** | Medium | Grep sprint marker strings in remote bundle | P16R parity pattern |
| FP-006 | Runtime Error | **Partial** | Medium | API smoke + CORS classify | `demo_quick_validate.sh` |
| FP-007 | UI Complexity | **No** | Hard | Visual/heuristic test | — |
| FP-008 | Reality Gap | **Partial** | Hard | Score delta Local vs Preview automated; role sim manual | — |
| FP-009 | Commercial Gap | **Partial** | Easy/Medium | Grep invoice placeholders; log file row count | `trial_readiness_check.sh` |
| FP-010 | Founder Assumption | **No** | Hard | Requires human E2E log | — |
| FP-011 | Environment Drift | **Yes** | Easy | `validate_pilot_deploy_env.py`, `demo_pre_checklist.sh` | ✅ Exists |
| FP-012 | Capability Regression | **Partial** | Medium | Diff capability scores JSON if tracked | — |
| FP-013 | Preview/Production Divergence | **Yes** | Easy | Compare bundle hashes + dates | — |
| FP-014 | Broken Trial Flow | **No** | Hard | Multi-day simulation | — |
| FP-015 | Missing Evidence | **Partial** | Medium | Check file exists: E2E log, observation log mtime | — |
| FP-016 | Wrong Default Tab | **Partial** | Medium | Fetch HTML/JS; grep default route strings | — |
| FP-017 | Engineer Chrome | **Partial** | Easy | Grep bundle for PG镜像, 场景仿真 | — |
| FP-018 | Draft Language | **Partial** | Hard | POST sample Chinese; detect response language | API test extend |
| FP-019 | Git/Vercel Disconnect | **Partial** | Medium | Compare git push time vs deploy API | Needs Vercel token |
| FP-020 | Scope Creep | **Partial** | Medium | Git log during trial date range | — |

---

## Easy (implement first)

### E1 — CORS preflight check

| Field | Detail |
|-------|--------|
| **Patterns** | FP-002, FP-006 |
| **Input** | `PREVIEW_URL`, `API_BASE_URL` |
| **Logic** | `curl -sI -X OPTIONS -H "Origin: $PREVIEW" "$API/api/inbox/cases"` → expect 200 + ACAO |
| **Output** | PASS/FAIL + origin echoed |
| **Effort** | ~30 min |
| **Existing** | Manual in P16R audits |

### E2 — Cold URL / Preview SSO

| Field | Detail |
|-------|--------|
| **Patterns** | FP-004, FP-014 |
| **Input** | `PREVIEW_URL` |
| **Logic** | `curl -sI "$URL"` → fail if 401 or `_vercel_sso_nonce` in body |
| **Output** | PASS/FAIL |
| **Effort** | ~15 min |

### E3 — Bundle hash extraction

| Field | Detail |
|-------|--------|
| **Patterns** | FP-001, FP-005, FP-013 |
| **Input** | Any deploy URL |
| **Logic** | `curl -s URL \| grep -oE 'index-[A-Za-z0-9]+\.js' \| head -1` |
| **Output** | Hash string; compare across envs |
| **Effort** | ~20 min |

### E4 — Backend pilot posture

| Field | Detail |
|-------|--------|
| **Patterns** | FP-011, FP-003 (backend half) |
| **Input** | `.env.cloudrun` |
| **Logic** | `python3 scripts/validate_pilot_deploy_env.py` |
| **Output** | exit 0/1 |
| **Effort** | ✅ Done |

### E5 — Local guardrail + readiness

| Field | Detail |
|-------|--------|
| **Patterns** | FP-006, FP-012 (Cap 2) |
| **Input** | localhost:8001 |
| **Logic** | `guardrail_inbox_triage.sh` + `demo_quick_validate.sh` |
| **Output** | PASS/FAIL |
| **Effort** | ✅ Done |

### E6 — Engineer chrome grep

| Field | Detail |
|-------|--------|
| **Patterns** | FP-017, FP-003 (frontend) |
| **Input** | Deploy URL |
| **Logic** | Fetch main JS bundle; grep `场景仿真\|PG镜像\|VITE_API` |
| **Output** | FAIL if matches on product_only URL |
| **Effort** | ~45 min |

### E7 — Invoice placeholder grep

| Field | Detail |
|-------|--------|
| **Patterns** | FP-009 |
| **Input** | `docs/trial/` invoice templates |
| **Logic** | `rg '\[Andy (Zelle\|Venmo\|WeChat)' docs/` → fail if hits |
| **Output** | PASS/FAIL |
| **Effort** | ~15 min |

### E8 — Git clean ui/

| Field | Detail |
|-------|--------|
| **Patterns** | FP-005 |
| **Input** | repo root |
| **Logic** | `git status --porcelain ui/` → fail if dirty before deploy |
| **Output** | PASS/FAIL |
| **Effort** | ~10 min |

---

## Medium (v1 runner scope)

### M1 — Deployment parity scorer

| Field | Detail |
|-------|--------|
| **Patterns** | FP-001, FP-013 |
| **Input** | local, preview, production URLs |
| **Logic** | Hash compare + optional sprint marker string set |
| **Output** | deployment_score 0–100; FAIL if delta > threshold |
| **Effort** | ~4 hrs |
| **Blocker** | Need stable marker strings per sprint |

### M2 — Vercel env audit (API)

| Field | Detail |
|-------|--------|
| **Patterns** | FP-003, FP-011 |
| **Input** | Vercel token, project ID |
| **Logic** | Vercel API → list env vars; check PRODUCT_ONLY + API_BASE |
| **Output** | PASS/FAIL per var |
| **Effort** | ~4 hrs |
| **Blocker** | Requires `VERCEL_TOKEN` secret |

### M3 — CORS auto-patch hook

| Field | Detail |
|-------|--------|
| **Patterns** | FP-002, FP-004 |
| **Input** | New Preview URL post-deploy |
| **Logic** | Append origin to Cloud Run ALLOWED_ORIGINS + redeploy |
| **Output** | Updated env |
| **Effort** | ~6 hrs |
| **Blocker** | GCP credentials; safety review |

### M4 — Production staleness alarm

| Field | Detail |
|-------|--------|
| **Patterns** | FP-013 |
| **Input** | prod + preview hashes |
| **Logic** | FAIL if same hash > 7 days OR prod ≠ preview after promote gate |
| **Output** | days_stale, alert |
| **Effort** | ~2 hrs |

### M5 — Evidence file presence

| Field | Detail |
|-------|--------|
| **Patterns** | FP-015 |
| **Input** | Sprint ID |
| **Logic** | Check `*E2E*`, observation log non-empty |
| **Output** | PASS/FAIL |
| **Effort** | ~2 hrs |

### M6 — Bundle string parity (sprint markers)

| Field | Detail |
|-------|--------|
| **Patterns** | FP-005, FP-008 |
| **Input** | Marker strings from sprint verdict |
| **Logic** | curl bundle | grep each marker |
| **Output** | missing[] list |
| **Effort** | ~3 hrs |

### M7 — Capability score regression diff

| Field | Detail |
|-------|--------|
| **Patterns** | FP-012 |
| **Input** | pre/post JSON score file |
| **Logic** | Fail if any cap Δ < -5 without waiver |
| **Effort** | ~3 hrs |
| **Blocker** | Need committed score JSON per sprint |

---

## Hard (manual checklist only)

### H1 — Role simulation (Chen Kui, Role C, Assistant)

| Field | Detail |
|-------|--------|
| **Patterns** | FP-008, FP-010, FP-014 |
| **Why hard** | Judgment, language, trust signals |
| **Mitigation** | P16-Q simulation template as manual section |

### H2 — UI 10-second / 5-second test

| Field | Detail |
|-------|--------|
| **Patterns** | FP-007 |
| **Why hard** | Visual hierarchy subjective |
| **Mitigation** | Optional: Playwright screenshot + human review |

### H3 — Draft language quality

| Field | Detail |
|-------|--------|
| **Patterns** | FP-018 |
| **Why hard** | NLP quality judgment |
| **Partial auto** | POST Chinese sample; fail if response mostly ASCII English |

### H4 — Founder 15-min E2E

| Field | Detail |
|-------|--------|
| **Patterns** | FP-010, FP-015 |
| **Why hard** | Human certification |
| **Mitigation** | Checklist + log file template; fail if log missing |

### H5 — Payment relationship judgment

| Field | Detail |
|-------|--------|
| **Patterns** | FP-009 |
| **Why hard** | "Would damage relationship" is human |
| **Partial auto** | All CM* checks from POST_SPRINT_HEALTH_CHECK |

---

## Existing script reuse map

| Script | Covers | Gap |
|--------|--------|-----|
| `run_demo_local.sh` | Local deploy L1 | No remote |
| `guardrail_inbox_triage.sh` | Cap 2 runtime | No CORS/browser |
| `demo_quick_validate.sh` | API smoke | localhost only |
| `validate_pilot_deploy_env.py` | Backend env E4 | No Vercel frontend |
| `trial_readiness_check.sh` | Commercial partial | No URL parity |
| `trial_launch_check.sh` | Pre-trial bundle | Not post-sprint |
| `demo_pre_checklist.sh` | Local preflight | No Preview |
| `check_unified_intake_prod_posture.sh` | Prod backend | No frontend |
| `health_check.sh` | Lab stack 8011 | Wrong port/product |
| `summarize_readiness_posture.sh` | Readiness probe | Extend for Preview |

---

## Recommended automation roadmap

| Phase | Deliverable | Patterns | Effort |
|-------|-------------|----------|--------|
| **A** | `scripts/post_sprint_check.sh` Easy bundle | FP-002,004,011,013,017 | 4 hrs |
| **B** | Parity scorer + bundle markers | FP-001,005,008 | 1 day |
| **C** | Vercel env audit (token) | FP-003,019 | 1 day |
| **D** | CORS auto-patch hook | FP-002 | 1 day |
| **E** | Score JSON + regression diff | FP-012 | 0.5 day |

**Do not automate yet:** FP-007, FP-010, FP-014 — keep in REALITY_VALIDATION_CHECKLIST manual.

---

## CI integration suggestion

```yaml
# Future .github/workflows/post-sprint-health.yml (design only)
on:
  workflow_dispatch:
    inputs:
      preview_url: required
      production_url: optional
jobs:
  health:
    runs:
      - scripts/post_sprint_check.sh --preview ${{ inputs.preview_url }}
```

---

*End of P16-S Phase 7 — Automation Report*

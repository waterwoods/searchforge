# P16 Pre-Commit Review

**Date:** 2026-06-06  
**Mission:** P16-REPO-COMMIT-AND-PRESERVE-SPRINT — Phase 1  
**Branch:** `sprint-a/broker-front-door` @ `517f728`  
**Audience:** Founder — maximum 2 pages

---

## Executive Summary

The working tree contains **1,775 dirty paths**. Almost all of it (**94.5%**) is intentional documentation housekeeping from an archival migration — not product drift. This review confirms the classification from `P16_DIRTY_TREE_FINAL_CLASSIFICATION.md` and authorizes three hygiene commits (A → B → C) that preserve governance, release records, and sprint history **without** touching product code, scripts, or customer/broker flows.

---

## 1. What Will Be Committed?

**1,679 paths** across three commits (~94.6% of dirty tree):

| Commit | Message | Paths | Contents |
|--------|---------|------:|----------|
| **A** | `chore(repo): preserve governance and release documentation` | ~402 | Product constitution (`P16_*.md`), founder memos, repo census, promotion gates, branch archaeology, audit reports, operator onboarding (`AGENTS.md`, `FOUNDER_ONE_PATH.md`, `15_MINUTE_ENGINEER_ONBOARDING.md`), doc system map |
| **B** | `chore(repo): preserve release and deployment records` | ~46 | Deployment readiness, trial docs (`docs/trial/`), runbooks, release verification, environment preservation, rollback references, deploy alignment audits |
| **C** | `chore(repo): archive historical sprint artifacts` | ~1,231 | 1,228 deleted legacy sprint reports from `docs/` root, 471 new paths under `docs/sprints/archive/` and `docs/archive/`, historical investigations, legacy sprint documentation |

**Why three commits?** Single 1,679-path commit is unreviewable. Splitting by purpose enables bisect, rollback, and clear audit trail: governance first, release records second, bulk archive last.

---

## 2. What Will NOT Be Committed?

### DO_NOT_COMMIT (3 paths — never stage)

| Path | Reason |
|------|--------|
| `configs/demo.env.example` | Env template; verify no secrets before any future commit |
| `demo_brain_report.html` | Generated local HTML report |
| `docs/archive/root_archaeology/demo_brain_report.html` | Duplicate generated artifact |

### REVIEW_REQUIRED (93 paths — deferred to next sprint)

These affect demo runtime, product behavior, or infrastructure. **Excluded from A/B/C** per mission scope (no feature work, no triage/AC changes):

| Category | Count | Examples |
|----------|------:|---------|
| Scripts | 40 | `run_demo_local.sh`, `trial_launch_check.sh`, `scripts/deploy/` |
| Source code (UI + API) | 24 | `ui/src/App.tsx`, `services/fiqa_api/app_main.py`, `case_store.py` |
| Configs / infrastructure | 23 | `docker-compose.yml`, `Makefile`, `configs/p16z24_add_car_customers.json` |
| Tests | 3 | `test_deployment_profile.py`, `test_operator_surface_collapse.py` |
| Unknown | 3 | `pipelines/`, `ui/src/routes/`, `ui/src/features/intake/prototypes/` |

**Explicit exclusions per founder priorities:** `triage.py`, AC03/AC05/AC07 flows, Cloud Run, Vercel — none are in SAFE_TO_COMMIT; any related dirty paths stay in REVIEW_REQUIRED.

---

## 3. Why?

| Decision | Rationale |
|----------|-----------|
| Commit docs now | 94.5% of dirt is archival migration; leaving it uncommitted risks data loss and blocks promotion |
| Defer scripts/source | 93 paths change demo runtime or product behavior; require line-by-line founder review |
| Exclude generated HTML | Local artifacts, not reproducible from repo |
| Exclude `demo.env.example` | Env templates may contain local overrides; verify before commit |
| No main merge this sprint | Preservation first; promotion decision follows clean tree + push |

---

## Verification Checklist

- [x] SAFE_TO_COMMIT count matches classification (1,679 paths)
- [x] DO_NOT_COMMIT (3) excluded from all staging
- [x] REVIEW_REQUIRED (93) excluded from all staging
- [x] Release refs verified locally: `release/p16-demo-ready-v1`, `p16-demo-ready-v1`, `archive/production-pre-p16-demo`
- [x] No branches deleted, no history rewritten, no infrastructure deployed

**Authorized to proceed:** Commits A → B → C.

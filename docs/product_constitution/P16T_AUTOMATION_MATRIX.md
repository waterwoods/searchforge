# P16-T Phase 4 — Failure Pattern Automation Matrix

**Date:** 2026-06-01  
**Scope:** Top 20 failure patterns from `FAILURE_PATTERN_LIBRARY.md`  
**Runner:** `scripts/post_sprint_check.sh` v0.1  
**Reference:** `P16S_AUTOMATION_REPORT.md` (updated with P16-T implementation status)

---

## Classification legend

| Class | Meaning |
|-------|---------|
| **Automated** | Detected by `post_sprint_check.sh` or existing script without human |
| **Partially automated** | Script detects proxy signal; human confirms or second step needed |
| **Not automated** | Manual checklist / founder judgment only |

---

## Matrix (FP-001 – FP-020)

| FP | Pattern | Severity | Class | Detection | Script / check |
|----|---------|----------|-------|-----------|----------------|
| FP-001 | Deployment Parity | P0 | **Partially automated** | Bundle hash mismatch logged; marker grep on Preview | `post_sprint_check.sh` parity note + markers |
| FP-002 | CORS Origin Block | P0 | **Automated** | OPTIONS preflight 200 + ACAO | `cors_preflight` |
| FP-003 | Feature Flag Drift | P0 | **Partially automated** | Product-only Chinese markers in Preview bundle | `product_only_flag` (bundle grep, not dashboard) |
| FP-004 | Preview Protection | P0 | **Automated** | Cold curl 401 / SSO | `preview_url_reachable`, `preview_protection_absent` |
| FP-005 | Not Deployed | P0 | **Partially automated** | Sprint marker strings missing from remote bundle | `bundle_sprint_markers`, `git_commit` |
| FP-006 | Runtime Error | P1 | **Partially automated** | API `/readyz`; CORS classify | `cloud_run_health`, `cors_preflight` |
| FP-007 | UI Complexity Creep | P1 | **Not automated** | 10-sec / 5-sec visual test | REALITY_VALIDATION_CHECKLIST |
| FP-008 | Reality Gap | P0 | **Partially automated** | Local vs Preview marker delta; no score auto | Runner + manual scorecard |
| FP-009 | Commercial Gap | P1 | **Partially automated** | Invoice placeholder grep exists (`trial_readiness_check.sh`) | Not in v0.1 runner |
| FP-010 | Founder Assumption | P0 | **Not automated** | Andy incognito E2E log | REALITY Q1–Q2 |
| FP-011 | Environment Drift | P1 | **Partially automated** | `validate_pilot_deploy_env.py` WARN; local demo scripts | Optional runner line |
| FP-012 | Capability Regression | P1 | **Not automated** | 7-cap score diff | POST_SPRINT § Capability |
| FP-013 | Preview/Production Divergence | P0 | **Partially automated** | Hash compare Preview vs Prod | Parity note in runner |
| FP-014 | Broken Trial Flow | P0 | **Not automated** | Multi-day journey sim | TRIAL_ONE_PATH manual |
| FP-015 | Missing Evidence | P1 | **Not automated** | E2E log / observation log exists | REALITY Q21–23 |
| FP-016 | Wrong Default Tab | P0 | **Partially automated** | product_only markers imply broker-first build | `product_only_flag` (proxy) |
| FP-017 | Engineer Chrome | P2 | **Partially automated** | Simulation/PG grep (future `--strict-chrome`) | Partial via product_only markers |
| FP-018 | Draft Language | P2 | **Not automated** | Chinese paste → draft language quality | API test extend (future) |
| FP-019 | Git/Vercel Disconnect | P1 | **Partially automated** | Git branch/commit recorded; no deploy timestamp API | `git_branch`, `git_commit` |
| FP-020 | Scope Creep | P1 | **Not automated** | Git log during trial window | Manual freeze review |

---

## Summary counts

| Classification | Count | FP-IDs |
|----------------|-------|--------|
| **Automated** | 2 | FP-002, FP-004 |
| **Partially automated** | 11 | FP-001, FP-003, FP-005, FP-006, FP-008, FP-009, FP-011, FP-013, FP-016, FP-017, FP-019 |
| **Not automated** | 7 | FP-007, FP-010, FP-012, FP-014, FP-015, FP-018, FP-020 |

---

## Coverage by POST_SPRINT_HEALTH_CHECK section

| Section | Automated today | Partial | Manual only |
|---------|-----------------|---------|-------------|
| Deploy | P1, P4, PR1, P2 (markers) | P3, PA1–PA4 | P5 E2E browser |
| Environment | — | C3 WARN | V1–V4, C1–C2, F1–F3 |
| Runtime | R6 | R2–R3 via CORS | R1, R4–R5, R7–R8 |
| Capability | — | — | All 7 caps + CP1–3 |
| Reality | Q24–26 proxy | Q4–6 proxy | Q1–23 most |
| Commercial | — | trial_readiness (separate) | CM1–CM5 |

---

## Roadmap (post P16-T)

| Priority | Enhancement | FPs addressed | Effort |
|----------|-------------|---------------|--------|
| P0 | Fail runner if prod bundle ≠ preview hash >7d | FP-001, FP-013 | 2 hrs |
| P0 | `--strict-preview` fail if vercel curl needed | FP-004 clarity | 30 min |
| P1 | Vercel env API check | FP-003, FP-019 | 1 day |
| P1 | Invoice placeholder in `--commercial` | FP-009 | 15 min |
| P2 | Chinese draft language smoke | FP-018 | 4 hrs |
| P2 | JSON output + CI workflow_dispatch | All automated | 4 hrs |

---

## P16-T impact

Before P16-T: **0** checks in single post-sprint script.  
After P16-T v0.1: **10** checks, **2** FPs fully automated, **11** partially covered.

**Estimated time saved per sprint:** 45–90 min of manual curl/grep repetition (conservative).

---

*End of P16-T Phase 4 — Automation Matrix*

# P16-T Phase 1 — P16-S Baseline Review

**Date:** 2026-06-01  
**Sprint:** P16-T Health Check Runner v0.1 + Reality Closure  
**Inputs reviewed:** P16-S deliverables (Phases 1–10)

---

## Purpose

Confirm P16-S artifacts are sufficient to operationalize post-sprint health checks before implementing `post_sprint_check.sh`.

---

## Document review

### `FAILURE_PATTERN_LIBRARY.md`

| Aspect | Assessment |
|--------|------------|
| **Completeness** | 20 patterns (FP-001–FP-020) with symptoms, root cause, detection, fix, prevention |
| **Operability** | Each FP maps to detection methods — many are curl/grep/scriptable |
| **Gaps** | Index "Still open P16-R" is stale baseline; P16-T must re-verify FP-001–004 |
| **Verdict** | ✅ Ready — mandatory reference for runner blockers |

**Key insight:** Four P0 patterns (FP-001–004) account for most deploy/reality waste. Runner v0.1 must detect these first.

---

### `POST_SPRINT_HEALTH_CHECK.md`

| Aspect | Assessment |
|--------|------------|
| **Structure** | Six sections: Deploy, Environment, Runtime, Capability, Reality, Commercial |
| **Gate rules** | P1/P4/PA1/PA3 fail → Deploy fail; V1/V2/V3/C1/F1 fail → Environment fail |
| **Evidence rule** | curl transcript / bundle hash required — not "looks fine" |
| **Gaps** | 40+ manual rows; only ~10 automatable in v0.1 without browser |
| **Verdict** | ✅ Ready as manual gate; runner covers minimum deploy/API subset |

**Mapping to runner v0.1:**

| Health check row | Runner check |
|------------------|--------------|
| P1 Cold access | `preview_url_reachable` + `preview_protection_absent` |
| P4 CORS | `cors_preflight` |
| P2 Sprint strings | `bundle_sprint_markers` |
| PR1 Production accessible | `production_url_reachable` |
| R6 Readiness | `cloud_run_health` |
| F1 product_only | `product_only_flag` |
| G1 Branch | `git_branch` / `git_commit` |

---

### `REALITY_VALIDATION_CHECKLIST.md`

| Aspect | Assessment |
|--------|------------|
| **Rule** | Localhost PASS necessary but not sufficient |
| **Pass threshold** | Zero No on Preview survival (Q24–27) and Broker Day 0 (Q13–14) |
| **P16-R baseline** | Andy Fail (SSO), Broker Fail, Production Fail (41d stale) |
| **Gaps** | 30 questions — 22+ require human judgment or browser |
| **Verdict** | ✅ Ready as founder gate; automation cannot replace Reality section |

**Runner relationship:** Automates Q24 (cold curl), Q25 (CORS), Q26 (bundle grep). Q1–23 remain manual.

---

### `P16S_HEALTHCHECK_RUNNER_DESIGN.md`

| Aspect | Assessment |
|--------|------------|
| **Entry point** | `scripts/post_sprint_check.sh` (primary) |
| **CLI** | `--preview`, `--production`, `--api`, `--markers`, `--sprint` |
| **Scoring** | Weighted health + risk score — deferred to v0.2 |
| **Non-goals** | No Playwright, no auto-prod, no CORS auto-patch |
| **Verdict** | ✅ Design approved for v0.1 implementation in P16-T |

**P16-T scope vs design:**

| Design element | P16-T v0.1 |
|----------------|------------|
| 10 minimum checks | ✅ Implemented |
| JSON output | Deferred v0.2 |
| Weighted scores | Simplified pass/fail ratio |
| `--reality-manual` | Deferred |
| vercel curl fallback | ✅ Added for 401 preview bundle |

---

## P16-S success criterion (restated)

> Future Andy has a checklist that catches FP-004 (SSO) and FP-005 (not deployed) **before** sprint close.

**P16-T closes the remaining gap:** P16-S created the checklist and design; P16-T ships the script.

---

## Baseline state entering P16-T

| Item | P16-S status | P16-T action |
|------|--------------|--------------|
| Failure vocabulary | ✅ 20 FPs | Re-audit FP-001–004 |
| Manual health check | ✅ Document | Run with live data (Phase 6) |
| Runner script | ❌ Design only | **Implement v0.1** |
| Automation matrix | ✅ P16S_AUTOMATION_REPORT | Extend in Phase 4 |
| AGENTS.md entry | ❌ Not added | Optional post-P16-T (out of scope) |

---

## Conclusion

P16-S documentation is **complete and operationalizable**. P16-T should:

1. Not modify Constitution or P16-S docs
2. Implement runner per design (minimum 10 checks)
3. Re-verify FP-001–004 with live curl evidence
4. Fill POST_SPRINT_HEALTH_CHECK with actual 2026-06-01 data

**Baseline review:** ✅ PASS — proceed to reality closure audit.

---

*End of P16-T Phase 1 — Baseline Review*

# P16-T Phase 8 — Final Verdict

**Date:** 2026-06-01  
**Sprint:** P16-T Health Check Runner v0.1 + Reality Closure  
**Type:** Systems sprint — runner implementation + audits; no product features; no Constitution edits; no P17

---

## Executive summary

P16-T converts P16-S from **documents into an operational process**. Future sprints can run:

```bash
bash scripts/post_sprint_check.sh
```

and receive a meaningful **PASS / FAIL** report in ~7 seconds. First live run: **FAIL** (8/10) — correctly identifying FP-004 as the remaining P0 blocker.

---

## Required answers

### 1. Is Health Check Runner operational?

**Yes.**

| Criterion | Status |
|-----------|--------|
| Script exists | `scripts/post_sprint_check.sh` |
| 10 minimum checks | ✅ Implemented |
| PASS/FAIL output | ✅ |
| Exit code 0/1 | ✅ Verified |
| Default URLs | P16-R canonical |
| FP hints on fail | ✅ |
| vercel curl fallback | ✅ For SSO-blocked bundle audit |

---

### 2. Which failure patterns are now prevented?

**Fully auto-detected (will FAIL sprint gate):**

- FP-002 — CORS origin block (current deploy)
- FP-004 — Preview SSO / 401

**Partially prevented (detected or logged):**

- FP-001 — Parity note + marker grep
- FP-003 — product_only bundle markers
- FP-005 — Sprint marker grep
- FP-006 — API readiness
- FP-013 — Hash mismatch Preview vs Prod
- FP-016 — product_only proxy markers
- FP-019 — Git branch/commit recorded

**Not prevented by runner (manual gate still required):**

- FP-007, FP-008, FP-009, FP-010, FP-012, FP-014, FP-015, FP-018, FP-020

---

### 3. Which are still open?

| FP | Status (2026-06-01) |
|----|---------------------|
| FP-001 | Open — Production stale |
| FP-002 | Closed today — latent on redeploy |
| FP-003 | Open — dashboard env not persisted |
| FP-004 | **Open — Preview 401 SSO** |
| FP-008 | Open — reality gap until cold access |
| FP-009 | Open — commercial |
| FP-010 | Open — no E2E log |
| FP-013 | Open — prod ≠ preview |
| FP-014 | Open — trial flow blocked at Day 0 |

See `P16T_REALITY_CLOSURE_AUDIT.md` for FP-001–004 detail.

---

### 4. Has Deployment Reality improved?

| Dimension | P16-R end | P16-T |
|-----------|-----------|-------|
| Preview bundle content | ✅ P16-O + product_only | ✅ Unchanged — still correct |
| Preview cold access | ❌ 401 | ❌ Still 401 |
| CORS | ✅ Patched | ✅ Verified PASS |
| Production | ❌ 41d stale | ❌ Still stale |
| Detection process | Manual audit hours | **7-sec script** |

**Net:** Deployment **content** on Preview unchanged (good). Deployment **process** improved materially (repeatable gate). Distribution reality **unchanged** for brokers.

---

### 5. Is Preview safe for founder testing?

| Mode | Safe? | Notes |
|------|-------|-------|
| Cold URL / incognito | **No** | 401 SSO |
| `vercel curl` / logged-in Vercel | **Yes** | Bundle verified correct |
| localhost | **Yes** | Not deployed reality |

**After Andy disables Deployment Protection:** Re-run runner → checks 4+6 should PASS → then 15-min E2E.

---

### 6. Is Production safe?

| Question | Answer |
|----------|--------|
| Cold HTTP | ✅ 200 |
| Correct trial UI | ❌ Wrong — pre-P16-O, no product_only |
| Safe to send to Chen Kui | **No** — wrong default tab, stale bundle |
| API health | ✅ CORS + `/readyz` OK |

Production is **reachable but misleading** for trial wedge.

---

### 7. What must happen before Chen Kui Day 0?

| Priority | Action | Owner |
|----------|--------|-------|
| P0 | Disable Preview SSO | Andy |
| P0 | `post_sprint_check.sh` → overall PASS | Andy/Agent |
| P0 | Andy 15-min Preview E2E log | Andy |
| P1 | Persist Vercel env dashboard | Andy |
| P1 | Promote to Production OR document Preview-only trial URL | Andy |
| P1 | Fill invoice payment IDs | Andy |
| P2 | Supervised Day 0 dry run | Andy + broker |

---

### 8. Should P17 remain blocked?

**Yes.**

| Gate | Result |
|------|--------|
| POST_SPRINT_HEALTH_CHECK | FAIL |
| `post_sprint_check.sh` | FAIL (exit 1) |
| REALITY_VALIDATION Preview survival | FAIL |
| P16-R parity checklist all [x] | No |

P17 stays blocked until Preview cold PASS + founder E2E + explicit GO on Reality Gate.

---

## Deliverables index

| Phase | Document | Status |
|-------|----------|--------|
| 1 | `P16T_BASELINE_REVIEW.md` | ✅ |
| 2 | `P16T_REALITY_CLOSURE_AUDIT.md` | ✅ |
| 3 | `P16T_RUNNER_IMPLEMENTATION.md` | ✅ |
| 3 | `scripts/post_sprint_check.sh` | ✅ |
| 4 | `P16T_AUTOMATION_MATRIX.md` | ✅ |
| 5 | `P16T_DEPLOY_VERIFICATION.md` | ✅ |
| 6 | `P16T_REALITY_GATE.md` | ✅ |
| 7 | `P16T_FOUNDER_REVIEW.md` | ✅ |
| 8 | `P16T_FINAL_VERDICT.md` | ✅ |

---

## Success criterion

> A future sprint should finish and immediately run `bash scripts/post_sprint_check.sh` and receive a meaningful PASS / FAIL report.

**Met.** The goal was preventing wasted time, not shipping product. The runner fails on real blockers and passes on real fixes (CORS, bundle, API).

---

## One sentence

**P16-T makes "is the deployed product what we think?" a 7-second bash command — and today's answer is still FAIL until Andy turns off Preview SSO.**

---

*End of P16-T Health Check Runner v0.1 + Reality Closure*

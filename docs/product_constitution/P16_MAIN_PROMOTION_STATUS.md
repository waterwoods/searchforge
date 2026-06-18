# P16 Main Promotion Status

**Date:** 2026-06-06  
**Mission:** P16-PUSH-AND-GOVERNANCE-CLOSEOUT — Phase 5  
**Candidate:** `sprint-a/broker-front-door` @ `b3c8ec3`  
**Current `main`:** `31572ca` (2025-11-24)  
**Evaluation only — no merge performed**

---

## Verdict: **CONDITIONAL GO**

Main promotion is technically feasible (0 merge conflicts) but not safe until UNSURE runtime paths are resolved and founder signs off on 102+ commit scope.

---

## 1. What blockers remain?

| # | Blocker | Status | Required action |
|---|---------|--------|-----------------|
| 1 | **17 UNSURE runtime paths** unstaged | ❌ Open | Founder bundle review: commit, revert, or split per `P16_RUNTIME_GATE_REVIEW.md` |
| 2 | **Partial resolver inconsistency** | ⚠️ Open | Test deleted in `b3c8ec3`; `active_vehicle_resolver.py` deletion still unstaged — resolve Bundle D as unit |
| 3 | **Founder business sign-off** | ❌ Open | Review `git log main..sprint-a/broker-front-door` (~102 commits, large blast radius) |
| 4 | **Post-promotion validation** | ❌ Open | Run `trial_launch_check.sh` + `guardrail_inbox_triage.sh` on clean tree after UNSURE resolution |
| 5 | **Production deploy alignment** | ⚠️ Deferred | Vercel Production serves pre-P16 UX — promotion ≠ production deploy |

**Resolved since prior gate:**

- ✅ Preservation refs on origin (release branch, tag, archive, sprint tip)
- ✅ Runtime KEEP bundle committed (`b3c8ec3`)
- ✅ Sprint branch fully pushed (0 ahead of origin)

---

## 2. What runtime files remain?

### UNSURE — 17 paths (founder review required)

| Bundle | Paths |
|--------|-------|
| **A — UI** (9) | `clientConfig.ts`, `inboxTriage.ts`, `request.ts`, `BrokerWorkbenchTab.tsx`, `CustomerEntryTab.tsx`, `MyRequestsTab.tsx`, `WorkbenchSummary.tsx`, `intakePure.ts`, `UnifiedIntakePage.tsx` |
| **B — Deploy** (3) | `deploy_paid_pilot.sh`, `validate_pilot_deploy_env.py`, `triage.sh` (deleted locally) |
| **C — Config** (1) | `configs/clients/chen_kui/ui_copy.json` |
| **D — Triage** (2) | `markers.json`, `active_vehicle_resolver.py` (deleted locally) |
| **E — Persistence** (2) | `case_store.py`, `service_record_repository.py` |

### DO_NOT_COMMIT — 2 paths

| Path | Reason |
|------|--------|
| `configs/demo.env.example` | Local template |
| `demo_brain_report.html` (deleted) | Generated artifact |

These 19 tracked paths + 15 untracked closeout docs = current dirty tree (34 total).

---

## 3. Main promotion verdict

| Scenario | Verdict |
|----------|---------|
| Merge today with 17 UNSURE paths dirty | **NO GO** |
| Merge after push only (current state) | **NO GO** — UNSURE paths still unstaged |
| Merge after UNSURE resolution + trial checks | **CONDITIONAL GO** |
| Merge after clean tree + founder diff review + trial checks pass | **GO** |

**Overall: CONDITIONAL GO**

---

## 4. What exact work remains before promotion?

```
1. Resolve 17 UNSURE runtime paths
   → Commit approved bundles OR revert to HEAD
   → Resolve Bundle D (resolver) as atomic unit
   → Target: ≤2 dirty paths (DO_NOT_COMMIT only)

2. Validate on clean tree
   → bash scripts/guardrail_inbox_triage.sh
   → bash scripts/trial_launch_check.sh
   → bash scripts/demo_pre_checklist.sh

3. Founder promotion session (dedicated, ~2 hours)
   → git log --oneline main..sprint-a/broker-front-door
   → Review high-risk paths: case_store, markers, deploy scripts, demo tabs
   → Sign off on 102-commit scope

4. Execute merge (separate session)
   → git checkout main && git merge sprint-a/broker-front-door
   → git push origin main
   → Tag post-promotion if desired

5. Post-merge (optional, not blocking promotion)
   → Production Vercel redeploy
   → Cloud Run SHA alignment
   → Local branch cleanup (59 stale branches)
```

**Do NOT merge before steps 1–3.**

---

## Merge Mechanics (unchanged)

```bash
git merge-base main HEAD  → 31572ca
git log --oneline main..HEAD | wc -l  → ~103 (includes b3c8ec3)
git merge-tree dry-run  → 0 conflicting files
```

Technical merge is clean. Risk is business scope and uncommitted runtime state — not git conflicts.

---

*Phase 5 complete. No merge performed.*

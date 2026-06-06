# P16 Repository Census Report

**Date:** 2026-06-05  
**Mission:** Repo Census only — no deletions, no merges, no code changes  
**Current HEAD:** `sprint-a/broker-front-door`  
**Remote:** `origin` → `git@github.com:waterwoods/searchforge.git`

---

## SECTION 1 — Branch Summary

| Metric | Count |
|--------|------:|
| **Unique branches (deduplicated)** | **73** |
| Local branches | 71 |
| Remote branches (`origin/*`) | 13 |
| Local + Remote (both) | 11 |
| Local only | 60 |
| Remote only | 2 |

### Active Line vs Stale Main

| Branch | Last Commit | Commits Ahead of `main` | Status |
|--------|-------------|------------------------:|--------|
| `main` | 2025-11-24 | 0 | **Stale** — no commits in last 30 days |
| `sprint-a/broker-front-door` | 2026-06-04 | **98** | **Active P16 line** — 33 commits in last 30 days |
| `reduction/p1-simplification-loops` | 2026-05-30 | 92 | Active simplification work — 27 commits in last 30 days |

> **Critical finding:** All P16 product work lives on feature branches. `main` has not moved in ~6 months. The de facto mainline is `sprint-a/broker-front-door`.

### Prefix Clusters (Branch Explosion Hotspots)

| Prefix | Count | Risk |
|--------|------:|------|
| `auto-evolution/` | **49** | 🔴 Severe — local-only experiment sprawl |
| `sprint/` | 6 | 🟡 Multiple parallel sprint lines |
| `feat/` | 4 | 🟢 Mostly merged or small |
| `reduction/` | 3 | 🟢 Active, intentional |

---

## SECTION 2 — KEEP (Current Mainline)

These branches represent the product's operational truth or intended pilot line.

| Branch | Last Commit | Author | Ahead | Behind | Local | Remote | Merged? |
|--------|-------------|--------|------:|-------:|:-----:|:------:|:-------:|
| `main` | 2025-11-24 | Andy | 0 | 0 | Y | Y | — |
| `sprint-a/broker-front-door` | 2026-06-04 | Andy | 98 | 0 | Y | Y | No |

**Notes:**

- **`main`** — Canonical remote default, but stale. Must receive merge from active line before Pilot deploy parity.
- **`sprint-a/broker-front-door`** — Current working branch; all P16 intake/workbench work lands here. This is the branch to protect and eventually promote to `main`.

---

## SECTION 3 — REVIEW (May Have Value)

Branches worth Founder review before any deletion decision.

| Branch | Last Commit | Author | Ahead | Behind | Local | Remote | Merged? | Why Review |
|--------|-------------|--------|------:|-------:|:-----:|:------:|:-------:|------------|
| `reduction/p1-simplification-loops` | 2026-05-30 | Andy | 92 | 0 | Y | Y | No | Active simplification — 27 commits/30d |
| `reduction/p0-hardening-loops` | 2026-05-26 | Andy | 81 | 0 | Y | — | No | Hardening loops — 16 commits/30d |
| `reduction/safe-batch-loops` | 2026-05-26 | Andy | 76 | 0 | Y | — | No | Safe batch reduction — 11 commits/30d |
| `checkpoint/before-simplification-execution-20260526-0346` | 2026-05-26 | Andy | 68 | 0 | Y | — | No | Safety checkpoint before simplification |
| `sprint/pilot-saas-survivability-office-trust-hardening` | 2026-05-09 | Andy | 66 | 0 | Y | — | No | Pilot survivability work |
| `sprint/scoped-broker-identity-office-operational-safety` | 2026-05-09 | Andy | 66 | 0 | Y | — | No | Broker identity / office safety |
| `sprint/minimal-paid-saas-survivability-20260509` | 2026-05-04 | Andy | 65 | 0 | Y | — | No | Paid SaaS survivability sprint |
| `sprint/binding-session-continuity-per-office` | 2026-05-04 | Andy | 65 | 0 | Y | — | No | Session continuity |
| `sprint/office-ownership-minimal-auth-enforcement` | 2026-05-04 | Andy | 65 | 0 | Y | — | No | Office ownership auth |
| `sprint/org-continuity-db-column-promotion` | 2026-05-04 | Andy | 65 | 0 | Y | — | No | DB column promotion |
| `chen-kui-insurance` | 2026-04-20 | Andy | 15 | 0 | Y | Y | No | Customer trial branch — may have trial-specific commits |
| `feat/v2-image-case-progress` | 2026-04-20 | Andy | 22 | 0 | Y | — | No | Image case progress experiment |
| `feat/phase-b` | 2025-11-10 | Andy | 0 | 30 | Y | Y | **Yes** | Merged — candidate for deletion after review |
| `feat/proxy-dockerhub-bypass` | 2025-11-22 | Andy | 0 | 4 | Y | Y | **Yes** | Merged — infra fix, safe to delete |
| `feat/steward-phase-b` | 2025-11-12 | Andy | 0 | 11 | Y | Y | **Yes** | Merged — candidate for deletion |
| `develop` | 2025-10-28 | waterwoods | 26 | 36 | — | Y | No | Legacy develop line — remote only |
| `stash-review/20260420` | 2026-04-20 | Andy | 16 | 0 | Y | — | No | Stash review snapshot |

---

## SECTION 4 — EXPERIMENT (Experimental Nature)

| Branch | Last Commit | Ahead | Local | Remote | Merged? |
|--------|-------------|------:|:-----:|:------:|:-------:|
| `auto-evolution/*` (49 branches) | 2026-04-20 → 2026-05-04 | 15–65 | Y | 1 | No |
| `merge/preview-auto-evolution-20260420` | 2026-04-20 | 15 | Y | — | No |
| `feature/langgraph-integration` | 2025-11-10 | 0 | Y | Y | **Yes** |
| `crowdstrike-ops-copilot` | 2026-03-22 | 8 | — | Y | No |

### auto-evolution/ — Full Inventory (49 branches, all local-only except one)

All dated April–May 2026. None merged into `main`. All 42–65 commits ahead of stale `main`. Representative themes:

- Entity/resolver evolution (`entity-*`, `resolver-*`, `llm-*`, `pg-*`)
- Frontend extraction (`frontend-*`)
- Latency/performance (`http-latency-*`, `live-latency-*`, `prod-parity-*`)
- SaaS boundary/operator system (`real-saas-boundary-*`, `long-horizon-*`, `tenant-auth-*`)
- Production guardrails (`production-guardrail-system`, `doc-finalize-ci-*`)

Only `auto-evolution/20260420-v2` exists on remote (`origin/`). The other 48 are **local-only**.

---

## SECTION 5 — DELETE_CANDIDATE (Suggestion Only — Do Not Execute)

| Branch | Last Commit | Author | Ahead | Behind | Local | Remote | Merged? | Rationale |
|--------|-------------|--------|------:|-------:|:-----:|:------:|:-------:|-----------|
| `chore/build-cache-setup` | 2025-11-10 | Andy | 0 | 23 | Y | Y | **Yes** | Merged + 7 months stale |
| `backup/20251108-221444` | 2025-11-08 | Andy | 1 | 33 | Y | Y | No | Backup snapshot — 7 months old, 33 behind main |

**Also review for deletion after Founder sign-off (merged + stale):**

| Branch | Merged? | Last Commit | Notes |
|--------|:-------:|-------------|-------|
| `feat/phase-b` | Yes | 2025-11-10 | Safe delete candidate |
| `feat/proxy-dockerhub-bypass` | Yes | 2025-11-22 | Safe delete candidate |
| `feat/steward-phase-b` | Yes | 2025-11-12 | Safe delete candidate |
| `feature/langgraph-integration` | Yes | 2025-11-10 | LangGraph experiment — merged, out of P16 scope |

> **49 `auto-evolution/*` branches** are not marked DELETE_CANDIDATE yet because they are unmerged and may contain salvageable code. Recommend a separate **auto-evolution archaeology sprint** before bulk deletion.

---

## SECTION 6 — Merge Status

### Branches Merged Into `main`

| Branch | Last Commit | Still Exists Locally? | Still Exists on Remote? |
|--------|-------------|:---------------------:|:-----------------------:|
| `chore/build-cache-setup` | 2025-11-10 | Y | Y |
| `feat/phase-b` | 2025-11-10 | Y | Y |
| `feat/proxy-dockerhub-bypass` | 2025-11-22 | Y | Y |
| `feat/steward-phase-b` | 2025-11-12 | Y | Y |
| `feature/langgraph-integration` | 2025-11-10 | Y | Y |

**Only 5 of 73 branches are merged into `main`.** The active product line (`sprint-a/broker-front-door`, 98 commits) has never been merged back.

---

## SECTION 7 — Recent Activity (Last 30 Days)

### Top Active Branches

| Rank | Branch | Commits (30d) | Last Commit |
|-----:|--------|--------------:|-------------|
| 1 | `sprint-a/broker-front-door` | **33** | 2026-06-04 |
| 2 | `reduction/p1-simplification-loops` | **27** | 2026-05-30 |
| 3 | `reduction/p0-hardening-loops` | **16** | 2026-05-26 |
| 4 | `reduction/safe-batch-loops` | **11** | 2026-05-26 |
| 5 | `checkpoint/before-simplification-execution-20260526-0346` | 3 | 2026-05-26 |
| 6 | `sprint/pilot-saas-survivability-office-trust-hardening` | 1 | 2026-05-09 |
| 7 | `sprint/scoped-broker-identity-office-operational-safety` | 1 | 2026-05-09 |

**`main`:** 0 commits in last 30 days.

---

## SECTION 8 — Top Risks

### 🔴 R1 — Branch Explosion (`auto-evolution/`)

- **49 local branches**, 48 never pushed to remote
- All from a concentrated April–May 2026 auto-evolution sprint
- Creates cognitive load: impossible to know which branch has the "final" resolver/entity work
- **Duplicate themes:** multiple `resolver-*`, `frontend-*`, `pg-*`, `llm-*` branches with overlapping goals

### 🔴 R2 — Mainline Drift

- `main` last touched **2025-11-24** (~6 months ago)
- Active line `sprint-a/broker-front-door` is **98 commits ahead**
- Risk: deploy/recovery scripts referencing `main` will not reflect product reality
- Risk: new engineer clones repo and lands on stale `main`

### 🟡 R3 — Zombie Branches

- `backup/20251108-221444` — 7 months old, local + remote, unmerged
- 6 `sprint/*` branches — last touched May 4–9, no activity in 30 days except 2 with 1 commit each
- `develop` (remote only) — last touched 2025-10-28, diverged from main

### 🟡 R4 — Dangerous / Confusing Branches

| Branch | Risk |
|--------|------|
| `crowdstrike-ops-copilot` | Unrelated vertical — remote only, could confuse scope |
| `develop` | Legacy line — 26 ahead, 36 behind main |
| `feature/langgraph-integration` | Out-of-scope agent framework — merged but still present |
| `auto-evolution/long-horizon-saas-operating-system-*` | Name implies platform scope beyond P16 pilot |
| `auto-evolution/tenant-auth-rls-*` | Multi-tenant/auth — explicitly out of P16 scope per AGENTS.md |

### 🟡 R5 — Parallel Sprint Lines

Six `sprint/*` branches from May 2026 with similar commit counts (65–66 ahead). Likely represent parallel experiments that may have been superseded by `sprint-a/broker-front-door`. Need archaeology to determine which are dead ends.

---

## SECTION 9 — Founder Recommendation

### 1. Repository Health Score: **38 / 100**

| Factor | Score Impact |
|--------|-------------|
| Clear active line exists (`broker-front-door`) | +15 |
| Recent meaningful activity (7 branches active in 30d) | +10 |
| Remote has only 13 branches (not fully synced) | +5 |
| `main` stale 6 months, 98 commits behind active line | −25 |
| 49 local-only experiment branches | −20 |
| Only 5/73 branches merged into main | −10 |
| Parallel sprint lines with unclear ownership | −7 |
| Out-of-scope branches present (crowdstrike, langgraph, tenant-auth) | −5 |

### 2. Is the Repo Ready for Pilot Phase?

**Product: Likely yes** — on `sprint-a/broker-front-door`  
**Repo hygiene: No** — not until mainline is clarified

Pilot can proceed **from the active branch**, but Founder should not treat `main` as deploy truth. Before external broker trial, run one **mainline promotion sprint**: merge `sprint-a/broker-front-door` → `main`, tag a release.

### 3. Recommended Next Steps (Priority Order)

| Step | Action | Risk |
|------|--------|------|
| **1** | **Promote active line** — merge `sprint-a/broker-front-door` → `main`, tag `p16-pilot-baseline` | Low if CI passes |
| **2** | **Delete merged stale branches** (5 branches) — safe, reversible via git reflog | Very low |
| **3** | **Archive `auto-evolution/`** — create one tag or tarball snapshot, then delete all 49 local branches | Medium — do archaeology first |
| **4** | **Resolve parallel `sprint/*` lines** — diff against `broker-front-door`, delete superseded | Medium |
| **5** | **Remove out-of-scope remotes** — `crowdstrike-ops-copilot`, evaluate `develop` | Low |
| **6** | **Push active reduction branches to remote** — `p0`, `safe-batch` are local-only | Low |

### 4. Branches Most Worth Keeping (Long-Term)

| Priority | Branch | Reason |
|----------|--------|--------|
| ★★★ | `main` | Canonical — must be updated |
| ★★★ | `sprint-a/broker-front-door` | Active P16 product line |
| ★★ | `reduction/p1-simplification-loops` | Active simplification aligned with Validate Mode |
| ★★ | `checkpoint/before-simplification-execution-20260526-0346` | Rollback safety net |
| ★ | `chen-kui-insurance` | Customer trial context — review before delete |
| ★ | `reduction/p0-hardening-loops` | Hardening work in progress |

---

## Appendix A — Full Branch Inventory

| Branch | Last Commit | Author | Ahead | Behind | Local | Remote | Merged? | Category |
|--------|-------------|--------|------:|-------:|:-----:|:------:|:-------:|----------|
| auto-evolution/100-offices-operational-chaos-20260507 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/20260420-v1 | 2026-04-20 | Andy | 15 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/20260420-v2 | 2026-04-23 | Andy | 41 | 0 | Y | Y | No | EXPERIMENT |
| auto-evolution/30-customers-reality-simulation-20260507 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/active-fix-final-20260426-2106 | 2026-04-26 | Andy | 56 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/active-vehicle-resolver-20260425-1916 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/add-car-break-evolution-20260424 | 2026-04-24 | Andy | 44 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/add-car-destruction- | 2026-04-24 | Andy | 45 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/add-car-long-evolution-20260424-0515 | 2026-04-24 | Andy | 42 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/add-car-scenario-hardening-20260424-0037 | 2026-04-24 | Andy | 42 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/ambiguity-clarify-20260425-2229 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/assist-decouple-final-20260426-2036 | 2026-04-26 | Andy | 56 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/case-io-decouple-20260426-2226 | 2026-04-26 | Andy | 56 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/doc-finalize-ci-20260428-0259 | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/entity-fast-fix-2125 | 2026-04-24 | Andy | 42 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/entity-primary-multivehicle-20260425-0042 | 2026-04-24 | Andy | 42 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/entity-triage-evolution-20260424 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/final-eval-20260427-0223 | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/final-mainline-convergence | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/final-pg-llm-live-clarify-20260425-2342 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/frontend-broker-extraction-20260504-0821 | 2026-05-04 | Andy | 63 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/frontend-customer-entry-extraction-20260504-0800 | 2026-05-04 | Andy | 61 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/frontend-phase1-5-components | 2026-04-28 | Andy | 60 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/frontend-phase1-extract | 2026-04-28 | Andy | 59 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/http-latency-cut-20260426-1624 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/live-latency-20260426-0724 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/llm-ambiguity-resolver-20260425-2059 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/llm-chaos-validation-0114 | 2026-04-24 | Andy | 42 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/llm-entity-fusion-0000 | 2026-04-24 | Andy | 42 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/long-horizon-saas-operating-system-20260507 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/long-productization-sprint-20260504-1910 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/master-blueprint-audit-20260427-2050 | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/pg-chaos-validation-20260425-2030 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/pg-llm-live-chaos-20260425-2138 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/pg-multivehicle-persistence-20260426-1200 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/pg-truth-pipeline-20260426-0409 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/prod-parity-latency-20260426-0104 | 2026-04-24 | Andy | 55 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/product-only-wire-closure-support-export-20260507-0222 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/production-guardrail-system | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/real-saas-boundary-operator-system-20260507-0203 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/resolver-decision-20260427-1852 | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/resolver-final-convergence | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/resolver-takeover-final | 2026-04-27 | Andy | 58 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/system-discovery-20260505-071315 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/system-slimming-final-20260426-2348 | 2026-04-26 | Andy | 56 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/tenant-auth-rls-support-replay-foundation-20260507-0247 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/triage-orchestration-deep-optimization-20260507-0038 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/vehicle-entity-mvp-2026-04-25 | 2026-04-24 | Andy | 49 | 0 | Y | - | No | EXPERIMENT |
| auto-evolution/workbench-timeout-fix-20260504-1843 | 2026-05-04 | Andy | 64 | 0 | Y | - | No | EXPERIMENT |
| backup/20251108-221444 | 2025-11-08 | Andy | 1 | 33 | Y | Y | No | DELETE_CANDIDATE |
| checkpoint/before-simplification-execution-20260526-0346 | 2026-05-26 | Andy | 68 | 0 | Y | - | No | REVIEW |
| chen-kui-insurance | 2026-04-20 | Andy | 15 | 0 | Y | Y | No | REVIEW |
| chore/build-cache-setup | 2025-11-10 | Andy | 0 | 23 | Y | Y | Yes | DELETE_CANDIDATE |
| crowdstrike-ops-copilot | 2026-03-22 | Andy | 8 | 0 | - | Y | No | EXPERIMENT |
| develop | 2025-10-28 | waterwoods | 26 | 36 | - | Y | No | REVIEW |
| feat/phase-b | 2025-11-10 | Andy | 0 | 30 | Y | Y | Yes | REVIEW |
| feat/proxy-dockerhub-bypass | 2025-11-22 | Andy | 0 | 4 | Y | Y | Yes | REVIEW |
| feat/steward-phase-b | 2025-11-12 | Andy | 0 | 11 | Y | Y | Yes | REVIEW |
| feat/v2-image-case-progress | 2026-04-20 | Andy | 22 | 0 | Y | - | No | REVIEW |
| feature/langgraph-integration | 2025-11-10 | Andy | 0 | 26 | Y | Y | Yes | EXPERIMENT |
| main | 2025-11-24 | Andy | 0 | 0 | Y | Y | Yes | KEEP |
| merge/preview-auto-evolution-20260420 | 2026-04-20 | Andy | 15 | 0 | Y | - | No | EXPERIMENT |
| reduction/p0-hardening-loops | 2026-05-26 | Andy | 81 | 0 | Y | - | No | REVIEW |
| reduction/p1-simplification-loops | 2026-05-30 | Andy | 92 | 0 | Y | Y | No | REVIEW |
| reduction/safe-batch-loops | 2026-05-26 | Andy | 76 | 0 | Y | - | No | REVIEW |
| sprint-a/broker-front-door | 2026-06-04 | Andy | 98 | 0 | Y | Y | No | KEEP |
| sprint/binding-session-continuity-per-office | 2026-05-04 | Andy | 65 | 0 | Y | - | No | REVIEW |
| sprint/minimal-paid-saas-survivability-20260509 | 2026-05-04 | Andy | 65 | 0 | Y | - | No | REVIEW |
| sprint/office-ownership-minimal-auth-enforcement | 2026-05-04 | Andy | 65 | 0 | Y | - | No | REVIEW |
| sprint/org-continuity-db-column-promotion | 2026-05-04 | Andy | 65 | 0 | Y | - | No | REVIEW |
| sprint/pilot-saas-survivability-office-trust-hardening | 2026-05-09 | Andy | 66 | 0 | Y | - | No | REVIEW |
| sprint/scoped-broker-identity-office-operational-safety | 2026-05-09 | Andy | 66 | 0 | Y | - | No | REVIEW |
| stash-review/20260420 | 2026-04-20 | Andy | 16 | 0 | Y | - | No | REVIEW |

---

## Success Criteria Check

| Question | Answer |
|----------|--------|
| How many branches total? | **73 unique** (71 local, 13 remote) |
| Which are truly important? | `main`, `sprint-a/broker-front-door`, `reduction/p1-simplification-loops` |
| Which are historical garbage? | 5 merged stale branches + `backup/20251108-221444` — safe to delete |
| Which can be deleted later? | 49 `auto-evolution/*` after archaeology snapshot |
| Anything deleted? | **No** — census only |
| Anything merged? | **No** — census only |
| Code modified? | **No** — census only |

---

*Generated by P16 Repo Census Sprint — 2026-06-05*

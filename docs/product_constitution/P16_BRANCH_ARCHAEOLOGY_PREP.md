# P16 Branch Archaeology Prep

**Date:** 2026-06-05  
**Mission:** P16-PROMOTE — Phase 5  
**Mode:** Read-only inventory (no branch deletion)  
**Canonical line:** `sprint-a/broker-front-door` @ `517f728`

---

## Summary

| Prefix | Branch count | Merged into sprint? | Unique commits vs sprint | On origin |
|--------|-------------:|:-------------------:|:------------------------:|:---------:|
| `auto-evolution/*` | 49 | 49/49 ✅ | 0 | 1 (`20260420-v2`) |
| `sprint/*` | 6 | 6/6 ✅ | 0 | 0 |
| `reduction/*` | 3 | 2/3 | **1** (`p1-simplification-loops`) | 1 (`p1-simplification-loops`) |
| `checkpoint/*` | 1 | 1/1 ✅ | 0 | 0 |
| **Total** | **59** | **58/59** | **1** | **2** |

**Key finding:** 58 of 59 branches are fully absorbed into `sprint-a/broker-front-door`. Only `reduction/p1-simplification-loops` has 1 unique commit not on sprint.

---

## Value ranking guide

| Rank | Criteria |
|------|----------|
| **HIGH VALUE** | Unique commits, recent, documents decisions not captured elsewhere |
| **MEDIUM VALUE** | Fully merged but useful archaeology / bisect points |
| **LOW VALUE** | Duplicate tips (many branches share same SHA), fully merged, stale |

---

## `reduction/*` (3 branches)

| Branch | Last commit | SHA | Merged? | Unique | On origin | Value |
|--------|-------------|-----|:-------:|:------:|:---------:|-------|
| `reduction/p1-simplification-loops` | 2026-05-30 | `1bbc6b3` | ❌ | **1** | ✅ | **HIGH** — only branch with unique work |
| `reduction/p0-hardening-loops` | 2026-05-26 | `796b798` | ✅ | 0 | ❌ | LOW |
| `reduction/safe-batch-loops` | 2026-05-26 | `926ca22` | ✅ | 0 | ❌ | LOW |

**`reduction/p1-simplification-loops` unique commit:** `docs: activate Constitution V1 recovery point record` — review before deletion; may need cherry-pick or merge.

---

## `checkpoint/*` (1 branch)

| Branch | Last commit | SHA | Merged? | Unique | Value |
|--------|-------------|-----|:-------:|:------:|-------|
| `checkpoint/before-simplification-execution-20260526-0346` | 2026-05-26 | `90e73f9` | ✅ | 0 | MEDIUM — restore point meta-doc |

Tag `20260526-0346` referenced in checkpoint report. Keep until post-promotion cleanup.

---

## `sprint/*` (6 branches)

All share tip `0c2ed6d` or `f14f755`; all merged into sprint.

| Branch | Last commit | SHA | Merged? | Value |
|--------|-------------|-----|:-------:|-------|
| `sprint/pilot-saas-survivability-office-trust-hardening` | 2026-05-09 | `f14f755` | ✅ | MEDIUM |
| `sprint/scoped-broker-identity-office-operational-safety` | 2026-05-09 | `f14f755` | ✅ | LOW (duplicate tip) |
| `sprint/binding-session-continuity-per-office` | 2026-05-04 | `0c2ed6d` | ✅ | LOW |
| `sprint/minimal-paid-saas-survivability-20260509` | 2026-05-04 | `0c2ed6d` | ✅ | LOW |
| `sprint/office-ownership-minimal-auth-enforcement` | 2026-05-04 | `0c2ed6d` | ✅ | LOW |
| `sprint/org-continuity-db-column-promotion` | 2026-05-04 | `0c2ed6d` | ✅ | LOW |

**Note:** `f14f755` and `0c2ed6d` tips are ancestors of `517f728`. Safe deletion candidates **after** promotion.

---

## `auto-evolution/*` (49 branches)

### HIGH VALUE (unique decision points — still merged, useful for bisect)

| Branch | Date | SHA | Subject | Value |
|--------|------|-----|---------|-------|
| `auto-evolution/add-car-destruction-` | 2026-04-24 | `fac91f2` | Destruction scenario libraries | HIGH |
| `auto-evolution/vehicle-entity-mvp-2026-04-25` | 2026-04-24 | `63b1cba` | Triage oracle alignment | HIGH |
| `auto-evolution/active-fix-final-20260426-2106` | 2026-04-26 | `606e5ec` | Non-blocking assist + PG-active vehicle API | HIGH |
| `auto-evolution/frontend-customer-entry-extraction-20260504-0800` | 2026-05-04 | `24c49b9` | Customer entry tab extraction | HIGH |
| `auto-evolution/frontend-broker-extraction-20260504-0821` | 2026-05-04 | `475da6a` | Node 22 pin for Vite | MEDIUM |
| `auto-evolution/20260420-v2` | 2026-04-23 | `6b89357` | Unified intake prod posture check | MEDIUM (on origin) |

### LOW VALUE (duplicate tips — safe deletion candidates post-promotion)

**17 branches** share tip `0c2ed6d` (2026-05-04 productization):
`100-offices-operational-chaos-20260507`, `30-customers-reality-simulation-20260507`, `long-horizon-saas-operating-system-20260507`, `long-productization-sprint-20260504-1910`, `product-only-wire-closure-support-export-20260507-0222`, `real-saas-boundary-operator-system-20260507-0203`, `system-discovery-20260505-071315`, `tenant-auth-rls-support-replay-foundation-20260507-0247`, `triage-orchestration-deep-optimization-20260507-0038`, etc.

**10 branches** share tip `8dd0cc6` (2026-04-27 docs lock-in):
`doc-finalize-ci-20260428-0259`, `final-eval-20260427-0223`, `final-mainline-convergence`, `master-blueprint-audit-20260427-2050`, `production-guardrail-system`, `resolver-decision-20260427-1852`, `resolver-final-convergence`, `resolver-takeover-final`, etc.

**8 branches** share tip `a1bbe0e` (2026-04-24 entity triage reports):
`active-vehicle-resolver-20260425-1916`, `ambiguity-clarify-20260425-2229`, `entity-triage-evolution-20260424`, `final-pg-llm-live-clarify-20260425-2342`, `http-latency-cut-20260426-1624`, `live-latency-20260426-0724`, `llm-ambiguity-resolver-20260425-2059`, `pg-chaos-validation-20260425-2030`, `pg-llm-live-chaos-20260425-2138`, `pg-multivehicle-persistence-20260426-1200`, `pg-truth-pipeline-20260426-0409`, `prod-parity-latency-20260426-0104`

**4 branches** share tip `606e5ec` (2026-04-26 assist decouple):
`active-fix-final-20260426-2106`, `assist-decouple-final-20260426-2036`, `case-io-decouple-20260426-2226`, `system-slimming-final-20260426-2348`

**5 branches** share tip `25eac2a` (2026-04-24 add-car hardening):
`add-car-long-evolution-20260424-0515`, `add-car-scenario-hardening-20260424-0037`, `entity-fast-fix-2125`, `entity-primary-multivehicle-20260425-0042`, `llm-chaos-validation-0114`, `llm-entity-fusion-0000`

---

## Cleanup preparation (future sprint — NOT executed)

### Phase A — After mainline promotion

1. Cherry-pick or merge `reduction/p1-simplification-loops` unique commit if still needed.
2. Tag final promotion SHA on origin.

### Phase B — Safe deletion candidates (LOW VALUE, merged, not on origin)

~45 `auto-evolution/*` branches with duplicate tips.  
5 `sprint/*` branches (keep `pilot-saas-survivability` as named reference).  
2 `reduction/*` branches (`p0-hardening-loops`, `safe-batch-loops`).

### Phase C — Keep until explicit review

| Branch | Reason |
|--------|--------|
| `reduction/p1-simplification-loops` | 1 unique commit |
| `checkpoint/before-simplification-execution-20260526-0346` | Named restore point |
| `auto-evolution/20260420-v2` | Only auto-evolution branch on origin |
| `archive/production-pre-p16-demo` | Rollback target (not in scope but related) |

---

## Branch count by last-commit month

| Month | Count |
|-------|------:|
| 2026-05 | 12 |
| 2026-04 | 47 |

All branches are **2+ months old** relative to baseline date. No active evolution branches newer than sprint HEAD.

---

*End of P16 Branch Archaeology Prep — Phase 5*

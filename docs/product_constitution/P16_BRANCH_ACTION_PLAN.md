# P16 Branch Action Plan

**Date:** 2026-06-06  
**Mission:** P16-REPO-HYGIENE-SPRINT — Phase 5  
**Mode:** Classification only — **no deletion, merge, or push**

**Total branches examined:** 87 (local + remote tracking)

---

## Summary

| Recommendation | Count | Action |
|----------------|------:|--------|
| **KEEP** | 10 | Preserve indefinitely |
| **REVIEW** | 23 | Founder review before any archive/delete |
| **ARCHIVE** | 44 | Candidate for remote archive; keep local until approved |
| **DELETE_CANDIDATE** | 10 | Fully merged; safe to delete after confirmation |

---

## Priority Groups

### `auto-evolution/*` — 50 local branches

**Recommendation:** ARCHIVE (44 with >50 unique commits) / REVIEW (6 with ≤50)

These are historical autonomous-evolution experiment branches from April–May 2026. All are superseded by `sprint-a/broker-front-door` @ `517f728`. No merge to main planned.

| Branch | Last Commit | Unique vs main | Recommendation | Rationale |
|--------|-------------|:-------------:|:--------------:|-----------|
| `auto-evolution/100-offices-operational-chaos-20260507` | 2026-05-04 | 65 | ARCHIVE | Superseded; operational chaos sim |
| `auto-evolution/30-customers-reality-simulation-20260507` | 2026-05-04 | 65 | ARCHIVE | Superseded; shares HEAD with above |
| `auto-evolution/long-horizon-saas-operating-system-20260507` | 2026-05-04 | 65 | ARCHIVE | Superseded SaaS OS experiment |
| `auto-evolution/long-productization-sprint-20260504-1910` | 2026-05-04 | 65 | ARCHIVE | Superseded productization sprint |
| `auto-evolution/product-only-wire-closure-support-export-20260507-0222` | 2026-05-04 | 65 | ARCHIVE | Superseded wire-closure work |
| `auto-evolution/real-saas-boundary-operator-system-20260507-0203` | 2026-05-04 | 65 | ARCHIVE | Superseded boundary experiment |
| `auto-evolution/system-discovery-20260505-071315` | 2026-05-04 | 65 | ARCHIVE | Superseded discovery branch |
| `auto-evolution/tenant-auth-rls-support-replay-foundation-20260507-0247` | 2026-05-04 | 65 | ARCHIVE | Out-of-scope auth experiment |
| `auto-evolution/triage-orchestration-deep-optimization-20260507-0038` | 2026-05-04 | 65 | ARCHIVE | Superseded triage optimization |
| `auto-evolution/frontend-broker-extraction-20260504-0821` | 2026-05-04 | 63 | ARCHIVE | Frontend extraction merged elsewhere |
| `auto-evolution/frontend-customer-entry-extraction-20260504-0800` | 2026-05-04 | 61 | ARCHIVE | Frontend extraction merged elsewhere |
| `auto-evolution/workbench-timeout-fix-20260504-1843` | 2026-05-04 | 64 | ARCHIVE | Timeout fix incorporated |
| `auto-evolution/frontend-phase1-5-components` | 2026-04-28 | 60 | ARCHIVE | Frontend phase work superseded |
| `auto-evolution/frontend-phase1-extract` | 2026-04-28 | 59 | ARCHIVE | Frontend phase work superseded |
| `auto-evolution/doc-finalize-ci-20260428-0259` | 2026-04-27 | 58 | ARCHIVE | CI/doc finalize superseded |
| `auto-evolution/final-eval-20260427-0223` | 2026-04-27 | 58 | ARCHIVE | Final eval superseded |
| `auto-evolution/final-mainline-convergence` | 2026-04-27 | 58 | ARCHIVE | Convergence attempt superseded |
| `auto-evolution/master-blueprint-audit-20260427-2050` | 2026-04-27 | 58 | ARCHIVE | Blueprint audit superseded |
| `auto-evolution/production-guardrail-system` | 2026-04-27 | 58 | ARCHIVE | Guardrail work incorporated |
| `auto-evolution/resolver-decision-20260427-1852` | 2026-04-27 | 58 | ARCHIVE | Resolver work superseded |
| `auto-evolution/resolver-final-convergence` | 2026-04-27 | 58 | ARCHIVE | Resolver convergence superseded |
| `auto-evolution/resolver-takeover-final` | 2026-04-27 | 58 | ARCHIVE | Resolver takeover superseded |
| `auto-evolution/active-fix-final-20260426-2106` | 2026-04-26 | 56 | ARCHIVE | Active fix superseded |
| `auto-evolution/assist-decouple-final-20260426-2036` | 2026-04-26 | 56 | ARCHIVE | Decouple work superseded |
| `auto-evolution/case-io-decouple-20260426-2226` | 2026-04-26 | 56 | ARCHIVE | Case I/O decouple superseded |
| `auto-evolution/system-slimming-final-20260426-2348` | 2026-04-26 | 56 | ARCHIVE | Slimming work incorporated |
| `auto-evolution/pg-multivehicle-persistence-20260426-1200` | 2026-04-24 | 55 | ARCHIVE | PG persistence experiment |
| `auto-evolution/active-vehicle-resolver-20260425-1916` | 2026-04-24 | 55 | ARCHIVE | Vehicle resolver experiment |
| `auto-evolution/ambiguity-clarify-20260425-2229` | 2026-04-24 | 55 | ARCHIVE | Ambiguity resolver experiment |
| `auto-evolution/final-pg-llm-live-clarify-20260425-2342` | 2026-04-24 | 55 | ARCHIVE | PG+LLM clarify experiment |
| `auto-evolution/http-latency-cut-20260426-1624` | 2026-04-24 | 55 | ARCHIVE | Latency experiment |
| `auto-evolution/live-latency-20260426-0724` | 2026-04-24 | 55 | ARCHIVE | Latency experiment |
| `auto-evolution/llm-ambiguity-resolver-20260425-2059` | 2026-04-24 | 55 | ARCHIVE | LLM resolver experiment |
| `auto-evolution/entity-triage-evolution-20260424` | 2026-04-24 | 55 | ARCHIVE | Entity triage experiment |
| `auto-evolution/pg-chaos-validation-20260425-2030` | 2026-04-24 | 55 | ARCHIVE | PG chaos validation |
| `auto-evolution/pg-llm-live-chaos-20260425-2138` | 2026-04-24 | 55 | ARCHIVE | PG+LLM chaos validation |
| `auto-evolution/pg-truth-pipeline-20260426-0409` | 2026-04-24 | 55 | ARCHIVE | PG truth pipeline experiment |
| `auto-evolution/prod-parity-latency-20260426-0104` | 2026-04-24 | 55 | ARCHIVE | Prod parity experiment |
| `auto-evolution/add-car-destruction-` | 2026-04-24 | 45 | REVIEW | Add-car stress test; verify no unique fixes |
| `auto-evolution/add-car-break-evolution-20260424` | 2026-04-24 | 44 | REVIEW | Add-car evolution branch |
| `auto-evolution/add-car-long-evolution-20260424-0515` | 2026-04-24 | 42 | REVIEW | Add-car long evolution |
| `auto-evolution/add-car-scenario-hardening-20260424-0037` | 2026-04-24 | 42 | REVIEW | Scenario hardening |
| `auto-evolution/entity-fast-fix-2125` | 2026-04-24 | 42 | REVIEW | Entity fast fix |
| `auto-evolution/entity-primary-multivehicle-20260425-0042` | 2026-04-24 | 42 | REVIEW | Multivehicle entity |
| `auto-evolution/llm-chaos-validation-0114` | 2026-04-24 | 42 | REVIEW | LLM chaos validation |
| `auto-evolution/llm-entity-fusion-0000` | 2026-04-24 | 42 | REVIEW | Entity fusion experiment |
| `auto-evolution/20260420-v2` | 2026-04-23 | 41 | REVIEW | Early evolution v2 |
| `auto-evolution/vehicle-entity-mvp-2026-04-25` | 2026-04-24 | 49 | REVIEW | Vehicle entity MVP |
| `auto-evolution/20260420-v1` | 2026-04-20 | 15 | REVIEW | Early evolution v1 |

---

### `reduction/*` — 3 branches

| Branch | Last Commit | Unique vs main | Recommendation | Rationale |
|--------|-------------|:-------------:|:--------------:|-----------|
| `reduction/p1-simplification-loops` | 2026-05-30 | 92 | ARCHIVE | Simplification loops; incorporated into sprint-a |
| `reduction/p0-hardening-loops` | 2026-05-26 | 81 | ARCHIVE | Hardening loops superseded |
| `reduction/safe-batch-loops` | 2026-05-26 | 76 | ARCHIVE | Safe batch work superseded |

---

### `sprint/*` and `sprint-a/*` — 9 branches

| Branch | Last Commit | Unique vs main | Recommendation | Rationale |
|--------|-------------|:-------------:|:--------------:|-----------|
| `sprint-a/broker-front-door` | 2026-06-04 | 98 | **KEEP** | Active promotion candidate @ demo-ready HEAD |
| `release/p16-demo-ready-v1` | 2026-06-04 | 98 | **KEEP** | Frozen release pointer |
| `sprint/pilot-saas-survivability-office-trust-hardening` | 2026-05-09 | 66 | REVIEW | SaaS survivability experiment |
| `sprint/scoped-broker-identity-office-operational-safety` | 2026-05-09 | 66 | REVIEW | Identity/safety experiment |
| `sprint/binding-session-continuity-per-office` | 2026-05-04 | 65 | REVIEW | Session continuity experiment |
| `sprint/minimal-paid-saas-survivability-20260509` | 2026-05-04 | 65 | REVIEW | Paid SaaS experiment |
| `sprint/office-ownership-minimal-auth-enforcement` | 2026-05-04 | 65 | REVIEW | Auth enforcement experiment |
| `sprint/org-continuity-db-column-promotion` | 2026-05-04 | 65 | REVIEW | DB column promotion experiment |

---

### `checkpoint/*` — 1 branch

| Branch | Last Commit | Unique vs main | Recommendation | Rationale |
|--------|-------------|:-------------:|:--------------:|-----------|
| `checkpoint/before-simplification-execution-20260526-0346` | 2026-05-26 | 68 | **KEEP** | Named restore point before simplification |

---

## KEEP Branches (full list)

| Branch | SHA | Last Commit | Unique vs main | Rationale |
|--------|-----|-------------|:--------------:|-----------|
| `main` | `31572ca` | 2025-11-24 | 0 | Canonical mainline (stale) |
| `sprint-a/broker-front-door` | `517f728` | 2026-06-04 | 98 | Active work + promotion candidate |
| `release/p16-demo-ready-v1` | `517f728` | 2026-06-04 | 98 | Frozen demo release |
| `archive/production-pre-p16-demo` | `85bacc6` | 2026-04-21 | 25 | Pre-P16 rollback (on origin) |
| `checkpoint/before-simplification-execution-20260526-0346` | `90e73f9` | 2026-05-26 | 68 | Restore point |
| `backup/20251108-221444` | `39609b3` | 2025-11-08 | 1 | Historical backup |

---

## DELETE_CANDIDATE Branches (10)

Fully merged into `main` (0 unique commits). Safe to delete after founder confirms no local work:

| Branch | Last Commit |
|--------|-------------|
| `chore/build-cache-setup` | 2025-11-10 |
| `feat/phase-b` | 2025-11-10 |
| `feat/proxy-dockerhub-bypass` | 2025-11-22 |
| `feat/steward-phase-b` | 2025-11-12 |
| `feature/langgraph-integration` | 2025-11-10 |
| `origin/chore/build-cache-setup` | 2025-11-10 |
| `origin/feat/phase-b` | 2025-11-10 |
| `origin/feat/proxy-dockerhub-bypass` | 2025-11-22 |
| `origin/feature/langgraph-integration` | 2025-11-10 |

---

## REVIEW Branches (other)

| Branch | Last Commit | Unique vs main | Rationale |
|--------|-------------|:--------------:|-----------|
| `chen-kui-insurance` | 2026-04-20 | 15 | Client-specific branch; may have unique config |
| `feat/v2-image-case-progress` | 2026-04-20 | 22 | Image case progress feature |
| `merge/preview-auto-evolution-20260420` | 2026-04-20 | 15 | Merge preview artifact |
| `stash-review/20260420` | 2026-04-20 | 16 | Stash review artifact |
| `origin/chen-kui-insurance` | 2026-03-29 | 9 | Remote client branch (different SHA) |
| `origin/crowdstrike-ops-copilot` | 2026-03-22 | 8 | Unrelated vertical experiment |
| `origin/develop` | 2025-10-28 | 26 ahead, 36 behind | Legacy develop branch |

---

## No-Action Policy

Per Phase 0 guardrails:

- **No branch deletion** in this sprint
- **No merges** in this sprint
- **No pushes** in this sprint
- All ARCHIVE and DELETE_CANDIDATE items require explicit founder approval in a follow-up sprint

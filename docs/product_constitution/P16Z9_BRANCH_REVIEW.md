# P16-Z9 Phase 6 — Branch / Sprint Review

**Date:** 2026-06-02  
**Sprint:** P16-Z9 SSOT Consolidation  
**Method:** `git branch -a`, commit dates, remote tracking, sprint doc cross-reference

---

## Executive summary

**84 branches** exist; **~45 are `auto-evolution/*` experiments** from April–May 2026. Active paid-pilot work lives on **`sprint-a/broker-front-door`** (current). **`main`** is integration target. Most `auto-evolution/*` branches are **safe archive candidates** — merged learnings live in product_constitution docs and `inbox_triage/` code.

---

## Active branches (keep / work here)

| Branch | Status | Purpose | Action |
|--------|--------|---------|--------|
| **`sprint-a/broker-front-door`** | **Current HEAD** (`*`) | P16-Z6 memory UI + broker front door | Continue Z8 engine slice here or child branch |
| **`main`** | Integration | Production merge target | Merge sprint-a when guardrail + batteries green |
| **`chen-kui-insurance`** | Remote exists | Client/industry pack | Keep until pilot config stable |
| **`reduction/p1-simplification-loops`** | Remote tracked | Simplification execution | Align with SIMPLIFICATION_MASTER_PLAN |
| **`reduction/p0-hardening-loops`** | Local | Hardening | Merge or close after p1 |
| **`reduction/safe-batch-loops`** | Local | Batch reduction | Review for open PRs |

---

## Stale but potentially useful (review before delete)

| Branch | Last activity | Notes |
|--------|---------------|-------|
| `auto-evolution/20260420-v2` | 2026-04-23, ahead 18 | Early convergence — check for unmerged fixes |
| `auto-evolution/final-mainline-convergence` | 2026-04-27 | Name suggests merge candidate — verify diff vs main |
| `auto-evolution/production-guardrail-system` | 2026-04-27 | May overlap current guardrail scripts |
| `checkpoint/before-simplification-execution-20260526-0346` | May 2026 | Safety checkpoint — keep tag, delete branch optional |
| `sprint/binding-session-continuity-per-office` | — | Continuity theme — check if superseded by Z4–Z6 |
| `sprint/pilot-saas-survivability-*` | May 2026 | Survivability — align with CURRENT_PRODUCT_SHAPE |
| `feat/v2-image-case-progress` | — | Image progress — defer Tier 3 |

---

## Dead branches — safe archive candidates

### auto-evolution/* (bulk)

**~45 branches** including:

- `add-car-*`, `entity-*`, `llm-*`, `pg-*` (April 2026 lab)
- `long-horizon-saas-operating-system-20260507`
- `100-offices-operational-chaos-20260507`
- `30-customers-reality-simulation-20260507`
- `tenant-auth-rls-support-replay-foundation-20260507`

**Rationale:** Pre–paid-pilot exploration; constitution blocks P17/platform outcomes. Learnings captured in P16-Z0/Z2 archaeology.

**Action:** Tag `archive/auto-evolution-202604` on main, delete remote branches after 30-day notice OR move to single `archive/auto-evolution` branch with tags.

### Other dead

| Branch | Rationale |
|--------|-----------|
| `backup/20251108-221444` | Old backup |
| `stash-review/20260420` | Stash review complete |
| `merge/preview-auto-evolution-20260420` | Merge attempt — close if merged |
| `feature/langgraph-integration` | Out of pilot scope |
| `feat/phase-b`, `feat/steward-phase-b` | Phase B — verify merged |
| `crowdstrike-ops-copilot` (remote only) | Unrelated vertical |

---

## Sprint doc vs branch alignment

| Sprint | Code expected on | Branch reality |
|--------|------------------|----------------|
| P16-Y | triage.py rules | main / sprint-a |
| P16-Z6 UI | BrokerWorkbenchTab | sprint-a/broker-front-door |
| P16-Z8 engine | triage.py slice | **Planned** — not separate branch required |
| Role D battery | scripts + configs | main |

**Gap:** Z6 may be on sprint-a unmerged to main — **deploy blocker** for Role D re-run.

---

## Branch hygiene policy (P16-Z9)

| Rule | Detail |
|------|--------|
| Max active feature branches | 2 (1 eng + 1 founder config) |
| Naming | `sprint/<cap>-<topic>` or `fix/<ticket>` — no new `auto-evolution/*` |
| Before new branch | Check P16Z9_DUPLICATE_AUDIT — don't re-explore |
| After sprint | Merge or delete within 7 days |
| Archive | Tag + delete; docs in product_constitution |

---

## Recommended actions (founder)

| Priority | Action |
|----------|--------|
| 1 | Merge `sprint-a/broker-front-door` → `main` when Z6 guardrail green |
| 2 | Run Role D battery on **deployed** preview post-merge |
| 3 | Bulk-delete `auto-evolution/*` after tag (or archive repo mirror) |
| 4 | Close `SimulationAssistant` branch work if any open |
| 5 | Keep `chen-kui-insurance` until invoice paid |

---

## Remote tracking summary

| Remote branch | Local | Track |
|---------------|-------|-------|
| `origin/main` | yes | ✅ |
| `origin/sprint-a/broker-front-door` | yes | ✅ active |
| `origin/chen-kui-insurance` | yes | ✅ |
| `origin/reduction/p1-simplification-loops` | yes | ✅ |
| `origin/develop` | remote only | Review vs main — may be stale |

---

*End of P16-Z9 Phase 6 — Branch Review*

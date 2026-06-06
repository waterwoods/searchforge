# P16 Remote Preservation Risk Audit

**Date:** 2026-06-06  
**Mission:** P16-RUNTIME-REVIEW-AND-PUSH — Phase 5  
**Question:** What would be lost if Andy's laptop died today?

---

## Executive Risk Summary

| Risk Level | Item | Impact |
|------------|------|--------|
| 🔴 **Critical** | `release/p16-demo-ready-v1` branch (local only) | Cannot recover demo pin from remote |
| 🔴 **Critical** | `p16-demo-ready-v1` tag (local only) | Cannot checkout immutable demo snapshot |
| 🔴 **Critical** | 7 commits on `sprint-a/broker-front-door` | P16 hygiene + 3 product fixes lost |
| 🟡 **Medium** | 53 unstaged runtime paths | Product-only surface work uncommitted |
| 🟡 **Medium** | 61 local-only branches | Mostly auto-evolution experiments |
| 🟢 **Low** | Rollback branch | Already on origin |
| 🟢 **Low** | Main branch | On origin |

---

## 1. Local-Only Branches — 61 total

Key preservation branches:

| Branch | SHA | On Origin? | Purpose |
|--------|-----|:----------:|---------|
| `release/p16-demo-ready-v1` | `517f728` | ❌ | **Demo freeze** |
| `sprint-a/broker-front-door` | `4d5bf46` | ⚠️ partial | Active line (origin stale) |
| `archive/production-pre-p16-demo` | `85bacc6` | ✅ | Rollback |

Other 60 local-only branches are predominantly `auto-evolution/*` experiment branches — **not required for paid pilot** but represent historical exploration work.

---

## 2. Local-Only Tags — 3 total

| Tag | Points To | On Origin? | Purpose |
|-----|-----------|:----------:|---------|
| `p16-demo-ready-v1` | `517f728` | ❌ | **P16 demo snapshot** |
| `checkpoint/pre-reduction-safe-restore-point-20260526-0346` | — | ❌ | Pre-reduction checkpoint |
| `proxy-mvp-pass` | — | ❌ | Legacy proxy milestone |

All other tags (`backup-20251108-221444`, `constitution-v1`, `v1.0.0-fiqa-freeze`, etc.) are on origin.

---

## 3. Local-Only Commits

### `sprint-a/broker-front-door` — 7 commits not on origin

| SHA | Type | Loss impact |
|-----|------|-------------|
| `4d5bf46` | Hygiene D | Script tiers, missed archive, simulation fixtures |
| `932b7d1` | Hygiene C | 1,200+ sprint report archive migration |
| `50cce37` | Hygiene B | Release/deployment records |
| `69bf9b0` | Hygiene A | Governance/constitution docs |
| `517f728` | Product | Active case choice gate (**demo pin**) |
| `29a00f8` | Product | Add-car triage parity |
| `b0d6073` | Product | Workbench import fix |

Without push: **entire P16 sprint preservation layer is laptop-only.**

---

## 4. Untracked / Uncommitted Reports

| Item | Status | Risk |
|------|--------|------|
| Phase 1–6 reports (this sprint) | Uncommitted | Audit trail lost |
| Prior P16 reports | Committed in `4d5bf46` / A–C | Safe once pushed |
| `demo_brain_report.html` | DO_NOT_COMMIT | Regenerable local artifact |
| `configs/demo.env.example` | Modified unstaged | Verify no secrets; local template |

---

## 5. Deployment Manifests

| Manifest | In dirty tree? | On origin at demo SHA? |
|----------|:--------------:|:----------------------:|
| `docker-compose.yml` | M (comments only, committed in D) | N/A — committed |
| `docker-compose.product.yml` | Committed in D | Not on origin until push |
| `scripts/deploy_paid_pilot.sh` | M (unstaged) | Parent on origin; local diff lost |
| Cloud Run manifests | Not dirty | On origin |
| Vercel config | Not dirty | On origin |

**Deployment risk:** Paid pilot deploy script changes are **local only** (unstaged). Origin still has pre-change version.

---

## 6. What IS Safe on Origin Today

| Asset | SHA / Branch | Recoverable? |
|-------|--------------|:--------------:|
| Pre-P16 production | `archive/production-pre-p16-demo` @ `85bacc6` | ✅ |
| Stale sprint-a line | `sprint-a/broker-front-door` @ `d05e94d` | ✅ (incomplete) |
| Main | `main` | ✅ |
| Demo-ready pin | `517f728` | ❌ (not reachable from origin refs) |

---

## Loss Scenario Matrix

| Scenario | Lost | Recoverable from origin? |
|----------|------|:------------------------:|
| Laptop dies, no push | Demo pin, 4 hygiene commits, 3 product commits, 53 runtime diffs | Partially (`d05e94d` only) |
| Push sprint branch only | 53 unstaged runtime diffs | Demo pin still lost |
| Push sprint + release + tag | 53 unstaged runtime diffs only | Demo pin ✅ |

---

## Zero-Surprise Checklist

| # | Item | Action |
|---|------|--------|
| 1 | Push `sprint-a/broker-front-door` | Required |
| 2 | Push `release/p16-demo-ready-v1` | Required |
| 3 | Push `p16-demo-ready-v1` tag | Required |
| 4 | Commit this sprint's 6 reports | Recommended before push |
| 5 | Decide on 53 runtime paths | Separate sprint |
| 6 | Ignore 60 auto-evolution branches | Optional archival |

---

## Verdict

**Three pushes required** to eliminate critical preservation risk. Unstaged runtime work is a **separate, medium risk** — it does not block demo recovery if release branch/tag are pushed.

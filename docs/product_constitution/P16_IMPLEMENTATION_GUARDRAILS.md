# P16-A Phase 5 — Implementation Guardrails

**Date:** 2026-05-31  
**Scope:** Sprint A (P16-B) and immediate trial prep  
**Authority:** Constitution V1 (`NORTH_STAR_V1.md`), Capability contracts, P14-B exclusions

---

## Mission Boundary

Sprint A implements **Capability 1 — Broker Front Door** only. Every change must map to contract `CAPABILITY_01_BROKER_FRONT_DOOR.md` §6 acceptance criteria.

**If a change does not improve broker Day 1 unsupervised experience, it is out of scope.**

---

## Allowed (Sprint A)

| Category | Specific changes | Maps to |
|----------|------------------|---------|
| **Default broker tab** | `activeTab` default `'broker'` in product_only; read `?tab=` param | A1, Contract §6 |
| **Hide engineer chrome** | PG tags, API URL, 路由/指标, engineer filters hidden in product_only | A2, A10 |
| **Wayfinding** | One-line banner above paste area | A3 |
| **Loading states** | "首次分析约30秒" on first paste/triage; 503 retry hint | A5 |
| **Demo queue UX** | Progress indicator during seed load | A4 |
| **Cancellation auto-open** | Select cancellation case after demo queue completes | A4 |
| **Paste expectation copy** | "原样粘贴微信/通知文字，不用整理" | A6 |
| **Pilot intro alignment** | Collapse Add-Car-first intro; cancellation-first trial copy | A7 |
| **Inline practice** | 3 scenarios replacing hidden Simulation tab | A8 |
| **Tab simplification** | Hide 我的办理 in product_only trial | A9 |
| **Filter simplification** | 全部 / 需今天处理 / 24小时内 only | A10 |
| **Constitution doc updates** | Sprint A completion notes in scoreboard only (post-sprint) | Cap 7 |

---

## Not Allowed (Sprint A and immediate horizon)

| Category | Examples | Why excluded |
|----------|----------|--------------|
| **Stripe** | Payment integration, checkout | Constitution locked — manual invoice v1 |
| **OAuth / auth** | Login, SSO, multi-tenant | Out of paid pilot scope |
| **CRM** | Contact sync, pipeline, HubSpot | Not our category |
| **WeChat sync** | Auto-import messages | v2+; manual paste is v1 |
| **OCR** | Document scanning | Out of scope |
| **Schema redesign** | Postgres schema changes, new tables | Sprint A is UI-only |
| **Repo cleanup** | Archive migrations, doc moves, script renames | P1 reduction — separate track |
| **Architecture changes** | New services, LangGraph, RAG expansion | Platform work forbidden |
| **Capability expansion** | New capabilities beyond Cap 1 | Constitution has exactly 7 |
| **Triage engine tuning** | Prompt changes, new intent classes | Cap 2 — fix-now from trial only |
| **Commercial pack** | Pricing, terms, invoice | Sprint B |
| **Lifecycle polish** | Follow-up queue redesign | Sprint C |
| **Postgres prod deploy** | Can run parallel but not mixed into UI PR | Cap 7 — separate gate |

---

## File Touch Allowlist (Sprint A)

**May modify:**

```
ui/src/pages/UnifiedIntakePage.tsx
ui/src/features/intake/components/BrokerWorkbenchTab.tsx
ui/src/features/intake/utils/intakePure.ts
ui/src/config/productSurface.ts
configs/clients/chen_kui/ui_copy.json
```

**May modify (docs, minimal):**

```
docs/product_constitution/IMPLEMENTATION_SCOREBOARD.md   # post-sprint rescore only
docs/trial/*                                              # only if A8 playbook alignment requires
```

**Do not modify in Sprint A:**

```
services/*          # backend / triage engine
scripts/*           # unless guardrail fix required
docker-compose*     # deploy track
docs/archive/*      # repo cleanup
AGENTS.md           # unless critical drift (avoid)
```

---

## PR / Commit Discipline

| Rule | Detail |
|------|--------|
| **Branch** | Create `sprint-a/broker-front-door` from `constitution-v1` |
| **Commit scope** | One logical item per commit (A1, A2, …) when possible |
| **Commit message** | Reference capability: `sprint-a(A1): default broker tab in product_only` |
| **Pre-commit** | Run `bash scripts/guardrail_inbox_triage.sh` before merge |
| **No drive-by** | No formatting sweeps, no unrelated fixes |
| **No constitution edits** | Do not change `NORTH_STAR_V1.md` or contracts during Sprint A |

---

## Stop Conditions (escalate to founder)

1. Guardrail FAIL after UI change → stop, revert, diagnose  
2. Change requires backend API modification → out of Sprint A scope  
3. A8 inline practice exceeds 8h → ship A1–A7 first, defer A8  
4. Prod deploy needed to test → coordinate Cap 7 separately, do not block A1–A7 local  
5. Any request for Stripe, OAuth, WeChat sync → redirect to constitution exclusions  

---

## Success Definition

Sprint A is **done** when:

- Contract 01 §6 acceptance criteria met with manual test evidence  
- `IMPLEMENTATION_SCOREBOARD.md` Cap 1 rescore ≥ 70 (target 75)  
- Guardrail PASS  
- Founder dry-run Day 0 playbook without Simulation tab  

---

*End of P16-A Phase 5 — Implementation Guardrails*

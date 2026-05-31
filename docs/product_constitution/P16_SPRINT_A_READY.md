# P16-A Phase 4 — Sprint A Readiness Report

**Date:** 2026-05-31  
**Sprint:** A — Broker Front Door (Capability 1)  
**Goal:** Score 35 → 75; unsupervised Day 1 ≥ 70; cancellation value ≤ 5 min  
**Authority:** `SPRINT_A_FRONT_DOOR.md`, `IMPLEMENTATION_BACKLOG.md`, `CAPABILITY_GAP_MATRIX.md`, `TOP_50_ROI_FIXES.md`

**Prerequisite:** Constitution V1 tagged (`constitution-v1`) before any item below is implemented (P16-B).

---

## Sprint A Contract Success Criteria

| # | Criterion | Sprint items |
|---|-----------|--------------|
| 1 | Trial URL opens **办公室工作台** by default | A1 |
| 2 | product_only hides PG tags, API URL, 路由/指标, engineer filters | A2, A10 |
| 3 | Broker loads 加载演示队列 with visible progress | A4 |
| 4 | Cancellation case auto-opens after demo queue | A4 |
| 5 | Founder dry-run completes Day 0 playbook without Simulation tab | A8 |
| 6 | Chen Kui archetype reaches Case focus + 下一步 + draft without founder | A1–A7 bundle |

---

## Per-Item Readiness Matrix

### A1 — Default Broker Tab

| Dimension | Detail |
|-----------|--------|
| **Current state** | `UnifiedIntakePage` initializes `activeTab` to `'customer'` (客户报送). Comment: "Customer Entry is the default visible tab." |
| **Target state** | Trial/product_only opens `'broker'` (办公室工作台) by default; `?tab=` override for founder demos. |
| **Files likely touched** | `ui/src/pages/UnifiedIntakePage.tsx`; trial URL docs (Sprint B doc-only: `BROKER_ONE_PAGER.md`, `TRIAL_ONE_PATH.md`) |
| **Risk** | **Low** — isolated default change; deep-link regression if URL param omitted |
| **Rollback** | Revert default to `'customer'`; remove URL param reader |
| **Acceptance criteria** | Fresh load on `/workbench/unified-intake` in product_only → broker tab active; `?tab=customer` still works |
| **Manual test** | 1) `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, build/run. 2) Open workbench incognito. 3) Confirm 办公室工作台 selected without click. |

---

### A2 — Hide Engineer Chrome (PG / API / Debug)

| Dimension | Detail |
|-----------|--------|
| **Current state** | `BrokerWorkbenchTab.tsx` shows 路由/指标, 数据接口 + API URL, PG mirror tags via `intakePure.ts`; engineer filters 镜像异常/旧识别/测试/正式 visible. |
| **Target state** | When `isUnifiedIntakeProductOnlyUi()` is true: zero PG tags, no API URL, no 路由/指标, broker-safe filters only. |
| **Files likely touched** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`; `ui/src/features/intake/utils/intakePure.ts`; `ui/src/config/productSurface.ts` |
| **Risk** | **Low** — conditional render; dev builds must retain full surface |
| **Rollback** | Remove conditional guards; restore full operator surface in dev builds |
| **Acceptance criteria** | Broker UX checklist: 0 engineer labels in screenshot walkthrough |
| **Manual test** | product_only build → load workbench → inspect queue header, case cards, filter bar |

---

### A3 — Broker Wayfinding Banner

| Dimension | Detail |
|-----------|--------|
| **Current state** | Four tabs; PILOT_INTRO is Add-Car-first wall of text; no "start here" for brokers. |
| **Target state** | Persistent one-liner above paste: **「经纪人：请在本页粘贴客户消息」**; optional sub-line: manual paste, no auto-send. |
| **Files likely touched** | `UnifiedIntakePage.tsx`; `BrokerWorkbenchTab.tsx`; optional `configs/clients/chen_kui/ui_copy.json` |
| **Risk** | **Low** — copy-only UI addition |
| **Rollback** | Remove banner component |
| **Acceptance criteria** | Unsupervised test user finds paste area in <10s without tab switching |
| **Manual test** | New user test: URL only → paste area located |

---

### A4 — Demo Queue Progress + Auto-Open Cancellation

| Dimension | Detail |
|-----------|--------|
| **Current state** | 加载演示队列 takes 15–30s silent; strongest case may not be cancellation; user may abandon. |
| **Target state** | Progress during seed ("正在加载13条示例 (3/13…)"); on complete, cancellation case selected and scrolled into view. |
| **Files likely touched** | `BrokerWorkbenchTab.tsx` (demo queue handler ~line 479+) |
| **Risk** | **Medium** — cancellation case ID may drift if demo data changes |
| **Rollback** | Remove auto-select; remove progress state |
| **Acceptance criteria** | After demo load: same-day cancellation visible; 下一步 + draft on screen |
| **Manual test** | Click 加载演示队列 → watch progress → confirm cancellation case open |

---

### A5 — First-Request Loading States

| Dimension | Detail |
|-----------|--------|
| **Current state** | First paste/triage can take ~30s or hit warming with no user feedback. |
| **Target state** | Loading copy: **「首次分析约30秒，请稍候」** on paste analyze and demo queue; graceful 503 message with retry hint. |
| **Files likely touched** | `BrokerWorkbenchTab.tsx`; intake API error handling |
| **Risk** | **Low** — UX copy + error path |
| **Rollback** | Revert to generic Ant Design loading only |
| **Acceptance criteria** | No silent spinner >5s without message |
| **Manual test** | Cold start paste → message visible; simulate 503 → retry guidance |

---

### A6 — Paste Expectation Copy

| Dimension | Detail |
|-----------|--------|
| **Current state** | Paste placeholder generic; brokers may expect WeChat sync. |
| **Target state** | Helper text: **「原样粘贴微信/通知文字，不用整理」** |
| **Files likely touched** | `BrokerWorkbenchTab.tsx`; `ui_copy.json` |
| **Risk** | **Low** |
| **Rollback** | Restore previous placeholder |
| **Acceptance criteria** | Copy visible before first paste |
| **Manual test** | Read paste area without scrolling |

---

### A7 — Pilot Intro / Story Alignment

| Dimension | Detail |
|-----------|--------|
| **Current state** | `PILOT_INTRO` in `UnifiedIntakePage.tsx` is Add-Car-first; contradicts cancellation-first constitution. |
| **Target state** | Collapsed by default in product_only; trial intro mentions cancellation / urgent messages as lead wedge. |
| **Files likely touched** | `ui/src/pages/UnifiedIntakePage.tsx` |
| **Risk** | **Medium** — copy review; founder sign-off on messaging |
| **Rollback** | Restore Add-Car intro block |
| **Acceptance criteria** | Broker not overwhelmed Day 0; story matches BROKER_ONE_PAGER cancellation wedge |
| **Manual test** | First visit → intro collapsed; expand → cancellation mentioned |

---

### A8 — Inline Practice Scenarios (Simulation Replacement)

| Dimension | Detail |
|-----------|--------|
| **Current state** | Playbook references Simulation Assistant; tab hidden in product_only (`showSimulationTab = !isUnifiedIntakeProductOnlyUi()`). |
| **Target state** | Inline panel with 3 scenarios (cancellation, missing doc, add-car) runnable from broker tab. |
| **Files likely touched** | `BrokerWorkbenchTab.tsx`; `docs/trial/` playbook; possibly patterns from `ScenarioReplayTab` |
| **Risk** | **Medium–High** — largest Sprint A item (~8h); scope creep risk |
| **Rollback** | Hide panel; revert to kickoff-only training |
| **Acceptance criteria** | Playbook Day 0 training completable without Simulation tab |
| **Manual test** | Run 3 inline scenarios end-to-end on prod build |

---

### A9 — Hide 我的办理 Tab (Trial Mode)

| Dimension | Detail |
|-----------|--------|
| **Current state** | Four tabs including 我的办理 — purpose unclear for broker trial. |
| **Target state** | Hidden in product_only trial configuration. |
| **Files likely touched** | `ui/src/pages/UnifiedIntakePage.tsx` |
| **Risk** | **Low** |
| **Rollback** | Restore tab in Tabs items array |
| **Acceptance criteria** | Broker sees ≤3 tabs (workbench primary) |
| **Manual test** | product_only → 我的办理 absent |

---

### A10 — Simplify Queue Filters

| Dimension | Detail |
|-----------|--------|
| **Current state** | Segmented filters include 镜像异常, 旧识别, 测试, 正式 — meaningless to brokers. |
| **Target state** | product_only: **全部 / 需今天处理 / 24小时内** |
| **Files likely touched** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` |
| **Risk** | **Low** — overlaps A2; implement together |
| **Rollback** | Restore full filter set in dev mode |
| **Acceptance criteria** | No engineer filter labels visible |
| **Manual test** | Toggle filters → only broker labels |

---

## Sprint A File Map (consolidated)

| File | Items |
|------|-------|
| `ui/src/pages/UnifiedIntakePage.tsx` | A1, A3, A7, A9 |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | A2, A3, A4, A5, A6, A8, A10 |
| `ui/src/features/intake/utils/intakePure.ts` | A2 |
| `ui/src/config/productSurface.ts` | A2 (if needed) |
| `configs/clients/chen_kui/ui_copy.json` | A3, A6 (optional) |

---

## Recommended Implementation Order (P16-B)

| Day | Items | Rationale |
|-----|-------|-----------|
| 1 | A1, A2, A10 | Fixes Day-1 tab + trust killers (P0 ROI) |
| 2 | A3, A6, A7 | Wayfinding + copy alignment |
| 3 | A4, A5 | Demo queue + loading (first value moment) |
| 4–5 | A8, A9 | Simulation replacement + tab cleanup |
| 5 | QA + guardrail | `guardrail_inbox_triage.sh` must stay PASS |

---

## Sprint A Exit Tests

| # | Test | Owner |
|---|------|-------|
| 1 | Unsupervised URL open → broker tab | Engineering |
| 2 | Screenshot audit — zero engineer chrome | Founder |
| 3 | Demo queue → progress → cancellation open | Engineering |
| 4 | Real paste → loading message → case card | Engineering |
| 5 | Playbook Day 0 without Simulation | Founder |
| 6 | Time to cancellation value <5 min | Founder dry-run |
| 7 | `bash scripts/guardrail_inbox_triage.sh` PASS | Operator |

---

## Dependencies (external to Sprint A code)

| Dependency | Owner | Required before |
|------------|-------|-----------------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` on prod preview | Founder/deploy | Sprint A prod verify |
| Broker UX checklist (Gate 2) | Founder | Day 7 dry-run |
| Guardrail PASS | Operator | Every deploy |
| **constitution-v1 tag** | Founder | **Before first code change** |

---

## Sprint A Rollback (summary)

1. **Git:** `git checkout constitution-v1` or revert Sprint A commits  
2. **Env:** unset `VITE_UNIFIED_INTAKE_PRODUCT_ONLY`  
3. **Trial URL:** interim founder-guided kickoff with manual tab click  
4. **Do not rollback:** Postgres prod deploy if completed in parallel  

---

*End of P16-A Phase 4 — Sprint A Readiness Report*

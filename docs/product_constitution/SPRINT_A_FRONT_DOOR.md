# Sprint A — Broker Front Door

**Version:** P15 Sprint Definition  
**Date:** 2026-05-31  
**Scope:** **Capability 1 — Broker Front Door ONLY**  
**Goal:** Score 35 → 75; unsupervised Day 1 ≥ 70; cancellation value in ≤5 min without founder translation.

**Out of scope for Sprint A:** Trial commercial docs (Sprint B), lifecycle polish (Sprint C), intake label pack (Sprint D), engine tuning, new tabs, WeChat sync, Stripe.

---

## Sprint A Success Criteria (Contract §6)

- [ ] Trial URL opens **办公室工作台** by default  
- [ ] product_only hides PG tags, API URL, 路由/指标, engineer filters  
- [ ] Broker loads 加载演示队列 with visible progress  
- [ ] Cancellation case auto-opens after demo queue  
- [ ] Founder dry-run completes Day 0 playbook without Simulation tab  
- [ ] Chen Kui archetype reaches Case focus + 下一步 + draft without founder on screen  

---

## Improvement Specifications

### A1 — Default Broker Tab

| | |
|--|--|
| **Current state** | `UnifiedIntakePage` initializes `activeTab` to `'customer'` (客户报送). Comment says "Customer Entry is the default visible tab." |
| **Target state** | Trial/product_only opens `'broker'` (办公室工作台) by default; optional `?tab=` override for founder demos. |
| **Files likely affected** | `ui/src/pages/UnifiedIntakePage.tsx`; trial URL docs (`BROKER_ONE_PAGER.md`, `TRIAL_ONE_PATH.md`, share links) |
| **Acceptance criteria** | Fresh load on `/workbench/unified-intake` in product_only → broker tab active; `?tab=customer` still works |
| **Manual test** | 1) Set `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, build/run. 2) Open workbench URL incognito. 3) Confirm 办公室工作台 selected without click. |
| **Rollback** | Revert default to `'customer'`; remove URL param reader |

---

### A2 — Hide Engineer Chrome (PG / API / Debug)

| | |
|--|--|
| **Current state** | `BrokerWorkbenchTab.tsx` shows 路由/指标, 数据接口 + API URL, PG mirror tags via `intakePure.ts`; engineer filters 镜像异常/旧识别/测试/正式 visible. |
| **Target state** | When `isUnifiedIntakeProductOnlyUi()` is true: zero PG tags, no API URL, no 路由/指标, broker-safe filters only (全部 / 需今天处理 / 24小时内). |
| **Files likely affected** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`; `ui/src/features/intake/utils/intakePure.ts`; `ui/src/config/productSurface.ts` |
| **Acceptance criteria** | Broker UX checklist: 0 engineer labels in screenshot walkthrough |
| **Manual test** | product_only build → load workbench → inspect queue header, case cards, filter bar |
| **Rollback** | Remove conditional guards; restore full operator surface in dev builds |

---

### A3 — Broker Wayfinding Banner

| | |
|--|--|
| **Current state** | Four tabs; PILOT_INTRO is Add-Car-first wall of text; no "start here" for brokers. |
| **Target state** | Persistent one-liner above paste: **「经纪人：请在本页粘贴客户消息」**; optional sub-line: manual paste, no auto-send. |
| **Files likely affected** | `ui/src/pages/UnifiedIntakePage.tsx`; `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`; `configs/clients/chen_kui/ui_copy.json` (optional) |
| **Acceptance criteria** | Unsupervised test user finds paste area in &lt;10s without tab switching |
| **Manual test** | New user test: URL only → paste area located |
| **Rollback** | Remove banner component |

---

### A4 — Demo Queue Progress + Auto-Open Cancellation

| | |
|--|--|
| **Current state** | 加载演示队列 takes 15–30s silent; strongest case may not be cancellation; user may abandon. |
| **Target state** | Progress during seed ("正在加载13条示例 (3/13…)"); on complete, cancellation case selected and scrolled into view. |
| **Files likely affected** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` (demo queue handler ~line 479+) |
| **Acceptance criteria** | After demo load: same-day cancellation visible; 下一步 + draft on screen |
| **Manual test** | Click 加载演示队列 → watch progress → confirm cancellation case open |
| **Rollback** | Remove auto-select; remove progress state |

---

### A5 — First-Request Loading States

| | |
|--|--|
| **Current state** | First paste/triage can take ~30s or hit warming with no user feedback. |
| **Target state** | Loading copy: **「首次分析约30秒，请稍候」** on paste analyze and demo queue; graceful 503 message with retry hint. |
| **Files likely affected** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`; intake API error handling |
| **Acceptance criteria** | No silent spinner &gt;5s without message |
| **Manual test** | Cold start paste → message visible; simulate 503 → retry guidance |
| **Rollback** | Revert to generic Ant Design loading only |

---

### A6 — Paste Expectation Copy

| | |
|--|--|
| **Current state** | Paste placeholder generic; brokers may expect WeChat sync. |
| **Target state** | Helper text: **「原样粘贴微信/通知文字，不用整理」** |
| **Files likely affected** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`; `ui_copy.json` |
| **Acceptance criteria** | Copy visible before first paste |
| **Manual test** | Read paste area without scrolling |
| **Rollback** | Restore previous placeholder |

---

### A7 — Pilot Intro / Story Alignment

| | |
|--|--|
| **Current state** | `PILOT_INTRO` in `UnifiedIntakePage.tsx` is Add-Car-first; contradicts cancellation-first constitution. |
| **Target state** | Collapsed by default in product_only; trial intro mentions cancellation / urgent messages as lead wedge. |
| **Files likely affected** | `ui/src/pages/UnifiedIntakePage.tsx` |
| **Acceptance criteria** | Broker not overwhelmed Day 0; story matches BROKER_ONE_PAGER cancellation wedge |
| **Manual test** | First visit → intro collapsed; expand → cancellation mentioned |
| **Rollback** | Restore Add-Car intro block |

---

### A8 — Inline Practice Scenarios (Simulation Replacement)

| | |
|--|--|
| **Current state** | Playbook references Simulation Assistant; tab hidden in product_only (`showSimulationTab = !isUnifiedIntakeProductOnlyUi()`). |
| **Target state** | Inline panel with 3 scenarios (cancellation, missing doc, add-car) runnable from broker tab. |
| **Files likely affected** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx`; `docs/trial/` playbook; possibly extract from `ScenarioReplayTab` patterns |
| **Acceptance criteria** | Playbook Day 0 training completable without Simulation tab |
| **Manual test** | Run 3 inline scenarios end-to-end on prod build |
| **Rollback** | Hide panel; revert to kickoff-only training |

---

### A9 — Hide 我的办理 Tab (Trial Mode)

| | |
|--|--|
| **Current state** | Four tabs including 我的办理 — purpose unclear for broker trial. |
| **Target state** | Hidden in product_only trial configuration. |
| **Files likely affected** | `ui/src/pages/UnifiedIntakePage.tsx` |
| **Acceptance criteria** | Broker sees ≤3 tabs (customer entry optional hide later; workbench primary) |
| **Manual test** | product_only → 我的办理 absent |
| **Rollback** | Restore tab in Tabs items array |

---

### A10 — Simplify Queue Filters

| | |
|--|--|
| **Current state** | Segmented filters include 镜像异常, 旧识别, 测试, 正式 — meaningless to brokers. |
| **Target state** | product_only: **全部 / 需今天处理 / 24小时内** |
| **Files likely affected** | `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` |
| **Acceptance criteria** | No engineer filter labels visible |
| **Manual test** | Toggle filters → only broker labels |
| **Rollback** | Restore full filter set in dev mode |

---

## Sprint A File Map (Summary)

| File | Changes |
|------|---------|
| `ui/src/pages/UnifiedIntakePage.tsx` | Default tab, URL param, intro collapse, hide tabs |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx` | Chrome hide, banner, loading, demo queue, filters, inline practice |
| `ui/src/features/intake/utils/intakePure.ts` | Conditional PG label helpers for product_only |
| `ui/src/config/productSurface.ts` | Possibly trial-mode flag if needed beyond product_only |
| `docs/BROKER_ONE_PAGER.md` | Trial URL with `?tab=broker` (doc only — Sprint B pricing separate) |

---

## Sprint A Test Plan

| # | Test | Pass |
|---|------|------|
| 1 | Unsupervised URL open → broker tab | ✓ |
| 2 | Screenshot audit — zero engineer chrome | ✓ |
| 3 | Demo queue → progress → cancellation open | ✓ |
| 4 | Real paste → loading message → case card | ✓ |
| 5 | Playbook Day 0 without Simulation | ✓ |
| 6 | Time to cancellation value &lt;5 min | ✓ |
| 7 | `guardrail_inbox_triage.sh` still PASS | ✓ |

---

## Sprint A Rollback Plan

1. **Git revert** sprint branch commits (UI-only; no schema changes expected)  
2. **Env rollback:** unset `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` → full operator UI returns  
3. **Trial URL:** revert to founder-guided kickoff with manual tab click (interim)  
4. **Do not rollback:** prod Postgres deploy if completed in parallel — persistence is independent  

---

## Estimated Effort

| Item | Hours |
|------|-------|
| A1–A2 Tab + URL | 3 |
| A3 Chrome hide | 5 |
| A4 Wayfinding | 1 |
| A5 Demo queue + cancellation | 5 |
| A6 Loading + paste copy | 3 |
| A7 Intro alignment | 2 |
| A8 Inline practice | 8 |
| A9–A10 Tabs + filters | 7 |
| QA + dry-run fixes | 4 |
| **Total** | **~38h (~5 days)** |

---

## Dependencies (External to Sprint A)

| Dependency | Owner | Required before |
|------------|-------|-----------------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` on prod preview | Founder/deploy | Sprint A verify on prod |
| Broker UX checklist (Gate 2) | Founder | Day 7 dry-run |
| Guardrail PASS | Operator | Every deploy |

---

*End of Sprint A — Broker Front Door*

# P16-C Phase 1 — Local Product Validation

**Date:** 2026-05-31  
**Branch:** `sprint-a/broker-front-door` @ `c2e3dff`  
**Configuration:** Broker trial parity — backend `UNIFIED_INTAKE_PRODUCT_ONLY=1`, UI build `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, `VITE_API_BASE_URL=http://127.0.0.1:8001`  
**Method:** `npm run build` + `vite preview` on Node 22; backend via `run_demo_local.sh`; browser snapshot + CDP text audit  
**Guardrail:** `bash scripts/guardrail_inbox_triage.sh` → **PASS**

---

## 1. Initial URL

| Surface | URL |
|---------|-----|
| **Validated (product_only preview)** | `http://127.0.0.1:4174/workbench/unified-intake` |
| Trial canonical (dev, when UI starts) | `http://localhost:5173/workbench/unified-intake` |
| Production alias (pre-Sprint A — **not trial config**) | `https://ui-smoky-beta.vercel.app/workbench/unified-intake` |

**Note:** Port 4173 was occupied; preview bound to **4174**. Trial docs should reference whichever preview port is active after build.

---

## 2. Initial Tab

| Check | Result |
|-------|--------|
| Default selected tab | **办公室工作台** ✅ |
| Document title | `加车报价试点 · 办公室工作台` |
| Manual tab click required? | **No** |
| `?tab=customer` override | Not tested this session; implemented in Sprint A code |

---

## 3. Visible Navigation Items

| Location | Items visible |
|----------|---------------|
| **Top bar (left)** | 金盾·陈魁团队 · 客户统一受理 |
| **Top bar (right)** | 返回工作台 |
| **Intake tabs** | 客户报送 — 报送入口（加车优先） · **办公室工作台** — 加车旗舰路径 · 与客户报送同一服务记录 |
| **Sidebar lab routes** | **None** (RAG Lab, Agent Studio, Graph Lab hidden in product_only) |
| **Hidden vs production** | 我的办理, 场景仿真 — **absent** ✅ |

**Tab count:** 2 (production has 4).

---

## 4. Visible Banners

| Banner | Visible? | Content summary |
|--------|----------|-----------------|
| **Broker wayfinding** | ✅ Yes | 「经纪人：请在本页粘贴客户消息」+ manual paste / no auto-send sub-line |
| **Product intro (PILOT_INTRO)** | Collapsed | 「显示产品说明」button; expanded text is cancellation-first when opened |
| **Network / CORS error** | ⚠️ Yes (local preview) | `Network Error（若控制台有 CORS 提示…）` — preview origin not in `ALLOWED_ORIGINS` |
| **Demo queue hint** | ✅ Yes | 「0/12 条示例已就绪」+ auto-open cancellation promise |
| **Practice scenarios panel** | ✅ Yes | 「练习场景（无需仿真页）」 |

---

## 5. Visible Engineer Artifacts

| Artifact | product_only local | Production workbench (对比) |
|----------|-------------------|----------------------------|
| PG 镜像 tags | **Absent** ✅ | Present (`PG 已镜像` on case cards) |
| 数据接口 / API URL | **Absent** ✅ | Present |
| 路由/指标 debug tag | **Absent** ✅ | Present |
| Engineer filters (镜像异常/旧识别/测试/正式) | **Absent** ✅ | Present |
| 场景仿真 tab | **Hidden** ✅ | Visible |
| 我的办理 tab | **Hidden** ✅ | Visible |
| English broker_next_step leaks on cards | Not observed empty queue | Present on prod cards |

**CDP engineer-term scan (local):** `[]` — zero matches for PG, 镜像异常, 数据接口, 路由/指标, 场景仿真, 我的办理.

---

## 6. Visible Customer-Facing Artifacts

| Artifact | Present? | Notes |
|----------|----------|-------|
| Chen Kui team branding | ✅ | 金盾·陈魁团队 header + card |
| Broker paste workflow | ✅ | Textarea + 「开始整理」 |
| Trust line (no auto-send) | ✅ | In wayfinding + intro |
| Inline practice (3 scenarios) | ✅ | 取消/付款风险, 缺材料跟进, 加车报价 |
| Demo queue CTA | ✅ | 「加载演示队列」 |
| Add-Car portal tab | ⚠️ Still visible | Secondary tab; not default |
| Add-Car tagline on header card | ⚠️ | 「车险报送入口 · 加车报价为当前旗舰流程」 |
| Tab suffix Add-Car copy | ⚠️ | Both tabs mention 加车 |

**Practice scenario click test:** 「取消/付款风险」 loads cancellation sample into paste area — **PASS**.

---

## 7. First Screen Screenshot Inventory

| # | Capture | What it shows |
|---|---------|---------------|
| 1 | `p16c-local-workbench-first-screen.png` (full page) | Broker tab selected; team card; collapsed intro; tab bar; queue area with CORS error; wayfinding banner; paste + practice panel |
| 2 | Production baseline (browser) | 客户报送 default; 4 tabs; Add-Car CTA buttons; no broker wayfinding |

**First-screen hierarchy (broker tab, top → bottom):**

1. Dark header — team name + 返回工作台  
2. White team card — 金盾保险 · 陈魁团队 + Add-Car tagline  
3. 「显示产品说明」 (collapsed)  
4. Two-tab bar — **办公室工作台 selected**  
5. Network error alert (local preview only — deploy blocker for demo queue)  
6. Quick experience row — 加载演示队列 + progress hint  
7. Empty queue panel — 「暂无服务记录」 + guidance  
8. Broker workbench panel — wayfinding, practice scenarios, paste, 开始整理  

---

## Backend Posture (trial parity)

```
GET http://127.0.0.1:8001/readyz → 200
intake_path_ready: true
intake_core_readiness: true
readiness_mode: intake_core
```

---

## Validation Summary

| Dimension | Verdict |
|-----------|---------|
| Sprint A default tab | ✅ PASS |
| Engineer chrome purge | ✅ PASS |
| Wayfinding + paste copy | ✅ PASS |
| Tab simplification | ✅ PASS (2 tabs) |
| Inline practice | ✅ PASS |
| Demo queue E2E | ⚠️ BLOCKED locally (CORS) |
| Copy wedge alignment | ⚠️ Partial (Add-Car flavor remains) |
| Remote deploy parity | ❌ Not validated — no Vercel Preview with env |

---

*End of P16-C Phase 1 — Local Product Validation*

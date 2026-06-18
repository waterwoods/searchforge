# P16 Demo Tab Runtime Audit — RESTORE-DEMO-TABS-SPRINT

**Date:** 2026-06-06  
**Alias:** `https://ui-waterwoods-andys-projects-1f411b73.vercel.app`

---

## Before fix (broken state)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_2S7zGtHDyHX2WW4fZdKtuQ9CwJHL` |
| **Deployment URL** | `https://ui-erdln9896-andys-projects-1f411b73.vercel.app` |
| **Bundle** | `index-DMOKMAa_.js` |
| **Build stamp** | `2026-06-06T13:10:04.774Z` |
| **Deploy trigger** | P16 Office Visibility sprint (`P16_PREVIEW_DEPLOY_REPORT.md`) |

### Build-time flags (inferred from behavior + deploy log)

| Variable | Baked value | Effect |
|----------|-------------|--------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | `1` | `productOnlyUi = true` |
| `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO` | **unset** | `supervisedDemoUi = false` |
| `VITE_API_BASE_URL` | Cloud Run URL | ✅ |
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | present | ✅ queue auth |

### Tab visibility (broken)

| Tab | Visible? |
|-----|----------|
| 客户报送 | ❌ |
| 办公室工作台 | ✅ (only surface — `singleTabMode`) |
| 场景仿真 | ❌ |
| 我的办理 | ❌ (expected in supervised mode — secondary drawer) |

### HTTP probe

```
curl -sI https://ui-waterwoods-andys-projects-1f411b73.vercel.app/workbench/unified-intake
→ HTTP/2 200
```

---

## After fix (restored state)

| Field | Value |
|-------|-------|
| **Deployment ID** | `dpl_2tzhtecntoYKBRwa7BTfoSVVRThd` |
| **Deployment URL** | `https://ui-do075u1o0-andys-projects-1f411b73.vercel.app` |
| **Alias** | `https://ui-waterwoods-andys-projects-1f411b73.vercel.app` |
| **Bundle** | `index-CEY2l3TS.js` |
| **Target** | Preview |
| **Status** | Ready |

### Build-time flags

| Variable | Baked value | Effect |
|----------|-------------|--------|
| `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` | `1` | Office Visibility product-only cards preserved |
| `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO` | **`1`** | 3-tab supervised demo layout |
| `VITE_API_BASE_URL` | `https://fiqa-api-g7zatxrycq-uw.a.run.app` | ✅ |
| `VITE_UNIFIED_INTAKE_INTAKE_API_KEY` | from `.env.cloudrun` | ✅ |

### Expected tab visibility (verified)

| Tab | Visible? | Default on load? |
|-----|----------|------------------|
| 客户报送 | ✅ | ✅ |
| 办公室工作台 | ✅ | — |
| 场景仿真 | ✅ | — |
| 我的办理 | Hidden as top tab | Accessible via 客户报送 drawer (supervised mode) |

### Browser verification (2026-06-06)

- Page load: 3 tabs in DOM (`客户报送`, `办公室工作台`, `场景仿真`)
- Default selected: **客户报送** (`document.title`: 加车报价 · 客户统一报送)
- 办公室工作台 tab: paste box, 加载演示队列, practice scenarios, queue cards — Office Visibility surface intact
- `document.title` on broker tab: **办公室工作台 · 客户消息整理**

---

## productOnly flag summary

| Surface | `PRODUCT_ONLY` | `SUPERVISED_DEMO` | Tabs |
|---------|----------------|-------------------|------|
| Full dev (`localhost:5173`) | off | off | 4 (incl. 我的办理) |
| Broker trial only | on | off | 1 (办公室工作台) |
| **Waterwoods Preview** | on | **on** | **3** |
| Production (current) | varies | not set on dashboard | TBD — separate promotion |

---

## Operator rule

Always use the **`ui-waterwoods` alias** for supervised demo. Raw hash deployment URLs may lack CORS allowlisting on Cloud Run.

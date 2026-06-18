# P16 Demo Tab Root Cause — RESTORE-DEMO-TABS-SPRINT

**Sprint:** P16-RESTORE-DEMO-TABS-SPRINT  
**Date:** 2026-06-06  
**Symptom:** Waterwoods Preview showed only **办公室工作台** (single-tab mode). Expected **客户报送 · 办公室工作台 · 场景仿真**.

---

## Investigation summary

| Question | Answer |
|----------|--------|
| **A. Hidden by configuration?** | **Yes** — build-time env, not runtime toggle |
| **B. Hidden by code?** | **Yes** — intentional gate when `productOnlyUi && !supervisedDemoUi` |
| **C. Hidden by deployment env vars?** | **Yes** — Preview deploy baked `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` but omitted `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1` |

---

## Gating logic (source of truth)

`ui/src/config/productSurface.ts`:

- `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` → `productOnlyUi = true` (paid-pilot / broker trial surface)
- `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1` → `supervisedDemoUi = true` (Preview supervised demo: 3-tab customer-first layout)

`ui/src/pages/UnifiedIntakePage.tsx`:

```typescript
const showCustomerTab = !productOnlyUi || supervisedDemoUi;
const showSimulationTab = !productOnlyUi || supervisedDemoUi;
const showMyRequestsTab = !productOnlyUi && !supervisedDemoUi;
const singleTabMode = productOnlyUi && !showCustomerTab && !showMyRequestsTab && !showSimulationTab;
```

When `productOnlyUi=true` and `supervisedDemoUi=false`:

| Flag / derived | Value |
|----------------|-------|
| `showCustomerTab` | `false` |
| `showSimulationTab` | `false` |
| `showMyRequestsTab` | `false` |
| `singleTabMode` | **`true`** → renders `BrokerWorkbenchTab` directly, **no `<Tabs>` chrome** |

Default tab in that mode: `broker` (办公室工作台).

When **both** flags are `1`:

| Flag / derived | Value |
|----------------|-------|
| `showCustomerTab` | `true` |
| `showSimulationTab` | `true` |
| `showMyRequestsTab` | `false` (drawer inside 客户报送) |
| `singleTabMode` | `false` → full 3-tab bar |
| Default tab | `customer` (客户报送) |

---

## Exact condition causing disappearance

```
productOnlyUi === true  (VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 baked at build)
AND
supervisedDemoUi === false  (VITE_UNIFIED_INTAKE_SUPERVISED_DEMO absent at build)
```

Vite replaces `import.meta.env.VITE_*` at compile time. There is no runtime override in the browser.

---

## Was this intentional?

**Partially.**

| Design intent | Status |
|---------------|--------|
| **Broker-only trial** (Chen Kui paste path, hide customer/sim tabs) | Intentional when only `PRODUCT_ONLY=1` |
| **Supervised demo** (Wu Miss script: 3 tabs, customer-first default) | Intentional when **both** flags set — documented in `WU_MISS_DEMO_SCRIPT.md` and `productSurface.ts` |
| **Office Visibility redeploy (2026-06-06)** | Unintentional regression — deploy command in `P16_PREVIEW_DEPLOY_REPORT.md` passed `PRODUCT_ONLY=1` but not `SUPERVISED_DEMO=1` |

The Office Visibility sprint correctly preserved product-only workbench chrome; it did not intend to remove supervised-demo tab layout from Waterwoods.

---

## Should Waterwoods show all 3 tabs?

**Yes.** Waterwoods is the **supervised demo / founder preview** alias (`WU_MISS_DEMO_SCRIPT.md`, `P16F_CONTEXT.md`). It must ship:

- 客户报送 (default)
- 办公室工作台 (with Office Visibility cards)
- 场景仿真

Production broker-only URLs may remain single-tab when deployed with only `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`.

---

## Exact change required

Add build flag to Preview deploy (no application code change):

```bash
vercel deploy --yes \
  -b VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 \
  -b VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1 \
  -b VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app \
  -b VITE_UNIFIED_INTAKE_INTAKE_API_KEY="${UNIFIED_INTAKE_INTAKE_API_KEY}"

vercel alias set <new-deployment-url> ui-waterwoods-andys-projects-1f411b73.vercel.app
```

**Follow-up (recommended):** Persist both `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` and `VITE_UNIFIED_INTAKE_SUPERVISED_DEMO` in Vercel Preview dashboard to prevent flag drift on future redeploys.

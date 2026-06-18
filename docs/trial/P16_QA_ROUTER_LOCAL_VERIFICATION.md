# P16 QA Router Local Verification

**Sprint:** P16-QA-PREVIEW-ROUTER-RUNTIME-RECOVERY  
**Date:** 2026-06-07  
**Fix:** `ui/src/App.tsx` — `{LabRoutes()}` instead of `<LabRoutes />`

---

## Build

| Step | Command | Result |
|------|---------|--------|
| Build | `npm run build` (Node 22.22.0) | ✅ PASS |
| Typecheck | Skipped (project scaffold) | N/A |
| Unit tests | None in UI package | N/A |

Bundle after fix: `index-CRxIZkcv.js` (local dist)

---

## Route verification (Vite preview :4173)

| URL | Result |
|-----|--------|
| `/workbench/unified-intake` | ✅ Loads unified intake |
| `/workbench/unified-intake?tab=customer` | ✅ Customer First entry — phone, name, Continue |
| `/workbench/unified-intake?tab=office` | ✅ Office workbench tab |
| `/workbench/unified-intake?tab=simulation` | ✅ Simulation tab |

**Runtime crash:** None observed. No `[ble] is not a <Route>` error.

---

## Customer tab elements (local)

- ✅ Add-Car Request heading
- ✅ Phone Number field
- ✅ Name (optional) field
- ✅ Continue / 继续 button
- ✅ Three tabs: 客户报送 · 办公室工作台 · 场景仿真

---

*End of P16 QA Router Local Verification*

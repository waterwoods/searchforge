# P16 QA Router Runtime Root Cause

**Sprint:** P16-QA-PREVIEW-ROUTER-RUNTIME-RECOVERY  
**Date:** 2026-06-07  
**Broken Preview:** https://ui-emtvr6y44-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

---

## Error

```
[ble] is not a <Route> component. All component children of <Routes> must be a <Route> or <React.Fragment>
```

(`ble` is the minified name of `LabRoutes` in the production bundle.)

---

## Answers

### 1. Which file caused the runtime crash?

**`ui/src/App.tsx`** — nested route tree under `<Route path="/">`.

### 2. Which line or route definition is invalid?

```74:74:ui/src/App.tsx
                                <LabRoutes />
```

When `isUnifiedIntakeProductOnlyUi()` is **false** (lab / non-product-only build), the non-product branch renders `<LabRoutes />` as a **direct child** of a parent `<Route>`. React Router v6 requires those children to be `<Route>` or `<React.Fragment>`, not an arbitrary component wrapper.

`LabRoutes()` internally returns a Fragment of `<Route>` elements, but that only works if the function is **invoked** (`LabRoutes()`) or routes are inlined — not when React mounts `<LabRoutes />` as its own component node.

### 3. Why did build pass but runtime failed?

- **Vite build** type-checks and bundles JSX; it does not execute React Router's runtime child validation.
- React Router validates route children **at render time** when `<Routes>` mounts.
- The invalid pattern is behind a **conditional** (`productOnlyUi ? … : <LabRoutes />`), so local dev with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` never hit the broken branch.
- The broken Preview deploy was built **without** `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1`, so `productOnlyUi === false` at runtime → lab branch → crash.

### 4. Why did QA Preview show runtime error / blank page?

1. Preview bundle took the **lab route branch** (`LabRoutes` component as child).
2. React Router threw on mount → red error boundary / blank content area.
3. Customer First UI never rendered — failure is **100% frontend router config**, not backend or Postgres.

---

## Fix (minimal)

Replace `<LabRoutes />` with `{LabRoutes()}` so Fragment + Route children are passed directly to the parent Route.

Also deploy Preview with `VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1` (and supervised demo flag if needed) so QA uses the product-only route set.

---

*End of P16 QA Router Runtime Root Cause*

# P16 Preview Blank Page — Browser Audit

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07  
**Broken URL:** https://ui-6hc7cfoxk-andys-projects-1f411b73.vercel.app/workbench/unified-intake?tab=customer

---

## Observations

| Signal | Finding |
|--------|---------|
| Page title | Loads: `加车报价 · 统一报送` |
| `#root` innerHTML | **Empty** — React never mounted |
| Accessibility tree | Document node only; no tabs, inputs, or header |
| CSS | `index-D2fAzD03.css` loads (HTTP 200) |
| JS bundle | `index-BxgUOLwB.js` loads (HTTP 200) |
| Network API calls | **None** — crash occurs before any fetch |
| Visible error UI | None (ErrorBoundary did not catch module init failure) |

---

## Root runtime error (inferred from bundle + code)

Deployed bundle contains:

```text
const Aie={...ADD_CAR_FIELD_LABELS,primary_driver:"Driver License",...
```

`ADD_CAR_FIELD_LABELS` is referenced at **module top level** in `customerFirstEntry.ts` but was **not imported** in commit `7ede46d`. At runtime this throws:

```text
ReferenceError: ADD_CAR_FIELD_LABELS is not defined
```

This aborts the JS module graph during initial parse/eval, leaving `#root` empty.

---

## Audit questions

| # | Question | Answer |
|---|----------|--------|
| 1 | JS runtime exception? | **Yes** — `ReferenceError` on `ADD_CAR_FIELD_LABELS` at module init |
| 2 | Missing asset/chunk? | **No** — HTML, CSS, and main JS all return 200 |
| 3 | Router error? | **No** — crash happens before React Router renders |
| 4 | Env/config error? | **No** — env vars present; failure is pure JS reference |
| 5 | API call crashing root? | **No** — no API calls observed |
| 6 | Vercel serving bad build? | **Yes** — build succeeded but shipped broken JS from status simplification commit |

---

## Comparison (post-fix)

| | Broken (`index-BxgUOLwB.js`) | Fixed (`index-Bs99AAgT.js`) |
|---|------------------------------|-----------------------------|
| `#root` content | Empty | Full Customer First UI |
| Console | Module ReferenceError (inferred) | Clean |
| Tabs visible | No | Yes |

---

*End of P16 Preview Blank Page Browser Audit*

# P16-W Phase 1 — Runtime Repro

**Date:** 2026-06-01  
**Sprint:** P16-W Runtime Crash Recovery

---

## Preview URL

| Field | Value |
|-------|-------|
| Canonical alias | https://ui-waterwoods-andys-projects-1f411b73.vercel.app |
| Deploy URL (same bundle after fix) | https://ui-nqnsh47ak-andys-projects-1f411b73.vercel.app |
| Route tested | `/workbench/unified-intake` |
| Pre-fix bundle | `index-CKPYkrkL.js` |
| Post-fix bundle | `index-OFXnRnil.js` |

---

## Reproduction steps

1. Open Preview URL in browser (cold — HTTP 200, no SSO wall).
2. Land on broker workbench (`/workbench/unified-intake`).
3. Click **加载演示队列** (Load demo queue).
4. Runtime error boundary renders immediately.

Initial page load **does not** crash. Crash is triggered when queue cards render.

---

## Stack trace (captured from Preview, pre-fix)

```
ReferenceError: getCompactQueuePreview is not defined
    at Bt (assets/index-CKPYkrkL.js:479:3394)
    at assets/index-CKPYkrkL.js:479:14609
    at Array.map (<anonymous>)
    at T2 (assets/index-CKPYkrkL.js:479:14582)
    at …
```

---

## Bundle hash

| State | HTML reference | Deployment |
|-------|----------------|------------|
| Broken | `/assets/index-CKPYkrkL.js` | `dpl_9zWWj1payFg4NuGdNVVe4C6aenwv` |
| Fixed | `/assets/index-OFXnRnil.js` | `dpl_8ydHn7c9igGs1p45V5hrKD38kdbH` |

Verified via:

```bash
curl -s https://ui-waterwoods-andys-projects-1f411b73.vercel.app | grep -o 'index-[^"]*\.js'
```

---

## Screenshots

| When | What |
|------|------|
| Pre-fix | Red **Runtime Error** heading; message `getCompactQueuePreview is not defined` after clicking 加载演示队列 |
| Post-fix | Demo queue loads 12/12; case detail + draft panels render; no error boundary |

---

## Consistency

**Yes — reproducible 100% of the time** on pre-fix bundle whenever:

- Demo queue is loaded, or
- Any saved case list renders via `renderRecentCaseCard()` (action-now, tracking, or filtered queue)

Paste-only triage (before queue cards mount) does **not** trigger the crash because `renderRecentCaseCard` is not called until cases appear in the sidebar list.

---

*End of P16-W Phase 1*

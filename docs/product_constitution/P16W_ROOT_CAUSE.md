# P16-W Phase 3 — Root Cause Analysis

**Date:** 2026-06-01

---

## Verdict

**C. Import removed** (during component extraction) — not a deletion, rename, merge conflict, or conditional compile issue.

Secondary note: latent since 2026-05-04; surfaced on Preview now that SSO is fixed and founders exercise demo queue.

---

## Evidence matrix

| Hypothesis | Result | Evidence |
|------------|--------|----------|
| A. Function deleted | ❌ | `getCompactQueuePreview` exists at `intakePure.ts:586`; exported via `utils/index.ts` |
| B. Function renamed | ❌ | No rename commits; symbol unchanged in git history |
| **C. Import removed** | ✅ | `UnifiedIntakePage.tsx` had import before `879e807`; `BrokerWorkbenchTab.tsx` never received it |
| D. Conditional compile | ❌ | No `#ifdef` / env-gated code; Vite bundle contains call site `getCompactQueuePreview(re)` in broken deploy |
| E. product_only branch | ❌ Partial | P16-I added `productOnlyUi` early return but call remains **before** branch at line 730 |
| F. Merge conflict | ❌ | Clean single-commit extraction; no conflict markers |
| G. Dead code path | ❌ | Called on every queue card render — actively exercised by demo queue |

---

## Mechanism

1. `renderRecentCaseCard()` executes `getCompactQueuePreview(savedCase)` at line 730.
2. Without import, `getCompactQueuePreview` is an unresolved free variable → `ReferenceError` at runtime.
3. TypeScript did not block deploy (likely `noUnusedLocals` / strict scope gap or build path not catching free identifiers in this file during Vercel build).
4. Page shell loads; crash occurs when React maps cases to cards (demo queue, API refresh, or post-triage list update).

---

## Why now?

| Factor | Detail |
|--------|--------|
| SSO fixed (P16-V) | Preview now reachable; founders hit broker workbench for first time on deployed URL |
| Demo queue | Primary trial onboarding path — clicks 加载演示队列 |
| product_only | Queue sidebar visible in trial layout (`productOnlyUi` queue section at lines 205–207) |

Bug existed locally too but was masked by limited queue-card testing on deployed Preview.

---

*End of P16-W Phase 3*

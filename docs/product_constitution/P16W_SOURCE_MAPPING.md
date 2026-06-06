# P16-W Phase 2 — Source Mapping

**Date:** 2026-06-01  
**Symbol:** `getCompactQueuePreview`

---

## Repository search (entire repo)

| Location | Role |
|----------|------|
| `ui/src/features/intake/utils/intakePure.ts:586` | **Definition** |
| `ui/src/features/intake/utils/index.ts` | Re-export (`export * from './intakePure'`) |
| `ui/src/features/intake/components/BrokerWorkbenchTab.tsx:730` | **Call site** (only runtime call in `ui/`) |
| `docs/archive/...` | Historical sprint specs only — not executed code |

No other TypeScript/JavaScript call sites exist in the active codebase.

---

## 1. Definition location

```586:610:ui/src/features/intake/utils/intakePure.ts
export function getCompactQueuePreview(caseItem: SavedCase): string {
    const collected = (caseItem.collected_fields ?? []).map(humanizeStructuredField);
    const stillNeeded = (caseItem.still_needed_fields ?? []).map(humanizeStructuredField);
    const focus = inferCaseFocusFromText(caseItem.source_text ?? '');
    // ... flow-specific compact preview for queue cards
}
```

Function is exported and available via `@/features/intake/utils`.

---

## 2. Import location

| File | Import status (pre-fix) |
|------|-------------------------|
| `BrokerWorkbenchTab.tsx` | **Missing** — used at line 730, not in import block (lines 56–103) |
| `UnifiedIntakePage.tsx` (pre-extraction) | **Present** — imported at line 109 before May 4 extraction |

Pre-fix import block in `BrokerWorkbenchTab.tsx` included `getQueueReadinessLabel`, `getPreviewText`, etc., but **not** `getCompactQueuePreview`.

---

## 3. Call sites

| File | Line | Context |
|------|------|---------|
| `BrokerWorkbenchTab.tsx` | 730 | `renderRecentCaseCard()` — called unconditionally before `productOnlyUi` branch |
| `BrokerWorkbenchTab.tsx` | 1268 | `actionNowCases.map(renderRecentCaseCard)` |
| `BrokerWorkbenchTab.tsx` | 1276 | `trackingCases.map(renderRecentCaseCard)` |
| `BrokerWorkbenchTab.tsx` | 1280 | `workbenchFilteredCases.map(renderRecentCaseCard)` |

All call paths funnel through `renderRecentCaseCard`.

---

## 4. Git history

| Commit | Date | Change |
|--------|------|--------|
| `879e807` | 2026-05-04 | **Introduced bug** — `BrokerWorkbenchTab.tsx` extracted from `UnifiedIntakePage.tsx`; import list copied but `getCompactQueuePreview` omitted while usage retained at line 724 |
| `901b0df` | 2026-05-31 | P16-I product-only UI refactor — added early-return branch in `renderRecentCaseCard` but **did not remove** the unconditional call at line 730 |
| `b0d6073` | 2026-06-01 | **Fix** — restored missing import |

Evidence:

```bash
git log -S 'getCompactQueuePreview' -- ui/src/features/intake/components/BrokerWorkbenchTab.tsx
# 879e807 frontend: extract broker workbench tab component

git show 879e807^:ui/src/pages/UnifiedIntakePage.tsx | grep getCompactQueuePreview
# 109:    getCompactQueuePreview,
# 672:        const compactPreview = getCompactQueuePreview(savedCase);
```

Function definition in `intakePure.ts` has been stable since the queue-preview sprint; it was never deleted or renamed.

---

*End of P16-W Phase 2*

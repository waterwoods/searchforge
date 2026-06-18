# P16 Preview Blank Page — Code Audit

**Sprint:** P16-PREVIEW-BLANK-PAGE-RECOVERY  
**Date:** 2026-06-07  
**Regression commit:** `7ede46d feat(p16): collapse customer status to four business states`

---

## Root cause

**File:** `ui/src/features/intake/utils/customerFirstEntry.ts`

**Introduced in status simplification sprint:**

```typescript
const STATUS_SURFACE_FIELD_LABELS: Record<string, string> = {
    ...ADD_CAR_FIELD_LABELS,  // ← used but never imported
    primary_driver: 'Driver License',
    ...
};
```

`ADD_CAR_FIELD_LABELS` is exported from `@/features/intake/constants` and correctly imported elsewhere (e.g. `intakePure.ts`), but the new spread in `customerFirstEntry.ts` omitted the import.

Because this runs at **module initialization**, any import chain reaching `customerFirstEntry.ts` crashes the entire app bundle before React mounts.

---

## Import chain to crash

```
main.tsx → App.tsx → UnifiedIntakePage → CustomerEntryTab
  → CustomerFirstEntryScreen → customerFirstEntry.ts (ReferenceError)
```

Also affects any route that eagerly loads intake utils.

---

## Files reviewed (status simplification diff)

| File | Risk | Finding |
|------|------|---------|
| `App.tsx` | Router | ✅ No regression |
| `CustomerFirstEntryScreen.tsx` | Render crash | ✅ Safe; imports from `customerFirstEntry` |
| `AddCarRecordSummaryRail.tsx` | Status mapping | ✅ No change causing blank page |
| `customerFirstEntry.ts` | Module init | ❌ **Missing import** |
| `CustomerEntryTab.tsx` | Props/null | ✅ Safe |
| `customerPortalPresentation.tsx` | Imports | ✅ Safe |
| `intakePure.ts` | Status mapping | ✅ Has correct import |

---

## Searches performed

| Pattern | Result |
|---------|--------|
| Direct object access without null checks in new status code | None fatal at init |
| Switch missing default in `customerBusinessStateDisplay` | Has `default` branch ✅ |
| Invalid Route children in `App.tsx` | Unchanged ✅ |
| Production-only import failures | None found |
| Bare identifier in bundle | `ADD_CAR_FIELD_LABELS` in broken bundle only |

---

## Fix applied

```typescript
import { ADD_CAR_FIELD_LABELS } from '@/features/intake/constants';
```

One-line import — minimal, no business-rule or Constitution changes.

---

*End of P16 Preview Blank Page Code Audit*

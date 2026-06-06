# P16-W Phase 5 — Fix Options

**Date:** 2026-06-01

---

## Option A — Minimal surgical fix (recommended)

Add missing import to `BrokerWorkbenchTab.tsx`:

```typescript
import {
    // ...
    getCompactQueuePreview,
    // ...
} from '@/features/intake/utils';
```

| Dimension | Estimate |
|-----------|----------|
| Risk | **Very low** — restores intended behavior from pre-extraction page |
| Time | **5 minutes** |
| Files touched | **1** (`BrokerWorkbenchTab.tsx`) |

---

## Option B — Correct architectural fix

Move `getCompactQueuePreview` call inside the non-`productOnlyUi` branch (only compute when `compactPreview` is displayed), plus add import.

| Dimension | Estimate |
|-----------|----------|
| Risk | Low — slightly more diff surface; easy to miss a branch |
| Time | 15–30 minutes + regression on full UI queue cards |
| Files touched | 1–2 |

Benefit: avoids unused computation in product_only cards. Does not fix the ReferenceError without the import.

---

## Option C — Rollback

Redeploy pre-P16-I bundle or revert `901b0df` / `879e807`.

| Dimension | Estimate |
|-----------|----------|
| Risk | **High** — loses P16-I/P16-O trial UX, SSO parity work, marker strings |
| Time | 30–60 minutes + re-validation |
| Files touched | Many |

Does not address root cause; reintroduces old UX debt.

---

## Recommendation

**Option A.** Single-line import restore matches extraction oversight exactly. Smallest diff, lowest risk, immediate queue recovery.

---

*End of P16-W Phase 5*

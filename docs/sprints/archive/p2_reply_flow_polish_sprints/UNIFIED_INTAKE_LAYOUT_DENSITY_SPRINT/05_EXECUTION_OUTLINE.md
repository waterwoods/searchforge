# Execution Outline

## Workstreams

1. **Audit** — Baseline spacing, width, column usage (`UnifiedIntakePage.tsx`).
2. **Customer layout** — Portal shell, width, grouping.
3. **Workbench layout** — Two-column ops layout, sticky queue.
4. **Docs** — Blueprint + specs + report.
5. **Verify** — `npm run build`; optional `vercel --prod`.

## Loop plan (3)

| Loop | Focus |
|------|--------|
| 1 | Page shell + customer portal framing + align pilot alert |
| 2 | Workbench two-column density + sticky queue |
| 3 | Tab chrome polish + final ROI tweak |

## Validation

- `cd ui && npm run build`
- Manual: customer first screen, workbench first screen, 1440px width.

## Deployment

- If `ui/` changed: `cd ui && vercel --prod` (founder-owned token; capture URL if successful).

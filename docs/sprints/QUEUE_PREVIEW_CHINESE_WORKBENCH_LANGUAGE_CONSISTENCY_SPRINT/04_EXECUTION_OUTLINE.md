# Execution Outline

**Sprint:** Queue Preview Chinese + Workbench Language Consistency Sprint  
**Created:** 2026-03-20

---

## Workstreams

1. **Queue readiness + compact preview** — `getQueueReadinessLabel`, `getCompactQueuePreview`, `inferCaseFocusFromText` (broker-facing returns)
2. **Structured field labels** — Use Chinese labels for broker view; `humanizeStructuredField` or broker-specific mapping
3. **Case report + draft readiness** — `getCaseReportOneLiner`, `getDraftReadinessLabel`
4. **Copy case snapshot** — `handleCopyCaseSnapshot` output
5. **Category display** — `CATEGORY_DISPLAY_LABELS` for broker-facing display
6. **Message strings** — Optional: success/error messages (lower priority)

## Loop plan

- **Loop 1:** Queue readiness, compact preview, case focus labels (highest visibility)
- **Loop 2:** Structured field labels, case report one-liner, draft readiness, copy snapshot
- **Loop 3:** Category labels, any remaining high-visibility English; stop if low-value

## Validation plan

- `cd ui && npm run build` after each loop
- Manual inspection: queue cards, case detail, copy-paste output
- No unit test changes (wording-only)

## Risk mitigation

- Wording-only; no logic changes
- Do not touch demo queue loading
- Preserve existing Chinese where already good (已收集, 还缺, 您的下一步, etc.)

---

*Part of Queue Preview Chinese + Workbench Language Consistency Sprint*

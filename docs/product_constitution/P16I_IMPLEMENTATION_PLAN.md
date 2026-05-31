# P16-I Implementation Plan — UI Simplicity Sprint

**Date:** 2026-05-31  
**Authority:** P16-H verdict, UI Simplicity Review, Top 50 Deletions, Contract Simplicity Amendments  
**Constraint:** Hide / collapse / rename / reorder / copy only. No backend, triage, schema, auth, or new capabilities.

---

## Priority Actions → Files

| # | Action | Target file(s) | Risk | Acceptance criteria | Rollback |
|---|--------|----------------|------|---------------------|----------|
| 1 | Hide 客户报送 tab in product_only | `UnifiedIntakePage.tsx` | Low | Trial URL shows workbench only; no customer tab visible | Remove `showCustomerTab` guard |
| 2 | Cancellation-first tagline (not Add-Car) | `ui_copy.json`, `UnifiedIntakePage.tsx` | Low | Header tagline mentions paste/cancel, zero「加车旗舰」 | Revert ui_copy trial keys |
| 3 | Paste above fold | `BrokerWorkbenchTab.tsx` | Medium | Paste textarea visible without scroll on 1440×900 product_only | Restore Col order |
| 4 | Remove tab suffix subtitles | `UnifiedIntakePage.tsx` | Low | Tab labels ≤4 chars, no secondary suffix in product_only | Restore suffix Text nodes |
| 5 | Collapse 整理明细 by default | `BrokerWorkbenchTab.tsx` | Low | Case detail default: glance + draft; detail in collapse | Remove Collapse wrapper |
| 6 | Promote 追加客户补充 near draft | `BrokerWorkbenchTab.tsx` | Medium | Append paste within same viewport as draft copy | Restore original order |
| 7 | Reduce queue filters/badges | `BrokerWorkbenchTab.tsx` | Medium | Queue rows: urgency + one-line preview; no filter bar in trial | Restore Segmented + tags |
| 8 | Remove explanatory paragraphs | `UnifiedIntakePage.tsx`, `BrokerWorkbenchTab.tsx` | Low | ≤1 trust line above fold; no tag wall intro | Restore PILOT_INTRO tags |
| 9 | One primary action per screen | `BrokerWorkbenchTab.tsx` | Medium | Draft copy only primary CTA on case detail | Restore 复制摘要 + status radio |
| 10 | Progressive disclosure | All intake components | Low | Lab mode unchanged when `VITE_UNIFIED_INTAKE_PRODUCT_ONLY` unset | Env flag off |

---

## Additional product_only hides (Top 20 subset)

| Action | File | Rollback |
|--------|------|----------|
| Hide 返回工作台 | `AppLayout.tsx` | Remove productOnlyUi guard |
| Hide 显示产品说明 | `UnifiedIntakePage.tsx` | Restore link block |
| Merge 练习场景 into demo card | `BrokerWorkbenchTab.tsx` | Split cards again |
| Hide 复制摘要 | `BrokerWorkbenchTab.tsx` | Show button |
| Status radio → overflow menu | `BrokerWorkbenchTab.tsx` | Inline Radio.Group |
| Hide follow-up CRM block | `BrokerWorkbenchTab.tsx` | Remove `!productOnlyUi` guard |
| Hide queue「与客户报送同源」 | `BrokerWorkbenchTab.tsx` | Restore Card extra |
| Single queue list (no 立即/等待 split) | `BrokerWorkbenchTab.tsx` | Restore sections |
| Hide founderQueue N/13 after load | `BrokerWorkbenchTab.tsx` | Always show Tag |
| document.title → 办公室工作台 | `ui_copy.json` | Revert title key |

---

## Deferred (documented, not shipped)

- Customer portal message-first redesign (tab hidden instead)
- Dark header → minimal white (medium risk, low ROI)
- Pagination hide when ≤50 (shipped if trivial)
- Full queue card tag strip removal in lab mode

---

## Validation

```bash
bash scripts/guardrail_inbox_triage.sh
source scripts/with_node22_path.sh && cd ui && VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1 VITE_API_BASE_URL=https://fiqa-api-g7zatxrycq-uw.a.run.app npm run build
```

Inspect `/workbench/unified-intake` in preview — paste above fold, one tab, cancellation copy.

---

*End of P16-I Implementation Plan*

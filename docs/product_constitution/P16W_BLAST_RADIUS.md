# P16-W Phase 4 — Blast Radius

**Date:** 2026-06-01  
**Pre-fix bundle:** `index-CKPYkrkL.js`

---

## Screen impact

| Screen | Pre-fix | Trigger | Notes |
|--------|---------|---------|-------|
| **Broker workbench shell** | ✅ Loads | Page mount | Paste area, scenario chips, header render |
| **Customer entry** | ✅ N/A | — | Tab hidden in product_only; route `?tab=customer` redirects to broker; does not call `getCompactQueuePreview` |
| **Queue list** | ❌ Crash | Demo queue, refresh, any case in sidebar | `renderRecentCaseCard` → line 730 |
| **Case detail** | ⚠️ Partial | After queue crash | If case opened via paste→triage without queue render, detail panel works; demo queue path crashes before stable navigation |
| **Draft panel** | ⚠️ Partial | Paste→triage path | Works when triage completes without queue cards mounting first |
| **Follow-up** | ⚠️ Partial | Requires open case | Blocked when queue crash prevents case selection from sidebar |

---

## Failure modes observed

| Action | Result (pre-fix) |
|--------|------------------|
| Open Preview URL | PASS |
| Paste + 开始整理 (no queue) | PASS — triage + draft render |
| 加载演示队列 | **FAIL** — ReferenceError |
| 取消/付款风险 → 开始整理 | PASS (if queue empty) |
| 缺材料跟进 → 开始整理 | PASS |
| 加车报价 → 开始整理 | PASS |
| 刷新列表 (with existing cases) | **FAIL** — same ReferenceError |

---

## product_only vs full UI

Both modes crash: `getCompactQueuePreview` is called **before** the `productOnlyUi` early return in `renderRecentCaseCard`. The product-only simplified card UI never uses `compactPreview`, but the call still executes.

---

## API / backend

No impact. `guardrail_inbox_triage.sh` PASS — engine and API unaffected.

---

*End of P16-W Phase 4*

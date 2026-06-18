# P16 Card Presentation Audit

**Surface:** Office Workbench queue cards in **product-only** mode (`isUnifiedIntakeProductOnlyUi()`)

---

## Before

Product-only `renderRecentCaseCard()` showed:

| Element | Shown |
|---------|-------|
| Urgency tag | Yes |
| Active “当前” tag | Yes |
| `source_text` preview | Yes (90 chars) |
| Vehicle summary | **No** |
| Case ID | **No** |
| Submitted status | **No** |
| Missing fields | **No** |
| Office next step (中文) | **No** |

**Broker scan time:** Must open each card → **>30s** to find Tesla submit in noisy queue.

Non–product-only cards already included AddCar strip, case ID, readiness tags, compact preview, next step — but pilot hides that branch.

---

## Gap vs success criteria

Broker must see **without opening**:

1. Vehicle — `primary_vehicle_summary` or `buildOfficeCaseHeadline()`
2. Case ID — `formatQueueCaseIdShort(case_id)`
3. Submitted status — `addCarQueueStatusPhase` + green “已正式送达办公室”
4. Missing fields — `still_needed_fields` → 待补问
5. Next step — `buildOfficeNextAction()` (中文 office step)

---

## After (minimal product-only card)

| Element | Implementation |
|---------|----------------|
| Readiness + submitted tags | `getQueueReadinessLabel`, formal phase tag |
| Add-car status strip | Reuse `AddCarCaseStatusStrip` |
| Vehicle headline | `primary_vehicle_summary` \|\| `buildOfficeCaseHeadline` |
| Case ID | Monospace, copyable, short format |
| Missing fields | Orange 待补问 line (≤4 fields) |
| Next step | `buildOfficeNextAction` preview (56 chars) |
| Non–add-car fallback | `getCompactQueuePreview` |

**Clutter control:** Dropped raw `source_text` as primary headline for add-car; kept one secondary line for non–add-car only.

---

## Visual hierarchy

```
[已报送办公室] [已正式送达办公室]
AddCarCaseStatusStrip
2024 Tesla Model Y          ← bold
服务记录编号：ea74…          ← mono
待补问：电话
办公室侧下一步：联系客户补齐…
```

Estimated broker identification time: **≤5 seconds** when case is in first screen.

---

## Audit verdict

Presentation fix is **UI-only**, reuses existing office copy helpers, no new components beyond wiring existing strips into product-only branch.

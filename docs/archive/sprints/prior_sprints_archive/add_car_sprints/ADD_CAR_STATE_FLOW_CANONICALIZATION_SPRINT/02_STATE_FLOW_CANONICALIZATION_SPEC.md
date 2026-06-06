# Add-Car state / flow canonicalization spec

## Current inconsistency (evidence-based)

- **Lifecycle vs strip:** `lifecycle_status` values are mapped in `UnifiedIntakePage.tsx` (`LIFECYCLE_STATUS_LABELS`), but the **submitted-phase** strip used **“办公室处理队列中”** while lifecycle **office_followup** used **“办公室跟进”**—two metaphors for “office is working it.”
- **Generic intake:** For non–Add-Car, a small `Tag` only distinguished `handoff_pending` vs a generic “信息收集中,” **ignoring** `handed_off` / `office_followup`—weaker parity with the strip vocabulary.
- **Next-action headings:** Result card uses **“办公室侧下一步（系统整理）”** (`add_car_broker_next_step_heading`); workbench queue preview used a bare **“下一步：”**—same field (`broker_next_step`), **different framing**, weaker “one record” feel.
- **Customer suggested question:** Progress card used **“下一步（系统建议）”** while the Add-Car lane uses **“您这边下一步”**—parallel concepts, **different heading family**.

## Target canonical state model (practical, API-aligned)

Map existing API fields; **do not** add new lifecycle enums in this sprint.

| Source | Canonical customer/office-facing label | Notes |
|--------|----------------------------------------|--------|
| `lifecycle_status: collecting` | **信息收集中** | Matches outline “collecting.” |
| `lifecycle_status: handoff_pending` | **资料已齐 · 可提交** | Task-clear: ready to submit to office. |
| `lifecycle_status: handed_off` | **已交办公室** | Record is in office queue. |
| `lifecycle_status: office_followup` | **办公室处理中** | Office-owned processing / follow-up. |
| `quote_ready_status: need_more` | **整理度：信息不足** | “待补充” lives in **仍缺 / 待补充** chips. |
| `quote_ready_status: almost_ready` | **整理度：差一点** | |
| `quote_ready_status: quote_ready` | **整理度：可报价** | Aligns with business “可报价.” |
| Submitted strip (handed_off, no office_followup) | **办公室处理中** | Single phrase for “in office hands” after submit (replaces “办公室处理队列中”). |

## Target canonical next-action model

| Owner | UI role | Config / copy |
|-------|---------|----------------|
| **客户** | What the customer should do next (rule lane + optional `next_best_question`) | `add_car_customer_next_lane_heading`, `portal_customer_next_suggested_heading` |
| **办公室** | What the broker should do (`broker_next_step`) | `add_car_broker_next_step_heading`, `generic_broker_next_step_heading`, `office_workbench_broker_next_preview_label` (queue preview prefix) |

## Target continuity model

- **Same caption** for the status strip on portal progress, result card, and workbench: `add_car_status_strip_label` (default **当前状态**).
- **Same record label** for case id: `add_car_case_record_id_label` (**服务记录编号**).
- **Same office next-step vocabulary** in closure card and queue row: broker heading family + preview prefix.

## Tech-fit check summary

| Layer | Fit | Main risk |
|-------|-----|-----------|
| **Frontend** | **Yes** for this phase. `UnifiedIntakePage.tsx` already centralizes strips, headings, and workbench cards; risk is **size/complexity** if logic keeps growing without later extraction (outline §9.1 / §10.2). |
| **Backend** | **Yes.** `triage.py` already exposes `lifecycle_status`, `broker_next_step`, `quote_ready_status`, `collection_stage`, structured fields. Risk: **monolith growth** in `triage.py` (outline §9.2)—mitigate with future record/state modules, not this sprint. |
| **Config** | **Yes.** `ui_copy.json` + `clientConfig.ts` are the right place for canonical **words**; remaining gap is deeper **behavior** still in code. |

**Overall:** Stack fits **Stage A → sellable pilot** per master outline §10.1; no stack replacement.

## Acceptance criteria

- [ ] Canonical vocabulary documented in this file matches visible UI for Add-Car strip + lifecycle tags.
- [ ] Workbench queue **broker_next_step** line uses the same **office next-step** framing as the customer result card (via config).
- [ ] Generic intake lifecycle `Tag` uses the **same map** as the status strip when `lifecycle_status` is set.
- [ ] `cd ui && npm run build` passes after UI changes.

# WORKBENCH DETAIL PARITY — Spec

## Current office-side weakness (pre-sprint)

- Status strip and **加车 · 接手就绪度** panel already echoed lifecycle, but **formal “送达”** could be confused with “case_id exists” (record can persist before customer submits).
- **No compact “报送与送达” block** with yes/no formal delivery, **current接手状态**, and **bounded time** in one scan.
- **Process owner** (`addCarNextOwnerLine`) lived on the customer rail but was not echoed on the office detail surface.

## Target office-side parity model

| Dimension | Target |
|-----------|--------|
| 状态 | Same lifecycle vocabulary as customer strip (`collecting` / `handoff_pending` / `handed_off` / `office_followup`). |
| 已送达 / 已接手 | **Formal送达** = `lifecycle_status` ∈ {`handed_off`, `office_followup`} (aligned with `addCarQueueStatusPhase` → `submitted`). Not inferred from `case_id` alone. |
| 时间 | Show **记录创建** / **最近更新** from API ISO strings only; localized display, no invented events. |
| 还缺什么 | Existing tags + readiness mirror; unchanged this sprint beyond clearer mental model. |
| 下一步 | **broker_next_step** (existing) + **流程主要负责方** = `addCarNextOwnerLine` (shared with customer rail). |

## Submitted/received observability goal

- Answer **正式送达办公室：是/否** from lifecycle, not from persistence alone.
- When `handoff_pending` or `collecting`, show **short honest notes** (client-pack copy).
- When lifecycle missing but `case_id` exists, show a **cautious** one-liner (no fake precision).

## Acceptance criteria

1. Add-Car office detail shows a **报送与送达** panel: formal yes/no, optional接手状态 label, optional timestamps, process owner line.
2. **`isFormalSubmissionToOfficeComplete`** treats **`handoff_pending` / `collecting`** as **not** formally submitted even if `case_id` exists (customer + office same story).
3. **复制 case 摘要** for Add-Car includes formal送达,接手状态, times, process owner, then broker next step.
4. Build passes; no new insurance-only hardcoding beyond existing Add-Car paths.

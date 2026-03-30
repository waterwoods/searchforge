# WORKBENCH DETAIL PARITY SPRINT — Final Report

## Implemented

1. **`OfficeWorkbenchAddCarSubmissionSnapshot`** on broker workbench detail (Add-Car only): **正式送达办公室** yes/no from `addCarQueueStatusPhase` (lifecycle `handed_off` / `office_followup` vs intake), **当前接手状态** tag label, contextual notes for `handoff_pending` / `collecting` / missing lifecycle, **记录创建** and **最近更新** when ISO timestamps parse, **流程主要负责方** via shared **`addCarNextOwnerLine`**.
2. **`isFormalSubmissionToOfficeComplete`** fix: **`handoff_pending` and `collecting` override `case_id`** so customer/office steps and “formal submit” match (record can exist before formal submit).
3. **`handleCopyCaseSnapshot`**: Add-Car lines for formal送达,接手状态, timestamps, process owner, then existing broker next step.
4. **`UiCopy` + defaults + `chen_kui` client pack** for new office strings.

## Partial / backend-dependent

- **True “submitted-at” event** is not modeled; only **`created_at` / `updated_at`** from persisted cases (honest bound).
- Legacy cases with **empty `lifecycle_status`** rely on the cautious copy + status strip; full parity depends on backfill or always-populated lifecycle.

## Recommended next sprint

- Optional **explicit `submitted_at`** (or office-received marker) in API when product is ready—keep UI ready to display one bounded field.
- **Queue card** one-line time/正式送达 for scan without opening detail (small follow-up).

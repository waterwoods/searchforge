# Final report — HANDOFF STATE STABILITY + SUBMITTED SIGNAL

## What was implemented

- **`isFormalSubmissionToOfficeComplete`** (`ui/src/components/intake/AddCarRecordSummaryRail.tsx`): true when `case_id` is set or `lifecycle_status` is `handed_off` / `office_followup`—explicitly **not** equivalent to `handoff_ready`.
- **Customer portal** (`ui/src/pages/UnifiedIntakePage.tsx`): Replaced closure/input gating that used `handoff_ready` with **`formalSubmissionComplete`** so `handoff_pending` keeps the submit lane and progress card until persist.
- **`computeAddCarFlowStep`**: Step 3 only after formal submission complete (not merely `handoff_ready`).
- **Right rail**: Completion hints and “why here” copy distinguish office-received vs ready-to-submit.
- **Toasts**: Suppress misleading “已提交” success toast for Add-Car when `handoff_pending` and no `case_id`; toast on `case_id` as before.
- **Closure**: Optional **送达办公室时间** line from `triage.created_at` when present.
- **Workbench queue**: Add-Car branch returns **已报送办公室** for `handed_off` / `office_followup`.
- **Copy**: `portal_submitted_at_prefix` in `ui/src/api/clientConfig.ts` defaults + `configs/clients/chen_kui/ui_copy.json`.

## What remains partial

- **Office “physically opened the case”** is not modeled—only **persisted receipt** (`case_id` / `created_at`).
- **Dual-write / PG** may mirror cases; UI still keys off JSON/API shape.
- Legacy or edge cases with malformed `lifecycle_status` fall back to existing normalization in `case_store`.

## What still depends on backend/state quality

- Formal submission requires **`persist_case` path** returning `case_id` (unchanged contract).
- **`created_at`** visibility depends on save_case including it on the returned payload (already true for new cases).

## Recommended next sprint

- **Broker workbench case header**: same `created_at` + lifecycle chip in detail view for parity with portal closure.
- Optional: explicit **`submitted_at`** field only if product requires audit-grade separation from `created_at` (would be a small schema/API addition—not done here).

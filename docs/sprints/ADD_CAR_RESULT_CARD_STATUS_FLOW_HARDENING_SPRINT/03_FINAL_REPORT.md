# ADD-CAR RESULT CARD + STATUS FLOW HARDENING — Final report

## What changed

- **Status strip** on Add-Car pre-handoff progress card and post-handoff result card, driven only by existing triage fields (`quote_ready_status`, `lifecycle_status`, `collection_stage`).
- **Case card framing** for Add-Car handoff: eyebrow copy + hint line; optional **服务记录编号** when `case_id` exists (copyable).
- **办公室侧下一步** block when `broker_next_step` is non-empty (Add-Car handoff).
- **Boundary section** “本条记录 vs 新事项” with configurable `add_car_boundary_hint` before existing `handoff_new_issue_hint`.
- **Client-config** optional strings for the above (`ui/src/api/clientConfig.ts` + defaults).

## What was verified

- `cd ui && npm run build` — pass.
- `bash scripts/guardrail_inbox_triage.sh` — pass (13/13 HT + batteries).

## What remains

- Broker workbench tab could receive the same status-strip pattern for parity (out of minimal sprint scope).
- If backend does not populate `lifecycle_status` / `broker_next_step` on some paths, the strip will still show identity + quote readiness but fewer lifecycle chips.

## Recommended next sprint

**Workbench parity + case ID deep link** — mirror the Add-Car status strip and record reference on the office workbench case header for end-to-end “same case” trust.

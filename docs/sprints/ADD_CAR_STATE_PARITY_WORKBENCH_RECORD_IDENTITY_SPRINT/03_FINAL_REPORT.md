# ADD-CAR STATE PARITY + WORKBENCH RECORD IDENTITY — Final report

## What changed

- Added `getOfficeLifecycleTag()` in `UnifiedIntakePage.tsx` so workbench uses the **same** `LIFECYCLE_STATUS_LABELS` as the customer `AddCarCaseStatusStrip` (fixes `handed_off` → **已交办公室** instead of **已移交**).
- Workbench **queue cards**: monospace **服务记录编号：{case_id}** with Ant Design `copyable`.
- Workbench **opened case**: same id block + `office_workbench_case_id_hint` under it.
- Replaced queue button label with configurable **`office_workbench_open_record_cta`** (default 打开本条服务记录).
- Extended `UiCopy` / `DEFAULT_UI_COPY` and **Chen Kui** `ui_copy.json` with `office_workbench_case_id_hint` and `office_workbench_open_record_cta`.

## What improved

- **Record continuity:** office can match customer closure **without opening** the row (id visible on card).
- **State language parity:** lifecycle chips align with customer-facing strip semantics.
- **Product language:** less “case” jargon in the primary queue CTA; more **服务记录** framing.

## What remains

- Customer **pre-handoff** still has no case id (only after persistence returns `case_id`) — backend/product truth unchanged.
- Queue rows do not embed the full **AddCarCaseStatusStrip** chip row (intentionally scoped out to avoid clutter).
- **FLOW** still chat-shaped; this sprint does not change turn structure.
- **HANDOFF** engine reply polish remains the scorecard’s **highest** next leverage item.

## Estimated score movement (conservative)

| Dimension | Before | After | Note |
|-----------|--------|-------|------|
| **STATE** | 3 / 5 | **~3.25 / 5** | Workbench parity for id + lifecycle; not full strip-on-queue. |
| **FLOW** | 3 / 5 | **~3.1 / 5** | Slight gain: “where is this record?” clearer when switching tabs. |

## Recommended next sprint

**Add-Car handoff / reply polish** (scorecard primary): shorter acknowledgements, `already_sent` edge behavior — raises HANDOFF and perceived FLOW more than further STATE chrome.

**Runner-up:** optional **mini status strip** on queue rows for Add-Car-only rows if user testing shows cards still too dense to scan.

## Validation

- `npm run build` (UI): PASS.
- `bash scripts/guardrail_inbox_triage.sh`: PASS.
- Manual UI tab walk: not executed in this session (inferred safe from compile + guardrails).

## Timing

- **Start:** 2026-03-27 (sprint execution)
- **End:** 2026-03-27 (same session)
- **Elapsed:** ~35–45 minutes (audit, implement, build, guardrail, docs)

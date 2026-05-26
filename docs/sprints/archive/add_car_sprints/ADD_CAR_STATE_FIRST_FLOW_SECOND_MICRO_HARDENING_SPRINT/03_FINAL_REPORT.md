# ADD-CAR STATE-FIRST / FLOW-SECOND MICRO-HARDENING — Final report

## What changed

- **Customer (pre-handoff):** Add-Car progress card now includes a **“您这边下一步”** bordered lane derived from `lifecycle_status`, `still_needed_fields`, or `next_best_question`; duplicate generic “下一步（系统建议）” suppressed when this lane is active.
- **Customer (post-handoff Add-Car):** **办公室侧下一步** moved to sit **right after 服务记录编号**, before category / structured panel.
- **Office workbench:** **AddCarCaseStatusStrip** on **queue cards** and **opened record** for Add-Car-shaped cases; queue row lifecycle tag omitted when strip is shown (dedupe).
- **Config:** `add_car_customer_next_lane_heading` in `UiCopy` + Chen Kui `ui_copy.json`; defaults in `clientConfig.ts`.

## What improved

- **STATE:** Same strip component and caption key (`add_car_status_strip_label`) on customer + workbench surfaces.  
- **NEXT ACTION:** Customer and office “next” are **more scannable** and **ordered** (state → record → office next on closure).  
- **CONTINUITY:** Queue and detail **read like the same record** in the same state vocabulary as the portal.

## What remains

- **FLOW** still chat-backed; this sprint does not change interaction model.  
- **Backend population** of `lifecycle_status` / `broker_next_step` on all paths still gates how often the new UI shines.  
- **Browser QA** and guardrail triage script not re-run as part of this micro-sprint.

## Estimated score movement (Add-Car path, conservative)

| Dimension | Before | After | Note |
|-----------|--------|-------|------|
| **STATE** | 3 / 5 | **3.5 / 5** | Clearer cross-surface state + next-action ordering; still dependent on API fields. |
| **FLOW** | 3 / 5 | **3.25 / 5** | Slightly more task-shaped via state-driven next lane; still conversation-centric. |
| **PAGE / HANDOFF** | (unchanged) | — | Not primary targets of this sprint. |

## Recommended next step

Bias to **pilot runs** and **broker dry-run observation**; if engineering time is limited, next **code** increment is optional **reply / already_sent** handoff behavior (separate sprint theme)—not more layout churn.

## Sprint timing

- **Start:** 2026-03-27 (session)  
- **End:** 2026-03-27 (session)  
- **Elapsed:** ~15–25 minutes (docs + implementation + `npm run build`)

# ADD-CAR STATE + FLOW CANONICALIZATION — Final report

## What changed

- Documented a **practical canonical** state / next-action / continuity model in `02_STATE_FLOW_CANONICALIZATION_SPEC.md` (aligned to master outline: state-driven flow, one record, client pack for words).
- **Unified lifecycle wording:** `office_followup` label **办公室跟进 → 办公室处理中**; submitted-phase **handed_off** chip **办公室处理队列中 → 办公室处理中** (matches closure language).
- **Generic intake lifecycle tag** now uses the same `LIFECYCLE_STATUS_LABELS` map as strips (supports `handed_off`, `office_followup`, etc., not only two hardcoded strings).
- **Next-action scanability:** progress card `next_best_question` heading wired to **`portal_customer_next_suggested_heading`** (“您这边下一步（系统建议）”) — same family as **您这边下一步**.
- **Workbench continuity:** queue preview prefix **`office_workbench_broker_next_preview_label`** default **办公室侧下一步：** — aligns with **办公室侧下一步（系统整理）** on the customer result card.

## What improved

- **STATE:** Fewer competing phrases for “office is working it”; lifecycle chip parity on non–Add-Car progress card.
- **FLOW:** Customer “next” hints read as one ownership lane; office queue shows broker next step with the same vocabulary as the handoff card.
- **Record continuity:** Same config keys already governed strip caption and case id; broker preview now echoes office-side heading family.

## What remains

- **FLOW** still chat-centric at the interaction model (scorecard): needs further task-first UX work, not just copy.
- **Backend** population of `lifecycle_status` / `broker_next_step` on all edge paths (scorecard gap)—not fully audited this sprint.
- **`triage.py` size** remains the long-term structural risk (outline §9.2).

## Estimated score movement

| Dimension | Before (scorecard) | After (estimate) | Why |
|-----------|-------------------|------------------|-----|
| **STATE** | 3 / 5 | **3.25 / 5** | Wording parity + generic lifecycle tag fix; no new backend state machine. |
| **FLOW** | 3 / 5 | **3.15 / 5** | Clearer customer/office next labels; thread metaphor unchanged. |

## Recommended next sprint

**Handoff reply polish + `already_sent` behavior** (per scorecard `03_FINAL_REPORT.md`) — highest leverage for perceived FLOW/HANDOFF without architecture churn.

**Runner-up:** Workbench/detail **full broker_next_step** block styling parity with customer card (optional micro-pass).

## Sprint timing

- **Start:** 2026-03-28 (this session)
- **End:** 2026-03-28 (this session)
- **Elapsed:** ~25–40 minutes (docs + targeted UI/config + build)

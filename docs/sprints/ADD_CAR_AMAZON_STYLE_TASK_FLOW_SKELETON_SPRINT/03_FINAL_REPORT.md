# ADD-CAR AMAZON-STYLE TASK FLOW SKELETON SPRINT — Final report

## What changed

- **Flow track:** Default and Chen Kui client copy for steps **2** and **3** aligned to master outline (**补齐关键信息**, **办公室接手处理**); optional **加车办理进度** label when Add-Car path is active.
- **Skeleton meta block:** Pre-handoff Add-Car progress card adds **本步说明** + dynamic completion copy + **下一步主要负责** (customer-scoped) from `lifecycle_status` / `still_needed_fields` / `next_best_question`.
- **Record-first:** **服务记录编号** shown in pre-handoff Add-Car progress when `lastCaseId` exists.
- **Thread de-emphasis:** Pre-handoff Add-Car conversation moved behind **Collapse** (default closed), same family as post-handoff transcript pattern.
- **Handoff office ownership:** `add_car_broker_next_step_heading` and post-handoff divider copy tightened to reference **接手 / 第三步**.
- **Types/defaults:** `clientConfig.ts` extended for new optional keys; `DEFAULT_UI_COPY` updated.

## What improved

- **Task vs chat:** Progress + completion + owner scan before opening the bubble transcript.
- **Alignment:** UI language matches **Amazon-style Task Flow Skeleton (Add-Car v1)** in the master outline.
- **Pilot-safe:** Bounded to customer entry + config; no triage engine or schema changes.

## What remains weak

- **Step granularity** is still **3 coarse beats** (not sub-steps inside step 2).
- **Owner** for office is explicit only after handoff (pre-handoff is correctly customer-heavy).
- **Non–Add-Car** paths keep an expanded thread (intentional scope boundary).

## Estimated score movement (conservative)

| Dimension | Before → After | Why |
|-----------|----------------|-----|
| **FLOW** | ~6.5 → ~7.5 | Clearer macro steps, collapsed thread, explicit completion/owner strip for Add-Car. |
| **STATE** | ~7 → ~7.25 | Same backend state; slightly stronger **record id** surfacing and step-3 wording in closure. |

## Recommended next sprint

**Pilot validation / observation sprint:** run real or realistic broker–customer sessions against the skeleton; log where confusion remains (esp. `handoff_pending` vs customer mental model, and attachment paths).

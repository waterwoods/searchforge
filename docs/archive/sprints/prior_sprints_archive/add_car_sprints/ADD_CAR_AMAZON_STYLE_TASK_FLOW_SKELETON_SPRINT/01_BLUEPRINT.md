# ADD-CAR AMAZON-STYLE TASK FLOW SKELETON SPRINT — Blueprint

## Sprint goal

Strengthen the **Add-Car** customer path so it reads as an **Amazon-style task-flow skeleton**: clear task, current step, completion logic, next action, and **who owns** the next action—without redesigning the whole product or polishing generic UI.

## Why now

Add-Car is the flagship wedge; service record and state-driven flow are the target spine. The remaining gap is **chat-shaped progression** versus **task-shaped progression**. This sprint is the last bounded hardening pass on that skeleton before shifting emphasis to **real pilot validation**.

## Read-first docs

1. `docs/UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md` — especially **§4.2** and **Amazon-style Task Flow Skeleton (Add-Car v1)**.
2. `docs/PROJECT_TRUTH_SWITCH.md` — scope, safe-edit zones, validation gate.
3. (Optional context) `docs/sprints/MATURE_SKELETON_COMMERCIAL_INTAKE_BACKBONE/` — flow backbone language.

## Scope

- Add-Car **step visibility** aligned to the three macro steps (开始报送 → 补齐关键信息 → 办公室接手处理).
- **Completion-condition** and **next-owner** copy in the pre-handoff progress surface.
- **Thread de-emphasis** on Add-Car pre-handoff (collapsed by default; progress and record id first).
- **Client pack / defaults** for flow labels and office-side heading on handoff.
- Lightweight sprint documentation (this folder only).

## Non-scope

- Full workflow engine, CRM/platform work, database redesign, non–Add-Car expansion, broad visual redesign, carrier integration, heavy `triage.py` changes.

## Target outcome

A broker or customer can **scan** the Add-Car path and answer: *which step am I in, why am I still here, what finishes this step, who acts next,* with the **service record** and **state card** more primary than the message thread.

# Add-Car task-flow skeleton spec (Amazon-style, Stage 1)

## Current weakness (pre-sprint)

- The **three-step macro model** from the master outline was only partially reflected in UI defaults (step labels were “收齐报价要点 / 转交办公室” rather than **补齐关键信息 / 办公室接手处理**).
- **Why the case is still on-step** and **who owns the next move** relied heavily on the user reading the **chat thread** and scattered tags.
- The **thread** remained as visually dominant as the **progress card** during Add-Car intake, so the page still felt “chat progression” first.

## Target three-step skeleton (customer-facing)

| Step | Meaning | Transition in | What moves it forward | Primary owner of next action |
|------|---------|---------------|------------------------|------------------------------|
| **1 — 开始报送** | Intake anchored; user has chosen Add-Car / started input | Empty → first interaction | First customer submit / starter | **Customer** (system guides) |
| **2 — 补齐关键信息** | Record exists in flight; gaps and next questions explicit | After first turn until `handoff_ready` | Customer supplies missing fields / answers; system updates state | **Customer** supplies; **system** surfaces gaps/`下一步` |
| **3 — 办公室接手处理** | Stage 1 handoff satisfied; office continues on the record | `handoff_ready` on last system turn | Office follow-up (customer may append on **same record** only) | **Office** |

*Note:* Step indices in the UI remain **coarse** (1 = before conversation, 2 = in progress, 3 = handed off)—no new workflow engine; mapping matches the **macro** outline in `UNIFIED_INTAKE_PRODUCT_AND_TECHNICAL_MASTER_OUTLINE.md`.

## Completion-condition clarity (target)

- **Step 2:** Surface explicit text for: still missing structured fields, “answer next question,” or “ready to submit to office” (`handoff_pending`).
- **Step 2 → 3:** Customer completes **formal submit** when system says ready; then copy states **办公室接手** and shows office-side next step when present.

## Next-action ownership (target)

- **Pre-handoff Add-Car:** One block labels **下一步主要负责** with **客户** and a concrete action (补充 / 提交).
- **Post-handoff Add-Car:** **办公室侧下一步** heading makes **office ownership** explicit; divider **第三步 · 办公室已接手** ties closure to the skeleton.

## Thread de-emphasis (target)

- **Pre-handoff Add-Car:** Thread inside a **collapsed** panel by default; **progress card** (status, record id when available, skeleton copy, customer next lane) stays open above.
- **Post-handoff:** Unchanged pattern (already collapsed transcript).

## Acceptance criteria

1. Flow track labels match master skeleton wording for steps 2 and 3 (config + defaults).
2. Add-Car path shows **加车办理进度** when Add-Car is active (configurable).
3. Pre-handoff Add-Car progress card includes **本步说明** + **下一步主要负责** derived from triage state.
4. **服务记录编号** appears in the pre-handoff progress card when `case_id` is known.
5. Pre-handoff Add-Car **thread** is collapsed by default.
6. `cd ui && npm run build` passes.
